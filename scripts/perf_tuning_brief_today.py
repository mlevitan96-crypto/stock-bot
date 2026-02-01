#!/usr/bin/env python3
"""
Synthesize PERF_TUNING_BRIEF_TODAY.md from diagnostics, shadow comparison, and intelligence recommendations.

Inputs:
- PERF_TODAY_* artifacts
- telemetry/YYYY-MM-DD/computed/blocked_counterfactuals_summary.json
- telemetry/YYYY-MM-DD/computed/exit_quality_summary.json
- reports/SHADOW_TUNING_COMPARISON.md
- telemetry/YYYY-MM-DD/computed/intelligence_recommendations.json

Output: reports/PERF_TUNING_BRIEF_TODAY.md

Sections: What happened today; What diagnostics say; Which shadow profiles improved; Intelligence recommendations; NOT LIVE YET list.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"
TELEMETRY_DIR = REPO / "telemetry"


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _latest_telemetry_date() -> str:
    if not TELEMETRY_DIR.exists():
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dates = [d.name for d in TELEMETRY_DIR.iterdir() if d.is_dir() and len(d.name) == 10]
    return max(dates) if dates else datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main() -> int:
    date_str = _latest_telemetry_date()
    computed = TELEMETRY_DIR / date_str / "computed"

    raw = _load(REPORTS / "PERF_TODAY_RAW_STATS.json")
    blocked = _load(computed / "blocked_counterfactuals_summary.json")
    exit_qual = _load(computed / "exit_quality_summary.json")
    comparison_path = REPORTS / "SHADOW_TUNING_COMPARISON.md"
    comparison_text = comparison_path.read_text(encoding="utf-8") if comparison_path.exists() else "(Run compare_shadow_profiles.py)"
    intel_rec = _load(computed / "intelligence_recommendations.json")

    stats = (raw or {}).get("stats") or {}
    signals = (raw or {}).get("signals_summary") or {}
    gates = (raw or {}).get("gates_summary") or {}

    lines = [
        "# Performance Tuning Brief — Today",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Date:** {date_str}",
        "",
        "## 1) What happened today",
        "",
        f"- **Net PnL (USD):** {stats.get('net_pnl_usd', 'N/A')}",
        f"- **Win rate (%):** {stats.get('win_rate_pct', 'N/A')}",
        f"- **Max drawdown (USD):** {stats.get('max_drawdown_usd', 'N/A')}",
        f"- **Trade count:** {stats.get('total_trades', 'N/A')}",
        f"- **Trade intents:** {signals.get('trade_intent_count', 'N/A')} (entered: {signals.get('entered', 'N/A')}, blocked: {signals.get('blocked', 'N/A')})",
        "",
        "## 2) What diagnostics say (blocked vs exits)",
        "",
    ]
    if blocked and isinstance(blocked.get("per_blocked_reason"), dict):
        lines.append("**Blocked counterfactuals:**")
        for reason, v in blocked["per_blocked_reason"].items():
            if isinstance(v, dict):
                lines.append(f"- **{reason}:** count={v.get('count')}, avg CF PnL (30m)={v.get('avg_counterfactual_pnl_30m')}, % would win (30m)={v.get('pct_would_win_30m')}")
        lines.append("")
    else:
        lines.append("No blocked counterfactuals summary available.")
        lines.append("")

    if exit_qual and isinstance(exit_qual.get("per_exit_reason"), dict):
        lines.append("**Exit quality:**")
        for reason, v in exit_qual["per_exit_reason"].items():
            if isinstance(v, dict):
                lines.append(f"- **{reason}:** count={v.get('count')}, avg PnL={v.get('avg_pnl')}, left on table (avg)={v.get('left_on_table_avg')}, avg time (min)={v.get('avg_time_in_trade_minutes')}")
        lines.append("")
    else:
        lines.append("No exit quality summary available.")
        lines.append("")

    lines.extend([
        "## 3) Which shadow profiles improved expectancy",
        "",
        "See SHADOW_TUNING_COMPARISON.md. Excerpt:",
        "",
        "```",
        comparison_text[:2000] + ("..." if len(comparison_text) > 2000 else ""),
        "```",
        "",
        "## 4) Intelligence recommendations",
        "",
    ])
    recs = (intel_rec or {}).get("recommendations") or []
    if recs:
        lines.append("| Entity type | Entity | Status | Confidence | Suggested action |")
        lines.append("|-------------|--------|--------|------------|------------------|")
        for r in recs[:50]:
            lines.append(f"| {r.get('entity_type')} | {r.get('entity')} | {r.get('status')} | {r.get('confidence')} | {r.get('suggested_action')} |")
    else:
        lines.append("No intelligence recommendations available. Run build_intelligence_profitability_today.py.")
    lines.append("")

    lines.extend([
        "## 5) NOT LIVE YET — Proposed config changes",
        "",
        "The following are **recommendations only**; not applied. Any change that would affect live trading must be:",
        "- CONFIG ONLY,",
        "- DISABLED by default,",
        "- Documented and applied only after human review.",
        "",
        "- **PARAM_TUNING:** Consider relaxing displacement (e.g. DISPLACEMENT_MAX_PNL_PCT or DISPLACEMENT_SCORE_ADVANTAGE) if blocked counterfactuals show positive CF PnL.",
        "- **PARAM_TUNING:** Consider increasing MIN_EXEC_SCORE if entry quality is poor.",
        "- **PARAM_TUNING:** Consider tightening trailing-stop or time-exit if exit quality shows high left-on-table.",
        "- **STRUCTURAL:** Add regime filter to reduce trading in hostile regimes.",
        "- **STRUCTURAL:** Diversify symbols/themes to reduce single-name risk.",
        "",
    ])

    out_path = REPORTS / "PERF_TUNING_BRIEF_TODAY.md"
    REPORTS.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
