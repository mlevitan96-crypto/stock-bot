"""
Exit Join Reconciler — resolves delayed exits, partial fills, regime-driven exits.
Uses time-window tolerance for snapshot↔exit_attribution↔master_trade_log joins.
NO-APPLY; logging/analysis only.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Default tolerance: 5 minutes for exit snapshot↔exit_attribution match
EXIT_JOIN_WINDOW_SEC = 300


def _parse_ts(ts: str) -> int | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def reconcile_exit_snapshots_to_outcomes(
    exit_snapshots: List[Dict[str, Any]],
    master_trade_log: List[Dict[str, Any]],
    exit_attribution: List[Dict[str, Any]],
    window_sec: int = EXIT_JOIN_WINDOW_SEC,
) -> Dict[str, Any]:
    """
    Reconcile EXIT_DECISION/EXIT_FILL snapshots to master_trade_log and exit_attribution.
    Returns stats: matched_by_trade_id, matched_by_surrogate, unmatched, reasons.
    """
    from telemetry.snapshot_join_keys import (
        extract_exit_join_key_from_snapshot,
        extract_exit_join_key_from_master_trade,
        extract_exit_join_key_from_exit_attribution,
    )

    mtl_by_ejk: Dict[str, Dict] = {}
    for m in master_trade_log:
        if m.get("exit_ts"):
            ejk, _ = extract_exit_join_key_from_master_trade(m)
            mtl_by_ejk[ejk] = m

    ea_by_ejk: Dict[str, Dict] = {}
    ea_by_sym_entry: Dict[Tuple[str, str], Dict] = {}
    for e in exit_attribution:
        ejk, _ = extract_exit_join_key_from_exit_attribution(e)
        ea_by_ejk[ejk] = e
        sym = str(e.get("symbol", "")).upper()
        entry_ts = str(e.get("entry_timestamp", ""))[:19]
        ea_by_sym_entry[(sym, entry_ts)] = e

    matched_by_trade_id = 0
    matched_by_surrogate = 0
    unmatched = 0
    reasons: Dict[str, int] = defaultdict(int)

    for s in exit_snapshots:
        ejk, fields = extract_exit_join_key_from_snapshot(s)
        sym = str(s.get("symbol", "")).upper()
        exit_ts = s.get("timestamp_utc", "")
        exit_sec = _parse_ts(exit_ts)
        entry_ts = fields.get("entry_timestamp_utc") or s.get("entry_timestamp_utc")

        if ejk in mtl_by_ejk or ejk in ea_by_ejk:
            matched_by_trade_id += 1
            continue

        # Surrogate: symbol + entry_ts + time window
        found = False
        if sym and entry_ts:
            cand = ea_by_sym_entry.get((sym, str(entry_ts)[:19]))
            if cand:
                matched_by_surrogate += 1
                found = True
        if found:
            continue

        # Window-based: find exit_attribution within window
        for e in exit_attribution:
            if str(e.get("symbol", "")).upper() != sym:
                continue
            e_ts = e.get("timestamp") or e.get("exit_timestamp", "")
            e_sec = _parse_ts(e_ts)
            if e_sec is not None and exit_sec is not None and abs(e_sec - exit_sec) <= window_sec:
                matched_by_surrogate += 1
                found = True
                break
        if found:
            continue

        unmatched += 1
        if not entry_ts:
            reasons["missing_entry_ts"] += 1
        elif not str(ejk).startswith("live:"):
            reasons["surrogate_no_match"] += 1
        else:
            reasons["trade_id_not_in_mtl_or_ea"] += 1

    return {
        "matched_by_trade_id": matched_by_trade_id,
        "matched_by_surrogate": matched_by_surrogate,
        "unmatched": unmatched,
        "reasons": dict(reasons),
        "total_exit_snapshots": len(exit_snapshots),
        "total_exits_mtl": len([m for m in master_trade_log if m.get("exit_ts")]),
        "total_exits_ea": len(exit_attribution),
    }
