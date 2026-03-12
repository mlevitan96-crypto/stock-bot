#!/usr/bin/env python3
"""
Evaluate promotion status from shortlist and cluster recommendations.
Produces PROMOTION_STATUS_${DATE}.json for the assertion step.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate promotion status for daily checkpoint.")
    parser.add_argument(
        "--shortlist",
        required=True,
        help="Path to PROMOTION_SHORTLIST_${DATE}.promotable.backfill.json",
    )
    parser.add_argument(
        "--correlation-notes",
        required=True,
        help="Path to CLUSTER_RECOMMENDATIONS_${DATE}.json",
    )
    parser.add_argument("--output", required=True, help="Output PROMOTION_STATUS_${DATE}.json path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    with open(root / args.shortlist, encoding="utf-8") as f:
        shortlist_data = json.load(f)
    with open(root / args.correlation_notes, encoding="utf-8") as f:
        clusters = json.load(f)

    shortlist = shortlist_data.get("shortlist", [])
    recommendations = clusters.get("recommendations", [])

    status = {
        "shortlist_count": len(shortlist),
        "top_config_id": shortlist[0].get("config_id") if shortlist else None,
        "cluster_recommendations_count": len(recommendations),
        "scope": "shadow_only",
        "decision_required": len(shortlist) > 0,
        "correlation_notes_summary": [
            r.get("recommendation", "")[:80] for r in recommendations if isinstance(r, dict)
        ][:5],
    }

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
