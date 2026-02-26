#!/usr/bin/env python3
"""
B1 — Build canonical equity ledger from attribution + exit_attribution join.
Output: reports/replay/canonical_equity_trades.jsonl (one JSON object per line).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Build canonical equity trades ledger (joined attribution + exit)")
    ap.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    ap.add_argument("--out", type=Path, default=REPO / "reports" / "replay" / "canonical_equity_trades.jsonl")
    args = ap.parse_args()

    from scripts.analysis.attribution_loader import load_joined_closed_trades

    attr_path = REPO / "logs" / "attribution.jsonl"
    exit_path = REPO / "logs" / "exit_attribution.jsonl"
    if not attr_path.exists() or not exit_path.exists():
        print("Missing logs/attribution.jsonl or logs/exit_attribution.jsonl", file=sys.stderr)
        return 1

    joined = load_joined_closed_trades(
        attr_path, exit_path,
        start_date=args.start,
        end_date=args.end,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for rec in joined:
            f.write(json.dumps(rec, default=str) + "\n")

    print(f"Wrote {len(joined)} trades to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
