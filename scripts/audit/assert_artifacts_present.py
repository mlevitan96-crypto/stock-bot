#!/usr/bin/env python3
"""
Assert that all required artifact paths exist. FAIL-CLOSED: exit 1 if any missing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert required artifacts exist")
    ap.add_argument("--required", nargs="+", required=True, help="Paths to required files (relative to cwd or absolute)")
    ap.add_argument("--base-dir", default=None, help="Base dir for relative paths")
    args = ap.parse_args()

    base = Path(args.base_dir).resolve() if args.base_dir else Path.cwd()
    missing = []
    for p in args.required:
        path = (base / p) if not Path(p).is_absolute() else Path(p)
        if not path.exists():
            missing.append(str(path))

    if missing:
        for m in missing:
            print("Missing:", m, file=sys.stderr)
        return 1
    print("All required artifacts present:", len(args.required))
    return 0


if __name__ == "__main__":
    sys.exit(main())
