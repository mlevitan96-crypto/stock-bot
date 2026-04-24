#!/usr/bin/env python3
"""Smoke: fail if logs/signal_context.jsonl is missing or has zero valid JSON lines."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    args = ap.parse_args()
    path = args.root.resolve() / "logs" / "signal_context.jsonl"
    if not path.is_file():
        print("FAIL: missing", path, file=sys.stderr)
        return 1
    n = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                n += 1
    if n == 0:
        print("FAIL: zero valid JSONL rows in", path, file=sys.stderr)
        return 2
    print("OK:", n, "rows in", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
