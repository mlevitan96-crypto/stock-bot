#!/usr/bin/env python3
"""
Shadow: Identify signal clusters from correlation matrix (hierarchical: merge until threshold).
Read-only. Uses correlation as similarity; clusters are groups with pairwise correlation >= threshold.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Identify signal clusters from correlations")
    ap.add_argument("--correlations", required=True)
    ap.add_argument("--method", default="hierarchical")
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.correlations)
    if not path.exists():
        print(f"Correlations missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    names = data.get("signal_names", [])
    corr = data.get("correlation_matrix", [])
    if not names or len(corr) != len(names):
        print("Invalid correlation matrix", file=sys.stderr)
        return 2

    # Greedy clustering: merge signals that have correlation >= threshold with any in cluster
    n = len(names)
    used = [False] * n
    clusters = []
    for i in range(n):
        if used[i]:
            continue
        cluster = [i]
        used[i] = True
        for j in range(i + 1, n):
            if used[j]:
                continue
            if any(corr[j][k] >= args.threshold for k in cluster):
                cluster.append(j)
                used[j] = True
        clusters.append([names[k] for k in cluster])
    clusters = [c for c in clusters if c]

    out = {
        "signal_names": names,
        "method": args.method,
        "threshold": args.threshold,
        "clusters": clusters,
        "cluster_count": len(clusters),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Clusters:", len(clusters))
    return 0


if __name__ == "__main__":
    sys.exit(main())
