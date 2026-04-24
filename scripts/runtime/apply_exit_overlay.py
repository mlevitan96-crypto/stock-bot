#!/usr/bin/env python3
"""
Apply exit weight delta to produce a paper overlay. Base from existing tuning or schema defaults.
Entries unchanged; exit-only. Output: config/overlays/exit_aggression_paper.json (or config/tuning/overlays/).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Schema default keys for exit_weights (from config/tuning/schema.json)
DEFAULT_EXIT_WEIGHT_KEYS = [
    "flow_deterioration", "darkpool_deterioration", "sentiment_deterioration",
    "score_deterioration", "regime_shift", "sector_shift", "vol_expansion", "thesis_invalidated",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply exit weight overlay for paper")
    ap.add_argument("--base-config", default=None, help="Base config (optional); else use defaults or tuning overlay")
    ap.add_argument("--weight-delta", type=float, default=0.15, help="Add this to primary exit weight")
    ap.add_argument("--mode", default="paper")
    ap.add_argument("--output", required=True, help="e.g. config/overlays/exit_aggression_paper.json")
    args = ap.parse_args()

    base_weights = {}
    if args.base_config:
        p = Path(args.base_config)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            base_weights = (data.get("exit_weights") or {}).copy()
    if not base_weights:
        # Use existing overlay as base if present
        for candidate in [
            Path("config/tuning/overlays/exit_flow_weight_phase9.json"),
            Path("config/tuning/overlays/exit_flow_plus_0_02.json"),
        ]:
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                base_weights = (data.get("exit_weights") or {}).copy()
                break
    if not base_weights:
        base_weights = {k: 0.2 for k in DEFAULT_EXIT_WEIGHT_KEYS}

    # Apply +delta to primary exit weight (flow_deterioration as highest impact)
    primary = "flow_deterioration"
    if primary not in base_weights:
        primary = next(iter(base_weights), "flow_deterioration")
    delta = float(args.weight_delta)
    out_weights = dict(base_weights)
    out_weights[primary] = round(out_weights.get(primary, 0.2) + delta, 4)

    out = {
        "version": "exit_aggression_paper_+0.15",
        "exit_weights": out_weights,
        "meta": {"mode": args.mode, "delta_applied": delta, "primary_key": primary},
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, primary, "=", out_weights[primary])
    return 0


if __name__ == "__main__":
    sys.exit(main())
