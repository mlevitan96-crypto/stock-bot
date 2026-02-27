#!/usr/bin/env python3
"""
Orchestrate dozens of profitability iterations (each runs 30d backtest via run_profit_iteration).
Resumable: skips iter_XXXX that already have iteration_result.json.
Writes to out/iter_0001/, out/iter_0002/, ... with iteration_result.json each.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", default=None, help="Path to truth_30d.json (optional; iterations use attribution logs)")
    ap.add_argument("--iterations", type=int, default=48)
    ap.add_argument("--parallelism", type=int, default=6)
    ap.add_argument("--objective", default="MAX_PNL_AFTER_COSTS")
    ap.add_argument("--no_suppression", action="store_true")
    ap.add_argument("--out", required=True, help="Output dir for iter_0001, iter_0002, ...")
    args = ap.parse_args()

    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = REPO / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    iter_script = REPO / "scripts" / "learning" / "run_profit_iteration.py"
    if not iter_script.exists():
        print(f"Missing {iter_script}", file=sys.stderr)
        return 1

    days = 30
    procs = []
    next_i = 1
    done = 0
    n = args.iterations
    par = args.parallelism

    while done < n:
        while next_i <= n and len(procs) < par:
            iter_id = f"iter_{next_i:04d}"
            out_dir = out_root / iter_id
            res_path = out_dir / "iteration_result.json"
            if res_path.exists():
                done += 1
                next_i += 1
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            cmd = [
                sys.executable,
                str(iter_script),
                "--out_dir", str(out_dir),
                "--iter_id", iter_id,
                "--time_range", f"{days}d",
                "--objective", args.objective,
                "--auto_fix",
                "--allow_partial_data",
                "--force_direction_search",
                "--no_suppression",
            ]
            proc = subprocess.Popen(cmd, cwd=str(REPO))
            procs.append((next_i, proc))
            next_i += 1

        time.sleep(3)
        still = []
        for i, p in procs:
            if p.poll() is not None:
                done += 1
            else:
                still.append((i, p))
        procs = still

    print(f"Campaign complete: {done}/{n} iterations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
