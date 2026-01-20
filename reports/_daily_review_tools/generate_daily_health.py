#!/usr/bin/env python3
"""
Generate a Daily Health report from DROPLET production data.

Output:
- reports/DAILY_HEALTH_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from report_data_fetcher import ReportDataFetcher
from report_data_validator import validate_data_source, validate_report_data


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=False, help="YYYY-MM-DD (default: today UTC)")
    args = ap.parse_args()

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = Path("reports") / f"DAILY_HEALTH_{date}.md"

    with ReportDataFetcher(date=date) as fetcher:
        src = fetcher.get_data_source_info()
        validate_data_source(src)

        trades = fetcher.get_executed_trades()
        blocked = fetcher.get_blocked_trades()
        orders = fetcher.get_orders()
        gates = fetcher.get_gate_events()
        signals = fetcher.get_signals()
        shadow = fetcher.get_shadow_events()

        validate_report_data(
            {
                "attribution": trades,
                "blocked_trades": blocked,
                "signals": signals,
                "orders": orders,
                "gate": gates,
            }
        )

    lines: List[str] = []
    lines.append(f"# DAILY_HEALTH_{date}")
    lines.append("")
    lines.append("## Core counts")
    lines.append(f"- **signals**: `{len(signals)}`")
    lines.append(f"- **gate_events**: `{len(gates)}`")
    lines.append(f"- **orders**: `{len(orders)}`")
    lines.append(f"- **executed_trades(attribution)**: `{len(trades)}`")
    lines.append(f"- **blocked_trades**: `{len(blocked)}`")
    lines.append(f"- **shadow_events**: `{len(shadow)}`")
    lines.append("")
    lines.append("## Gate pressure (top reasons)")
    from collections import Counter

    gate_counts = Counter()
    for g in gates:
        msg = g.get("msg") or g.get("event") or g.get("gate_name") or "unknown"
        gate_counts[str(msg)] += 1
    for k, v in gate_counts.most_common(15):
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("## Data source")
    lines.append(f"- `{src.get('source')}`")
    lines.append(f"- target_date: `{src.get('target_date')}`")
    lines.append("")
    lines.append("## Notes")
    lines.append("- This report is intentionally lightweight; it’s a daily sanity/health snapshot.")
    lines.append("- For shadow analysis, also generate the shadow audit report.")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

