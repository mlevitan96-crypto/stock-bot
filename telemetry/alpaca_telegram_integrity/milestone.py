"""250-trade milestone: count canonical closed trades since regular session open."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set

from src.telemetry.alpaca_trade_key import build_trade_key

from telemetry.alpaca_telegram_integrity.session_clock import (
    effective_regular_session_open_utc,
    session_anchor_date_et_iso,
)


def _iter_jsonl(path: Path) -> Iterator[dict]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                yield o


def _parse_exit_epoch(rec: dict) -> Optional[float]:
    for k in ("exit_ts", "timestamp", "ts", "exit_timestamp"):
        v = rec.get(k)
        if not v:
            continue
        try:
            s = str(v).strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except (TypeError, ValueError):
            continue
    return None


@dataclass
class MilestoneSnapshot:
    session_open_utc_iso: str
    session_anchor_et: str
    unique_closed_trades: int
    realized_pnl_sum_usd: float
    sample_trade_keys: List[str]


def count_since_session_open(root: Path, now: Optional[datetime] = None) -> MilestoneSnapshot:
    open_utc = effective_regular_session_open_utc(now)
    open_epoch = open_utc.timestamp()
    anchor = session_anchor_date_et_iso(now)
    exit_path = root / "logs" / "exit_attribution.jsonl"
    keys: Set[str] = set()
    pnl_sum = 0.0
    samples: List[str] = []
    for rec in _iter_jsonl(exit_path):
        ex = _parse_exit_epoch(rec)
        if ex is None or ex < open_epoch:
            continue
        sym = rec.get("symbol")
        side = rec.get("side") or rec.get("position_side")
        et = rec.get("entry_ts") or rec.get("entry_timestamp")
        try:
            tk = build_trade_key(sym, side, et)
        except Exception:
            continue
        if tk in keys:
            continue
        keys.add(tk)
        pnl = rec.get("pnl")
        if pnl is not None:
            try:
                pnl_sum += float(pnl)
            except (TypeError, ValueError):
                pass
        if len(samples) < 5:
            samples.append(tk)
    return MilestoneSnapshot(
        session_open_utc_iso=open_utc.isoformat(),
        session_anchor_et=anchor,
        unique_closed_trades=len(keys),
        realized_pnl_sum_usd=round(pnl_sum, 2),
        sample_trade_keys=samples,
    )


def load_milestone_state(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        o = json.loads(path.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_milestone_state(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def should_fire_milestone(
    root: Path,
    target: int,
    snap: MilestoneSnapshot,
    state_path: Path,
) -> tuple[bool, Dict[str, Any]]:
    """Exactly once per session_anchor_et when count >= target."""
    st = load_milestone_state(state_path)
    anchor = snap.session_anchor_et
    if st.get("session_anchor_et") != anchor:
        st = {
            "session_anchor_et": anchor,
            "fired_milestone": False,
            "last_count": 0,
        }
    st["last_count"] = snap.unique_closed_trades
    fired = bool(st.get("fired_milestone"))
    should = snap.unique_closed_trades >= target and not fired
    return should, st


def mark_milestone_fired(state_path: Path, st: Dict[str, Any]) -> None:
    st["fired_milestone"] = True
    st["fired_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_milestone_state(state_path, st)
