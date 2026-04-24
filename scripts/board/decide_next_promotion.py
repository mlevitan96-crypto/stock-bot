#!/usr/bin/env python3
"""
Decide the next promotable action (mandatory). One of: ci_budget_relaxation, signal_pruning, symbol_focus, exit_amplification.
Output includes ## Chosen Path for render_execution_verdict. No architecture changes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Decide next promotion (mandatory)")
    ap.add_argument("--previous-promotion", required=True)
    ap.add_argument("--verdict", required=True, help="CSA_EXIT_EXPERIMENT_VERDICT_<date>.json")
    ap.add_argument("--candidate-types", nargs="+", default=[
        "ci_budget_relaxation", "signal_pruning", "symbol_focus", "exit_amplification",
    ])
    ap.add_argument("--require-selection", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    prom_path = Path(args.previous_promotion)
    verdict_path = Path(args.verdict)
    if not prom_path.exists():
        print(f"Previous promotion missing: {prom_path}", file=sys.stderr)
        return 2
    if not verdict_path.exists():
        print(f"Verdict missing: {verdict_path}", file=sys.stderr)
        return 2

    prom = json.loads(prom_path.read_text(encoding="utf-8"))
    verdict_data = json.loads(verdict_path.read_text(encoding="utf-8"))
    verdict = verdict_data.get("verdict", "EXTEND")

    # Select next type: if EXTEND/AMPLIFY prefer exit_amplification or symbol_focus; if REVERT prefer signal_pruning or ci_budget
    if verdict == "REVERT":
        chosen_type = "signal_pruning"
        description = "Prune one non-profitable signal to reduce noise; reversible."
    elif verdict == "AMPLIFY":
        chosen_type = "exit_amplification"
        description = "Amplify exit weight delta (e.g. +0.05) on same lever; paper-only."
    else:
        chosen_type = "symbol_focus"
        description = "Focus capital on symbols that already show edge; reduce universe size."

    chosen_path = f"{chosen_type}: {description}"

    lines = [
        "# Next Promotion Decision",
        "",
        "## Chosen Path",
        "",
        chosen_path,
        "",
        "## Rationale",
        "",
        f"Previous exit experiment verdict: {verdict}. Next promotion type: **{chosen_type}**.",
        "",
        "## Candidate Types Considered",
        "",
    ]
    for c in args.candidate_types:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("---")
    lines.append("*One next promotion required; no architecture changes.*")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Next promotion:", chosen_type)
    return 0


if __name__ == "__main__":
    sys.exit(main())
