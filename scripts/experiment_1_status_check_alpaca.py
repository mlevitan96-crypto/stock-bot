#!/usr/bin/env python3
"""
Alpaca Experiment #1 — full status check (analysis-only, read-only).

Counts trades, checks ledger health (valid/invalid/stale), break/completion
alert readiness, days elapsed, and prints a summary. No execution changes,
no risk scaling, no deploy authorization use.

This script MUST use the same trade log path(s) the live bot writes to.
If those paths change, update here and in MEMORY_BANK.md "Alpaca Data Sources".

Optional: --droplet runs the same checks using live data from the droplet
(via SSH). Requires droplet_config.json or DROPLET_* env vars.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"
VALIDATE_SCRIPT = REPO / "scripts" / "validate_hypothesis_ledger_alpaca.py"
# Canonical closed-trade log paths (must match live bot — see MEMORY_BANK "Alpaca Data Sources")
def _logs_dir(repo_root: Path) -> Path:
    try:
        from config.registry import Directories
        return (repo_root / Directories.LOGS).resolve()
    except ImportError:
        return repo_root / "logs"
EXPERIMENT_START_FLAG = REPO / "state" / "experiment_1_start.flag"
STALE_DAYS = int(os.environ.get("GOVERNANCE_LEDGER_STALE_DAYS", "7"))


def _iter_jsonl(path: Path, since_ts: str | None):
    """Yield JSON records from path with timestamp >= since_ts (ISO8601)."""
    if not path.exists():
        return
    cutoff = (since_ts or "")[:10]
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = (rec.get("timestamp") or rec.get("ts") or rec.get("exit_timestamp") or "")[:10]
            if cutoff and ts < cutoff:
                continue
            yield rec


def _count_closed_trades_since(repo_root: Path, since_ts: str | None) -> tuple[int, str | None, str | None]:
    """
    Count closed trades since given ISO8601 timestamp.
    Uses canonical paths: exit_attribution.jsonl, attribution.jsonl (closed only),
    then master_trade_log.jsonl (records with exit_ts) as fallback. Dedupes by (symbol, date).
    Returns (count, earliest_trade_timestamp, latest_trade_timestamp).
    """
    logs = _logs_dir(repo_root)
    seen: set[tuple[str, str]] = set()
    earliest: str | None = None
    latest: str | None = None

    # 1) exit_attribution.jsonl — one line per v2 equity exit (canonical)
    for rec in _iter_jsonl(logs / "exit_attribution.jsonl", since_ts):
        ts = rec.get("timestamp") or rec.get("exit_timestamp") or ""
        if not ts:
            continue
        key = (str(rec.get("symbol", "")).upper(), ts[:10])
        if key not in seen:
            seen.add(key)
            if not earliest or ts < earliest:
                earliest = ts
            if not latest or ts > latest:
                latest = ts

    # 2) attribution.jsonl — closed only (non-open_ trade_id, pnl or close_reason)
    for rec in _iter_jsonl(logs / "attribution.jsonl", since_ts):
        if str(rec.get("trade_id", "")).startswith("open_"):
            continue
        ctx = rec.get("context") or {}
        close_reason = ctx.get("close_reason") or rec.get("close_reason") or ""
        pnl = float(rec.get("pnl_usd", 0) or 0)
        if pnl == 0 and not (close_reason and close_reason not in ("unknown", "N/A", "")):
            continue
        ts = rec.get("timestamp") or rec.get("ts") or ""
        if not ts:
            continue
        key = (str(rec.get("symbol", "")).upper(), ts[:10])
        if key not in seen:
            seen.add(key)
            if not earliest or ts < earliest:
                earliest = ts
            if not latest or ts > latest:
                latest = ts

    # 3) master_trade_log.jsonl — records with exit_ts = closed trade (fallback)
    for rec in _iter_jsonl(logs / "master_trade_log.jsonl", since_ts):
        if not rec.get("exit_ts"):
            continue
        ts = (rec.get("exit_ts") or rec.get("timestamp") or "")[:19]
        if not ts:
            continue
        key = (str(rec.get("symbol", "")).upper(), ts[:10])
        if key not in seen:
            seen.add(key)
            if not earliest or ts < earliest:
                earliest = ts
            if not latest or ts > latest:
                latest = ts

    return len(seen), earliest, latest


def _get_experiment_start_ts(repo_root: Path) -> str | None:
    """Return ISO8601 experiment start from flag file or ledger first entry."""
    flag_path = repo_root / "state" / "experiment_1_start.flag"
    if flag_path.exists():
        try:
            return flag_path.read_text(encoding="utf-8").strip()
        except OSError:
            pass
    ledger_path = repo_root / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"
    if ledger_path.exists():
        try:
            with ledger_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return (data[0].get("timestamp") or "") or None
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _ledger_health_status(repo_root: Path) -> tuple[str, int]:
    """
    Run validator and optionally check staleness. Returns (status, exit_code)
    where status is "HEALTHY" | "INVALID" | "STALE" | "EMPTY" and exit_code is 0, 1, or 2.
    """
    validate = repo_root / "scripts" / "validate_hypothesis_ledger_alpaca.py"
    r = subprocess.run(
        [sys.executable, str(validate)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0:
        return "INVALID", 1
    # Valid structure; empty ledger is not "healthy" for completion
    ledger_path = repo_root / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"
    try:
        with ledger_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return "INVALID", 1
    if not isinstance(data, list):
        return "INVALID", 1
    if not data:
        return "EMPTY", 0
    last_ts = (data[-1].get("timestamp") or "").replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(last_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return "HEALTHY", 0
    if datetime.now(timezone.utc) - dt > timedelta(days=STALE_DAYS):
        return "STALE", 2
    return "HEALTHY", 0


def _days_elapsed(since_ts: str | None) -> int | None:
    if not since_ts:
        return None
    try:
        dt = datetime.fromisoformat(since_ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0, delta.days)
    except (ValueError, TypeError):
        return None


def _next_action(
    health: str,
    break_ready: bool,
    completion_ready: bool,
    trades: int,
    days: int | None,
) -> str:
    if break_ready:
        return "Send break alert (ledger invalid or stale); fix ledger and re-validate."
    if completion_ready:
        return "Send completion alert (window satisfied, ledger healthy); or already sent."
    if health == "EMPTY":
        if trades > 0:
            return "Tag baseline: run 'python scripts/tag_profit_hypothesis_alpaca.py NO' (or YES if hypothesis stated); then re-run status and daily governance."
        return "Add at least one ledger entry (tag_profit_hypothesis_alpaca.py); then re-run status."
    if health == "STALE" and trades > 0:
        return "Append fresh ledger entry (tag_profit_hypothesis_alpaca.py); run daily governance; then re-validate."
    if health in ("INVALID", "STALE"):
        return "Fix ledger (valid + fresh) before completion can be considered."
    sessions = days if days is not None else 0
    if sessions >= 7 or trades >= 500:
        return "Window satisfied; run completion notify when ready."
    return f"Continue experiment (need 7 sessions or 500 trades; current: {sessions} days / {trades} trades)."


def run_status(repo_root: Path) -> dict:
    """Run full status check; return dict of results."""
    start_ts = _get_experiment_start_ts(repo_root)
    count, earliest, latest = _count_closed_trades_since(repo_root, start_ts)
    health, validator_exit = _ledger_health_status(repo_root)
    days = _days_elapsed(start_ts)

    # Break alert when ledger invalid or stale (not when merely empty)
    break_alert_ready = health in ("INVALID", "STALE")
    sessions_elapsed = days if days is not None else 0
    # Completion requires healthy (non-empty, valid, fresh) ledger and window satisfied
    completion_alert_ready = (
        health == "HEALTHY" and (sessions_elapsed >= 7 or count >= 500)
    )

    next_action = _next_action(health, break_alert_ready, completion_alert_ready, count, days)

    return {
        "total_trades": count,
        "earliest_trade_timestamp": earliest,
        "latest_trade_timestamp": latest,
        "ledger_health": health,
        "validator_exit_code": validator_exit,
        "break_alert_ready": break_alert_ready,
        "completion_alert_ready": completion_alert_ready,
        "days_elapsed": days,
        "experiment_start_ts": start_ts,
        "next_action": next_action,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Alpaca Experiment #1 full status check (read-only)."
    )
    parser.add_argument(
        "--droplet",
        action="store_true",
        help="Run status on droplet and print live summary (requires droplet_config.json or DROPLET_*).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON only.",
    )
    args = parser.parse_args()

    if args.droplet:
        try:
            sys.path.insert(0, str(REPO))
            from droplet_client import DropletClient
        except ImportError:
            print("Droplet check requires droplet_client (run from repo root).", file=sys.stderr)
            return 1
        try:
            client = DropletClient()
        except Exception as e:
            print(f"Droplet config error: {e}", file=sys.stderr)
            return 1
        # Run this script on the droplet so it uses droplet's ledger and logs
        remote_cmd = "python3 scripts/experiment_1_status_check_alpaca.py" + (" --json" if args.json else "")
        out, err, rc = client._execute_with_cd(remote_cmd, timeout=45)
        print(out)
        if err and not args.json:
            print(err, file=sys.stderr)
        return rc

    res = run_status(REPO)

    if args.json:
        print(json.dumps(res, indent=2))
        return 0

    print("ALPACA EXPERIMENT #1 STATUS")
    print("---------------------------")
    print(f"Trades so far: {res['total_trades']}")
    print(f"Earliest trade (in window): {res['earliest_trade_timestamp'] or '—'}")
    print(f"Latest trade (in window): {res['latest_trade_timestamp'] or '—'}")
    print(f"Ledger health: {res['ledger_health']}")
    print(f"Break alert ready: {res['break_alert_ready']}")
    print(f"Completion alert ready: {res['completion_alert_ready']}")
    print(f"Days elapsed: {res['days_elapsed'] if res['days_elapsed'] is not None else '(unknown — set state/experiment_1_start.flag)'}")
    print(f"Next action: {res['next_action']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
