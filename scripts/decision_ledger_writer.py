"""
Decision ledger writer: atomic append JSONL and event builder for pipeline instrumentation.
Use at: after signal computation, after feature computation, after score computation,
after each gate evaluation, after order intent build, after order submission/skip.
Every candidate evaluation must emit at least one event line.
No silent drops—every block must have gate_name + reason + measured + params.
"""
from __future__ import annotations

import json
import math
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER_PATH = REPO_ROOT / "reports" / "decision_ledger" / "decision_ledger.jsonl"


def _sanitize(obj: Any) -> Any:
    """Replace NaN/Inf so JSON is valid."""
    if isinstance(obj, float):
        if math.isfinite(obj):
            return round(obj, 6)
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    return obj


def append_jsonl(path: Path, event_dict: Dict[str, Any]) -> None:
    """
    Atomic append one JSONL line. Safe under crashes (write + flush).
    Creates parent dirs if needed.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = _sanitize(event_dict)
    line = json.dumps(rec, default=str) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Event builder for pipeline instrumentation (one event per candidate)
# ---------------------------------------------------------------------------

_current_event: Dict[str, Any] = {}
_lock = threading.Lock()


def start_event(
    run_id: str,
    ts: float,
    symbol: str,
    venue: str = "alpaca",
    timeframe: str = "1m",
    mode: str = "observe",
) -> Dict[str, Any]:
    """Start a new decision event for one candidate. Returns the mutable event dict."""
    with _lock:
        global _current_event
        _current_event = {
            "run_id": run_id,
            "ts": int(ts) if isinstance(ts, (int, float)) else int(ts) if ts else 0,
            "ts_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else "",
            "symbol": symbol,
            "venue": venue,
            "timeframe": timeframe,
            "mode": mode,
            "signal_raw": {},
            "features": {},
            "score_components": {},
            "score_final": 0.0,
            "thresholds": {},
            "gates": [],
            "candidate_status": "GENERATED",
            "order_intent": None,
            "order_result": None,
        }
        return _current_event


def get_current_event() -> Optional[Dict[str, Any]]:
    """Return current in-progress event (for instrumentation)."""
    with _lock:
        return _current_event if _current_event else None


def set_signals(event: Optional[Dict[str, Any]], signal_raw: Dict[str, Any]) -> None:
    if not event:
        return
    event["signal_raw"] = dict(signal_raw) if signal_raw else {}


def set_features(event: Optional[Dict[str, Any]], features: Dict[str, Any]) -> None:
    if not event:
        return
    event["features"] = dict(features) if features else {}


def set_score_components(
    event: Optional[Dict[str, Any]],
    components: Dict[str, Any],
    score_final: float,
    thresholds: Dict[str, Any],
) -> None:
    if not event:
        return
    event["score_components"] = dict(components) if components else {}
    event["score_final"] = float(score_final)
    event["thresholds"] = dict(thresholds) if thresholds else {}


def append_gate(
    event: Optional[Dict[str, Any]],
    gate_name: str,
    pass_: bool,
    reason: str,
    params: Optional[Dict[str, Any]] = None,
    measured: Optional[Dict[str, Any]] = None,
) -> None:
    if not event:
        return
    gates = event.setdefault("gates", [])
    gates.append({
        "gate_name": gate_name,
        "pass": pass_,
        "reason": reason,
        "params": dict(params) if params else {},
        "measured": dict(measured) if measured else {},
    })


def set_candidate_status(event: Optional[Dict[str, Any]], status: str) -> None:
    if not event:
        return
    if status in ("GENERATED", "BLOCKED", "ORDERED", "SKIPPED"):
        event["candidate_status"] = status


def set_order_intent(event: Optional[Dict[str, Any]], intent: Dict[str, Any]) -> None:
    if not event:
        return
    event["order_intent"] = dict(intent) if intent else None


def set_order_result(event: Optional[Dict[str, Any]], result: Dict[str, Any]) -> None:
    if not event:
        return
    event["order_result"] = dict(result) if result else None


def emit(path: Optional[Path] = None) -> bool:
    """
    Write current event to ledger and clear. Returns True if an event was written.
    """
    with _lock:
        global _current_event
        ev = _current_event
        _current_event = {}
    if not ev:
        return False
    p = path or DEFAULT_LEDGER_PATH
    append_jsonl(p, ev)
    return True


def clear_current() -> None:
    """Clear current event without writing (e.g. on error path)."""
    with _lock:
        global _current_event
        _current_event = {}
