#!/usr/bin/env python3
"""
Scenario Lab batch runner: parallel, read-only scenario experiments (#2–N).
Loads historical or shadow trade logs; applies alternative entry/exit/sizing/session
logic in memory; writes ONLY to reports/scenario_lab/<scenario_id>_<DATE>.json.
NO broker writes. NO execution hooks. NO writes to Experiment #1 ledger or any
canonical governance ledger.
"""
from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
LOGS = REPO / "logs"
OUT_DIR = REPO / "reports" / "scenario_lab"

# Explicitly out of scope: no writes to canonical ledger
# LEDGER_PATH = REPO / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"
# This script must NEVER write to that path.


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


def _ts_to_minutes(ts: Any) -> float:
    """Convert timestamp to minutes-of-day (UTC) for session filter. 0 = midnight."""
    if ts is None:
        return 0.0
    try:
        if isinstance(ts, (int, float)):
            from datetime import datetime as dt, timezone as tz
            dt_obj = dt.fromtimestamp(float(ts), tz=tz.utc)
        elif isinstance(ts, str):
            from datetime import datetime as dt
            dt_obj = dt.fromisoformat(ts.replace("Z", "+00:00"))
            if dt_obj.tzinfo is None:
                dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        else:
            return 0.0
        return dt_obj.hour * 60.0 + dt_obj.minute + dt_obj.second / 60.0
    except (ValueError, TypeError, OSError):
        return 0.0


def run_one_scenario(scenario_id: str, params: dict[str, Any]) -> dict:
    """
    Run a single scenario: load logs, apply params, compute metrics. Read-only.
    params may include: entry_min_score, exit_min_hold_minutes, session_start_minutes,
    session_end_minutes, size_multiplier.
    """
    exit_path = LOGS / "exit_attribution.jsonl"
    attr_path = LOGS / "attribution.jsonl"
    rows = _read_jsonl(exit_path) or _read_jsonl(attr_path)
    if not rows:
        return {
            "scenario_id": scenario_id,
            "status": "no_data",
            "reason": "no_exit_attribution_or_attribution_logs",
            "trades": 0,
            "total_pnl": None,
            "expectancy": None,
            "params": params,
        }
    entry_min_score = params.get("entry_min_score")
    exit_min_hold = params.get("exit_min_hold_minutes")
    session_start = params.get("session_start_minutes")
    session_end = params.get("session_end_minutes")
    size_mult = params.get("size_multiplier", 1.0)

    filtered = []
    for r in rows:
        score = r.get("entry_score") or r.get("score") or r.get("composite_score")
        if entry_min_score is not None and score is not None:
            if float(score) < float(entry_min_score):
                continue
        exit_ts = r.get("exit_ts") or r.get("timestamp") or r.get("ts")
        entry_ts = r.get("entry_ts") or r.get("open_ts")
        if exit_min_hold is not None and exit_ts is not None and entry_ts is not None:
            try:
                et = float(exit_ts) if isinstance(exit_ts, (int, float)) else None
                at = float(entry_ts) if isinstance(entry_ts, (int, float)) else None
                if et is not None and at is not None and (et - at) / 60.0 < float(exit_min_hold):
                    continue
            except (TypeError, ValueError):
                pass
        if session_start is not None or session_end is not None:
            mins = _ts_to_minutes(exit_ts)
            if session_start is not None and mins < float(session_start):
                continue
            if session_end is not None and mins > float(session_end):
                continue
        filtered.append(r)

    total_pnl = sum((r.get("pnl") or 0) * float(size_mult) for r in filtered if isinstance(r.get("pnl"), (int, float)))
    n = len(filtered)
    return {
        "scenario_id": scenario_id,
        "status": "complete",
        "trades": n,
        "total_pnl": total_pnl,
        "expectancy": total_pnl / n if n else None,
        "params": params,
        "data_source": "logs/exit_attribution.jsonl or logs/attribution.jsonl",
    }


def _run_scenario_worker(args: tuple[str, dict]) -> dict:
    """Worker for ProcessPoolExecutor: (scenario_id, params) -> result dict."""
    return run_one_scenario(args[0], args[1])


