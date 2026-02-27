#!/usr/bin/env python3
"""
Compare baseline vs tuned exit edge metrics (apples-to-apples).
Output: edge_comparison.json with deltas and pass/fail.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--tuned", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    base_path = Path(args.baseline)
    tuned_path = Path(args.tuned)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    baseline = {}
    tuned = {}
    if base_path.exists():
        try:
            baseline = json.loads(base_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    if tuned_path.exists():
        try:
            tuned = json.loads(tuned_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    base_pnl = (baseline.get("baseline") or {}).get("total_pnl")
    tuned_pnl = (tuned.get("baseline") or {}).get("total_pnl")
    base_n = baseline.get("n_exits", 0)
    tuned_n = tuned.get("n_exits", 0)

    try:
        base_pnl_f = float(base_pnl) if base_pnl is not None else None
        tuned_pnl_f = float(tuned_pnl) if tuned_pnl is not None else None
        pnl_delta = (tuned_pnl_f - base_pnl_f) if (base_pnl_f is not None and tuned_pnl_f is not None) else None
    except (TypeError, ValueError):
        pnl_delta = None

    comparison = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_path": str(base_path),
        "tuned_path": str(tuned_path),
        "baseline_n_exits": base_n,
        "tuned_n_exits": tuned_n,
        "baseline_total_pnl": base_pnl,
        "tuned_total_pnl": tuned_pnl,
        "pnl_delta": pnl_delta,
        "improved": pnl_delta is not None and pnl_delta > 0,
    }
    out_path.write_text(json.dumps(comparison, indent=2, default=str), encoding="utf-8")
    print(f"Comparison: PnL delta={pnl_delta}, improved={comparison['improved']} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
