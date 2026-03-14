#!/usr/bin/env python3
"""
Alpaca fast-lane shadow cycle runner: 25-trade windows, go-forward only.
Evaluates every angle (strategy, exit_reason, regime, sector, hold, score, time-of-day, etc.),
promotes the single most profitable (dimension:value) per cycle. READ-ONLY from logs;
writes only to state/fast_lane_experiment/ and logs. No live impact.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
STATE_DIR = REPO / "state" / "fast_lane_experiment"
CONFIG_PATH = STATE_DIR / "config.json"
LEDGER_PATH = STATE_DIR / "fast_lane_ledger.json"
STATE_PATH = STATE_DIR / "fast_lane_state.json"
CYCLES_DIR = STATE_DIR / "cycles"
LOG_PATH = REPO / "logs" / "fast_lane_shadow.log"
WINDOW_SIZE = 25

DEFAULT_EPOCH_START_ISO = "2026-03-17T13:30:00Z"
LOGS_DIR = REPO / "logs"
UNIFIED_EVENTS = LOGS_DIR / "alpaca_unified_events.jsonl"
EXIT_ATTRIBUTION = LOGS_DIR / "exit_attribution.jsonl"

# --- Robust angle set (CSA/SRE: big slice of views to find what drives profitability) ---
def _norm(s: Any) -> str:
    v = (s or "").strip() or "unknown"
    return v if v else "unknown"

def _strategy(rec: dict) -> str:
    return _norm(rec.get("strategy_id") or rec.get("strategy") or rec.get("mode"))

def _exit_reason(rec: dict) -> str:
    return _norm(rec.get("exit_reason") or rec.get("close_reason") or rec.get("reason"))

def _exit_regime(rec: dict) -> str:
    return _norm(rec.get("exit_regime")).upper() or "UNKNOWN"

def _entry_regime(rec: dict) -> str:
    return _norm(rec.get("entry_regime")).upper() or "UNKNOWN"

def _regime_transition(rec: dict) -> str:
    e = _norm(rec.get("entry_regime")).upper()
    x = _norm(rec.get("exit_regime")).upper()
    return "same" if e == x and e != "UNKNOWN" else "shift"

def _sector(rec: dict) -> str:
    for key in ("exit_sector_profile", "entry_sector_profile"):
        prof = rec.get(key)
        if isinstance(prof, dict) and prof:
            primary = prof.get("primary") or prof.get("sector") or (list(prof.keys())[0] if prof else None)
            if primary:
                return _norm(str(primary)).upper()
    return "UNKNOWN"

def _hold_bucket(rec: dict) -> str:
    try:
        m = float(rec.get("time_in_trade_minutes") or rec.get("hold_minutes") or -1)
    except (TypeError, ValueError):
        return "unknown"
    if m < 0:
        return "unknown"
    if m < 60:
        return "short"
    if m <= 240:
        return "medium"
    return "long"

def _exit_score_band(rec: dict) -> str:
    try:
        s = float(rec.get("v2_exit_score") or rec.get("exit_score") or -999)
    except (TypeError, ValueError):
        return "unknown"
    if s < 0:
        return "unknown"
    if s < 2:
        return "low"
    if s <= 5:
        return "mid"
    return "high"

def _time_of_day(rec: dict) -> str:
    ts = rec.get("timestamp") or rec.get("ts") or rec.get("exit_timestamp") or ""
    if not ts or len(ts) < 16:
        return "unknown"
    try:
        h = int(ts[11:13])  # HH
        if h < 12:
            return "morning"
        if h < 16:
            return "afternoon"
        return "close"
    except (ValueError, IndexError):
        return "unknown"

def _day_of_week(rec: dict) -> str:
    ts = rec.get("timestamp") or rec.get("ts") or rec.get("exit_timestamp") or ""
    if not ts or len(ts) < 10:
        return "unknown"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%a")  # Mon, Tue, ...
    except Exception:
        return "unknown"

def _exit_regime_decision(rec: dict) -> str:
    return _norm(rec.get("exit_regime_decision") or "normal")

def _score_deterioration_bucket(rec: dict) -> str:
    try:
        s = float(rec.get("score_deterioration") or -1)
    except (TypeError, ValueError):
        return "unknown"
    if s < 0:
        return "unknown"
    if s < 0.2:
        return "low"
    if s <= 0.5:
        return "mid"
    return "high"

def _replacement(rec: dict) -> str:
    return "replaced" if rec.get("replacement_candidate") else "no_replacement"

def _symbol(rec: dict) -> str:
    return _norm(rec.get("symbol")).upper() or "UNKNOWN"

# Order: (dimension_name, extractor). All must return a string (unknown if missing).
ANGLE_EXTRACTORS: list[tuple[str, Callable[[dict], str]]] = [
    ("strategy", _strategy),
    ("exit_reason", _exit_reason),
    ("exit_regime", _exit_regime),
    ("entry_regime", _entry_regime),
    ("regime_transition", _regime_transition),
    ("sector", _sector),
    ("hold_bucket", _hold_bucket),
    ("exit_score_band", _exit_score_band),
    ("time_of_day", _time_of_day),
    ("day_of_week", _day_of_week),
    ("exit_regime_decision", _exit_regime_decision),
    ("score_deterioration_bucket", _score_deterioration_bucket),
    ("replacement", _replacement),
    ("symbol", _symbol),
]


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


def _load_epoch_start() -> str:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if isinstance(cfg, dict) and cfg.get("epoch_start_iso"):
                return str(cfg["epoch_start_iso"]).strip()
        except (json.JSONDecodeError, OSError):
            pass
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"epoch_start_iso": DEFAULT_EPOCH_START_ISO, "notes": "Go-forward only; Monday 2026-03-17 market open."}, f, indent=2)
    except OSError:
        pass
    return DEFAULT_EPOCH_START_ISO


def _iter_exit_trades_with_records():
    """
    Yield (index, trade_id, pnl_usd, timestamp_iso, rec_dict) for each exit.
    rec_dict is full row for exit_attribution; minimal for unified_events.
    """
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
                if (rec.get("event_type") or rec.get("kind") or rec.get("type") or "") != "exit_decision_made":
                    continue
                trade_id = rec.get("trade_id")
                pnl = rec.get("realized_pnl_usd") or rec.get("pnl_usd") or rec.get("pnl") or 0.0
                try:
                    pnl = float(pnl)
                except (TypeError, ValueError):
                    pnl = 0.0
                ts = rec.get("timestamp") or rec.get("ts") or ""
                rec_min = {"strategy_id": rec.get("strategy_id"), "mode": rec.get("mode"), "timestamp": ts}
                yield idx, str(trade_id or f"idx_{idx}"), pnl, ts, rec_min
        return

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
            if not isinstance(rec, dict):
                continue
            trade_id = rec.get("trade_id") or f"exit_attr_{idx}"
            pnl = rec.get("realized_pnl_usd") or rec.get("pnl") or rec.get("pnl_usd") or 0.0
            try:
                pnl = float(pnl)
            except (TypeError, ValueError):
                pnl = 0.0
            ts = rec.get("timestamp") or rec.get("ts") or rec.get("exit_timestamp") or ""
            yield idx, str(trade_id), pnl, ts, rec


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


def _compute_promoted_angle(trades: list[tuple[Any, str, float, str, dict]]) -> tuple[str, str, str, list[dict]]:
    """
    trades: list of (idx, trade_id, pnl_usd, ts, rec).
    Returns (promoted_angle, promoted_dimension, promoted_value, angle_rankings).
    angle_rankings: list of {dimension, value, pnl_usd, trade_count} sorted by pnl_usd desc.
    """
    by_angle: dict[tuple[str, str], list[float]] = defaultdict(list)
    for _, _, pnl, _, rec in trades:
        for dim, extract in ANGLE_EXTRACTORS:
            val = extract(rec)
            by_angle[(dim, val)].append(pnl)

    aggregated = []
    for (dim, val), pnls in by_angle.items():
        aggregated.append((dim, val, sum(pnls), len(pnls)))

    if not aggregated:
        return "strategy:unknown", "strategy", "unknown", []

    best = max(aggregated, key=lambda x: x[2])
    promoted_dimension, promoted_value, _, _ = best
    promoted_angle = f"{promoted_dimension}:{promoted_value}"

    rankings = [
        {"dimension": d, "value": v, "pnl_usd": round(pnl_sum, 4), "trade_count": n}
        for d, v, pnl_sum, n in sorted(aggregated, key=lambda x: -x[2])[:15]
    ]
    return promoted_angle, promoted_dimension, promoted_value, rankings


def main() -> int:
    _ensure_dirs()
    log = _setup_logging()
    epoch_start = _load_epoch_start()
    log.info("Fast-lane shadow cycle start; epoch_start=%s", epoch_start[:19] if epoch_start else "none")

    raw = list(_iter_exit_trades_with_records())
    trades_list = [row for row in raw if (row[3] if len(row) > 3 else "") >= epoch_start]
    if not trades_list:
        log.info("No post-epoch exit trades; skip cycle")
        return 0

    state = _load_state()
    last_idx = state.get("last_processed_trade_index", 0)
    start = last_idx
    window = trades_list[start : start + WINDOW_SIZE]
    if len(window) < WINDOW_SIZE:
        log.info("Insufficient new trades for a full window: %d (need %d)", len(window), WINDOW_SIZE)
        return 0

    trade_ids = [w[1] for w in window]
    pnls = [w[2] for w in window]
    pnl_usd = sum(pnls)
    pnl_per_trade = pnl_usd / len(pnls) if pnls else 0.0

    promoted_angle, promoted_dimension, promoted_value, angle_rankings = _compute_promoted_angle(window)

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
        "promoted_angle": promoted_angle,
        "promoted_dimension": promoted_dimension,
        "promoted_value": promoted_value,
        "angle_rankings": angle_rankings,
        "best_candidate_id": promoted_angle,
        "candidate_rankings": angle_rankings[:5],
        "timestamp_completed": timestamp_completed,
        "notes": "Promoted = most profitable angle this window. Shadow only; no live impact.",
    }

    ledger = _load_ledger()
    ledger.append(entry)
    _save_ledger(ledger)

    state["last_processed_trade_index"] = start + WINDOW_SIZE
    state["total_trades_processed"] = state.get("total_trades_processed", 0) + len(window)
    state["last_cycle_id"] = cycle_id
    _save_state(state)

    cycle_dir = CYCLES_DIR / cycle_id
    cycle_dir.mkdir(parents=True, exist_ok=True)
    with open(cycle_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)
    with open(cycle_dir / "trades_snapshot.json", "w", encoding="utf-8") as f:
        json.dump([{"trade_id": w[1], "pnl_usd": w[2]} for w in window], f, indent=2)

    log.info("Cycle %s completed: promoted=%s pnl_usd=%.2f", cycle_id, promoted_angle, pnl_usd)

    runner_ups = "; ".join(f"{r['dimension']}:{r['value']} (${r['pnl_usd']:.0f})" for r in angle_rankings[1:4])
    try:
        subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "notify_fast_lane_summary.py"),
                "--kind", "cycle",
                "--cycle-id", cycle_id,
                "--pnl-usd", str(pnl_usd),
                "--promoted", promoted_angle,
                "--runner-ups", runner_ups[:200] if runner_ups else "",
                "--notes", "Shadow only; no live impact.",
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
