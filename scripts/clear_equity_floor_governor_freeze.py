#!/usr/bin/env python3
"""
Deactivate account_equity_floor_breached in state/governor_freezes.json (dict-shaped freezes).

Also clears boolean production_freeze / meta_integrity_protect when present (rollback rollup).

Usage:
  PYTHONPATH=. python3 scripts/clear_equity_floor_governor_freeze.py --dry-run
  PYTHONPATH=. python3 scripts/clear_equity_floor_governor_freeze.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    if not args.dry_run and not args.apply:
        print("Specify --dry-run or --apply", file=sys.stderr)
        return 2

    path = REPO / "state" / "governor_freezes.json"
    if not path.exists():
        print("No governor_freezes.json — nothing to do")
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        print("Failed to read freezes:", e, file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("Unexpected format", file=sys.stderr)
        return 1

    changed = False
    out = dict(data)
    k = "account_equity_floor_breached"
    v = out.get(k)
    if isinstance(v, dict) and v.get("active") is True:
        nv = dict(v)
        nv["active"] = False
        nv["cleared_at"] = datetime.now(timezone.utc).isoformat()
        nv["cleared_by"] = "clear_equity_floor_governor_freeze.py"
        out[k] = nv
        changed = True
    elif v is True:
        out[k] = False
        changed = True

    for rollup in ("production_freeze", "meta_integrity_protect"):
        if out.get(rollup) is True:
            out[rollup] = False
            changed = True

    print(json.dumps({"changed": changed, "preview_keys": list(out.keys())}, indent=2))
    if args.dry_run or not changed:
        return 0
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Updated", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
