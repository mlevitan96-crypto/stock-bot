"""
First-5 Wheel submit Telegram integrity pager.

Fires at most five Telegram messages across the lifetime of the deployment for
successful Wheel broker submits (CSP or CC), with a file-backed counter so restarts
do not reset the budget. Best-effort; never raises.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

_MAX_FIRST_FIVE = 5
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_STATE = _REPO_ROOT / "state" / "wheel_first_five_submit_state.json"


def _state_path() -> Path:
    try:
        from config.registry import StateFiles

        p = getattr(StateFiles, "WHEEL_FIRST_FIVE_SUBMIT", None)
        if p is not None:
            return Path(p)
    except Exception:
        pass
    return _DEFAULT_STATE


def _load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version": 1, "sent": 0, "seen_order_ids": []}
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            return {"version": 1, "sent": 0, "seen_order_ids": []}
        data.setdefault("version", 1)
        data.setdefault("sent", 0)
        data.setdefault("seen_order_ids", [])
        if not isinstance(data["seen_order_ids"], list):
            data["seen_order_ids"] = []
        return data
    except Exception as e:
        log.debug("wheel_first_five load state: %s", e)
        return {"version": 1, "sent": 0, "seen_order_ids": []}


def _save_state(path: Path, data: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception as e:
        log.warning("wheel_first_five save state failed: %s", e)


def _format_message(
    *,
    phase: str,
    underlying: str,
    action: str,
    strike: float,
    order_id: Optional[str],
    iv_rank: Optional[float],
    underlying_mid: float,
    put_wall_strike: Optional[float],
    premium_usd: Optional[float],
) -> str:
    iv_s = f"{iv_rank:.1f}" if iv_rank is not None else "n/a"
    mid_s = f"{underlying_mid:.2f}"
    wall_s = f"{put_wall_strike:.2f}" if put_wall_strike is not None else "n/a"
    prem_s = f"{premium_usd:.2f}" if premium_usd is not None else "n/a"
    oid = order_id or "n/a"
    return (
        f"Wheel First-5 submit [{phase}]\n"
        f"Ticker: {underlying} | Action: {action} | Strike: {strike:g}\n"
        f"OrderId: {oid}\n"
        f"Auth context — [IV Rank]={iv_s} | [Premium USD]={prem_s} | [Underlying mid]={mid_s} | [Put wall strike]={wall_s}"
    )


def maybe_telegram_wheel_first_five_submit(
    *,
    phase: str,
    underlying: str,
    action: str,
    strike: float,
    order_id: Optional[str],
    iv_rank: Optional[float],
    underlying_mid: float,
    put_wall_strike: Optional[float],
    premium_usd: Optional[float] = None,
) -> None:
    """
    If ``order_id`` is set and fewer than five alerts have been sent, send Telegram
    and persist counter. Dedupes on ``order_id``.
    """
    if not order_id:
        return
    if str(os.getenv("WHEEL_FIRST_FIVE_TELEGRAM", "1")).strip().lower() in ("0", "false", "no", "off"):
        return
    path = _state_path()
    st = _load_state(path)
    sent = int(st.get("sent") or 0)
    seen: List[str] = [str(x) for x in (st.get("seen_order_ids") or []) if x]
    if order_id in seen:
        return
    if sent >= _MAX_FIRST_FIVE:
        return

    msg = _format_message(
        phase=phase,
        underlying=underlying.upper(),
        action=action,
        strike=float(strike),
        order_id=order_id,
        iv_rank=iv_rank,
        underlying_mid=float(underlying_mid),
        put_wall_strike=put_wall_strike,
        premium_usd=premium_usd,
    )
    try:
        from scripts.alpaca_telegram import send_governance_telegram

        ok = bool(send_governance_telegram(msg, script_name="wheel_first_five_submit"))
    except Exception as e:
        log.debug("wheel_first_five telegram send: %s", e)
        ok = False
    if not ok:
        return

    seen.append(str(order_id))
    st["sent"] = sent + 1
    st["seen_order_ids"] = seen[-50:]
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_state(path, st)
    log.info("Wheel First-5 Telegram sent (%s/%s) for %s order_id=%s", st["sent"], _MAX_FIRST_FIVE, underlying, order_id)
