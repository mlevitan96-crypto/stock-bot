#!/usr/bin/env python3
"""
Shadow: Convert alpha gates to a weighted contributor model (shadow-only).
Output: WEIGHTED_SIGNAL_MODEL.json with signal id, weight, normalized range; no veto.
Does not modify live or paper config.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert alpha gates to weighted model (shadow)")
    ap.add_argument("--schema", required=True, help="CANONICAL_SIGNAL_SCHEMA.json")
    ap.add_argument("--mode", default="shadow", choices=("shadow",))
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.schema)
    if not path.exists():
        print(f"Schema missing: {path}", file=sys.stderr)
        return 2

    schema = json.loads(path.read_text(encoding="utf-8"))
    signals = schema.get("signals", [])

    contributors = []
    for s in signals:
        if s.get("veto_allowed"):
            continue
        weight_slot = s.get("weight_slot", f"weight_{s.get('id', '')}")
        contributors.append({
            "signal_id": s.get("id"),
            "key_path": s.get("key_path"),
            "weight": 1.0,
            "weight_slot": weight_slot,
            "normalized_range": s.get("normalized_range", [-1.0, 1.0]),
            "veto_allowed": False,
        })

    model = {
        "version": "1.0",
        "mode": args.mode,
        "contract": "Weighted contributors only; no veto. Shadow-only, read-only.",
        "contributors": contributors,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(model, indent=2, default=str), encoding="utf-8")
    print("Weighted model:", len(contributors), "contributors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
