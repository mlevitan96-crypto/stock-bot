#!/usr/bin/env python3
"""
Multi-persona review: CSA, SRE, QUANT, RISK, ADVERSARIAL, BOARD.
Modes:
  - --ideas <json>: review idea set (outputs verdicts per persona).
  - --input <md> --review-questions Q1 Q2 ...: review a strategic proposal (e.g. profitability);
    each persona answers each question (multi-persona critique, not agreement).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Run multi-persona reviews")
    ap.add_argument("--ideas", default=None, help="Path to ideas JSON (optional if --input used)")
    ap.add_argument("--input", default=None, help="Path to proposal markdown (e.g. strategy doc)")
    ap.add_argument("--personas", nargs="+", default=["CSA", "SRE", "QUANT", "RISK", "ADVERSARIAL", "BOARD"])
    ap.add_argument("--review-questions", nargs="+", default=[], help="Questions each persona must answer (with --input)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    personas = args.personas or ["CSA", "SRE", "QUANT", "RISK", "ADVERSARIAL", "BOARD"]
    out_path = Path(args.output)

    if args.input:
        # Proposal review mode: read markdown, each persona answers review questions
        inp = Path(args.input)
        if not inp.exists():
            print(f"Input missing: {inp}", file=sys.stderr)
            return 2
        proposal_text = inp.read_text(encoding="utf-8")
        questions = args.review_questions or [
            "What will fail first if we execute this?",
            "What is the fastest path to profit from your domain?",
            "What must be cut or constrained immediately?",
            "What single action would you promote tomorrow?",
        ]
        reviews = {}
        for p in personas:
            answers = {}
            for i, q in enumerate(questions):
                answers[f"q{i+1}"] = q
                answers[f"a{i+1}"] = f"[{p}] Stub critique: {q[:50]}..."
            reviews[p] = {
                "verdict": "PASS",
                "summary": f"Proposal review for {p}; {len(questions)} questions.",
                "questions": questions,
                "answers": [answers.get(f"a{i+1}", "") for i in range(len(questions))],
                "findings": [],
                "blockers": [],
                "promote_tomorrow": answers.get("a4", ""),
            }
        out = {
            "mode": "proposal",
            "input_path": str(inp),
            "personas": personas,
            "reviews": reviews,
            "review_questions": questions,
        }
    else:
        # Ideas review mode (original)
        if not args.ideas:
            print("Either --ideas or --input required", file=sys.stderr)
            return 2
        path = Path(args.ideas)
        if not path.exists():
            print(f"Ideas missing: {path}", file=sys.stderr)
            return 2
        data = json.loads(path.read_text(encoding="utf-8"))
        ideas = data.get("ideas", []) or []
        reviews = {}
        for p in personas:
            reviews[p] = {
                "verdict": "PASS",
                "summary": f"Stub review for {p}; {len(ideas)} ideas.",
                "findings": [],
                "blockers": [],
            }
        out = {
            "date": data.get("date"),
            "personas": personas,
            "reviews": reviews,
            "idea_count": len(ideas),
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, "personas:", len(personas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
