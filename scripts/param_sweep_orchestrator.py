#!/usr/bin/env python3
"""Coarse param sweep. Stub: writes minimal results. Analytical only; no live config change. Droplet only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", default=None)
    ap.add_argument("--param-grid", default=None)
    ap.add_argument("--parallel", type=int, default=1)
    ap.add_argument("--lab-mode", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = {"status": "stub", "param_grid": args.param_grid, "runs": []}
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out / "pareto_frontier.json").write_text(json.dumps({"pareto_frontier": [], "status": "stub"}, indent=2), encoding="utf-8")
    print(f"Param sweep (stub) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
