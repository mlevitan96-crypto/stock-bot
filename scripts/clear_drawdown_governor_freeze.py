#!/usr/bin/env python3
"""
Deactivate drawdown-related entries in state/governor_freezes.json (dict-shaped freezes).

Usage:
  python3 scripts/clear_drawdown_governor_freeze.py --dry-run
  python3 scripts/clear_drawdown_governor_freeze.py --apply
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


def _is_drawdown_key(k: str) -> bool:
    s = str(k).lower()
    return "drawdown" in s or "max_drawdown" in s


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
    for k, v in list(out.items()):
        if not _is_drawdown_key(k):
            continue
        if isinstance(v, dict):
            if v.get("active") is True:
                v = dict(v)
                v["active"] = False
                v["cleared_at"] = datetime.now(timezone.utc).isoformat()
                v["cleared_by"] = "clear_drawdown_governor_freeze.py"
                out[k] = v
                changed = True
        elif v is True:
            out[k] = False
            changed = True

    print(json.dumps({"changed": changed, "keys_touched": [k for k in out if _is_drawdown_key(k)]}, indent=2))
    if args.dry_run or not changed:
        return 0
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Updated", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
