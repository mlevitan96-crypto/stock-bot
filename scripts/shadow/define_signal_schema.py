#!/usr/bin/env python3
"""
Shadow: Define canonical signal schema from classified gates.
All alpha signals: normalized output in [-1, +1], weight slot, no veto.
Output written to shadow/config for replay harness use only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Define canonical signal schema")
    ap.add_argument("--classification", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.classification)
    if not path.exists():
        print(f"Classification missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    gates = data.get("gates", [])
    alpha_only = [g for g in gates if g.get("classification") == "alpha"]

    signals = []
    seen = set()
    for g in alpha_only:
        key_path = g.get("key_path", "")
        if not key_path or key_path in seen:
            continue
        seen.add(key_path)
        signal_id = key_path.replace(".", "_")
        signals.append({
            "id": signal_id,
            "key_path": key_path,
            "normalized_range": [-1.0, 1.0],
            "weight_slot": f"weight_{signal_id}",
            "veto_allowed": False,
            "description": f"Alpha contributor from {g.get('source', '')}",
        })

    schema = {
        "version": "1.0",
        "contract": "All alpha signals contribute continuously; no signal may veto. Normalized to [-1, +1].",
        "signals": signals,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(schema, indent=2, default=str), encoding="utf-8")
    print("Canonical schema: ", len(signals), "signals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
