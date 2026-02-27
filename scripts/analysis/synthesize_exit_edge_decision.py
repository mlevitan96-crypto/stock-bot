#!/usr/bin/env python3
"""
Synthesize final board decision from edge metrics, regime analysis, and board review.
Output: BOARD_DECISION.json with decision (PROMOTE | TUNE | HOLD) and rationale.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edge", required=True)
    ap.add_argument("--regime", required=True)
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    edge_path = Path(args.edge)
    regime_path = Path(args.regime)
    board_path = Path(args.board)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    edge = {}
    if edge_path.exists():
        try:
            edge = json.loads(edge_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    regime = {}
    if regime_path.exists():
        try:
            regime = json.loads(regime_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    n_exits = edge.get("n_exits", 0)
    baseline_pnl = (edge.get("baseline") or {}).get("total_pnl")
    decision = "HOLD"
    rationale = "Evidence-only run; no behavior change. Re-run after CTR has more exits or tune config and re-run."

    if n_exits >= 30 and baseline_pnl is not None and float(baseline_pnl) > 0:
        decision = "TUNE"
        rationale = "Positive baseline PnL and sufficient exits; consider TUNE (config-only) then re-run for PROMOTE."
    elif n_exits >= 50:
        decision = "TUNE"
        rationale = "Sufficient sample; run TUNE path (config patch) and re-run exit edge discovery."

    out = {
        "decision": decision,
        "rationale": rationale,
        "n_exits": n_exits,
        "baseline_total_pnl": baseline_pnl,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "edge_path": str(edge_path),
        "regime_path": str(regime_path),
        "board_path": str(board_path),
    }
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"BOARD_DECISION: {decision}")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
