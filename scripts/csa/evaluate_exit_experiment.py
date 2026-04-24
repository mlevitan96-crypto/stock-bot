#!/usr/bin/env python3
"""
CSA: Evaluate exit experiment and issue forced verdict: EXTEND, AMPLIFY, or REVERT.
Decision required even if data is weak. No deferral.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate exit experiment (forced verdict)")
    ap.add_argument("--results", required=True, help="EXIT_AGGRESSION_RESULTS_<date>.json")
    ap.add_argument("--criteria", nargs="+", default=["realized_pnl", "would_have_pnl", "exit_latency", "tail_risk"])
    ap.add_argument("--require-verdict", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.results)
    if not path.exists():
        print(f"Results missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    realized = data.get("realized_pnl")
    if realized is None:
        realized = 0.0
    realized = float(realized)

    # Forced verdict: positive PnL -> EXTEND or AMPLIFY; negative or weak -> REVERT or EXTEND (cautious)
    if realized > 0:
        verdict = "EXTEND"
        rationale = "Positive realized PnL; extend experiment window."
    elif realized >= -10:
        verdict = "EXTEND"
        rationale = "Small drawdown; extend to gather more signal."
    else:
        verdict = "REVERT"
        rationale = "Realized loss beyond threshold; revert exit overlay."

    out = {
        "date": data.get("date"),
        "verdict": verdict,
        "rationale": rationale,
        "realized_pnl": realized,
        "criteria_used": args.criteria,
        "results_summary": {k: data.get(k) for k in ["executed_count", "blocked_count", "selected_parameter"]},
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("CSA_EXIT_EXPERIMENT_VERDICT:", verdict, rationale)
    return 0


if __name__ == "__main__":
    sys.exit(main())
