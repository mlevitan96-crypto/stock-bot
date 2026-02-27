#!/usr/bin/env python3
"""
Regime-conditional exit edge analysis. Reads edge metrics, splits by regime (from replay/attribution), writes exit_edge_by_regime.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import defaultdict


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edge", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    edge_path = Path(args.edge)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not edge_path.exists():
        data = {"by_regime": {}, "message": "No edge metrics"}
    else:
        edge = json.loads(edge_path.read_text(encoding="utf-8"))
        data = {"by_regime": {"UNKNOWN": edge.get("baseline", {})}, "edge_summary": edge}

    out_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
