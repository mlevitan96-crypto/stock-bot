#!/usr/bin/env python3
"""
Alpaca fast-lane shadow cycle runner: 25-trade windows.
READ-ONLY from trade logs; writes only to state/fast_lane_experiment/ and logs.
NO writes to main config or main experiment ledger. NO live orders.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE_DIR = REPO / "state" / "fast_lane_experiment"
LEDGER_PATH = STATE_DIR / "fast_lane_ledger.json"
STATE_PATH = STATE_DIR / "fast_lane_state.json"
CYCLES_DIR = STATE_DIR / "cycles"
LOG_PATH = REPO / "logs" / "fast_lane_shadow.log"
WINDOW_SIZE = 25

# Trade log: prefer unified events with exit_decision_made; fallback canonical exit_attribution
LOGS_DIR = REPO / "logs"
UNIFIED_EVENTS = LOGS_DIR / "alpaca_unified_events.jsonl"
EXIT_ATTRIBUTION = LOGS_DIR / "exit_attribution.jsonl"


def _ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CYCLES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _setup_logging() -> logging.Logger:
    _ensure_dirs()
    logger = logging.getLogger("fast_lane_shadow")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(fh)
    return logger


def _iter_exit_trades():
    """
    Yield (index, trade_id, pnl_usd, strategy_id) from either alpaca_unified_events (exit_decision_made)
    or exit_attribution.jsonl. Order: chronological by file position.
    """
    # 1) Try unified events
    if UNIFIED_EVENTS.exists():
        with open(UNIFIED_EVENTS, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = rec.get("event_type") or rec.get("kind") or rec.get("type") or ""
                if kind != "exit_decision_made":
                    continue
                trade_id = rec.get("trade_id")
                pnl = rec.get("realized_pnl_usd")
                if pnl is None:
                    pnl = rec.get("pnl_usd") or rec.get("pnl") or 0.0
                try:
                    pnl = float(pnl)
                except (TypeError, ValueError):
                    pnl = 0.0
                strategy_id = rec.get("strategy_id") or rec.get("mode") or "equity"
                yield idx, str(trade_id or f"idx_{idx}"), pnl, strategy_id
        return

    # 2) Fallback: exit_attribution.jsonl (canonical)
    if not EXIT_ATTRIBUTION.exists():
        return
    with open(EXIT_ATTRIBUTION, "r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            trade_id = rec.get("trade_id") or f"exit_attr_{idx}"
            pnl = rec.get("realized_pnl_usd")
            if pnl is None:
                pnl = rec.get("pnl") or rec.get("pnl_usd") or 0.0
            try:
                pnl = float(pnl)
            except (TypeError, ValueError):
                pnl = 0.0
            strategy_id = rec.get("strategy_id") or rec.get("mode") or "equity"
            yield idx, str(trade_id), pnl, strategy_id


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"last_processed_trade_index": 0, "total_trades_processed": 0, "last_cycle_id": None, "updated_at": None}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"last_processed_trade_index": 0, "total_trades_processed": 0, "last_cycle_id": None, "updated_at": None}


def _save_state(state: dict) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _load_ledger() -> list:
    if not LEDGER_PATH.exists():
        return []
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_ledger(ledger: list) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def _rank_candidates(trades: list[tuple]) -> tuple[str, list]:
    """
    trades: list of (trade_id, pnl_usd, strategy_id?).
    Return (best_candidate_id, candidate_rankings).
    Groups by strategy_id and ranks by PnL; if only one group, use that id.
    """
    if not trades:
        return "baseline", []
    from collections import defaultdict
    by_candidate = defaultdict(lambda: 0.0)
    for t in trades:
        sid = (t[2] or "baseline").strip() or "baseline"
        by_candidate[sid] += t[1]
    total_pnl = sum(t[1] for t in trades)
    rankings = [{"id": cid, "score": round(pnl, 4), "pnl_usd": round(pnl, 4)} for cid, pnl in sorted(by_candidate.items(), key=lambda x: -x[1])]
    best = rankings[0]["id"] if rankings else "baseline"
    return best, rankings


def main() -> int:
    _ensure_dirs()
    log = _setup_logging()
    log.info("Fast-lane shadow cycle start")

    trades_list = list(_iter_exit_trades())
    if not trades_list:
        log.info("No exit trades found; skip cycle")
        return 0

    state = _load_state()
    last_idx = state.get("last_processed_trade_index", 0)
    # Build (global_index, trade_id, pnl_usd, strategy_id) for slicing
    indexed = []
    for i, row in enumerate(trades_list):
        idx, tid, pnl = row[0], row[1], row[2]
        sid = row[3] if len(row) > 3 else "equity"
        indexed.append((idx, tid, pnl, sid))

    # Next window: from last_idx (exclusive) take WINDOW_SIZE
    # We key by position in file, not by global index of "exit" events only
    # So we use position in trades_list: next start = last_processed_trade_index (count of exits processed)
    start = last_idx
    window = indexed[start : start + WINDOW_SIZE]
    if len(window) < WINDOW_SIZE:
        log.info("Insufficient new trades for a full window: %d (need %d)", len(window), WINDOW_SIZE)
        return 0

    # Compute PnL for this window
    trade_ids = [w[1] for w in window]
    pnls = [w[2] for w in window]
    pnl_usd = sum(pnls)
    pnl_per_trade = pnl_usd / len(pnls) if pnls else 0.0

    # Candidate ranking (by strategy_id if present)
    best_candidate_id, candidate_rankings = _rank_candidates([(w[1], w[2], w[3]) for w in window])

    cycle_num = len(_load_ledger()) + 1
    cycle_id = f"cycle_{cycle_num:04d}"
    timestamp_completed = datetime.now(timezone.utc).isoformat()

    entry = {
        "cycle_id": cycle_id,
        "start_trade_id": trade_ids[0],
        "end_trade_id": trade_ids[-1],
        "trade_count": len(window),
        "pnl_usd": round(pnl_usd, 4),
        "pnl_per_trade_usd": round(pnl_per_trade, 4),
        "best_candidate_id": best_candidate_id,
        "candidate_rankings": candidate_rankings,
        "timestamp_completed": timestamp_completed,
        "notes": "CSA shadow cycle; no execution impact.",
    }

    ledger = _load_ledger()
    ledger.append(entry)
    _save_ledger(ledger)

    state["last_processed_trade_index"] = start + WINDOW_SIZE
    state["total_trades_processed"] = state.get("total_trades_processed", 0) + len(window)
    state["last_cycle_id"] = cycle_id
    _save_state(state)

    # Cycle artifacts
    cycle_dir = CYCLES_DIR / cycle_id
    cycle_dir.mkdir(parents=True, exist_ok=True)
    summary_path = cycle_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)
    trades_snapshot_path = cycle_dir / "trades_snapshot.json"
    with open(trades_snapshot_path, "w", encoding="utf-8") as f:
        json.dump([{"trade_id": w[1], "pnl_usd": w[2]} for w in window], f, indent=2)

    log.info("Cycle %s completed: pnl_usd=%.2f trades=%d", cycle_id, pnl_usd, len(window))

    # Notify
    try:
        subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "notify_fast_lane_summary.py"),
                "--kind", "cycle",
                "--cycle-id", cycle_id,
                "--pnl-usd", str(pnl_usd),
                "--best-candidate-id", best_candidate_id,
                "--notes", entry.get("notes", ""),
            ],
            cwd=str(REPO),
            timeout=30,
            check=False,
        )
    except Exception as e:
        log.warning("Notify cycle failed: %s", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
