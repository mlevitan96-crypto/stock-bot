#!/usr/bin/env python3
"""
Shadow: Build a replay manifest from a ledger directory (e.g. backfill).
Same contract as init_shadow_replay_harness; use for backfill-based replay. Read-only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Build replay manifest from ledger dir (e.g. backfill)")
    ap.add_argument("--ledger-dir", required=True)
    ap.add_argument("--signal-model", required=True)
    ap.add_argument("--read-only", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ledger_dir = Path(args.ledger_dir)
    model_path = Path(args.signal_model)
    if not model_path.exists():
        print(f"Signal model missing: {model_path}", file=sys.stderr)
        return 2

    ledgers = []
    if ledger_dir.exists():
        for f in sorted(ledger_dir.glob("FULL_TRADE_LEDGER_*.json")):
            ledgers.append(str(f.resolve()))

    manifest = {
        "read_only": True,
        "signal_model_path": str(model_path.resolve()),
        "ledger_paths": ledgers,
        "ledger_count": len(ledgers),
        "status": "ready",
        "ledger_source": str(ledger_dir.resolve()),
        "contract": "Replay deterministically; never touch live or paper config. Ranked candidates only.",
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print("Replay manifest: ledgers", len(ledgers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
