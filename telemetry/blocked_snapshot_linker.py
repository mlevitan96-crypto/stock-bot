"""
Blocked-Trade Snapshot Linker — links state/blocked_trades.jsonl to nearest ENTRY_DECISION snapshot.
Explains why trades were blocked and what intelligence was present. NO-APPLY.
Output: logs/blocked_trade_snapshots.jsonl (append-only).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configurable time window (seconds): link blocked trade to snapshot within this window
BLOCKED_SNAPSHOT_WINDOW_SEC = 600  # 10 minutes


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


def _load_jsonl(path: Path) -> List[Dict]:
    out = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def link_blocked_to_snapshots(
    blocked: List[Dict[str, Any]],
    entry_snapshots: List[Dict[str, Any]],
    window_sec: int = BLOCKED_SNAPSHOT_WINDOW_SEC,
) -> List[Dict[str, Any]]:
    """
    Link each blocked trade to nearest ENTRY_DECISION snapshot by symbol + time window.
    Returns list of linked records for logs/blocked_trade_snapshots.jsonl.
    """
    # Index snapshots by symbol, sorted by timestamp
    by_symbol: Dict[str, List[Dict]] = {}
    for s in entry_snapshots:
        sym = str(s.get("symbol", "")).upper()
        if sym not in by_symbol:
            by_symbol[sym] = []
        by_symbol[sym].append(s)
    for sym in by_symbol:
        by_symbol[sym].sort(key=lambda x: _parse_ts(x.get("timestamp_utc", "")) or 0)

    records = []
    for b in blocked:
        ts = b.get("timestamp") or b.get("ts", "")
        block_sec = _parse_ts(ts)
        sym = str(b.get("symbol", "")).upper()
        reason = b.get("reason", "unknown")
        direction = b.get("direction") or "long"
        score = b.get("score", 0.0)
        components = b.get("components") or b.get("signals") or {}

        snapshot = None
        snapshots = by_symbol.get(sym, [])
        if block_sec is not None and snapshots:
            best_delta = None
            for s in snapshots:
                s_sec = _parse_ts(s.get("timestamp_utc", ""))
                if s_sec is None:
                    continue
                delta = abs(block_sec - s_sec)
                if delta <= window_sec:
                    if best_delta is None or delta < best_delta:
                        best_delta = delta
                        snapshot = s

        comp_present = []
        comp_defaulted = []
        comp_missing = []
        regime_label = None
        if snapshot:
            comps = snapshot.get("components") or {}
            for cname, cval in comps.items():
                if isinstance(cval, dict):
                    if cval.get("present"):
                        comp_present.append(cname)
                    elif cval.get("defaulted"):
                        comp_defaulted.append(cname)
                    else:
                        comp_missing.append(cname)
            regime_label = snapshot.get("regime_label")

        blocked_join_key = f"blocked|{sym}|{str(ts)[:19]}|{reason}"
        rec = {
            "blocked_join_key": blocked_join_key,
            "timestamp_utc": ts,
            "symbol": sym,
            "blocked_reason": reason,
            "direction": direction,
            "score": score,
            "snapshot_linked": snapshot is not None,
            "snapshot_timestamp_utc": snapshot.get("timestamp_utc") if snapshot else None,
            "components_present": comp_present,
            "components_defaulted": comp_defaulted,
            "components_missing": comp_missing,
            "regime_label": regime_label,
            "notes": [],
        }
        if not snapshot:
            rec["notes"].append("no_entry_decision_snapshot_within_window")
        rec["notes"].append(f"block_reason:{reason}")
        records.append(rec)
    return records


def write_blocked_snapshots(
    base_dir: Path,
    records: List[Dict[str, Any]],
    log_path: Optional[Path] = None,
) -> int:
    """Append records to logs/blocked_trade_snapshots.jsonl. Returns count written."""
    path = (base_dir / (log_path or Path("logs/blocked_trade_snapshots.jsonl"))).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    for rec in records:
        line = json.dumps(rec, default=str) + "\n"
        try:
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            try:
                os.write(fd, line.encode("utf-8"))
                written += 1
            finally:
                os.close(fd)
        except Exception:
            pass
    return written
