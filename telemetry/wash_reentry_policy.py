"""
Wash-risk-aware re-entry scheduling (advisory; not tax/legal classification).

Reads ``state/alpaca_account_snapshot.json`` produced by
``scripts/run_alpaca_account_snapshot.py`` (``wash_risk_watchlist``).

Policy (when enabled):
- **Same NY calendar day** as ``last_loss_exit_ts`` → defer (block) new entries for that symbol.
- Otherwise on watchlist → **half** notional (qty multiplier 0.5, floored at 1 share when integer qty).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from zoneinfo import ZoneInfo

    _NY = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    _NY = timezone.utc


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ny_date(ts_utc: datetime) -> Any:
    return ts_utc.astimezone(_NY).date()


def load_wash_snapshot(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    p = path or (_repo_root() / "state" / "alpaca_account_snapshot.json")
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def wash_reentry_action(
    symbol: str,
    *,
    snapshot_path: Optional[Path] = None,
) -> Tuple[str, float]:
    """
    Returns (action, qty_multiplier) where action in ``defer_session``, ``half_size``, ``allow``.

    ``defer_session`` → multiplier 0.0 (caller should block).
    """
    snap = load_wash_snapshot(snapshot_path)
    if not snap:
        return "allow", 1.0
    wl = snap.get("wash_risk_watchlist") or []
    if not isinstance(wl, list):
        return "allow", 1.0
    sym = str(symbol or "").upper().strip()
    row = None
    for r in wl:
        if not isinstance(r, dict):
            continue
        if str(r.get("symbol") or "").upper().strip() == sym:
            row = r
            break
    if row is None:
        return "allow", 1.0

    ts_s = str(row.get("last_loss_exit_ts") or "").strip().replace("Z", "+00:00")
    try:
        loss_ts = datetime.fromisoformat(ts_s)
        if loss_ts.tzinfo is None:
            loss_ts = loss_ts.replace(tzinfo=timezone.utc)
        loss_ts = loss_ts.astimezone(timezone.utc)
    except Exception:
        return "half_size", 0.5

    now = datetime.now(timezone.utc)
    if _ny_date(loss_ts) == _ny_date(now):
        return "defer_session", 0.0
    return "half_size", 0.5
