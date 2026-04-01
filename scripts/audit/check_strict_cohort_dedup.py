#!/usr/bin/env python3
"""
Assert strict_cohort_trade_ids has no duplicate trade_id (SRE-EDGE-001 audit).

Loads a gate export JSON (or the newest ALPACA_STRICT_GATE_SNAPSHOT_*.json under reports/).

Exit 0 if len(ids) == len(set(ids)); exit 1 otherwise.

Usage:
  PYTHONPATH=. python3 scripts/audit/check_strict_cohort_dedup.py --root /root/stock-bot
  PYTHONPATH=. python3 scripts/audit/check_strict_cohort_dedup.py --json reports/daily/.../ALPACA_STRICT_GATE_SNAPSHOT_*.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _newest_gate_snapshot(root: Path) -> Path | None:
    root = root.resolve()
    candidates = sorted(
        root.glob("reports/**/ALPACA_STRICT_GATE_SNAPSHOT_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit strict_cohort_trade_ids for duplicates")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--json", type=Path, default=None, help="Gate export JSON path")
    args = ap.parse_args()
    root = args.root.resolve()
    path = args.json.resolve() if args.json else _newest_gate_snapshot(root)
    if not path or not path.is_file():
        print("ERROR: no gate snapshot JSON found (use --json)", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    ids = data.get("strict_cohort_trade_ids") or []
    if not isinstance(ids, list):
        print("ERROR: strict_cohort_trade_ids missing or not a list", file=sys.stderr)
        return 2

    n = len(ids)
    u = len(set(ids))
    dups = n - u
    print(json.dumps({"json_path": str(path), "cohort_len": n, "unique_len": u, "duplicates": dups}, indent=2))
    if dups != 0:
        from collections import Counter

        c = Counter(ids)
        examples = [k for k, v in c.items() if v > 1][:20]
        print("DUPLICATE trade_ids (sample):", examples, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
