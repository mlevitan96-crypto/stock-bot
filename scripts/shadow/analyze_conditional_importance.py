#!/usr/bin/env python3
"""
Shadow: Conditional importance of signals per cluster (e.g. mean absolute value by outcome).
Read-only. Diagnostics only; no weight changes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze conditional importance per cluster")
    ap.add_argument("--clusters", required=True)
    ap.add_argument("--signal-matrices", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    cluster_path = Path(args.clusters)
    matrix_path = Path(args.signal_matrices)
    if not cluster_path.exists():
        print(f"Clusters missing: {cluster_path}", file=sys.stderr)
        return 2
    if not matrix_path.exists():
        print(f"Signal matrices missing: {matrix_path}", file=sys.stderr)
        return 2

    cluster_data = json.loads(cluster_path.read_text(encoding="utf-8"))
    matrix_data = json.loads(matrix_path.read_text(encoding="utf-8"))
    names = matrix_data.get("signal_names", [])
    matrix = matrix_data.get("matrix", [])
    outcome = matrix_data.get("outcome", [])
    clusters = cluster_data.get("clusters", [])

    name_to_idx = {n: i for i, n in enumerate(names)}
    importance = []
    for c in clusters:
        idxs = [name_to_idx[s] for s in c if s in name_to_idx]
        if not idxs:
            importance.append({"cluster": c, "signals": c, "importance_win": {}, "importance_lose": {}, "mean_abs": {}})
            continue
        win_vals = [[] for _ in idxs]
        lose_vals = [[] for _ in idxs]
        for row, o in zip(matrix, outcome):
            for k, i in enumerate(idxs):
                v = row[i] if i < len(row) else 0
                if o == 1:
                    win_vals[k].append(abs(v))
                else:
                    lose_vals[k].append(abs(v))
        imp_win = {c[j]: sum(win_vals[j]) / len(win_vals[j]) if win_vals[j] else 0 for j in range(len(idxs))}
        imp_lose = {c[j]: sum(lose_vals[j]) / len(lose_vals[j]) if lose_vals[j] else 0 for j in range(len(idxs))}
        mean_abs = {c[j]: (imp_win[c[j]] + imp_lose[c[j]]) / 2 for j in range(len(idxs))}
        importance.append({
            "cluster": c,
            "importance_win": imp_win,
            "importance_lose": imp_lose,
            "mean_abs": mean_abs,
        })

    out = {
        "clusters_path": str(cluster_path.resolve()),
        "signal_matrices_path": str(matrix_path.resolve()),
        "conditional_importance": importance,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Conditional importance:", len(importance), "clusters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
