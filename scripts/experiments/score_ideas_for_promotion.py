#!/usr/bin/env python3
"""
Score ideas for promotion across dimensions: expectancy, consistency, drawdown, tail, regime, simplicity.
Consumes ideas + persona reviews; outputs IDEA_SCORECARD for CSA verdict and board packet.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Score ideas for promotion")
    ap.add_argument("--ideas", required=True)
    ap.add_argument("--reviews", required=True)
    ap.add_argument("--dimensions", nargs="+", default=["expectancy", "consistency", "drawdown", "tail", "regime", "simplicity"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ideas_path = Path(args.ideas)
    reviews_path = Path(args.reviews)
    if not ideas_path.exists():
        print(f"Ideas missing: {ideas_path}", file=sys.stderr)
        return 2
    if not reviews_path.exists():
        print(f"Reviews missing: {reviews_path}", file=sys.stderr)
        return 2

    ideas_data = json.loads(ideas_path.read_text(encoding="utf-8"))
    reviews_data = json.loads(reviews_path.read_text(encoding="utf-8"))
    ideas = ideas_data.get("ideas", []) or []
    dims = args.dimensions or ["expectancy", "consistency", "drawdown", "tail", "regime", "simplicity"]

    # Stub: one score row per idea with placeholder dimension scores
    scores = []
    for i, idea in enumerate(ideas[:100]):
        if not isinstance(idea, dict):
            continue
        row = {
            "index": i,
            "symbol": idea.get("symbol"),
            "type": idea.get("type"),
            "dimensions": {d: None for d in dims},
            "composite": None,
        }
        scores.append(row)

    out = {
        "date": ideas_data.get("date"),
        "dimensions": dims,
        "ideas": scores,
        "count": len(scores),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, "scores:", len(scores))
    return 0


if __name__ == "__main__":
    sys.exit(main())
