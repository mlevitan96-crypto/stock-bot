#!/usr/bin/env python3
"""
Phase 7 — Backfill joined closed trades from historical logs.

Reads logs/attribution.jsonl and logs/exit_attribution.jsonl; produces
reports/joined_closed_trades_<start>_<end>.jsonl with normalized records.
If older records lack fields, adds quality_flags=["missing"] and
missing_reason="backfill_missing_field:<field>". Never invents values.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.analysis.attribution_loader import load_joined_closed_trades


def _day_utc(ts) -> str:
    if ts is None:
        return ""
    s = str(ts)
    return s[:10] if len(s) >= 10 else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill joined closed trades JSONL from attribution + exit_attribution")
    ap.add_argument("--start", type=str, required=True, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", type=str, required=True, help="End date YYYY-MM-DD")
    ap.add_argument("--base-dir", type=Path, default=REPO, help="Repo root (logs/ under here)")
    ap.add_argument("--out", type=Path, default=None, help="Output path (default: reports/joined_closed_trades_<start>_<end>.jsonl)")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    attr_path = base / "logs" / "attribution.jsonl"
    exit_path = base / "logs" / "exit_attribution.jsonl"
    if not attr_path.exists() or not exit_path.exists():
        print(f"Missing logs: {attr_path} or {exit_path}", file=sys.stderr)
        return 1

    joined = load_joined_closed_trades(attr_path, exit_path, start_date=args.start, end_date=args.end)
    out_path = args.out
    if out_path is None:
        out_path = base / "reports" / f"joined_closed_trades_{args.start}_{args.end}.jsonl"
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    required_entry = ["entry_score", "entry_attribution_components", "entry_regime"]
    required_exit = ["exit_reason_code", "exit_quality_metrics", "pnl"]

    with out_path.open("w", encoding="utf-8") as f:
        for row in joined:
            quality_flags = []
            missing_reasons = []
            for k in required_entry:
                if row.get(k) is None and (k != "entry_attribution_components" or row.get("entry_attribution_components") is None):
                    missing_reasons.append(f"backfill_missing_field:{k}")
            for k in required_exit:
                if row.get(k) is None:
                    missing_reasons.append(f"backfill_missing_field:{k}")
            if missing_reasons:
                quality_flags.append("missing")
            out = dict(row)
            if quality_flags:
                out["quality_flags"] = quality_flags
            if missing_reasons:
                out["missing_reason"] = "; ".join(missing_reasons)
            f.write(json.dumps(out, default=str) + "\n")

    print(f"Wrote {len(joined)} joined records to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
