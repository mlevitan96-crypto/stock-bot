#!/usr/bin/env python3
"""
Defer retry engine: retry deferred candidates every UW_DEFER_RETRY_EVERY_MINUTES,
stop after UW_DEFER_MAX_MINUTES; re-check data health, attempt repair; log to uw_defer_retry_events.jsonl.
On expired: write symbol to state/uw_defer_expired_symbols.json so next pipeline run penalizes instead of defers.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

UW_DEFERRED_CANDIDATES = REPO / "reports" / "uw_health" / "uw_deferred_candidates.jsonl"
UW_DEFER_RETRY_EVENTS = REPO / "reports" / "uw_health" / "uw_defer_retry_events.jsonl"
UW_DEFER_EXPIRED_SYMBOLS = REPO / "state" / "uw_defer_expired_symbols.json"
DEFER_RETRY_MIN = int(os.environ.get("UW_DEFER_RETRY_EVERY_MINUTES", "15"))
DEFER_MAX_MIN = int(os.environ.get("UW_DEFER_MAX_MINUTES", "120"))


def _append_jsonl(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def _data_health_snapshot(symbol: str, base: Path) -> dict:
    from board.eod.uw_failure_diagnostics import _bars_status, _uw_root_cause_file_and_date
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bars = _bars_status(symbol, date_str, base)
    uw_path, uw_date = _uw_root_cause_file_and_date(base)
    now_date = date_str
    uw_fresh = False
    if uw_date and now_date:
        try:
            from datetime import datetime as dt_parse
            file_dt = dt_parse.strptime(uw_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            now_dt = dt_parse.strptime(now_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            uw_fresh = (now_dt - file_dt).total_seconds() < 25 * 3600  # within ~1 day
        except Exception:
            pass
    return {
        "bars_present": bars.get("has_bars"),
        "bars_count": bars.get("count", 0),
        "uw_root_cause_present": uw_path is not None and uw_path.exists(),
        "uw_root_cause_fresh": uw_fresh,
    }


def _load_deferred(limit: int = 500) -> list[dict]:
    if not UW_DEFERRED_CANDIDATES.exists():
        return []
    lines = UW_DEFERRED_CANDIDATES.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _load_expired_symbols() -> set:
    if not UW_DEFER_EXPIRED_SYMBOLS.exists():
        return set()
    try:
        data = json.loads(UW_DEFER_EXPIRED_SYMBOLS.read_text(encoding="utf-8"))
        return set(data if isinstance(data, list) else data.get("symbols", []))
    except Exception:
        return set()


def _add_expired_symbol(symbol: str) -> None:
    UW_DEFER_EXPIRED_SYMBOLS.parent.mkdir(parents=True, exist_ok=True)
    s = _load_expired_symbols()
    s.add(symbol)
    UW_DEFER_EXPIRED_SYMBOLS.write_text(json.dumps({"symbols": list(s), "updated": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")


def main() -> int:
    base = REPO
    now_ts = int(datetime.now(timezone.utc).timestamp())
    cutoff_first = now_ts - DEFER_MAX_MIN * 60  # deferrals older than this are expired
    retry_cutoff = now_ts - DEFER_RETRY_MIN * 60  # next_retry_ts before this are due for retry
    deferred = _load_deferred()
    # Group by (symbol, first_defer_ts) and take latest next_retry_ts
    by_key: dict[tuple, dict] = {}
    for r in deferred:
        sym = r.get("symbol", "")
        first = int(r.get("first_defer_ts") or 0)
        next_retry = int(r.get("next_retry_ts") or 0)
        if first < cutoff_first:
            # Already past max window: mark expired and skip
            _append_jsonl(UW_DEFER_RETRY_EVENTS, {
                "symbol": sym,
                "first_defer_ts": first,
                "retry_ts": now_ts,
                "attempt_no": -1,
                "data_health_snapshot": _data_health_snapshot(sym, base),
                "repair_attempted": False,
                "repair_success": False,
                "final_outcome": "expired_then_penalized",
            })
            _add_expired_symbol(sym)
            continue
        key = (sym, first)
        if next_retry > (by_key.get(key) or {}).get("next_retry_ts", 0):
            by_key[key] = {**r, "next_retry_ts": next_retry}
    # Retry those due
    attempt_no = 0
    for (sym, first), r in list(by_key.items()):
        next_retry = int(r.get("next_retry_ts") or 0)
        if next_retry > now_ts:
            continue
        attempt_no += 1
        snapshot = _data_health_snapshot(sym, base)
        repair_result = {"repair_attempted": False, "repair_success": False}
        if not snapshot.get("bars_present") or not snapshot.get("uw_root_cause_fresh"):
            from board.eod.uw_failure_diagnostics import attempt_repair, UW_MISSING_DATA
            repair_result = attempt_repair(UW_MISSING_DATA, sym, base)
            snapshot = _data_health_snapshot(sym, base)
        if snapshot.get("bars_present") and snapshot.get("uw_root_cause_fresh"):
            final_outcome = "resolved"
        elif (now_ts - first) >= DEFER_MAX_MIN * 60:
            final_outcome = "expired_then_penalized"
            _add_expired_symbol(sym)
        else:
            final_outcome = "still_deferred"
        _append_jsonl(UW_DEFER_RETRY_EVENTS, {
            "symbol": sym,
            "first_defer_ts": first,
            "retry_ts": now_ts,
            "attempt_no": attempt_no,
            "data_health_snapshot": snapshot,
            "repair_attempted": repair_result.get("repair_attempted"),
            "repair_success": repair_result.get("repair_success"),
            "final_outcome": final_outcome,
        })
    return 0


if __name__ == "__main__":
    sys.exit(main())
