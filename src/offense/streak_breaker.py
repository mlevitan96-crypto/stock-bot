"""
Two-loss streak breaker: after two consecutive losing closes, block new entries for 30 minutes.

State: ``state/offense_streak_state.json`` (recent realized PnL tail + optional block-until ISO).
Must never raise in hot paths.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from config.registry import Directories

_STATE_PATH = Directories.STATE / "offense_streak_state.json"
_STREAK_MINUTES = 30.0


def _load() -> Dict[str, Any]:
    try:
        if not _STATE_PATH.exists():
            return {"recent_pnls": []}
        raw = _STATE_PATH.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            return {"recent_pnls": []}
        if not isinstance(data.get("recent_pnls"), list):
            data["recent_pnls"] = []
        return data
    except Exception:
        return {"recent_pnls": []}


def _save(data: Dict[str, Any]) -> None:
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _STATE_PATH.write_text(json.dumps(data, indent=0), encoding="utf-8")
    except Exception:
        pass


def register_closed_trade_pnl(pnl_usd: Optional[Any]) -> None:
    """Append one closed-trade realized PnL (USD); refresh 30m entry block on two consecutive losses."""
    if pnl_usd is None:
        return
    try:
        p = float(pnl_usd)
        if p != p:  # NaN
            return
    except (TypeError, ValueError):
        return
    state = _load()
    hist: list = []
    for x in state.get("recent_pnls", []):
        try:
            hist.append(float(x))
        except (TypeError, ValueError):
            continue
    hist.append(p)
    hist = hist[-20:]
    state["recent_pnls"] = hist
    now = datetime.now(timezone.utc)
    if len(hist) >= 2 and hist[-2] < 0.0 and hist[-1] < 0.0:
        state["entry_block_until_utc"] = (now + timedelta(minutes=_STREAK_MINUTES)).isoformat()
    else:
        state.pop("entry_block_until_utc", None)
    state["updated_at_utc"] = now.isoformat()
    _save(state)


def entry_blocked_by_streak() -> Tuple[bool, str]:
    """Return (blocked, reason_code) if new entries should be suppressed."""
    state = _load()
    until_raw = state.get("entry_block_until_utc")
    if not until_raw:
        return False, ""
    try:
        until = datetime.fromisoformat(str(until_raw).replace("Z", "+00:00"))
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
    except Exception:
        return False, ""
    now = datetime.now(timezone.utc)
    if now < until:
        return True, "offense_streak_two_losses_30m"
    return False, ""
