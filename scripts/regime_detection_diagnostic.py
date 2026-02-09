#!/usr/bin/env python3
"""
Regime Detection Diagnostic — last N days regime_label, confidence, and key inputs.

For each day with a stockbot pack, prints regime from STOCK_REGIME_AND_UNIVERSE.json.
Flags days where regime is UNKNOWN and explains possible causes (e.g. missing _meta).
Optionally prints current pipeline state (regime_posture_state, market_context_v2).

Usage: python scripts/regime_detection_diagnostic.py [--days 14] [--base-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else (default or {})
    except Exception:
        return default if default is not None else {}


def _day_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def main() -> int:
    ap = argparse.ArgumentParser(description="Regime detection diagnostic for last N days")
    ap.add_argument("--days", type=int, default=14, help="Number of days to look back (default 14)")
    ap.add_argument("--base-dir", type=Path, default=ROOT, help="Repo root (default: script parent)")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    reports_stockbot = base / "reports" / "stockbot"
    state_dir = base / "state"

    today = datetime.now(timezone.utc).date()
    days_back = max(1, min(args.days, 30))
    unknown_days = []
    lines = [
        f"# Regime Detection Diagnostic (last {days_back} days)",
        f"Base: {base}",
        "",
    ]

    for i in range(days_back):
        d = today - timedelta(days=i)
        day_str = d.strftime("%Y-%m-%d")
        pack_dir = reports_stockbot / day_str
        regime_file = pack_dir / "STOCK_REGIME_AND_UNIVERSE.json"
        if not regime_file.exists():
            continue
        rec = _load_json(regime_file, {})
        regime = rec.get("regime") or rec.get("regime_label") or "UNKNOWN"
        sectors = rec.get("sectors") or []
        symbol_count = rec.get("symbol_count") or 0
        lines.append(f"## {day_str}")
        lines.append(f"- **regime_label:** {regime}")
        lines.append(f"- **symbol_count:** {symbol_count}")
        lines.append(f"- **sectors:** {len(sectors)} ({', '.join(str(s) for s in sectors[:5])}{'...' if len(sectors) > 5 else ''})")
        if regime == "UNKNOWN":
            unknown_days.append(day_str)
            lines.append("- **FLAG:** UNKNOWN — likely cause: daily_universe_v2._meta.regime_label was missing when pack was built (fixed by reading _meta in run_stockbot_daily_reports).")
        lines.append("")

    if unknown_days:
        lines.append("## Summary: UNKNOWN days")
        lines.append(f"Days with regime UNKNOWN: {', '.join(unknown_days)}")
        lines.append("")
    else:
        lines.append("## Summary: No UNKNOWN regime in pack history for this window.")
        lines.append("")

    # Current pipeline state (single snapshot)
    lines.append("## Current pipeline state (state files)")
    posture_path = state_dir / "regime_posture_state.json"
    market_path = state_dir / "market_context_v2.json"
    posture = _load_json(posture_path, {})
    market = _load_json(market_path, {})
    if posture:
        lines.append(f"- **regime_posture_state.regime_label:** {posture.get('regime_label', 'N/A')}")
        lines.append(f"- **regime_posture_state.regime_confidence:** {posture.get('regime_confidence', 'N/A')}")
        lines.append(f"- **regime_posture_state.regime_source:** {posture.get('regime_source', 'N/A')}")
    else:
        lines.append("- **regime_posture_state.json:** missing or empty")
    if market:
        lines.append(f"- **market_context_v2.market_trend:** {market.get('market_trend', 'N/A')}")
        lines.append(f"- **market_context_v2.volatility_regime:** {market.get('volatility_regime', 'N/A')}")
        lines.append(f"- **market_context_v2.risk_on_off:** {market.get('risk_on_off', 'N/A')}")
    else:
        lines.append("- **market_context_v2.json:** missing or empty")
    lines.append("")

    text = "\n".join(lines)
    print(text)
    return 0 if not unknown_days else 1


if __name__ == "__main__":
    sys.exit(main())
