#!/usr/bin/env python3
"""
CSA + Board rolling review: combine stability analysis and cluster risk.
Produces a single review JSON for downstream top-N promotable ideas.
Read-only; shadow-only; no auto-promotion.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run rolling promotion review (CSA + Board).")
    parser.add_argument("--stability", required=True, help="STABILITY_ANALYSIS_${END_DATE}.json path.")
    parser.add_argument("--cluster-risk", required=True, help="CLUSTER_RISK_OVER_TIME_${END_DATE}.json path.")
    parser.add_argument("--output", required=True, help="Output CSA_BOARD_REVIEW_${END_DATE}.json path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    with open(root / args.stability, encoding="utf-8") as f:
        stability = json.load(f)
    with open(root / args.cluster_risk, encoding="utf-8") as f:
        cluster_risk = json.load(f)

    analysis = stability.get("analysis", [])
    by_date = cluster_risk.get("by_date", [])

    # Cluster risk summary: all scope shadow_only => no blocking
    blocking_risk = False
    for day in by_date:
        for rec in day.get("recommendations", []):
            if isinstance(rec, dict) and rec.get("scope") != "shadow_only":
                blocking_risk = True
                break
    if not by_date:
        # Default from CLUSTER_RECOMMENDATIONS contract
        pass

    # Rank configs by stability: prefer high presence_days, low rank_persistence, low volatility
    ranked = []
    for a in analysis:
        score = (
            a.get("presence_days", 0) * 10
            - (a.get("rank_persistence") or 999) * 0.5
            - (a.get("volatility") or 0) * 2
        )
        ranked.append({
            **a,
            "csa_board_score": round(score, 4),
        })
    ranked.sort(key=lambda x: -x["csa_board_score"])

    review = {
        "stability_path": args.stability,
        "cluster_risk_path": args.cluster_risk,
        "blocking_cluster_risk": blocking_risk,
        "scope": "shadow_only",
        "ranked_configs": ranked,
        "summary": f"{len(ranked)} configs reviewed; cluster scope shadow-only, no gating.",
    }

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(review, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
