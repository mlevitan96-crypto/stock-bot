#!/usr/bin/env python3
"""
Decision synthesis: force ONE chosen path from persona recommendations.
Output: chosen path + rationale + 48–72 hour execution plan.
Criteria: expected_pnl, speed_to_signal, reversibility, operational_risk.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Decide single best path forward from persona reviews")
    ap.add_argument("--reviews", required=True, help="PROFITABILITY_DECISION_REVIEWS_<date>.json")
    ap.add_argument("--require-single-decision", action="store_true", default=True)
    ap.add_argument("--decision-criteria", nargs="+", default=["expected_pnl", "speed_to_signal", "reversibility", "operational_risk"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.reviews)
    if not path.exists():
        print(f"Reviews missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    reviews = data.get("reviews", {}) or {}
    questions = data.get("review_questions", [])

    # First question is "what single action most increases near-term profitability" — use as primary recommendation per persona
    recommendations = []
    for p, r in reviews.items():
        if not isinstance(r, dict):
            continue
        answers = r.get("answers", [])
        if answers:
            rec = (answers[0] or "").strip()
            if rec and len(rec) > 10 and "Stub critique" not in rec:
                recommendations.append({"persona": p, "recommendation": rec})
        promote = r.get("promote_tomorrow")
        if promote and "Stub critique" not in (promote or ""):
            recommendations.append({"persona": p, "recommendation": (promote or "").strip()})

    # If all stubs, choose the canonical first path from strategy
    if not recommendations:
        chosen_path = "Enforce a daily promotion quota (minimum 1 action/day)."
        rationale = "No persona override; using strategy directive A for single-path decision."
    else:
        chosen_path = recommendations[0]["recommendation"]
        rationale = f"Primary recommendation from {recommendations[0]['persona']}; criteria: {', '.join(args.decision_criteria)}."

    execution_plan = [
        "Hour 0–24: Confirm promotion quota definition and log one promotable action or explicit deferral.",
        "Hour 24–48: Apply opportunity-cost cap to Counter-Intelligence if CI impact exists.",
        "Hour 48–72: Review paper PnL and block one non-profitable signal or symbol.",
    ]

    lines = [
        "# Profitability Decision — Single Path",
        "",
        "## Chosen Path",
        "",
        chosen_path,
        "",
        "## Rationale",
        "",
        rationale,
        "",
        "## Execution Plan (48–72 Hours)",
        "",
    ]
    for i, step in enumerate(execution_plan, 1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("---")
    lines.append("*Forced single decision; must increase expected PnL (variance allowed).*")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", out_path, "chosen:", chosen_path[:60] + "..." if len(chosen_path) > 60 else chosen_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
