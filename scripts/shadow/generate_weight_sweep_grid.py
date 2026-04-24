#!/usr/bin/env python3
"""
Shadow: Generate a grid of weight combinations for bulk sweeps.
Read-only; uses WEIGHTED_SIGNAL_MODEL. Samples up to max-combinations for tractability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate weight sweep grid")
    ap.add_argument("--signal-model", required=True)
    ap.add_argument("--weight-range", nargs=2, type=float, default=[0.5, 1.5], metavar=("LO", "HI"))
    ap.add_argument("--step", type=float, default=0.1)
    ap.add_argument("--max-combinations", type=int, default=1000)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.signal_model)
    if not path.exists():
        print(f"Signal model missing: {path}", file=sys.stderr)
        return 2

    model = json.loads(path.read_text(encoding="utf-8"))
    contributors = model.get("contributors", [])
    if not contributors:
        print("No contributors in model", file=sys.stderr)
        return 2

    lo, hi = args.weight_range[0], args.weight_range[1]
    steps = [round(lo + i * args.step, 2) for i in range(int((hi - lo) / args.step) + 1)]
    steps = [s for s in steps if lo <= s <= hi]
    if not steps:
        steps = [1.0]

    slot_names = [c.get("weight_slot") or c.get("signal_id") for c in contributors]

    # Deterministic sample: use hash(seed + index) to pick weight per slot for each config
    configs = []
    for idx in range(args.max_combinations):
        h = hashlib.sha256(f"shadow_sweep_{idx}".encode()).digest()
        config = {}
        for i, slot in enumerate(slot_names):
            byte_idx = i % len(h)
            config[slot] = steps[int(h[byte_idx]) % len(steps)]
        config_id = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:12]
        configs.append({"config_id": config_id, "weights": config})

    out = {
        "signal_model_path": str(path.resolve()),
        "weight_range": [lo, hi],
        "step": args.step,
        "max_combinations": args.max_combinations,
        "slot_count": len(slot_names),
        "slot_names": slot_names,
        "config_count": len(configs),
        "configs": configs,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Sweep grid:", len(configs), "configs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
