#!/usr/bin/env python3
"""
Shadow: Compute correlation matrices between signals (optionally conditioned on outcome).
Read-only. Uses simple Pearson-style correlation; no scipy required.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _correlation(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2 or len(y) != n:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((b - my) ** 2 for b in y) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute signal correlations")
    ap.add_argument("--signal-matrices", required=True)
    ap.add_argument("--condition-on", default=None, choices=(None, "outcome"), help="Split by outcome if 'outcome'")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.signal_matrices)
    if not path.exists():
        print(f"Signal matrices missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    signal_names = data.get("signal_names", [])
    matrix = data.get("matrix", [])
    outcome = data.get("outcome", [])

    if not signal_names or not matrix:
        print("No signals or matrix", file=sys.stderr)
        return 2

    # Build columns
    cols = [[row[i] for row in matrix] for i in range(len(signal_names))]
    n = len(signal_names)
    corr = [[0.0] * n for _ in range(n)]
    for i in range(n):
        corr[i][i] = 1.0
        for j in range(i + 1, n):
            r = _correlation(cols[i], cols[j])
            corr[i][j] = corr[j][i] = round(r, 4)

    result = {
        "signal_names": signal_names,
        "correlation_matrix": corr,
        "condition_on": args.condition_on,
        "n_observations": len(matrix),
    }

    if args.condition_on == "outcome" and outcome:
        # By outcome: win vs loss
        win_cols = [[row[i] for row, o in zip(matrix, outcome) if o == 1] for i in range(len(signal_names))]
        lose_cols = [[row[i] for row, o in zip(matrix, outcome) if o == 0] for i in range(len(signal_names))]
        nw, nl = len(win_cols[0]) if win_cols else 0, len(lose_cols[0]) if lose_cols else 0
        corr_win = [[0.0] * n for _ in range(n)]
        corr_lose = [[0.0] * n for _ in range(n)]
        for i in range(n):
            corr_win[i][i] = corr_lose[i][i] = 1.0
            for j in range(i + 1, n):
                if nw >= 2:
                    rw = _correlation(win_cols[i], win_cols[j])
                    corr_win[i][j] = corr_win[j][i] = round(rw, 4)
                if nl >= 2:
                    rl = _correlation(lose_cols[i], lose_cols[j])
                    corr_lose[i][j] = corr_lose[j][i] = round(rl, 4)
        result["correlation_matrix_win"] = corr_win
        result["correlation_matrix_lose"] = corr_lose
        result["n_win"] = nw
        result["n_lose"] = nl

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print("Correlations: ", n, "x", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
