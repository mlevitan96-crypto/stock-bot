#!/usr/bin/env python3
"""Write reports/audit/A3_SHADOW_PROOF.md from state/shadow/a3_expectancy_floor_shadow.json. Run on droplet after A3 shadow."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    state_path = base / "state" / "shadow" / "a3_expectancy_floor_shadow.json"
    out_path = base / "reports" / "audit" / "A3_SHADOW_PROOF.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not state_path.exists():
        lines = [
            "# A3 shadow proof",
            "",
            "**Status:** Shadow state not found. Run scripts/shadow/run_a3_expectancy_floor_shadow.py first.",
            "",
        ]
    else:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        run_ts = data.get("run_ts", "")
        cmd = "python3 scripts/shadow/run_a3_expectancy_floor_shadow.py --since-hours 24"
        lines = [
            "# A3 shadow proof",
            "",
            f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Command run",
            "",
            f"`{cmd}`",
            "",
            "## Run timestamp",
            "",
            run_ts,
            "",
            "## Key metrics excerpt",
            "",
            f"- additional_admitted_trades: {data.get('additional_admitted_trades', 'N/A')}",
            f"- estimated_pnl_delta_usd: {data.get('estimated_pnl_delta_usd', 'N/A')} ({data.get('estimated_pnl_delta_label', '')})",
            f"- effective_floor_shadow: {data.get('effective_floor_shadow', 'N/A')}",
            f"- floor_breach_count: {data.get('floor_breach_count', 'N/A')}",
            "",
            "## Explicit statement",
            "",
            "**Shadow only; no live execution changes.** The A3 shadow script does not modify gating or place orders.",
            "",
        ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
