#!/usr/bin/env python3
"""Seed ``state/continuous_pnl_ledger.jsonl`` from current exit + run JSONL tails (post-deploy / post-epoch)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=REPO, help="Repo root (default: inferred).")
    ap.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-empty ledger (default: skip if ledger already has rows).",
    )
    args = ap.parse_args()
    from telemetry.continuous_pnl_ledger import (
        continuous_pnl_ledger_path,
        seed_continuous_pnl_ledger_from_logs,
        _ledger_has_v1_rows,
    )

    root = args.root.resolve()
    n = seed_continuous_pnl_ledger_from_logs(root, force=bool(args.force))
    if n == 0 and not args.force and _ledger_has_v1_rows(continuous_pnl_ledger_path(root)):
        print("Skipped: ledger already has v1 rows; pass --force to rebuild.", flush=True)
        return 0
    if n == 0:
        print("Wrote 0 rows (no qualifying exits in tail or all excluded).", flush=True)
        return 0
    print(f"Wrote {n} rows -> {root / 'state' / 'continuous_pnl_ledger.jsonl'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
