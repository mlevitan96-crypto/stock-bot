#!/usr/bin/env python3
"""
Shadow: Rank weight configurations by criteria (expected_pnl, stability, drawdown).
Higher pnl and stability better; lower drawdown better. Output top-n.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Rank weight configurations")
    ap.add_argument("--results", required=True)
    ap.add_argument("--criteria", nargs="+", default=["expected_pnl", "stability", "drawdown"])
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.results)
    if not path.exists():
        print(f"Results missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results", [])

    # Use realized_pnl as expected_pnl proxy
    def key(r):
        m = r.get("metrics", {}) or {}
        pnl = m.get("realized_pnl", m.get("expected_pnl", 0)) or 0
        stab = m.get("stability", 0) or 0
        dd = m.get("drawdown", 0) or 0
        return (-pnl, -stab, dd)

    sorted_results = sorted(results, key=key)
    top = sorted_results[: args.top_n]
    ranked = [{"rank": i + 1, **r} for i, r in enumerate(top)]

    out = {
        "results_path": str(path.resolve()),
        "criteria": args.criteria,
        "top_n": args.top_n,
        "ranking": ranked,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Ranking: top", len(ranked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
