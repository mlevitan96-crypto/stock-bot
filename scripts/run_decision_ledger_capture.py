#!/usr/bin/env python3
"""
Decision ledger capture: build decision_ledger.jsonl from telemetry (score_snapshot + blocked_trades).
Default: last 7 days. If sparse, extend to 30 days and note it.
Observe-only: no orders submitted; ledger is built from existing telemetry.
Usage:
  python scripts/run_decision_ledger_capture.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--symbols A,B] [--limit N] [--observe-only]
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

LEDGER_DIR = REPO / "reports" / "decision_ledger"
LEDGER_JSONL = LEDGER_DIR / "decision_ledger.jsonl"
SNAPSHOT_PATH = REPO / "logs" / "score_snapshot.jsonl"
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"


def _parse_ts(v) -> int | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return int(float(v))
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def _ts_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def load_snapshots(start_ts: int, end_ts: int, symbols: list[str] | None, limit: int | None) -> list[dict]:
    rows = []
    if not SNAPSHOT_PATH.exists():
        return rows
    for line in SNAPSHOT_PATH.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = r.get("ts")
        if ts is None:
            ts = _parse_ts(r.get("ts_iso"))
        if ts is None:
            continue
        if start_ts and int(ts) < start_ts:
            continue
        if end_ts and int(ts) > end_ts:
            continue
        sym = r.get("symbol", "")
        if symbols and sym not in symbols:
            continue
        rows.append(r)
    rows.sort(key=lambda x: (x.get("ts") or 0, x.get("symbol", "")))
    if limit is not None and limit > 0:
        rows = rows[-limit:]
    return rows


def load_blocked_by_ts_range(start_ts: int, end_ts: int) -> list[dict]:
    out = []
    if not BLOCKED_PATH.exists():
        return out
    for line in BLOCKED_PATH.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(r.get("timestamp") or r.get("ts"))
        if ts is None:
            continue
        if start_ts and ts < start_ts:
            continue
        if end_ts and ts > end_ts:
            continue
        out.append(r)
    return out


def snapshot_to_decision_event(snap: dict, blocked_lookup: dict) -> dict:
    """Convert one score_snapshot row (+ optional blocked_trades match) to DecisionEvent."""
    ts = snap.get("ts") or _parse_ts(snap.get("ts_iso")) or 0
    symbol = snap.get("symbol", "")
    gates_rec = snap.get("gates", {})
    composite_pass = gates_rec.get("composite_gate_pass", True)
    expectancy_pass = gates_rec.get("expectancy_gate_pass", True)
    block_reason = gates_rec.get("block_reason")

    score_final = float(snap.get("composite_score", 0) or 0)
    expectancy_floor = float(snap.get("expectancy_floor", 0) or 0)
    weighted = snap.get("weighted_contributions") or {}
    group_sums = snap.get("group_sums") or {}

    # Build score_components as { name: { value, weight, contribution } }
    score_components = {}
    for k, v in (weighted or {}).items():
        if isinstance(v, (int, float)):
            score_components[k] = {"value": v, "weight": None, "contribution": v}
        elif isinstance(v, dict):
            score_components[k] = {"value": v.get("value"), "weight": v.get("weight"), "contribution": v.get("contribution", v.get("value"))}
        else:
            score_components[k] = {"value": v, "weight": None, "contribution": v}

    gates = []
    gates.append({
        "gate_name": "composite_gate",
        "pass": composite_pass,
        "reason": "rejected" if not composite_pass else "passed",
        "params": {"threshold": snap.get("expectancy_floor")},
        "measured": {"score": score_final, "composite_pre_norm": snap.get("composite_pre_norm"), "composite_post_norm": snap.get("composite_post_norm")},
    })
    gates.append({
        "gate_name": "expectancy_gate",
        "pass": expectancy_pass,
        "reason": (block_reason or "passed") if not expectancy_pass else "passed",
        "params": {"expectancy_floor": expectancy_floor},
        "measured": {"composite_score": score_final},
    })

    # Merge blocked_trades if we have a match (same symbol, ts within same minute)
    ts_bucket = (ts // 60) * 60 if ts else 0
    blocked = blocked_lookup.get((symbol, ts)) or blocked_lookup.get((symbol, ts_bucket))
    if blocked:
        reason = blocked.get("reason") or blocked.get("block_reason") or block_reason
        gates.append({
            "gate_name": "block_reason",
            "pass": False,
            "reason": reason,
            "params": {},
            "measured": {"score": blocked.get("score"), "candidate_score": blocked.get("candidate_score")},
        })

    uw_deferred = snap.get("uw_deferred") is True
    defer_reason = snap.get("defer_reason")
    next_retry_ts = snap.get("next_retry_ts")
    if uw_deferred:
        candidate_status = "DEFERRED"
        if block_reason and "defer" not in (block_reason or "").lower():
            gates.append({
                "gate_name": "uw_defer",
                "pass": False,
                "reason": defer_reason or "uw_deferred",
                "params": {"next_retry_ts": next_retry_ts},
                "measured": {},
            })
    else:
        candidate_status = "BLOCKED" if block_reason else "GENERATED"

    run_id = os.environ.get("RUN_ID", f"replay_{ts}")
    out = {
        "run_id": run_id,
        "ts": ts,
        "ts_iso": _ts_iso(ts) if ts else "",
        "symbol": symbol,
        "venue": "alpaca",
        "timeframe": "1m",
        "mode": "observe",
        "signal_raw": snap.get("signal_group_scores") or {},
        "features": {},
        "score_components": score_components,
        "score_final": score_final,
        "thresholds": {
            "expectancy_floor": expectancy_floor,
            "min_exec_score": snap.get("expectancy_floor"),
        },
        "gates": gates,
        "candidate_status": candidate_status,
        "order_intent": None,
        "order_result": None,
    }
    if uw_deferred:
        out["uw_deferred"] = True
        out["defer_reason"] = defer_reason
        out["next_retry_ts"] = next_retry_ts
    return out


def build_blocked_lookup(blocked_rows: list[dict]) -> dict:
    """Key by (symbol, ts_bucket_minute) and (symbol, ts) for merge with snapshots."""
    by_key = {}
    for r in blocked_rows:
        sym = r.get("symbol", "")
        ts = _parse_ts(r.get("timestamp") or r.get("ts"))
        if ts is None:
            continue
        ts_bucket = (ts // 60) * 60
        by_key[(sym, ts_bucket)] = r
        by_key[(sym, ts)] = r
    return by_key


def main() -> int:
    ap = argparse.ArgumentParser(description="Build decision_ledger.jsonl from telemetry")
    ap.add_argument("--start", default=None, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", default=None, help="End date YYYY-MM-DD")
    ap.add_argument("--symbols", default=None, help="Comma-separated symbols filter")
    ap.add_argument("--limit", type=int, default=None, help="Max events to emit")
    ap.add_argument("--observe-only", action="store_true", default=True, help="No orders (default true)")
    args = ap.parse_args()

    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=7)
    if args.end:
        try:
            end_dt = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if args.start:
        try:
            start_dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    symbols = [s.strip() for s in (args.symbols or "").split(",") if s.strip()] or None

    snapshots = load_snapshots(start_ts, end_ts, symbols, args.limit)
    extended_note = ""
    if len(snapshots) < 100:
        # Extend to 30 days and note
        start_dt = end_dt - timedelta(days=30)
        start_ts = int(start_dt.timestamp())
        snapshots = load_snapshots(start_ts, end_ts, symbols, args.limit)
        extended_note = " (extended to 30 days: telemetry sparse)"

    blocked_rows = load_blocked_by_ts_range(start_ts, end_ts)
    blocked_lookup = build_blocked_lookup(blocked_rows)

    events = []
    for snap in snapshots:
        ev = snapshot_to_decision_event(snap, blocked_lookup)
        events.append(ev)

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    with LEDGER_JSONL.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, default=str) + "\n")
    print(f"Wrote {len(events)} events to {LEDGER_JSONL}{extended_note}")

    # reproduction.md
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=5,
        )
        git_hash = (commit.stdout or "").strip() or "unknown"
    except Exception:
        git_hash = "unknown"
    hostname = platform.node() or os.environ.get("HOSTNAME", "unknown")
    py_ver = sys.version.split()[0]

    sparse_note = ""
    if len(events) < 100:
        sparse_note = "\n- **Note:** Fewer than 100 events (telemetry sparse or window short). Extend window (--start/--end) or run live with DECISION_LEDGER_CAPTURE=1 to collect more.\n"
    repro = f"""# Decision ledger reproduction

- **Command:** `python3 scripts/run_decision_ledger_capture.py` (with optional --start/--end/--symbols/--limit)
- **Git commit:** {git_hash}
- **Droplet/hostname:** {hostname}
- **Python version:** {py_ver}
- **Config snapshot:** (main config from env/Config; score_snapshot from logs/score_snapshot.jsonl)
- **Time window:** {start_dt.date().isoformat()} to {end_dt.date().isoformat()}
- **Events:** {len(events)}{sparse_note}
- **Observe-only:** True (default)
"""
    (LEDGER_DIR / "reproduction.md").write_text(repro, encoding="utf-8")
    print(f"Wrote {LEDGER_DIR / 'reproduction.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
