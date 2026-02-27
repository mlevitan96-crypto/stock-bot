#!/usr/bin/env python3
"""
Generate CONTEXTUAL candidate policies from percent-move entry/exit intelligence.
Trade when: signal state predicts continuation (entry_score >= intel-derived min).
Exit when: hold window aligns with exhaustion/continuation from intel (or from exit_thresholds).
Output: candidate_policies.json for run_policy_simulations. Same schema.
Goal: massive iteration over entry+exit combinations to find profitable signal combinations.
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
    ap.add_argument("--truth", required=True, help="Path to truth (for validation)")
    ap.add_argument("--intelligence", required=True, help="entry_exit_intelligence.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--exit_thresholds", default=None, help="exit_thresholds.json (signal-driven exit hold windows)")
    ap.add_argument("--max_hold_cap_min", type=int, default=0, help="Cap hold_minutes_min at this (0 = no cap)")
    ap.add_argument("--max_candidates", type=int, default=400)
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    intel_path = Path(args.intelligence)
    if not intel_path.is_absolute():
        intel_path = REPO / intel_path
    if not intel_path.exists():
        print(f"Intelligence not found: {intel_path}", file=sys.stderr)
        return 1

    data = json.loads(intel_path.read_text(encoding="utf-8"))
    entry_rules = data.get("entry_intelligence", [])
    exit_rules = data.get("exit_intelligence", [])

    exit_thresholds_by_key = {}
    if args.exit_thresholds:
        et_path = Path(args.exit_thresholds)
        if not et_path.is_absolute():
            et_path = REPO / et_path
        if et_path.exists():
            et_data = json.loads(et_path.read_text(encoding="utf-8"))
            exit_thresholds_by_key = et_data.get("by_tier_direction", {})

    max_hold_cap = int(args.max_hold_cap_min) if args.max_hold_cap_min else 999

    policies = []
    seen = set()
    # More entry bands for profitability search: iterate more combinations
    entry_offsets = [0.0, -0.2, -0.3, -0.5, -0.7]

    for er in entry_rules:
        tier = er.get("tier", "")
        direction = er.get("direction", "up")
        lookback = int(er.get("lookback_minutes", 30))
        avg_score = float(er.get("avg_entry_score_before") or 0)
        if avg_score <= 0:
            continue
        dir_policy = "long" if direction == "up" else "short"

        # Hold options: from exit_thresholds (signal-driven) or from lookback
        hold_candidates = [lookback, max(5, lookback // 2), min(120, lookback * 2)]
        if exit_thresholds_by_key:
            key = f"{tier}_{direction}"
            if key in exit_thresholds_by_key:
                opts = exit_thresholds_by_key[key].get("hold_options_minutes", [])
                if opts:
                    hold_candidates = list(set(hold_candidates + opts))
                he = exit_thresholds_by_key[key].get("hold_exhaustion_min")
                hc = exit_thresholds_by_key[key].get("hold_continuation_min")
                if he is not None:
                    hold_candidates.append(he)
                if hc is not None:
                    hold_candidates.append(hc)
        hold_candidates = sorted(set(max(1, min(h, max_hold_cap)) for h in hold_candidates if h > 0))

        for off in entry_offsets:
            entry_min = round(max(0.0, avg_score + off), 2)
            for hold in hold_candidates:
                if hold <= 0:
                    hold = 30
                key = (tier, direction, entry_min, hold, dir_policy)
                if key in seen:
                    continue
                seen.add(key)
                policies.append({
                    "policy_id": f"policy_{len(policies)+1:04d}",
                    "entry_score_min": entry_min,
                    "hold_minutes_min": hold,
                    "direction": dir_policy,
                    "no_suppression": args.no_suppression,
                    "contextual_tier": tier,
                    "contextual_direction": direction,
                })
                if len(policies) >= args.max_candidates:
                    break
            if len(policies) >= args.max_candidates:
                break
        if len(policies) >= args.max_candidates:
            break

    # Add "both" direction variants for more combination coverage
    if len(policies) < args.max_candidates:
        for er in entry_rules:
            tier = er.get("tier", "")
            direction = er.get("direction", "up")
            lookback = int(er.get("lookback_minutes", 30))
            avg_score = float(er.get("avg_entry_score_before") or 0)
            if avg_score <= 0:
                continue
            for entry_min in [round(max(0.0, avg_score - 0.3), 2), round(max(0.0, avg_score - 0.5), 2)]:
                hold_candidates = [lookback, max(5, lookback // 2), min(120, lookback * 2)]
                if exit_thresholds_by_key:
                    for d in ("up", "down"):
                        key = f"{tier}_{d}"
                        if key in exit_thresholds_by_key:
                            opts = exit_thresholds_by_key[key].get("hold_options_minutes", [])
                            hold_candidates.extend(opts or [])
                hold_candidates = sorted(set(max(1, min(h, max_hold_cap)) for h in hold_candidates if h > 0))[:5]
                for hold in hold_candidates:
                    key = (tier, "both", entry_min, hold)
                    if key in seen:
                        continue
                    seen.add(key)
                    policies.append({
                        "policy_id": f"policy_{len(policies)+1:04d}",
                        "entry_score_min": entry_min,
                        "hold_minutes_min": hold,
                        "direction": "both",
                        "no_suppression": args.no_suppression,
                        "contextual_tier": tier,
                        "contextual_direction": "both",
                    })
                    if len(policies) >= args.max_candidates:
                        break
                if len(policies) >= args.max_candidates:
                    break
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
    print(f"Generated {len(policies)} contextual candidate policies -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
