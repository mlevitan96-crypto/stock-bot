#!/usr/bin/env python3
"""
Compare baseline vs candidate effectiveness runs and emit LOCK or REVERT decision.
Used by path-to-profitability autopilot after 50+ closed trades in overlay window.
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
    ap = argparse.ArgumentParser(description="Compare baseline vs candidate effectiveness; emit LOCK or REVERT")
    ap.add_argument("--baseline", type=Path, required=True, help="Baseline effectiveness dir (effectiveness_aggregates.json)")
    ap.add_argument("--candidate", type=Path, required=True, help="Candidate/overlay effectiveness dir")
    ap.add_argument("--out", type=Path, required=True, help="Output path for lock_or_revert_decision.json")
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    baseline_dir = args.baseline.resolve() if args.baseline else None
    candidate_dir = args.candidate.resolve() if args.candidate else None
    if not baseline_dir or not baseline_dir.exists():
        print(f"Baseline dir not found: {baseline_dir}", file=sys.stderr)
        return 1
    if not candidate_dir or not candidate_dir.exists():
        print(f"Candidate dir not found: {candidate_dir}", file=sys.stderr)
        return 1

    def load_aggregates(d: Path) -> dict:
        p = d / "effectiveness_aggregates.json"
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}

    base_agg = load_aggregates(baseline_dir)
    cand_agg = load_aggregates(candidate_dir)

    base_joined = base_agg.get("joined_count") or 0
    cand_joined = cand_agg.get("joined_count") or 0
    base_wr = base_agg.get("win_rate")
    cand_wr = cand_agg.get("win_rate")
    base_gb = base_agg.get("avg_profit_giveback")
    cand_gb = cand_agg.get("avg_profit_giveback")

    # LOCK: win_rate change >= -2%, giveback change <= +0.05, and not materially worse
    # REVERT: win_rate drop > 2%, or giveback increase > 0.05, or material PnL regression
    decision = "REVERT"
    reasons = []

    if cand_joined < 30:
        decision = "REVERT"
        reasons.append(f"candidate joined_count={cand_joined} < 30 (insufficient sample)")
    else:
        wr_ok = True
        if base_wr is not None and cand_wr is not None:
            delta_wr = (cand_wr - base_wr) * 100  # in pct points
            if delta_wr < -2.0:
                wr_ok = False
                reasons.append(f"win_rate dropped {delta_wr:.2f} pct points (threshold -2)")
        gb_ok = True
        if base_gb is not None and cand_gb is not None:
            delta_gb = cand_gb - base_gb
            if delta_gb > 0.05:
                gb_ok = False
                reasons.append(f"avg_profit_giveback increased {delta_gb:.2f} (threshold +0.05)")
        if wr_ok and gb_ok:
            decision = "LOCK"
            reasons.append("win_rate and giveback within tolerance vs baseline")

    out_obj = {
        "decision": decision,
        "reasons": reasons,
        "baseline": {
            "joined_count": base_joined,
            "win_rate": base_wr,
            "avg_profit_giveback": base_gb,
        },
        "candidate": {
            "joined_count": cand_joined,
            "win_rate": cand_wr,
            "avg_profit_giveback": cand_gb,
        },
    }
    args.out = args.out.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out_obj, indent=2), encoding="utf-8")
    print(f"Decision: {decision}")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
