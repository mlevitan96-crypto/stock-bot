#!/usr/bin/env python3
"""
Shadow: Initialize the shadow replay harness (read-only).
Writes a manifest of ledger paths, signal model path, and read_only flag.
Does not run replays; only declares harness ready for bulk weight sweeps.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Initialize shadow replay harness (read-only)")
    ap.add_argument("--ledger-dir", default="reports/ledger")
    ap.add_argument("--signal-model", required=True, help="WEIGHTED_SIGNAL_MODEL.json path")
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
        "contract": "Replay deterministically; never touch live or paper config. Ranked candidates only.",
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print("Shadow replay ready: ledgers", len(ledgers), "model", model_path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
