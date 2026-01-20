#!/usr/bin/env python3
"""
Weight Impact Report (V2 composite tuning)
=========================================

Produces:
  reports/WEIGHT_IMPACT_<DATE>.md

Runs on the droplet (preferred) using droplet local logs/state.

Method:
- Use today's shadow `score_compare` events as the evaluation set.
- Recompute v2 score under:
  - BASELINE params (pre-tuning defaults)
  - CURRENT params (config.registry.COMPOSITE_WEIGHTS_V2)
- Compare score shifts and candidate set changes.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path("/root/stock-bot")

# Baseline params matching earlier v2 defaults (pre tuning).
BASELINE_V2_PARAMS: Dict[str, Any] = {
    "version": "baseline_defaults",
    "vol_center": 0.20,
    "vol_scale": 0.25,
    "vol_bonus_max": 0.6,
    "low_vol_penalty_center": 0.15,
    "low_vol_penalty_max": -0.10,
    "beta_center": 1.00,
    "beta_scale": 1.00,
    "beta_bonus_max": 0.4,
    "uw_center": 0.55,
    "uw_scale": 0.45,
    "uw_bonus_max": 0.20,
    "premarket_align_bonus": 0.10,
    "premarket_misalign_penalty": -0.10,
    "regime_align_bonus": 0.5,
    "regime_misalign_penalty": -0.25,
    "posture_conf_strong": 0.65,
    "high_vol_multiplier": 1.15,
    "mid_vol_multiplier": 1.00,
    "low_vol_multiplier": 0.90,
    "misalign_dampen": 0.25,
    "neutral_dampen": 0.60,
}


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    import json

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


def _session_window(date_str: str) -> Tuple[str, str]:
    # Compare as ISO string prefix; droplet logs are ISO timestamps.
    start = f"{date_str}T14:30"
    end = f"{date_str}T21:00"
    return start, end


def _in_window(ts: Any, start_prefix: str, end_prefix: str) -> bool:
    s = str(ts or "")
    return s >= start_prefix and s <= end_prefix


def _table(headers: List[str], rows: List[List[str]]) -> str:
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def main() -> int:
    date = os.getenv("REPORT_DATE", "").strip()
    if not date:
        raise SystemExit("REPORT_DATE is required (YYYY-MM-DD)")

    start_prefix, end_prefix = _session_window(date)
    shadow = _read_jsonl(ROOT / "logs/shadow.jsonl")
    events = [
        r
        for r in shadow
        if str(r.get("event_type") or "") == "score_compare"
        and str(r.get("symbol") or "")
        and _in_window(r.get("ts"), start_prefix, end_prefix)
    ]

    # Load state for reconstruction when v2_inputs are missing (most historical events).
    try:
        import json

        market_context = json.loads((ROOT / "state/market_context_v2.json").read_text(encoding="utf-8"))
    except Exception:
        market_context = {}
    try:
        import json

        posture_state = json.loads((ROOT / "state/regime_posture_state.json").read_text(encoding="utf-8"))
    except Exception:
        posture_state = {}
    try:
        import json

        risk = json.loads((ROOT / "state/symbol_risk_features.json").read_text(encoding="utf-8"))
    except Exception:
        risk = {}

    # risk features shape varies; accept common layouts
    risk_map: Dict[str, Any] = {}
    if isinstance(risk, dict):
        for k in ("symbols", "symbol_features", "features"):
            if isinstance(risk.get(k), dict):
                risk_map = risk.get(k)  # type: ignore[assignment]
                break
        if not risk_map:
            risk_map = {k: v for k, v in risk.items() if isinstance(v, dict) and k.isalpha() and len(k) <= 6}

    usable = list(events)

    from config.registry import COMPOSITE_WEIGHTS_V2
    from uw_composite_v2 import compute_composite_score_v3_v2

    current_params = dict(COMPOSITE_WEIGHTS_V2) if isinstance(COMPOSITE_WEIGHTS_V2, dict) else {}
    current_version = str(current_params.get("version", ""))

    rows: List[Tuple[str, float, float, float, bool, bool]] = []
    for r in usable:
        sym = str(r.get("symbol") or "").upper()
        v1 = float(r.get("v1_score") or 0.0)
        old_v2 = float(r.get("v2_score") or 0.0)
        v2_in = r.get("v2_inputs") or {}

        # Prefer per-event inputs; otherwise reconstruct from state feature store.
        rv = None
        bt = None
        if isinstance(v2_in, dict):
            try:
                rv = float(v2_in.get("realized_vol_20d")) if v2_in.get("realized_vol_20d") is not None else None
            except Exception:
                rv = None
            try:
                bt = float(v2_in.get("beta_vs_spy")) if v2_in.get("beta_vs_spy") is not None else None
            except Exception:
                bt = None
        if rv is None or bt is None:
            feat = risk_map.get(sym, {}) if isinstance(risk_map, dict) else {}
            if isinstance(feat, dict):
                try:
                    rv = float(feat.get("realized_vol_20d") or 0.0)
                except Exception:
                    rv = 0.0
                try:
                    bt = float(feat.get("beta_vs_spy") or 0.0)
                except Exception:
                    bt = 0.0
            else:
                rv, bt = 0.0, 0.0

        # Rebuild minimal inputs.
        direction = str(v2_in.get("direction") or "neutral").lower() if isinstance(v2_in, dict) else "neutral"
        sentiment = "BULLISH" if direction == "bullish" else ("BEARISH" if direction == "bearish" else "NEUTRAL")
        enriched = {
            "realized_vol_20d": float(rv or 0.0),
            "beta_vs_spy": float(bt or 0.0),
            "conviction": float(v2_in.get("uw_conviction") or 0.0) if isinstance(v2_in, dict) else 0.0,
            "trade_count": int(v2_in.get("trade_count") or 0) if isinstance(v2_in, dict) else 0,
            "sentiment": sentiment,
        }
        mc = {
            "volatility_regime": (v2_in.get("volatility_regime") if isinstance(v2_in, dict) else None) or str(market_context.get("volatility_regime") or "mid"),
            "market_trend": (v2_in.get("market_trend") if isinstance(v2_in, dict) else None) or str(market_context.get("market_trend") or ""),
            "spy_overnight_ret": float(v2_in.get("spy_overnight_ret") or 0.0) if isinstance(v2_in, dict) else float(market_context.get("spy_overnight_ret") or 0.0),
            "qqq_overnight_ret": float(v2_in.get("qqq_overnight_ret") or 0.0) if isinstance(v2_in, dict) else float(market_context.get("qqq_overnight_ret") or 0.0),
        }
        ps = {
            "posture": (v2_in.get("posture") if isinstance(v2_in, dict) else None) or str(posture_state.get("posture") or "neutral"),
            "regime_confidence": float(v2_in.get("posture_confidence") or 0.0) if isinstance(v2_in, dict) else float(posture_state.get("regime_confidence") or posture_state.get("regime_confidence", 0.0) or 0.0),
        }

        base_override = {"score": v1}
        base = compute_composite_score_v3_v2(sym, enriched, regime="mixed", market_context=mc, posture_state=ps, base_override=base_override, v2_params=BASELINE_V2_PARAMS) or {}
        tuned = compute_composite_score_v3_v2(sym, enriched, regime="mixed", market_context=mc, posture_state=ps, base_override=base_override, v2_params=current_params) or {}

        base_v2 = float(base.get("score") or 0.0)
        new_v2 = float(tuned.get("score") or 0.0)
        delta = new_v2 - base_v2
        pass_old = bool(old_v2 >= 3.0)
        pass_new = bool(new_v2 >= 3.0)
        rows.append((sym, base_v2, new_v2, delta, pass_old, pass_new))

    # Deduplicate by symbol, keep max abs delta
    by_sym: Dict[str, Tuple[str, float, float, float, bool, bool]] = {}
    for sym, b, n, d, po, pn in rows:
        cur = by_sym.get(sym)
        if cur is None or abs(d) > abs(cur[3]):
            by_sym[sym] = (sym, b, n, d, po, pn)

    movers = sorted(by_sym.values(), key=lambda x: abs(x[3]), reverse=True)
    entered = [m for m in movers if (not m[4]) and m[5]]
    left = [m for m in movers if m[4] and (not m[5])]

    out_lines: List[str] = []
    out_lines.append(f"# WEIGHT_IMPACT_{date}")
    out_lines.append("")
    out_lines.append("## Data source")
    out_lines.append("- **source**: `Droplet local logs`")
    out_lines.append(f"- **generated_utc**: `{datetime.now(timezone.utc).isoformat()}`")
    out_lines.append(f"- **events_used(score_compare)**: `{len(usable)}`")
    out_lines.append("")
    out_lines.append("## Weight versions")
    out_lines.append(f"- **baseline**: `{BASELINE_V2_PARAMS.get('version')}`")
    out_lines.append(f"- **current**: `{current_version}`")
    out_lines.append("")
    out_lines.append("## Candidate set impact (threshold=3.0)")
    out_lines.append(f"- **entered**: `{len(entered)}`")
    out_lines.append(f"- **left**: `{len(left)}`")
    out_lines.append("")
    out_lines.append("## Top movers (abs score delta, per symbol)")
    top_rows: List[List[str]] = []
    for sym, b, n, d, po, pn in movers[:25]:
        top_rows.append([sym, f"{b:.3f}", f"{n:.3f}", f"{d:+.3f}", "PASS" if po else "SKIP", "PASS" if pn else "SKIP"])
    out_lines.append(_table(["symbol", "baseline_v2", "current_v2", "delta", "old_gate", "new_gate"], top_rows if top_rows else [["(none)", "", "", "", "", ""]]))
    out_lines.append("")

    out_path = ROOT / "reports" / f"WEIGHT_IMPACT_{date}.md"
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

