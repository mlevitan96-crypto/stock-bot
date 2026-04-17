"""
Append-only entry intelligence snapshot at broker submit time (non-blocking).

Written from AlpacaExecutor._submit_order_guarded when submit_entry has stashed
_pending_entry_snapshot. Join ML training on exit_attribution.entry_order_id ↔ order_id.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping, Optional


def try_append_entry_snapshot(
    executor: Any,
    symbol: str,
    side: str,
    qty: int,
    order_obj: Any,
    client_order_id: Optional[str],
    caller: str,
) -> None:
    """
    Best-effort JSONL append; never raises. Skips audit dry-run and non-entry callers.
    """
    try:
        pending = getattr(executor, "_pending_entry_snapshot", None)
        if not isinstance(pending, dict) or not pending:
            return
        if not isinstance(caller, str):
            return
        if not (
            caller.startswith("submit_entry")
            or caller.startswith("paper_exec_mode")
        ):
            return
        oid = getattr(order_obj, "id", None)
        if oid is None:
            return
        oid_s = str(oid).strip()
        if not oid_s or oid_s.upper().startswith("AUDIT-DRYRUN"):
            return

        from config.registry import LogFiles

        path = LogFiles.ENTRY_SNAPSHOTS
        path.parent.mkdir(parents=True, exist_ok=True)

        comps = pending.get("components")
        if not isinstance(comps, Mapping):
            comps = {}
        # Full component dict as required by ML contract (same keys as composite_meta.components).
        components_out = {str(k): comps[k] for k in comps}

        try:
            score_f = float(pending.get("entry_score"))
        except (TypeError, ValueError):
            score_f = float("nan")

        rec = {
            "msg": "entry_snapshot",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "symbol": str(symbol or "").upper().strip(),
            "order_id": oid_s,
            "client_order_id": (str(client_order_id).strip() if client_order_id else None),
            "trade_id": pending.get("trade_id"),
            "composite_score": score_f,
            "components": components_out,
            "market_regime": pending.get("market_regime"),
            "side": str(side or "").lower(),
            "qty": qty,
            "caller": caller,
        }
        ph = pending.get("passive_uw_harvest")
        if isinstance(ph, dict) and ph:
            rec["passive_uw_harvest"] = ph
        # Pillar 1 — microstructure alpha (telemetry-only; no execution gates).
        for _k in ("ofi_l1_roll_60s_sum", "ofi_l1_roll_300s_sum"):
            if _k in pending:
                try:
                    rec[_k] = float(pending[_k])
                except (TypeError, ValueError):
                    rec[_k] = pending[_k]
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        return
