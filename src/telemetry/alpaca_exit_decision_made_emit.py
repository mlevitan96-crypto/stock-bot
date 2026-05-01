"""
Terminal ``exit_decision_made`` rows on ``logs/run.jsonl`` + post-epoch milestone hooks.

Emitted only when ``terminal_close`` attribution succeeded and entry time is on/after
``epoch_start_ts`` (see ``epoch_manager`` / ``scripts/reset_epoch.py``).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.telemetry.epoch_manager import (
    get_epoch_start_ts,
    increment_post_epoch_exit_and_check_milestone,
)
from src.telemetry.post_epoch_milestone_tracker import notify_milestone_async


def _append_run(rec: Dict[str, Any]) -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / "logs" / "run.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    rec.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def _entry_epoch(entry_time_iso: Optional[str]) -> Optional[float]:
    if not entry_time_iso or not isinstance(entry_time_iso, str):
        return None
    try:
        t = entry_time_iso.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return float(dt.timestamp())
    except Exception:
        return None


def maybe_emit_exit_decision_made_and_track_milestones(
    *,
    trade_id: str,
    symbol: str,
    canonical_trade_id: str,
    trade_key: str,
    entry_time_iso: Optional[str],
    terminal_close: bool,
    feature_snapshot: Optional[Dict[str, Any]] = None,
) -> None:
    if not terminal_close:
        return
    epoch_ts = float(get_epoch_start_ts() or 0.0)
    if epoch_ts <= 0.0:
        return
    ent_ep = _entry_epoch(entry_time_iso)
    if ent_ep is None or ent_ep + 1e-6 < epoch_ts:
        return
    rec: Dict[str, Any] = {
        "event_type": "exit_decision_made",
        "terminal_close": True,
        "trade_id": str(trade_id),
        "symbol": str(symbol).upper(),
        "canonical_trade_id": str(canonical_trade_id or trade_key or ""),
        "trade_key": str(trade_key or canonical_trade_id or ""),
        "entry_timestamp": str(entry_time_iso or ""),
        "entry_timestamp_epoch": float(ent_ep),
        "epoch_start_ts": float(epoch_ts),
    }
    snap = feature_snapshot if isinstance(feature_snapshot, dict) else {}
    if snap:
        rec["feature_snapshot_at_exit"] = dict(snap)
    try:
        _append_run(rec)
    except Exception:
        return
    try:
        n, hit = increment_post_epoch_exit_and_check_milestone()
    except Exception:
        return
    if hit is not None:
        notify_milestone_async(milestone=int(hit), post_epoch_count=int(n), epoch_start_ts=float(epoch_ts))
