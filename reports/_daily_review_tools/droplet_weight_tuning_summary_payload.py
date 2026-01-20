#!/usr/bin/env python3
"""
Droplet-native weight tuning summary (shadow-only).

Writes:
  reports/WEIGHT_TUNING_SUMMARY_<DATE>.md

Env:
  REPORT_DATE=YYYY-MM-DD (required)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path("/root/stock-bot")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict):
                    out.append(r)
    except Exception:
        return []
    return out


def _date_match(ts: Any, date_str: str) -> bool:
    s = str(ts or "")
    return date_str in s


def _fmt_money(x: float) -> str:
    return f"{x:,.2f}"


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def main() -> int:
    date = os.getenv("REPORT_DATE", "").strip()
    if not date:
        raise SystemExit("REPORT_DATE required")

    # Inputs
    shadow = _read_jsonl(ROOT / "logs/shadow.jsonl")
    attrib = _read_jsonl(ROOT / "logs/attribution.jsonl") if (ROOT / "logs/attribution.jsonl").exists() else []
    risk = {}
    try:
        risk = json.loads((ROOT / "state/symbol_risk_features.json").read_text(encoding="utf-8"))
    except Exception:
        risk = {}

    score_compare = [r for r in shadow if r.get("event_type") == "score_compare" and _date_match(r.get("ts"), date)]
    shadow_pnl = [r for r in shadow if r.get("event_type") in ("shadow_pnl_update", "shadow_exit") and _date_match(r.get("ts"), date)]

    # PnL by symbol (real)
    real_pnl_by_symbol: Dict[str, float] = {}
    for r in attrib:
        if not _date_match(r.get("ts"), date):
            continue
        sym = str(r.get("symbol") or "").upper()
        if not sym:
            continue
        real_pnl_by_symbol[sym] = real_pnl_by_symbol.get(sym, 0.0) + float(r.get("pnl_usd") or 0.0)

    # PnL by symbol (shadow): realized exits + latest unrealized
    shadow_realized: Dict[str, float] = {}
    shadow_unreal: Dict[str, float] = {}
    for r in shadow_pnl:
        sym = str(r.get("symbol") or "").upper()
        if not sym:
            continue
        if r.get("event_type") == "shadow_exit":
            shadow_realized[sym] = shadow_realized.get(sym, 0.0) + float(r.get("realized_pnl_usd") or 0.0)
        if r.get("event_type") == "shadow_pnl_update":
            shadow_unreal[sym] = float(r.get("unrealized_pnl_usd") or 0.0)
    shadow_pnl_by_symbol = {s: shadow_realized.get(s, 0.0) + shadow_unreal.get(s, 0.0) for s in set(shadow_realized) | set(shadow_unreal)}

    # Vol/beta features
    feats = (risk.get("symbols") or {}) if isinstance(risk, dict) else {}

    def _feat(sym: str, k: str) -> float:
        v = feats.get(sym, {}) if isinstance(feats, dict) else {}
        if isinstance(v, dict):
            try:
                return float(v.get(k) or 0.0)
            except Exception:
                return 0.0
        return 0.0

    # Classify symbols
    syms = sorted(set(real_pnl_by_symbol) | set(shadow_pnl_by_symbol))
    v2_better = []
    v1_better = []
    both_bad = []
    both_good = []
    for s in syms:
        rp = real_pnl_by_symbol.get(s, 0.0)
        sp = shadow_pnl_by_symbol.get(s, 0.0)
        if sp > rp:
            v2_better.append(s)
        elif rp > sp:
            v1_better.append(s)
        if rp <= 0 and sp <= 0:
            both_bad.append(s)
        if rp > 0 and sp > 0:
            both_good.append(s)

    # Aggregate evidence for v2_better vs v1_better
    def _agg(sym_list: List[str]) -> Dict[str, float]:
        vols = [_feat(s, "realized_vol_20d") for s in sym_list]
        betas = [_feat(s, "beta_vs_spy") for s in sym_list]
        return {"vol_20d_mean": _mean(vols), "beta_mean": _mean(betas)}

    a_v2 = _agg(v2_better)
    a_v1 = _agg(v1_better)

    # Pull current weights version
    try:
        from config.registry import COMPOSITE_WEIGHTS_V2
        w = dict(COMPOSITE_WEIGHTS_V2) if isinstance(COMPOSITE_WEIGHTS_V2, dict) else {}
    except Exception:
        w = {}

    lines: List[str] = []
    lines.append(f"# WEIGHT_TUNING_SUMMARY_{date}")
    lines.append("")
    lines.append("## Data source")
    lines.append("- `Droplet local logs/state`")
    lines.append(f"- generated_utc: `{datetime.now(timezone.utc).isoformat()}`")
    lines.append("")
    lines.append("## Snapshot")
    lines.append(f"- symbols_with_real_pnl: `{len(real_pnl_by_symbol)}`")
    lines.append(f"- symbols_with_shadow_pnl: `{len(shadow_pnl_by_symbol)}`")
    lines.append(f"- score_compare_events: `{len(score_compare)}`")
    lines.append("")
    lines.append("## Classification (shadow vs real)")
    lines.append(f"- v2_better: `{len(v2_better)}`")
    lines.append(f"- v1_better: `{len(v1_better)}`")
    lines.append(f"- both_good: `{len(both_good)}`")
    lines.append(f"- both_bad: `{len(both_bad)}`")
    lines.append("")
    lines.append("## Empirical risk profile (means)")
    lines.append(f"- v2_better vol_20d_mean: `{a_v2['vol_20d_mean']:.4f}` | beta_mean: `{a_v2['beta_mean']:.3f}`")
    lines.append(f"- v1_better vol_20d_mean: `{a_v1['vol_20d_mean']:.4f}` | beta_mean: `{a_v1['beta_mean']:.3f}`")
    lines.append("")
    lines.append("## Current COMPOSITE_WEIGHTS_V2 (shadow-only)")
    lines.append(f"- version: `{w.get('version','')}`")
    # show key weights
    keys = [
        "vol_bonus_max",
        "low_vol_penalty_max",
        "beta_bonus_max",
        "uw_bonus_max",
        "premarket_align_bonus",
        "premarket_misalign_penalty",
        "regime_align_bonus",
        "regime_misalign_penalty",
        "misalign_dampen",
    ]
    for k in keys:
        if k in w:
            lines.append(f"- {k}: `{w.get(k)}`")
    lines.append("")
    lines.append("## Why these weights (brutally honest)")
    lines.append("- Today’s tuning is driven by observed differences in shadow vs real symbol outcomes and the regime/posture context.")
    lines.append("- We strengthen penalties for **misaligned direction vs posture** and modestly reward **high-vol/high-beta** only when aligned.")
    lines.append("- We add an explicit UW-strength bonus (conviction+trade_count) and a futures/premarket alignment term (SPY/QQQ overnight proxy).")
    lines.append("")
    out_path = ROOT / "reports" / f"WEIGHT_TUNING_SUMMARY_{date}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

