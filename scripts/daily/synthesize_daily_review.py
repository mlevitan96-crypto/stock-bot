#!/usr/bin/env python3
"""
Synthesize daily review markdown from shadow artifact index.
Read-only; produces DAILY_REVIEW_${DATE}.md for human review.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize daily review from artifact index.")
    parser.add_argument(
        "--artifact-index",
        required=True,
        help="Path to SHADOW_ARTIFACT_INDEX_${DATE}.json",
    )
    parser.add_argument("--output", required=True, help="Output DAILY_REVIEW_${DATE}.md path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    index_path = root / args.artifact_index
    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)

    date = index.get("date", "unknown")
    lines = [
        "# Daily Review — Shadow Synthesis",
        "",
        f"**Date:** {date}",
        "",
        "## Scope",
        "- Read-only.",
        "- Shadow-only.",
        "- Human approval required for any promotion.",
        "",
        "## Artifact Index",
        "",
    ]

    for a in index.get("artifacts", []):
        status = "✓" if a.get("present") else "✗"
        lines.append(f"- {status} `{a.get('path', '')}`")
    lines.extend(["", "## Summary", ""])

    # Optional: summarize shortlist and ranking if present
    shortlist_path = None
    ranking_path = None
    clusters_path = None
    for a in index.get("artifacts", []):
        p = a.get("path", "")
        if "PROMOTION_SHORTLIST" in p and "promotable.backfill" in p:
            shortlist_path = (root / p) if a.get("present") else None
        elif "TRUE_REPLAY_RANKING" in p:
            ranking_path = (root / p) if a.get("present") else None
        elif "CLUSTER_RECOMMENDATIONS" in p:
            clusters_path = (root / p) if a.get("present") else None

    if shortlist_path and shortlist_path.exists():
        with open(shortlist_path, encoding="utf-8") as f:
            shortlist = json.load(f)
        count = len(shortlist.get("shortlist", []))
        lines.append(f"- Promotion shortlist (promotable backfill): **{count}** configs.")
        lines.append("")
    if ranking_path and ranking_path.exists():
        with open(ranking_path, encoding="utf-8") as f:
            ranking = json.load(f)
        rank_count = len(ranking.get("ranking", []))
        lines.append(f"- True replay ranking: **{rank_count}** configs.")
        lines.append("")
    if clusters_path and clusters_path.exists():
        with open(clusters_path, encoding="utf-8") as f:
            clusters = json.load(f)
        recs = clusters.get("recommendations", [])
        lines.append(f"- Cluster recommendations: **{len(recs)}** items (shadow-only, no gating).")
        lines.append("")

    lines.extend([
        "## Next Step",
        "",
        "Run promotion status evaluation; then assert explicit decision required.",
        "No auto-promotion. Await human decision.",
        "",
        "---",
        "*Daily governance checkpoint. Shadow-only synthesis.*",
    ])

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
