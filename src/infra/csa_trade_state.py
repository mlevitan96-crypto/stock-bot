"""
CSA every-100-trades state: persist trade-event count and last CSA run.
Used by primary trigger (trading engine) and backup trigger (droplet hook).
Pure functions + small helpers; no side effects except file I/O.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

# Default state path (repo root relative to this file)
_REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = Path(os.environ.get("TRADE_CSA_STATE_DIR", str(_REPO_ROOT / "reports" / "state")))
STATE_FILE = STATE_DIR / "TRADE_CSA_STATE.json"
EVENT_LOG = STATE_DIR / "trade_events.jsonl"  # One line per event for backup reconciliation


def _default_state() -> dict:
    return {
        "total_trade_events": 0,
        "last_csa_trade_count": 0,
        "last_csa_mission_id": "",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def load_state() -> dict:
    """Load state from TRADE_CSA_STATE.json. If missing or invalid, return defaults with zeros."""
    if not STATE_FILE.exists():
        return _default_state()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_state()
        # Ensure required keys
        for key in ("total_trade_events", "last_csa_trade_count", "last_csa_mission_id", "last_updated"):
            if key not in data:
                data[key] = _default_state()[key]
        return data
    except Exception:
        return _default_state()


def save_state(state: dict) -> None:
    """Write state to TRADE_CSA_STATE.json. Creates directory if needed."""
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def increment_trade_count(delta: int = 1, event_type: str = "executed") -> dict:
    """Increment total_trade_events by delta, append to event log for backup reconciliation, save, and return updated state."""
    state = load_state()
    state["total_trade_events"] = state.get("total_trade_events", 0) + delta
    # Append one line per event so backup trigger can reconcile count from log
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(EVENT_LOG, "a", encoding="utf-8") as f:
            for _ in range(delta):
                f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "type": event_type}, default=str) + "\n")
    except Exception:
        pass
    save_state(state)
    return state


def should_run_csa_every_100(state: dict) -> bool:
    """
    Return True if we should run CSA now:
    - total_trade_events > 0
    - total_trade_events % 100 == 0
    - total_trade_events > last_csa_trade_count (avoid double-run)
    """
    total = state.get("total_trade_events", 0)
    last = state.get("last_csa_trade_count", 0)
    return total > 0 and total % 100 == 0 and total > last


def _run_csa_wrapper(mission_id: str, total_at_run: int) -> None:
    """Call scripts/run_csa_every_100_trades.py with mission_id. State already updated by record_trade_event."""
    script = _REPO_ROOT / "scripts" / "run_csa_every_100_trades.py"
    if not script.exists():
        return
    try:
        subprocess.run(
            [os.environ.get("PYTHON", "python"), str(script), "--mission-id", mission_id, "--trade-count", str(total_at_run)],
            cwd=str(_REPO_ROOT),
            timeout=300,
            check=False,
        )
    except Exception:
        pass


def reset_state_for_today() -> dict:
    """
    Reset trade count to start of today (market open). Zeros total_trade_events and last_csa_trade_count,
    clears the event log, and saves state. Use after deploy or when CSA review should start fresh from today.
    Returns the new state.
    """
    state = _default_state()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if EVENT_LOG.exists():
        try:
            EVENT_LOG.unlink()
        except Exception:
            pass
    save_state(state)
    return state


def get_trade_event_count_from_log() -> int:
    """Count lines in trade_events.jsonl for backup reconciliation. Returns 0 if missing."""
    if not EVENT_LOG.exists():
        return 0
    try:
        with open(EVENT_LOG, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def reconcile_state_from_log(state: dict | None = None) -> dict:
    """If event log has more events than state, update state and save. Returns current state."""
    s = state if state is not None else load_state()
    log_count = get_trade_event_count_from_log()
    if log_count > s.get("total_trade_events", 0):
        s["total_trade_events"] = log_count
        save_state(s)
    return s


def record_trade_event(event_type: str = "executed", _run_csa_in_background: bool = True) -> None:
    """
    Single function called for every final trade decision (executed, blocked, counter_intel_rejected).
    Increments total_trade_events, then if we hit a 100-event milestone, runs CSA (in background by default).
    Updates last_csa_trade_count/last_csa_mission_id immediately to avoid double-runs; does not block the trading thread.
    """
    state = increment_trade_count(1, event_type=event_type)
    if not should_run_csa_every_100(state):
        return
    total = state["total_trade_events"]
    mission_id = "CSA_TRADE_100_" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    # Claim this milestone so no other path (e.g. backup trigger) runs CSA for this count
    state["last_csa_trade_count"] = total
    state["last_csa_mission_id"] = mission_id
    save_state(state)
    if _run_csa_in_background:
        thread = threading.Thread(target=_run_csa_wrapper, args=(mission_id, total), daemon=True)
        thread.start()
    else:
        _run_csa_wrapper(mission_id, total)
