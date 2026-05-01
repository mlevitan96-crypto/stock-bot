"""
Persistent post-epoch anchor for ML / milestone accounting.

File: ``state/epoch_state.json`` (override with ``EPOCH_STATE_JSON_PATH`` for tests).

Thread-safe within the trading process (single global lock). Cross-process writers
only use ``scripts/reset_epoch.py`` while the engine is stopped, per ops playbook.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_lock = threading.Lock()
_SCHEMA_VERSION = 1


def _epoch_path() -> Path:
    raw = os.environ.get("EPOCH_STATE_JSON_PATH", "").strip()
    if raw:
        return Path(raw)
    from config.registry import StateFiles

    return StateFiles.EPOCH_STATE


def _default_state() -> Dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "epoch_start_ts": 0.0,
        "epoch_label": "",
        "post_epoch_terminal_exit_count": 0,
        "fired_milestones": [],
        "updated_at": "",
    }


def load_epoch_state() -> Dict[str, Any]:
    p = _epoch_path()
    out = _default_state()
    try:
        if p.is_file():
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                out.update(raw)
    except Exception:
        pass
    fired = out.get("fired_milestones")
    if not isinstance(fired, list):
        out["fired_milestones"] = []
    else:
        out["fired_milestones"] = [int(x) for x in fired if str(x).isdigit()]
    try:
        out["epoch_start_ts"] = float(out.get("epoch_start_ts") or 0.0)
    except (TypeError, ValueError):
        out["epoch_start_ts"] = 0.0
    try:
        out["post_epoch_terminal_exit_count"] = int(out.get("post_epoch_terminal_exit_count") or 0)
    except (TypeError, ValueError):
        out["post_epoch_terminal_exit_count"] = 0
    return out


def save_epoch_state(state: Dict[str, Any]) -> None:
    p = _epoch_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    body = dict(state)
    body["schema_version"] = _SCHEMA_VERSION
    body["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(body, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(str(tmp), str(p))


def get_epoch_start_ts() -> float:
    with _lock:
        return float(load_epoch_state().get("epoch_start_ts") or 0.0)


def anchor_new_epoch(*, epoch_label: str = "", epoch_start_ts: Optional[float] = None) -> Dict[str, Any]:
    """Set a new era floor and reset milestone counters."""
    ts = float(epoch_start_ts if epoch_start_ts is not None else time.time())
    with _lock:
        st = _default_state()
        st["epoch_start_ts"] = ts
        st["epoch_label"] = str(epoch_label or "")[:200]
        st["post_epoch_terminal_exit_count"] = 0
        st["fired_milestones"] = []
        save_epoch_state(st)
        return dict(st)


def increment_post_epoch_exit_and_check_milestone() -> Tuple[int, Optional[int]]:
    """
    Increment terminal-exit counter (post-epoch only; caller must have verified entry >= epoch).

    Returns (new_count, milestone_hit) where milestone_hit is one of 10,50,150,250 or None.
    """
    milestones = (10, 50, 150, 250)
    with _lock:
        st = load_epoch_state()
        if float(st.get("epoch_start_ts") or 0.0) <= 0.0:
            return int(st.get("post_epoch_terminal_exit_count") or 0), None
        n = int(st.get("post_epoch_terminal_exit_count") or 0) + 1
        st["post_epoch_terminal_exit_count"] = n
        fired: List[int] = [int(x) for x in (st.get("fired_milestones") or []) if str(x).isdigit()]
        fired_set = set(fired)
        hit: Optional[int] = None
        for m in milestones:
            if n == m and m not in fired_set:
                hit = m
                fired_set.add(m)
                break
        st["fired_milestones"] = sorted(fired_set)
        save_epoch_state(st)
        return n, hit


def mark_milestone_fired_external(milestone: int) -> None:
    """If Telegram failed, operator may use repair; normally not needed."""
    with _lock:
        st = load_epoch_state()
        fired = {int(x) for x in (st.get("fired_milestones") or []) if str(x).isdigit()}
        fired.add(int(milestone))
        st["fired_milestones"] = sorted(fired)
        save_epoch_state(st)
