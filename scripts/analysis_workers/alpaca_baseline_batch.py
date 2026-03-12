#!/usr/bin/env python3
"""
Alpaca baseline batch: read-only analysis workers for Experiment #1.
Computes: expectancy recomputation, slippage distribution, session/day PnL attribution,
counterfactual would-have-traded (stub when signals/logs insufficient).
No broker writes; no order placement. Safe to run in parallel with --workers N.
Default workers: min(4, cpu_count - 1) unless overridden.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOGS = REPO / "logs"
STATE = REPO / "state"
OUT_DIR = REPO / "reports" / "experiments"


def _read_jsonl(path: Path, max_lines: int = 0) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if max_lines and i >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return out


def worker_expectancy(_worker_id: int) -> dict:
    """Recompute expectancy from closed trades (attribution / exit_attribution). Read-only."""
    attribution_path = LOGS / "attribution.jsonl"
    exit_path = LOGS / "exit_attribution.jsonl"
    rows = _read_jsonl(exit_path) or _read_jsonl(attribution_path)
    if not rows:
        return {"metric": "expectancy", "status": "n_a", "reason": "no_attribution_or_exit_logs", "expectancy": None, "trades": 0, "total_pnl": None}
    total_pnl = sum((r.get("pnl") or 0) for r in rows if isinstance(r.get("pnl"), (int, float)))
    n = len(rows)
    return {"metric": "expectancy", "status": "ok", "trades": n, "total_pnl": total_pnl, "expectancy": total_pnl / n if n else None}


def worker_slippage(_worker_id: int) -> dict:
    """Slippage distribution from execution/fill data. Read-only. N/A if no fill vs signal data."""
    # Common log names that might contain fill/signal price
    for name in ("execution_fill.jsonl", "exit_attribution.jsonl", "attribution.jsonl"):
        path = LOGS / name
        if not path.exists():
            continue
        rows = _read_jsonl(path, max_lines=5000)
        fill_deltas = []
        for r in rows:
            fill_p = r.get("fill_price") or r.get("exit_price")
            sig_p = r.get("signal_price") or r.get("entry_price")
            if fill_p is not None and sig_p is not None and isinstance(fill_p, (int, float)) and isinstance(sig_p, (int, float)):
                fill_deltas.append(float(fill_p) - float(sig_p))
        if fill_deltas:
            avg = sum(fill_deltas) / len(fill_deltas)
            return {"metric": "slippage", "status": "ok", "n_fills": len(fill_deltas), "avg_slippage": avg, "min": min(fill_deltas), "max": max(fill_deltas)}
    return {"metric": "slippage", "status": "n_a", "reason": "no_fill_vs_signal_data_in_logs"}


def worker_session_pnl(_worker_id: int) -> dict:
    """Session/day PnL attribution from exit_attribution. Read-only."""
    path = LOGS / "exit_attribution.jsonl"
    rows = _read_jsonl(path)
    if not rows:
        return {"metric": "session_pnl", "status": "n_a", "reason": "no_exit_attribution", "by_day": {}}
    by_day: dict[str, float] = {}
    for r in rows:
        ts = r.get("exit_ts") or r.get("timestamp") or r.get("ts") or ""
        if isinstance(ts, (int, float)):
            from datetime import datetime, timezone
            try:
                dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
                day = dt.strftime("%Y-%m-%d")
            except (ValueError, OSError):
                day = "unknown"
        elif isinstance(ts, str):
            day = ts[:10] if len(ts) >= 10 else "unknown"
        else:
            day = "unknown"
        by_day[day] = by_day.get(day, 0.0) + (r.get("pnl") or 0)
    return {"metric": "session_pnl", "status": "ok", "by_day": by_day, "total_trades": len(rows)}


def worker_counterfactual(_worker_id: int) -> dict:
    """Counterfactual would-have-traded: stub when signals/logs not sufficient. Read-only."""
    blocked = STATE / "blocked_trades.jsonl"
    if not blocked.exists():
        return {"metric": "counterfactual", "status": "n_a", "reason": "blocked_trades.jsonl_missing"}
    rows = _read_jsonl(blocked, max_lines=2000)
    return {"metric": "counterfactual", "status": "stub", "blocked_count": len(rows), "note": "would-have-traded requires bars+signals; run full replay for estimates"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Alpaca baseline batch (read-only analysis workers).")
    parser.add_argument("--workers", type=int, default=None, help="Parallel workers; default min(4, cpu_count-1)")
    args = parser.parse_args()
    nproc = os.cpu_count() or 4
    workers = args.workers if args.workers is not None else min(4, max(1, nproc - 1))

    task_fns = [worker_expectancy, worker_slippage, worker_session_pnl, worker_counterfactual]
    results = [None] * len(task_fns)
    if workers <= 1:
        for i, task_fn in enumerate(task_fns):
            try:
                results[i] = task_fn(i)
            except Exception as e:
                results[i] = {"metric": task_fn.__name__.replace("worker_", ""), "status": "error", "error": str(e)}
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fut = {ex.submit(fn, i): i for i, fn in enumerate(task_fns)}
            for future in as_completed(fut):
                i = fut[future]
                try:
                    results[i] = future.result()
                except Exception as e:
                    results[i] = {"metric": task_fns[i].__name__.replace("worker_", ""), "status": "error", "error": str(e)}

    out = {"workers": workers, "results": results}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "alpaca_baseline_batch_results.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
    except OSError:
        pass
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
