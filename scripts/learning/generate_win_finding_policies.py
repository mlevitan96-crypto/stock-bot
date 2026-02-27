#!/usr/bin/env python3
"""
Generate a WIDE grid of policies to find winning combinations with high MIN_TRADES (e.g. 2000).
Concept: stocks move up or down; we need entry filters that capture moves ahead of time
and exit (hold) rules that exit before we lose. This grid includes:
- Permissive: low entry_min, low hold_min to reach 2000+ trades
- Intel-driven: from entry_exit_intelligence for signal-aligned combinations
Goal: find entry_min + hold_min + direction combinations that yield 2000+ trades and positive PnL.
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
    ap.add_argument("--truth", required=True)
    ap.add_argument("--intelligence", default=None, help="entry_exit_intelligence.json (optional)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max_candidates", type=int, default=600)
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    policies = []
    seen = set()

    # 1) Permissive grid: capture maximum trades to find if any 2000+ subset is profitable
    entry_mins = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5]
    hold_mins = [0, 5, 10, 15, 20, 25, 30, 45, 60]
    directions = ["long", "short", "both"]
    for em in entry_mins:
        for hm in hold_mins:
            for d in directions:
                key = ("perm", round(em, 2), hm, d)
                if key in seen:
                    continue
                seen.add(key)
                policies.append({
                    "policy_id": f"policy_{len(policies)+1:04d}",
                    "entry_score_min": round(em, 2),
                    "hold_minutes_min": hm,
                    "direction": d,
                    "no_suppression": args.no_suppression,
                    "source": "permissive_grid",
                })
                if len(policies) >= args.max_candidates:
                    break
            if len(policies) >= args.max_candidates:
                break
        if len(policies) >= args.max_candidates:
            break

    # 2) Intel-driven: what causes up/down (entry_score before move) + exit before we lose (hold from exhaustion)
    if args.intelligence and len(policies) < args.max_candidates:
        intel_path = Path(args.intelligence)
        if not intel_path.is_absolute():
            intel_path = REPO / intel_path
        if intel_path.exists():
            data = json.loads(intel_path.read_text(encoding="utf-8"))
            entry_rules = data.get("entry_intelligence", [])
            for er in entry_rules:
                if len(policies) >= args.max_candidates:
                    break
                tier = er.get("tier", "")
                direction = er.get("direction", "up")
                lookback = int(er.get("lookback_minutes", 30))
                avg_score = float(er.get("avg_entry_score_before") or 0)
                if avg_score <= 0:
                    continue
                dir_policy = "long" if direction == "up" else "short"
                for entry_min in [round(max(0, avg_score - 0.5), 2), round(max(0, avg_score - 0.3), 2), round(avg_score, 2)]:
                    for hold in [5, 10, 15, lookback, 30, 45, 60]:
                        if hold <= 0:
                            hold = 30
                        key = ("intel", tier, direction, entry_min, hold)
                        if key in seen:
                            continue
                        seen.add(key)
                        policies.append({
                            "policy_id": f"policy_{len(policies)+1:04d}",
                            "entry_score_min": entry_min,
                            "hold_minutes_min": hold,
                            "direction": dir_policy,
                            "no_suppression": args.no_suppression,
                            "source": "intel",
                            "contextual_tier": tier,
                        })
                        if len(policies) >= args.max_candidates:
                            break

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"policies": policies, "count": len(policies)}, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Generated {len(policies)} win-finding policies (permissive + intel) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
