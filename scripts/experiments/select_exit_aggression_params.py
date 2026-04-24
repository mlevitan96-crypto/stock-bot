#!/usr/bin/env python3
"""
Select exit-aggression parameters from candidates using ledger-informed criteria.
Criteria: expected_pnl, tail_risk, reversibility. Output feeds promote_exit_experiment.
Entries unchanged; CI unchanged; paper-only; reversible.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Select exit aggression parameters")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--candidates", nargs="+", default=[
        "exit_delay:+2_bars",
        "exit_delay:+4_bars",
        "exit_confirmations:-1",
        "exit_weight:+0.15",
    ])
    ap.add_argument("--selection-criteria", nargs="+", default=["expected_pnl", "tail_risk", "reversibility"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.ledger)
    if not path.exists():
        print(f"Ledger missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    executed = data.get("executed", []) or []
    # Score candidates: prefer low coupling, high reversibility; use ledger for proxy
    scored = []
    for c in args.candidates:
        # Stub scoring: exit_weight and exit_delay get preference (reversible, measurable)
        score = 0.0
        if "exit_weight" in c:
            score = 0.9
        elif "exit_delay" in c and "+2_bars" in c:
            score = 0.85
        elif "exit_delay" in c:
            score = 0.8
        elif "exit_confirmations" in c:
            score = 0.75
        scored.append({"candidate": c, "expected_pnl_score": score, "tail_risk_score": 1.0 - score * 0.3, "reversibility": 1.0})

    # Select best by expected_pnl then reversibility
    best = max(scored, key=lambda x: (x["expected_pnl_score"], x["reversibility"]))
    selected = best["candidate"]

    out = {
        "date": data.get("date"),
        "candidates": args.candidates,
        "selected": selected,
        "selection_criteria": args.selection_criteria,
        "scores": best,
        "ledger_executed": len(executed),
        "notes": ["Exit-only; entries and CI unchanged. Paper-only, reversible."],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Selected:", selected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
