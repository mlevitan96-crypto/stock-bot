"""Exit attribution enrichment for mode/strategy/regime bucketing (governance-grade)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(obj: Any, path: str, default=None):
    """Safe attribute/dict getter. path like 'a.b.c'"""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(part, default)
        else:
            cur = getattr(cur, part, default)
    return cur


def enrich_exit_row(
    row: Dict[str, Any],
    *,
    position: Any = None,
    order: Any = None,
    context: Any = None,
    mode: Optional[str] = None,
    strategy: Optional[str] = None,
    regime_label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns a COPY of `row` with governance-grade keys added.

    Priority:
    - explicit args (mode/strategy/regime_label)
    - context fields if present
    - position fields if present
    - env vars as fallback

    Nothing here should be considered authoritative for P&L math; it is for bucketing, replay, and governance.
    """
    out = dict(row or {})

    # ---- Mode
    m = (
        mode
        or _get(context, "mode")
        or _get(context, "run_mode")
        or os.getenv("RUN_MODE")
        or os.getenv("MODE")
        or out.get("mode")
        or out.get("run_mode")
        or "UNKNOWN"
    )
    out["mode"] = str(m).upper()

    # ---- Strategy
    s = (
        strategy
        or _get(position, "strategy")
        or _get(position, "strategy_label")
        or _get(context, "strategy")
        or out.get("strategy")
        or out.get("strategy_label")
        or "UNKNOWN"
    )
    out["strategy"] = str(s).upper()

    # ---- Regime
    r = (
        regime_label
        or _get(context, "regime_label")
        or _get(context, "regime")
        or out.get("regime_label")
        or out.get("exit_regime")
        or "UNKNOWN"
    )
    out["regime_label"] = str(r).upper()

    # ---- Core identifiers (best effort)
    out.setdefault(
        "symbol",
        _get(position, "symbol") or _get(order, "symbol") or out.get("symbol") or "UNKNOWN",
    )
    out.setdefault(
        "side",
        _get(position, "side") or _get(order, "side") or out.get("side") or "UNKNOWN",
    )

    # ---- Entry/exit timestamps (best effort)
    out.setdefault(
        "entry_ts",
        out.get("entry_ts")
        or out.get("entry_timestamp")
        or _get(position, "entry_ts")
        or _get(position, "opened_at")
        or _get(order, "filled_at")
        or None,
    )
    out.setdefault(
        "exit_ts",
        out.get("exit_ts")
        or out.get("timestamp")
        or _get(context, "ts")
        or _get(context, "timestamp")
        or _get(order, "submitted_at")
        or None,
    )

    # ---- Prices/sizing (best effort)
    out.setdefault(
        "entry_price",
        out.get("entry_price")
        or _get(position, "entry_price")
        or _get(position, "avg_entry_price")
        or None,
    )
    out.setdefault(
        "exit_price",
        out.get("exit_price")
        or _get(position, "exit_price")
        or _get(order, "avg_fill_price")
        or None,
    )
    out.setdefault(
        "qty",
        out.get("qty") or _get(position, "qty") or _get(order, "qty") or None,
    )

    # ---- Derived
    out.setdefault("_enriched_at", _utcnow_iso())

    return out
