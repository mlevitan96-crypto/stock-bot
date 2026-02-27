#!/usr/bin/env python3
"""
Build unified entry/exit intelligence from pre-move and post-move correlation outputs.
Summarizes: when to enter (including after small move if signal says more), when to exit vs hold.
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
    ap.add_argument("--pre", required=True, help="signal_pre_move_intelligence.json")
    ap.add_argument("--post", required=True, help="signal_post_move_intelligence.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pre_path = Path(args.pre)
    post_path = Path(args.post)
    if not pre_path.is_absolute():
        pre_path = REPO / pre_path
    if not post_path.is_absolute():
        post_path = REPO / post_path
    if not pre_path.exists():
        print(f"Pre-move file not found: {pre_path}", file=sys.stderr)
        return 1
    if not post_path.exists():
        print(f"Post-move file not found: {post_path}", file=sys.stderr)
        return 1

    pre = json.loads(pre_path.read_text(encoding="utf-8"))
    post = json.loads(post_path.read_text(encoding="utf-8"))

    pre_by_key = {(r["tier"], r["direction"], r["lookback_minutes"]): r for r in pre.get("pre_move_intelligence", [])}
    post_by_key = {(r["tier"], r["direction"], r["lookahead_minutes"]): r for r in post.get("post_move_intelligence", [])}

    entry_rules = []
    exit_rules = []
    for (tier, direction, lb_min), pr in pre_by_key.items():
        entry_rules.append({
            "tier": tier,
            "direction": direction,
            "lookback_minutes": lb_min,
            "avg_entry_score_before": pr.get("avg_entry_score_before"),
            "avg_move_pnl_pct": pr.get("avg_move_pnl_pct"),
            "implication": "Enter when entry_score is high in lookback before a likely move; can enter after small move if signal strengthens and tier suggests more move.",
        })
    for (tier, direction, la_min), po in post_by_key.items():
        exit_rules.append({
            "tier": tier,
            "direction": direction,
            "lookahead_minutes": la_min,
            "avg_pnl_pct_after": po.get("avg_pnl_pct_after"),
            "continuation_pct": po.get("continuation_pct"),
            "exhaustion_pct": po.get("exhaustion_pct"),
            "implication": "Exit when exhaustion_pct is high after a move; hold when continuation_pct is high.",
        })

    out = {
        "entry_intelligence": entry_rules,
        "exit_intelligence": exit_rules,
        "move_pcts": pre.get("move_pcts", []),
        "profitability_note": "Enter on signal even after a small move (+X% already) when pre-move intelligence shows more upside; exit when post-move intelligence shows exhaustion.",
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Entry/exit intelligence -> {out_path} (entry_rules={len(entry_rules)}, exit_rules={len(exit_rules)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
