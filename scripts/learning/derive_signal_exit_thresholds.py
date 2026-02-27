#!/usr/bin/env python3
"""
Derive signal-driven exit thresholds from entry_exit_intelligence.json.
High exhaustion_pct -> exit sooner (shorter recommended hold).
High continuation_pct -> hold longer.
Output: exit_thresholds.json for generate_contextual_policies (hold windows by tier/direction).
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
    ap.add_argument("--intelligence", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    intel_path = Path(args.intelligence)
    if not intel_path.is_absolute():
        intel_path = REPO / intel_path
    if not intel_path.exists():
        print(f"Intelligence not found: {intel_path}", file=sys.stderr)
        return 1

    data = json.loads(intel_path.read_text(encoding="utf-8"))
    exit_rules = data.get("exit_intelligence", [])

    # Per (tier, direction): recommend hold_min (exit sooner when exhaustion high),
    # hold_max (hold longer when continuation high), and list of (lookahead_min, exhaustion_pct, continuation_pct)
    by_tier_dir = {}
    for r in exit_rules:
        tier = r.get("tier", "")
        direction = r.get("direction", "up")
        lookahead = int(r.get("lookahead_minutes", 30))
        exhaustion = float(r.get("exhaustion_pct") or 0)
        continuation = float(r.get("continuation_pct") or 0)
        avg_pnl_after = float(r.get("avg_pnl_pct_after") or 0)
        key = (tier, direction)
        if key not in by_tier_dir:
            by_tier_dir[key] = {"hold_options": [], "exhaustion_hold_min": None, "continuation_hold_min": None}
        by_tier_dir[key]["hold_options"].append({
            "lookahead_minutes": lookahead,
            "exhaustion_pct": exhaustion,
            "continuation_pct": continuation,
            "avg_pnl_pct_after": avg_pnl_after,
        })

    thresholds = []
    for (tier, direction), v in sorted(by_tier_dir.items()):
        opts = v["hold_options"]
        if not opts:
            continue
        # When exhaustion dominates, prefer shorter hold (exit sooner)
        exhaustion_favor = [o for o in opts if o["exhaustion_pct"] >= 70]
        continuation_favor = [o for o in opts if o["continuation_pct"] >= 25 and o["avg_pnl_pct_after"] > 0]
        hold_exhaustion = min((o["lookahead_minutes"] for o in exhaustion_favor), default=15)
        hold_continuation = max((o["lookahead_minutes"] for o in continuation_favor), default=60) if continuation_favor else 60
        thresholds.append({
            "tier": tier,
            "direction": direction,
            "hold_exhaustion_min": hold_exhaustion,
            "hold_continuation_min": hold_continuation,
            "hold_options_minutes": sorted(set(o["lookahead_minutes"] for o in opts)),
        })

    out = {
        "exit_thresholds": thresholds,
        "by_tier_direction": {
            f"{t['tier']}_{t['direction']}": {
                "hold_exhaustion_min": t["hold_exhaustion_min"],
                "hold_continuation_min": t["hold_continuation_min"],
                "hold_options_minutes": t["hold_options_minutes"],
            }
            for t in thresholds
        },
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Derived {len(thresholds)} exit threshold rules -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
