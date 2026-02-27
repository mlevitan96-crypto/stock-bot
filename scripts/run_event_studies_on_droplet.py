#!/usr/bin/env python3
"""Event studies (lab-mode). Stub: writes minimal summary if no full implementation. Droplet only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", default=None)
    ap.add_argument("--lab-mode", action="store_true")
    ap.add_argument("--horizons", default="1,5,15,60,1440,4320")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {"horizons": args.horizons.split(","), "lab_mode": args.lab_mode, "status": "stub"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Event studies (stub) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