# Built-in scenario definitions (parameters only; no ledger writes)
SCENARIOS: dict[str, dict[str, Any]] = {
    "scenario_002": {"description": "Stricter entry threshold (score floor +0.5)", "entry_min_score": 3.0},
    "scenario_003": {"description": "Longer min-hold (exit timing)", "exit_min_hold_minutes": 60},
    "scenario_004": {"description": "Session filter (first 2h only)", "session_start_minutes": 0, "session_end_minutes": 120},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Scenario Lab batch (read-only). No ledger or broker writes.")
    parser.add_argument("--scenario", action="append", default=[], help="Scenario ID to run (repeat for multiple)")
    parser.add_argument("--all", action="store_true", help="Run all registered scenarios")
    parser.add_argument("--workers", type=int, default=None, help="Parallel workers; default min(4, cpu_count-1)")
    args = parser.parse_args()

    nproc = os.cpu_count() or 4
    workers = args.workers if args.workers is not None else min(4, max(1, nproc - 1))

    if args.all:
        to_run = list(SCENARIOS.items())
    elif args.scenario:
        to_run = [(sid, SCENARIOS.get(sid, {})) for sid in args.scenario]
        to_run = [(sid, p) for sid, p in to_run if p or sid not in SCENARIOS]
        if not to_run:
            for sid in args.scenario:
                to_run.append((sid, {}))
    else:
        to_run = list(SCENARIOS.items())

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    task_args = []
    for scenario_id, defn in to_run:
        params = {k: v for k, v in (defn or {}).items() if k != "description"}
        task_args.append((scenario_id, params))

    if workers <= 1 or len(task_args) <= 1:
        results = [_run_scenario_worker(a) for a in task_args]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_run_scenario_worker, a): a for a in task_args}
            results = [f.result() for f in as_completed(futures)]

    for res in results:
        sid = res.get("scenario_id", "unknown")
        out_path = OUT_DIR / f"{sid}_{date_str}.json"
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
        except OSError:
            pass
        print(json.dumps(res, indent=2))

    _write_scenario_summary(results, date_str)
    return 0


def _write_scenario_summary(results: list[dict], date_str: str) -> None:
    """Write reports/scenario_lab/SCENARIO_SUMMARY_<DATE>.md with ranking, CSA_REVIEW, SRE_REVIEW."""
    path = OUT_DIR / f"SCENARIO_SUMMARY_{date_str}.md"
    # Rank by expectancy (desc), then by total_pnl (desc); nulls last
    ranked = sorted(
        [r for r in results if r.get("status") == "complete" and r.get("trades", 0) > 0],
        key=lambda r: (
            r.get("expectancy") is None,
            -(r.get("expectancy") or 0),
            -(r.get("total_pnl") or 0),
        ),
    )
    lines = [
        "# Scenario Lab Summary",
        "",
        f"**Date:** {date_str}",
        "**Scope:** Parallel analysis-only scenarios. Experiment #1 remains canonical; no ledger writes.",
        "",
        "## Scenario ranking (by expectancy / PnL)",
        "",
    ]
    for i, r in enumerate(ranked, 1):
        sid = r.get("scenario_id", "?")
        exp = r.get("expectancy")
        pnl = r.get("total_pnl")
        n = r.get("trades", 0)
        exp_s = f"{exp:.2f}" if exp is not None else "N/A"
        pnl_s = f"{pnl:.2f}" if pnl is not None else "N/A"
        lines.append(f"- **{i}. {sid}** — expectancy: {exp_s}, total_pnl: {pnl_s}, trades: {n}")
    lines.extend([
        "",
        "## CSA_REVIEW",
        "",
        "- **Why this might be misleading:** Scenario replay uses the same historical logs; ranking reflects in-sample variation only. Best scenario may not hold out-of-sample. Selection bias if logs are incomplete or non-representative.",
        "- **Fragile assumptions:** Entry/exit/session filters are applied ex post; real execution would have different liquidity and slippage. No transaction cost or capacity constraints in replay.",
        "",
        "## SRE_REVIEW",
        "",
        "- **Data completeness:** Replay fidelity depends on exit_attribution.jsonl / attribution.jsonl being complete for the window. Gaps or partial writes invalidate comparisons.",
        "- **Replay fidelity:** Logic is simplified (score filter, min-hold, session window). Production exit logic and risk checks are not fully replayed.",
        "- **Failure modes:** Missing logs → scenario returns no_data. No broker or ledger writes; rollback is N/A (read-only).",
        "",
    ])
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
