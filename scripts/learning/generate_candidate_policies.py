#!/usr/bin/env python3
"""
Generate candidate policies (entry/exit/direction/sizing combinations) from signal stats.
Output: candidate_policies.json for run_policy_simulations. No suppression.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal_stats", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max_candidates", type=int, default=96)
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    stats_path = Path(args.signal_stats)
    if not stats_path.is_absolute():
        stats_path = REPO / stats_path
    if not stats_path.exists():
        policies = []
        print("Signal stats not found; generating default policy set", file=sys.stderr)
    else:
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        buckets = stats.get("entry_buckets", {})
        policies = []
        entry_thresholds = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6]
        hold_mins = [5, 15, 30, 60, 120]
        directions = ["long", "short", "both"]
        for i, (et, hold, direction) in enumerate(
            [(e, h, d) for e in entry_thresholds for h in hold_mins for d in directions]
        ):
            if i >= args.max_candidates:
                break
            policies.append({
                "policy_id": f"policy_{i+1:04d}",
                "entry_score_min": et,
                "hold_minutes_min": hold,
                "direction": direction,
                "no_suppression": args.no_suppression,
            })

    if len(policies) < args.max_candidates:
        for j in range(len(policies), args.max_candidates):
            policies.append({
                "policy_id": f"policy_{j+1:04d}",
                "entry_score_min": 0.0,
                "hold_minutes_min": 30,
                "direction": "both",
                "no_suppression": True,
            })

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"policies": policies, "count": len(policies)}, indent=2, default=str), encoding="utf-8")
    print(f"Generated {len(policies)} candidate policies -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
