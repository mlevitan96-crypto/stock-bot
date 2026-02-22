#!/usr/bin/env python3
"""Exit optimization sweep. Stub: writes minimal output. Droplet only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stub = {"status": "stub", "runs": []}
    (out / "exit_sweep.json").write_text(json.dumps(stub, indent=2), encoding="utf-8")
    (out / "exit_sweep_summary.json").write_text(json.dumps(stub, indent=2), encoding="utf-8")
    print(f"Exit optimization (stub) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
