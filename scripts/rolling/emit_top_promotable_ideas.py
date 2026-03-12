#!/usr/bin/env python3
"""
Emit top-N promotable ideas from CSA/Board rolling review.
Output shape is compatible with assert_promotion_decision_required (decision_required, shortlist_count, top_config_id).
Read-only; no auto-promotion.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit top-N promotable ideas from rolling review.")
    parser.add_argument("--review", required=True, help="CSA_BOARD_REVIEW_${END_DATE}.json path.")
    parser.add_argument("--top-n", type=int, default=3, help="Number of top ideas to emit.")
    parser.add_argument("--output", required=True, help="Output TOP_3_PROMOTABLE_IDEAS_${END_DATE}.json path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    with open(root / args.review, encoding="utf-8") as f:
        review = json.load(f)

    ranked = review.get("ranked_configs", [])[: args.top_n]
    ideas = [
        {
            "rank": i + 1,
            "config_id": c.get("config_id"),
            "presence_days": c.get("presence_days"),
            "rank_persistence": c.get("rank_persistence"),
            "volatility": c.get("volatility"),
            "csa_board_score": c.get("csa_board_score"),
        }
        for i, c in enumerate(ranked)
    ]

    # Shape compatible with assert_promotion_decision_required.py; configs alias for jq .configs[]
    out = {
        "decision_required": len(ideas) > 0,
        "shortlist_count": len(ideas),
        "top_config_id": ideas[0].get("config_id") if ideas else None,
        "ideas": ideas,
        "configs": ideas,  # alias for paper promotion block Phase 1 jq
        "review_path": args.review,
        "message": "Explicit human decision required. No auto-promotion." if ideas else "No promotable ideas.",
    }

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {out_path} (top {len(ideas)} ideas)")


if __name__ == "__main__":
    main()
