#!/usr/bin/env python3
"""
CSA: Render execution verdict for profitability Top-5 actions.
Checks ledger alignment and produces go/no-go + next steps. No deferral to more data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="CSA execution verdict for profitability actions or decision")
    ap.add_argument("--actions", default=None, help="Path to PROFITABILITY_TOP_5_ACTIONS_<date>.md")
    ap.add_argument("--decision", default=None, help="Path to PROFITABILITY_DECISION_<date>.md (single path)")
    ap.add_argument("--ledger", required=True, help="Path to FULL_TRADE_LEDGER_<date>.json")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    if not args.actions and not args.decision:
        print("One of --actions or --decision required", file=sys.stderr)
        return 2

    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        print(f"Ledger missing: {ledger_path}", file=sys.stderr)
        return 2
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    executed = ledger.get("executed", []) or []
    blocked = ledger.get("blocked", []) or []

    actions_list = []
    doc_path = Path(args.decision or args.actions)
    if not doc_path.exists():
        print(f"Document missing: {doc_path}", file=sys.stderr)
        return 2
    doc_text = doc_path.read_text(encoding="utf-8")

    if args.decision:
        # Decision doc: "## Chosen Path" section + execution plan
        chosen = re.search(r"## Chosen Path\s*\n+\s*(.+?)(?=\n## |\Z)", doc_text, re.DOTALL)
        actions_list = [chosen.group(1).strip()] if chosen and chosen.group(1).strip() else []
    else:
        actions_list = re.findall(r"^\d+\.\s+(.+)$", doc_text, re.MULTILINE)
        actions_list = [a.strip() for a in actions_list if len(a.strip()) > 5]

    verdict = "GO"
    blockers = []
    if len(executed) == 0 and len(blocked) > 0:
        blockers.append("No executed trades; consider promotion quota and signal subset.")
    if len(actions_list) == 0:
        verdict = "NO_GO"
        blockers.append("No chosen path or actions parsed from document.")

    out = {
        "verdict": verdict,
        "blockers": blockers,
        "actions_count": len(actions_list),
        "ledger_executed": len(executed),
        "ledger_blocked": len(blocked),
        "next_steps": ["Execute chosen path within 48–72 hours."] if verdict == "GO" else blockers,
        "notes": ["Profitability convergence; reversibility allowed, indecision is not."],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("CSA_EXECUTION_VERDICT:", verdict, *blockers if blockers else [])
    return 3 if verdict == "NO_GO" else 0


if __name__ == "__main__":
    sys.exit(main())
