#!/usr/bin/env python3
"""
Investigate why open orders aren't occurring.
Reads logs/run.jsonl, logs/gate.jsonl, logs/worker_debug.log and prints:
- Recent run completion (clusters, orders, risk_freeze, market_open)
- Skip-entry events (not_armed, not_reconciled, reduce_only_broker_degraded)
- Gate cycle_summary (considered, orders, gate_counts, reason)
- Worker debug: market open/closed, run_once, decide_and_execute returned N orders

Run from repo root (local or on droplet).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG_DIR = REPO / "logs"
STATE_DIR = REPO / "state"


def tail_jsonl(path: Path, n: int = 50) -> list:
    if not path.exists():
        return []
    lines = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    lines.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"Warning: could not read {path}: {e}", file=sys.stderr)
    return lines[-n:] if len(lines) > n else lines


def tail_lines(path: Path, n: int = 80) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return all_lines[-n:] if len(all_lines) > n else all_lines
    except Exception as e:
        print(f"Warning: could not read {path}: {e}", file=sys.stderr)
        return []


def main() -> int:
    print("=== Open orders investigation ===\n")
    print(f"Repo root: {REPO}")
    print(f"Log dir:   {LOG_DIR}\n")

    # 1) run.jsonl — complete, risk_freeze, clusters, orders
    run_path = LOG_DIR / "run.jsonl"
    run_events = tail_jsonl(run_path, 30)
    completes = [e for e in run_events if e.get("msg") == "complete" or "clusters" in e]
    print("--- Recent run completion (logs/run.jsonl) ---")
    if not completes:
        print("(no run completion events found)")
    else:
        for e in completes[-5:]:
            c = e.get("clusters", "?")
            o = e.get("orders", "?")
            rf = e.get("risk_freeze", "")
            mo = e.get("market_open", "")
            print(f"  clusters={c}, orders={o}, risk_freeze={rf or '—'}, market_open={mo}")
    print()

    # 2) Skip-entry events from run_once.jsonl, run.jsonl, gate.jsonl
    run_once_path = LOG_DIR / "run_once.jsonl"
    run_once_events = tail_jsonl(run_once_path, 50)
    gate_path = LOG_DIR / "gate.jsonl"
    gate_events = tail_jsonl(gate_path, 100)
    skip_events = [
        e for e in (run_once_events + run_events + gate_events)
        if e.get("msg") in ("not_armed_skip_entries", "not_reconciled_skip_entries", "reduce_only_broker_degraded")
        or e.get("event") in ("not_armed_skip_entries", "not_reconciled_skip_entries", "reduce_only_broker_degraded")
    ]
    print("--- Skip-entry events (not_armed / not_reconciled / reduce_only_broker_degraded) ---")
    if not skip_events:
        print("(none in last 50 run + 100 gate lines)")
    else:
        for e in skip_events[-10:]:
            msg = e.get("msg") or e.get("event") or "?"
            print(f"  {msg}  {e.get('trading_mode', '')} {e.get('base_url', '')} {e.get('action', '')}")
    print()

    # 3) Gate cycle_summary (considered, orders, gate_counts, reason)
    cycle_summaries = [e for e in gate_events if e.get("msg") == "cycle_summary" or (e.get("event") == "gate" and "considered" in e)]
    print("--- Gate cycle_summary (last 5) ---")
    if not cycle_summaries:
        print("(no cycle_summary in last 100 gate lines)")
    else:
        for e in cycle_summaries[-5:]:
            considered = e.get("considered", "?")
            orders = e.get("orders", "?")
            reason = e.get("reason", "")
            gc = e.get("gate_counts", {})
            print(f"  considered={considered}, orders={orders}, reason={reason or '—'}")
            if gc:
                print(f"    gate_counts: {gc}")
    print()

    # 4) worker_debug.log — market open/closed, run_once, decide_and_execute returned
    worker_path = LOG_DIR / "worker_debug.log"
    worker_lines = tail_lines(worker_path, 60)
    print("--- Worker debug (last 60 lines) ---")
    if not worker_lines:
        print("(no worker_debug.log or empty)")
    else:
        for line in worker_lines:
            line = line.rstrip()
            if not line:
                continue
            # Highlight key phrases
            if "Market" in line or "run_once" in line or "decide_and_execute" in line or "orders" in line:
                print(f"  {line}")
    print()

    # 5) ALPACA_BASE_URL hint
    base_url = os.environ.get("ALPACA_BASE_URL", "")
    if base_url:
        paper_ok = "paper-api.alpaca.markets" in base_url and "api.alpaca.markets" not in base_url.replace("paper-api.alpaca.markets", "")
        print("--- ALPACA_BASE_URL (from env) ---")
        print(f"  set: yes  paper_ok: {paper_ok}  (armed requires paper endpoint)")
    else:
        print("--- ALPACA_BASE_URL (from env) ---")
        print("  not set in this process (check .env on droplet); armed requires paper-api.alpaca.markets")
    print()
    print("See reports/open_orders_investigation.md for full checklist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
