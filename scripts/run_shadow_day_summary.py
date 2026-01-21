#!/usr/bin/env python3
"""
Shadow Day Summary (v2)
=======================

Inputs:
- logs/shadow_trades.jsonl
- logs/uw_attribution.jsonl (tail)
- state/uw_intel_pnl_summary.json
- state/regime_state.json

Output:
- reports/SHADOW_DAY_SUMMARY_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else datetime.now(timezone.utc).date().isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
            if isinstance(rec, dict):
                yield rec
        except Exception:
            continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    args = ap.parse_args()
    day = args.date.strip() or datetime.now(timezone.utc).date().isoformat()

    shadow_path = Path("logs/shadow_trades.jsonl")
    attrib_path = Path("logs/uw_attribution.jsonl")
    pnl = _read_json(Path("state/uw_intel_pnl_summary.json"))
    regime = _read_json(Path("state/regime_state.json"))

    trades = []
    for rec in _iter_jsonl(shadow_path):
        if _day_utc(str(rec.get("ts") or "")) != day:
            continue
        if str(rec.get("event_type", "")) != "shadow_trade_candidate":
            continue
        trades.append(rec)

    sectors = []
    syms = []
    v2_scores = []
    v1_scores = []
    for r in trades:
        syms.append(str(r.get("symbol", "")))
        v2_scores.append(float(r.get("v2_score", 0.0) or 0.0))
        v1_scores.append(float(r.get("v1_score", 0.0) or 0.0))
        snap = r.get("uw_attribution_snapshot") if isinstance(r.get("uw_attribution_snapshot"), dict) else {}
        sec = ((snap.get("v2_uw_sector_profile") or {}) if isinstance(snap.get("v2_uw_sector_profile"), dict) else {}).get("sector", "UNKNOWN")
        sectors.append(str(sec))

    # Biggest "winners/losers" are best-effort: rank by v2_score (no realized P&L in this log yet)
    ranked = sorted(trades, key=lambda x: float(x.get("v2_score", 0.0) or 0.0), reverse=True)
    top = ranked[:5]
    bottom = list(reversed(ranked[-5:])) if ranked else []

    # UW feature usage summary: count non-zero adjustments
    feat_counts = Counter()
    for r in trades:
        snap = r.get("uw_attribution_snapshot") if isinstance(r.get("uw_attribution_snapshot"), dict) else {}
        adj = snap.get("v2_uw_adjustments") if isinstance(snap.get("v2_uw_adjustments"), dict) else {}
        for k, v in adj.items():
            if k == "total":
                continue
            try:
                if abs(float(v)) > 1e-6:
                    feat_counts[k] += 1
            except Exception:
                continue

    out = Path("reports") / f"SHADOW_DAY_SUMMARY_{day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append(f"# Shadow Day Summary (v2) — {day}")
    lines.append("")
    lines.append("## 1. Overview")
    lines.append(f"- Shadow trade candidates: **{len(trades)}**")
    lines.append(f"- Unique symbols: **{len(set(syms))}**")
    lines.append(f"- Sectors: **{dict(Counter(sectors))}**")
    lines.append("")

    lines.append("## 2. Biggest would-be winners/losers (by v2 score, best-effort)")
    if not trades:
        lines.append("- No shadow trade candidates logged.")
    else:
        lines.append("### Top 5")
        for r in top:
            lines.append(f"- **{r.get('symbol','')}** v2_score={r.get('v2_score')} v1_score={r.get('v1_score')} dir={r.get('direction')}")
        lines.append("")
        lines.append("### Bottom 5")
        for r in bottom:
            lines.append(f"- **{r.get('symbol','')}** v2_score={r.get('v2_score')} v1_score={r.get('v1_score')} dir={r.get('direction')}")
    lines.append("")

    lines.append("## 3. UW feature usage summary (count of non-zero adjustments)")
    if feat_counts:
        for k, c in feat_counts.most_common():
            lines.append(f"- **{k}**: {c}")
    else:
        lines.append("- No UW adjustment usage detected in logged candidates.")
    lines.append("")

    lines.append("## 4. Regime timeline vs v2 behavior (snapshot)")
    if regime:
        lines.append(f"- Regime: **{regime.get('regime_label','NEUTRAL')}** (conf {regime.get('regime_confidence',0.0)})")
    else:
        lines.append("- Regime state missing.")
    lines.append("")

    lines.append("## 5. Paper P&L estimate (placeholder)")
    lines.append("- This summary currently ranks candidates by **v2 score**. To compute paper P&L, wire shadow positions/exits into `shadow_trades.jsonl` (future additive enhancement).")
    lines.append("")

    lines.append("## Inputs")
    lines.append(f"- shadow_trades: `{shadow_path}` exists={shadow_path.exists()}")
    lines.append(f"- uw_attribution: `{attrib_path}` exists={attrib_path.exists()}")
    lines.append(f"- uw_intel_pnl_summary: `state/uw_intel_pnl_summary.json` exists={Path('state/uw_intel_pnl_summary.json').exists()}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

