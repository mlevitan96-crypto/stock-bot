"""Milestone trade counts: canonical trade_key since session open or since integrity-arm epoch."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.governance.canonical_trade_count import compute_canonical_trade_count

from telemetry.alpaca_telegram_integrity.session_clock import (
    effective_regular_session_open_utc,
    session_anchor_date_et_iso,
)


@dataclass
class MilestoneSnapshot:
    session_open_utc_iso: str
    session_anchor_et: str
    unique_closed_trades: int
    realized_pnl_sum_usd: float
    sample_trade_keys: List[str]
    counting_basis: str = "session_open"
    count_floor_utc_iso: str = ""
    integrity_armed: bool = True


def count_since_session_open(root: Path, now: Optional[datetime] = None) -> MilestoneSnapshot:
    """Legacy name: counts since US regular session open (same as build_milestone_snapshot session_open)."""
    return build_milestone_snapshot(
        root, counting_basis="session_open", arm_epoch_utc=None, now=now
    )


def integrity_arm_state_path(root: Path) -> Path:
    return root / "state" / "alpaca_milestone_integrity_arm.json"


def load_integrity_arm_state(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        o = json.loads(path.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_integrity_arm_state(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def update_integrity_arm_state(
    root: Path,
    session_anchor_et: str,
    precheck_ok: bool,
) -> Dict[str, Any]:
    """
    When precheck_ok first becomes true for this session_anchor_et, record arm_epoch_utc = now.
    Resets arm_epoch when anchor changes.
    """
    path = integrity_arm_state_path(root)
    st = load_integrity_arm_state(path)
    if st.get("session_anchor_et") != session_anchor_et:
        st = {
            "session_anchor_et": session_anchor_et,
            "arm_epoch_utc": None,
            "armed_at_utc_iso": None,
        }
    if st.get("arm_epoch_utc") is None and precheck_ok:
        now = datetime.now(timezone.utc)
        st["arm_epoch_utc"] = now.timestamp()
        st["armed_at_utc_iso"] = now.isoformat()
    save_integrity_arm_state(path, st)
    return st


def build_milestone_snapshot(
    root: Path,
    *,
    counting_basis: str,
    arm_epoch_utc: Optional[float],
    now: Optional[datetime] = None,
) -> MilestoneSnapshot:
    """
    counting_basis:
      - session_open: count exits >= US regular session open (legacy).
      - integrity_armed: count exits >= arm_epoch_utc; 0 trades until armed.
    """
    now = now or datetime.now(timezone.utc)
    open_utc = effective_regular_session_open_utc(now)
    anchor = session_anchor_date_et_iso(now)

    if counting_basis == "session_open":
        open_epoch = open_utc.timestamp()
        return _snapshot_for_floor(
            root,
            floor_epoch=open_epoch,
            session_open_utc_iso=open_utc.isoformat(),
            session_anchor_et=anchor,
            counting_basis=counting_basis,
            count_floor_utc_iso=open_utc.isoformat(),
            integrity_armed=True,
        )

    # integrity_armed
    if arm_epoch_utc is None:
        return MilestoneSnapshot(
            session_open_utc_iso=open_utc.isoformat(),
            session_anchor_et=anchor,
            unique_closed_trades=0,
            realized_pnl_sum_usd=0.0,
            sample_trade_keys=[],
            counting_basis=counting_basis,
            count_floor_utc_iso="(not armed — waiting for green DATA_READY + coverage + strict ARMED + exit probe)",
            integrity_armed=False,
        )
    return _snapshot_for_floor(
        root,
        floor_epoch=arm_epoch_utc,
        session_open_utc_iso=open_utc.isoformat(),
        session_anchor_et=anchor,
        counting_basis=counting_basis,
        count_floor_utc_iso=datetime.fromtimestamp(arm_epoch_utc, tz=timezone.utc).isoformat(),
        integrity_armed=True,
    )


def _snapshot_for_floor(
    root: Path,
    *,
    floor_epoch: float,
    session_open_utc_iso: str,
    session_anchor_et: str,
    counting_basis: str,
    count_floor_utc_iso: str,
    integrity_armed: bool,
) -> MilestoneSnapshot:
    """Same trade_key + era-cut rules as dashboard / audit (`compute_canonical_trade_count`)."""
    out = compute_canonical_trade_count(root, floor_epoch=floor_epoch, max_samples=5)
    samples = list(out.get("sample_trade_keys") or [])
    return MilestoneSnapshot(
        session_open_utc_iso=session_open_utc_iso,
        session_anchor_et=session_anchor_et,
        unique_closed_trades=int(out.get("total_trades_post_era") or 0),
        realized_pnl_sum_usd=float(out.get("realized_pnl_sum_usd") or 0.0),
        sample_trade_keys=samples,
        counting_basis=counting_basis,
        count_floor_utc_iso=count_floor_utc_iso,
        integrity_armed=integrity_armed,
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
