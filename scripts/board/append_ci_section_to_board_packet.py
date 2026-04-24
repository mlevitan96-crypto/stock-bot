#!/usr/bin/env python3
"""
Append Counter-Intel section to the day board packet for board visibility.
Reads existing board markdown and CI impact JSON; appends ## Counter-Intel.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Append CI section to board packet")
    ap.add_argument("--board", required=True, help="Path to DAY_TRADING_INTELLIGENCE_BOARD_PACKET_<date>.md")
    ap.add_argument("--ci-impact", required=True, help="Path to CSA_COUNTER_INTEL_IMPACT_<date>.json")
    args = ap.parse_args()

    board_path = Path(args.board)
    impact_path = Path(args.ci_impact)
    if not board_path.exists():
        print(f"Board packet missing: {board_path}", file=sys.stderr)
        return 2
    if not impact_path.exists():
        print(f"CI impact file missing: {impact_path}", file=sys.stderr)
        return 2

    impact = json.loads(impact_path.read_text(encoding="utf-8"))
    summary = impact.get("summary", {})
    opp = summary.get("opportunity_cost_usd", impact.get("opportunity_cost_usd"))
    total = summary.get("total_ci_events", impact.get("event_count"))

    section = [
        "",
        "## Counter-Intel",
        "",
        f"- **CI events:** {total}",
        f"- **Opportunity cost (would-have PnL foregone):** ${opp}",
        f"- **Risk reasons:** {summary.get('risk_reasons_count', 'N/A')}",
        "",
        impact.get("protection_note", ""),
        "",
    ]

    existing = board_path.read_text(encoding="utf-8")
    if "## Counter-Intel" in existing:
        # Replace existing CI section: from "## Counter-Intel" to next "## " or end
        before, marker, after = existing.partition("## Counter-Intel")
        after = after.lstrip("\r\n")
        next_h2 = after.find("\n## ")
        if next_h2 >= 0:
            after = after[next_h2:].lstrip()
        else:
            after = ""
        new_content = before.rstrip() + "\n" + "\n".join(section).rstrip() + ("\n\n## " + after if after else "")
    else:
        new_content = existing.rstrip() + "\n" + "\n".join(section)

    board_path.write_text(new_content, encoding="utf-8")
    print("Appended CI section to", board_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
