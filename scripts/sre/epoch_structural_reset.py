#!/usr/bin/env python3
"""
Structural epoch reset (DANGEROUS): backs up then clears selected state files.

**Default:** dry-run only. Pass ``--execute`` to write files.

Touches:
  - state/position_metadata.json  → ``{}``
  - reports/state/TRADE_CSA_STATE.json → default zeros (canonical trade counters / CSA bookkeeping)

Does **not** delete logs, orders, or Alpaca broker state.

Usage:
  PYTHONPATH=. python scripts/sre/epoch_structural_reset.py --root /root/stock-bot --dry-run
  PYTHONPATH=. python scripts/sre/epoch_structural_reset.py --root /root/stock-bot --execute
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _backup(p: Path, stamp: str) -> Path:
    if not p.is_file():
        return p
    dest = p.with_suffix(p.suffix + f".bak_{stamp}")
    shutil.copy2(p, dest)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description="Epoch structural reset (position_metadata + CSA counters).")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--execute", action="store_true", help="Perform writes (otherwise dry-run).")
    ap.add_argument("--dry-run", action="store_true", help="Print plan only (default if --execute omitted).")
    args = ap.parse_args()
    root = args.root.resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")

    from config.registry import StateFiles
    from src.infra.csa_trade_state import STATE_FILE, _default_state

    targets = [
        ("position_metadata", StateFiles.POSITION_METADATA, {}),
        ("trade_csa_state", STATE_FILE, _default_state()),
    ]
    plan = []
    for name, path, new_body in targets:
        plan.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.is_file(),
                "would_write": new_body,
            }
        )
    print(json.dumps({"stamp": stamp, "execute": bool(args.execute), "targets": plan}, indent=2))
    if not args.execute:
        print("Dry-run only. Re-run with --execute after operator approval.", flush=True)
        return 0

    for name, path, new_body in targets:
        if path.is_file():
            _backup(path, stamp)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(new_body, indent=2, default=str), encoding="utf-8")
        print(f"Wrote {name} -> {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
