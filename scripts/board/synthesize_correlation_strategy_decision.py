#!/usr/bin/env python3
"""
Synthesize board decision for Shadow Signal Correlation & Cluster proposal.
Outputs chosen strategy-to-test (A/B/C/D) and a Chosen Path for CSA verdict.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthesize correlation analysis strategy decision")
    ap.add_argument("--reviews", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.reviews)
    if not path.exists():
        print(f"Reviews missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    reviews = data.get("reviews", {})
    questions = data.get("review_questions", [])

    # Default: A = run once on current backfill and review outputs (safest first step)
    strategy = "A"
    for p, r in reviews.items():
        if not isinstance(r, dict):
            continue
        for ans in (r.get("answers") or []):
            if not isinstance(ans, str):
                continue
            u = ans.upper()
            if "(B)" in u or " OPTION B " in u or "STRATEGY B" in u:
                strategy = "B"
                break
            if "(C)" in u or " OPTION C " in u or "STRATEGY C" in u:
                strategy = "C"
                break
            if "(D)" in u or " OPTION D " in u or "STRATEGY D" in u:
                strategy = "D"
                break
        if strategy != "A":
            break

    strategies = {
        "A": "Run once on current backfill and review outputs before committing to a cadence.",
        "B": "Run weekly as backfill grows to track stability of clusters and correlations.",
        "C": "Run only when native emission replaces backfill for highest fidelity.",
        "D": "Other (see board notes).",
    }
    chosen_path = f"APPROVE: Proceed with Shadow Signal Correlation & Cluster Analysis. Strategy to test: {strategy} — {strategies.get(strategy, strategies['D'])}"

    lines = [
        "# Board Decision — Shadow Signal Correlation & Cluster Analysis",
        "",
        "## Chosen Path",
        "",
        chosen_path,
        "",
        "## Strategy to Test",
        "",
        strategy,
        "",
        "## Rationale",
        "",
        "Board review synthesized. Shadow-only, read-only; no gating or promotion.",
        "",
        "---",
    ]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Strategy to test:", strategy)
    return 0


if __name__ == "__main__":
    sys.exit(main())
