#!/usr/bin/env python3
"""
Shadow: Emit cluster-aware recommendations (diagnostics only). No gating, no promotion, no weight changes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit cluster recommendations (shadow-only)")
    ap.add_argument("--clusters", required=True)
    ap.add_argument("--importance", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    cluster_path = Path(args.clusters)
    importance_path = Path(args.importance)
    if not cluster_path.exists():
        print(f"Clusters missing: {cluster_path}", file=sys.stderr)
        return 2
    if not importance_path.exists():
        print(f"Importance missing: {importance_path}", file=sys.stderr)
        return 2

    cluster_data = json.loads(cluster_path.read_text(encoding="utf-8"))
    importance_data = json.loads(importance_path.read_text(encoding="utf-8"))
    clusters = cluster_data.get("clusters", [])
    cond = importance_data.get("conditional_importance", [])

    recommendations = []
    for i, c in enumerate(clusters):
        imp = cond[i] if i < len(cond) else {}
        mean_abs = imp.get("mean_abs", {})
        top = sorted(mean_abs.items(), key=lambda x: -x[1])[:3]
        recommendations.append({
            "cluster_id": i,
            "signals": c,
            "top_signals_by_importance": [t[0] for t in top],
            "recommendation": "Review weight sweep for these signals; cluster may be redundant or complementary.",
        })
    recommendations.append({
        "cluster_id": "global",
        "recommendation": "Shadow-only. No gating, no promotion, no weight changes. Use for diagnostics and sweep design.",
    })

    out = {
        "clusters_path": str(cluster_path.resolve()),
        "importance_path": str(importance_path.resolve()),
        "recommendations": recommendations,
        "scope": "shadow_only",
        "contract": "No automatic actions; board and daily promotion loop retain control.",
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Cluster recommendations:", len(recommendations))
    return 0


if __name__ == "__main__":
    sys.exit(main())
