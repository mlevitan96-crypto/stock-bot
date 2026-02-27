#!/usr/bin/env python3
"""
Inspect exit_reason and exit_regime_decision counts from logs/exit_attribution.jsonl.
Usage: python scripts/inspect_exit_reasons.py [--date YYYY-MM-DD] [--path path/to/exit_attribution.jsonl]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = REPO_ROOT / "logs" / "exit_attribution.jsonl"


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def filter_by_date(records, date_str: str):
    for rec in records:
        ts = rec.get("timestamp") or rec.get("exit_ts") or ""
        if date_str in str(ts)[:10]:
            yield rec


def main():
    ap = argparse.ArgumentParser(description="Inspect exit reasons and regime decisions")
    ap.add_argument("--date", default=None, help="Filter by date YYYY-MM-DD (optional)")
    ap.add_argument("--path", default=None, help="Path to exit_attribution.jsonl")
    args = ap.parse_args()
    path = Path(args.path) if args.path else DEFAULT_PATH
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    records = list(iter_jsonl(path))
    if args.date:
        records = list(filter_by_date(records, args.date))
    if not records:
        print("No records found.")
        return 0
    by_reason = Counter(r.get("exit_reason") or "null" for r in records)
    by_regime = Counter(r.get("exit_regime_decision") or "null" for r in records)
    non_null_regime = sum(1 for r in records if (r.get("exit_regime_decision") or "").strip() and (r.get("exit_regime_decision") or "").lower() != "null")
    pct_regime = (non_null_regime / len(records)) * 100.0 if records else 0.0
    print("=== Exit reasons (exit_reason) ===")
    for reason, count in by_reason.most_common():
        print(f"  {reason}: {count}")
    print("\n=== Exit regime decisions (exit_regime_decision) ===")
    for regime, count in by_regime.most_common():
        print(f"  {regime}: {count}")
    print(f"\nTotal exits: {len(records)}")
    print(f"Exits with non-null regime: {non_null_regime} ({pct_regime:.1f}%)")
    unknown_count = by_reason.get("unknown", 0) + by_reason.get("unknown_exit", 0) + by_reason.get("null", 0)
    if unknown_count > len(records) * 0.1:
        print(f"WARN: unknown/null exit reasons: {unknown_count} ({100.0 * unknown_count / len(records):.1f}%)", file=sys.stderr)
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
