#!/usr/bin/env python3
"""
Simulate each candidate policy against real truth data. Resumable.
Writes iterations/policy_XXXX/iteration_result.json and baseline/backtest_summary.json for multi_model.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _simulate_one(truth: dict, policy: dict) -> dict:
    trades = truth.get("trades", [])
    exits = truth.get("exits", [])
    entry_min = float(policy.get("entry_score_min", 0))
    hold_min = int(policy.get("hold_minutes_min", 0))
    direction = (policy.get("direction") or "both").lower()

    total_pnl = 0.0
    count = 0
    wins = 0
    for t in trades:
        score = t.get("entry_score")
        try:
            s = float(score) if score is not None else 0.0
        except (TypeError, ValueError):
            s = 0.0
        if s < entry_min:
            continue
        pnl = t.get("pnl_usd")
        try:
            p = float(pnl) if pnl is not None else None
        except (TypeError, ValueError):
            p = None
        if p is None:
            pct = t.get("pnl_pct")
            try:
                pct_f = float(pct) if pct is not None else 0.0
            except (TypeError, ValueError):
                pct_f = 0.0
            notional = 1000.0
            p = (pct_f / 100.0) * notional if pct_f else 0.0
        else:
            p = float(p)
        hold = t.get("hold_minutes") or 0
        try:
            h = int(hold) if hold is not None else 0
        except (TypeError, ValueError):
            h = 0
        if hold_min and h < hold_min:
            continue
        total_pnl += p
        count += 1
        if p > 0:
            wins += 1

    win_rate = (100 * wins / count) if count else 0.0

    return {
        "TOTAL_PNL_AFTER_COSTS": round(total_pnl, 2),
        "trades_count": count,
        "win_rate_pct": round(win_rate, 2),
        "total_pnl_usd": round(total_pnl, 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--policies", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parallelism", type=int, default=8)
    ap.add_argument("--objective", default="MAX_PNL_AFTER_COSTS")
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    truth_path = Path(args.truth)
    if not truth_path.is_absolute():
        truth_path = REPO / truth_path
    policies_path = Path(args.policies)
    if not policies_path.is_absolute():
        policies_path = REPO / policies_path

    if not truth_path.exists():
        print(f"Truth not found: {truth_path}", file=sys.stderr)
        return 1
    if not policies_path.exists():
        print(f"Policies not found: {policies_path}", file=sys.stderr)
        return 1

    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    data = json.loads(policies_path.read_text(encoding="utf-8"))
    policies = data.get("policies", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = REPO / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    def do_one(i: int, policy: dict):
        pid = policy.get("policy_id", f"policy_{i+1:04d}")
        iter_dir = out_root / pid
        res_path = iter_dir / "iteration_result.json"
        if res_path.exists():
            return
        iter_dir.mkdir(parents=True, exist_ok=True)
        result = _simulate_one(truth, policy)
        iteration_result = {
            "iter_id": pid,
            "policy_id": pid,
            "objective": args.objective,
            "idea": f"entry_min={policy.get('entry_score_min')} hold_min={policy.get('hold_minutes_min')} dir={policy.get('direction')}",
            "no_suppression": args.no_suppression,
            "TOTAL_PNL_AFTER_COSTS": result["TOTAL_PNL_AFTER_COSTS"],
            "trades_count": result["trades_count"],
            "win_rate_pct": result["win_rate_pct"],
        }
        (iter_dir / "iteration_result.json").write_text(
            json.dumps(iteration_result, indent=2, default=str), encoding="utf-8"
        )
        (iter_dir / "baseline").mkdir(parents=True, exist_ok=True)
        (iter_dir / "baseline" / "backtest_summary.json").write_text(
            json.dumps({
                "total_pnl_usd": result["total_pnl_usd"],
                "trades_count": result["trades_count"],
                "win_rate_pct": result["win_rate_pct"],
            }, indent=2),
            encoding="utf-8",
        )

    with ThreadPoolExecutor(max_workers=args.parallelism) as ex:
        futures = [ex.submit(do_one, i, p) for i, p in enumerate(policies)]
        for f in as_completed(futures):
            f.result()

    print(f"Simulated {len(policies)} policies -> {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
