"""
Rolling zero-tolerance data-quality tripwire for Alpaca exit attribution (Kraken-style SRE).

Inspects the last N deduped closed trades in logs/exit_attribution.jsonl. If any row lacks
finite PnL (realized_pnl_usd or pnl), or entry_uw is missing finite earnings_proximity or
sentiment_score, the pipeline is considered degraded.

Callers (e.g. scripts/telemetry_milestone_watcher.py) send Telegram with the canonical message.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEGRADATION_TELEGRAM = (
    "🚨 [ALPACA DATA DEGRADATION] UW telemetry or PnL missing in recent stock trades. Pipeline leaking."
)


def _iter_jsonl(path: Path) -> List[dict]:
    if not path.is_file():
        return []
    out: List[dict] = []
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
                out.append(o)
    return out


def _dedupe_last_wins(rows: List[dict]) -> List[dict]:
    """Last row wins per trade_id (same contract as alpaca_ml_flattener)."""
    by_tid: Dict[str, dict] = {}
    order: List[str] = []
    for r in rows:
        tid = str(r.get("trade_id") or "").strip()
        if not tid:
            continue
        if tid not in by_tid:
            order.append(tid)
        by_tid[tid] = r
    return [by_tid[t] for t in order]


def _parse_iso_ts_epoch(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        from datetime import datetime, timezone

        s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (TypeError, ValueError):
        return None


def _exit_epoch(rec: dict) -> float:
    for k in ("exit_ts", "timestamp", "exit_timestamp"):
        t = _parse_iso_ts_epoch(rec.get(k))
        if t is not None:
            return t
    return 0.0


def _finite_scalar(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str) and v.strip().lower() in ("", "null", "none", "nan"):
        return False
    try:
        return math.isfinite(float(v))
    except (TypeError, ValueError):
        return False


def _pnl_ok(rec: dict) -> bool:
    """Either realized_pnl_usd or pnl must be a finite scalar (matches flattener label path)."""
    return _finite_scalar(rec.get("realized_pnl_usd")) or _finite_scalar(rec.get("pnl"))


def _entry_uw_telemetry_ok(rec: dict) -> Tuple[bool, str]:
    eu = rec.get("entry_uw")
    if not isinstance(eu, dict):
        return False, "entry_uw_missing"
    if not _finite_scalar(eu.get("earnings_proximity")):
        return False, "earnings_proximity_missing_or_nonfinite"
    if not _finite_scalar(eu.get("sentiment_score")):
        return False, "sentiment_score_missing_or_nonfinite"
    return True, "ok"


def last_n_closed_trades_by_exit_time(path: Path, n: int = 3) -> List[dict]:
    """Most recent N trades by exit time (after dedupe by trade_id)."""
    raw = _iter_jsonl(path)
    deduped = _dedupe_last_wins(raw)
    deduped.sort(key=_exit_epoch)
    if n <= 0:
        return []
    return deduped[-n:]


def evaluate_last_n_exit_quality(path: Path, n: int = 3) -> Tuple[bool, str]:
    """
    Returns (ok, detail). ok=False means degradation — caller should fire Telegram.

    If fewer than n closed trades exist, returns (True, skip reason) to avoid false alarms
    on empty / greenfield logs.
    """
    trades = last_n_closed_trades_by_exit_time(path, n=n)
    if len(trades) < n:
        return True, f"skip_need_{n}_deduped_closed_found_{len(trades)}"
    for rec in trades:
        tid = str(rec.get("trade_id") or "?")
        if not _pnl_ok(rec):
            return False, f"pnl_missing trade_id={tid}"
        uw_ok, uw_why = _entry_uw_telemetry_ok(rec)
        if not uw_ok:
            return False, f"{uw_why} trade_id={tid}"
    return True, "last_n_ok"


def default_exit_attribution_path(root: Path) -> Path:
    raw = (os.environ.get("EXIT_ATTRIBUTION_LOG_PATH") or "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (root / p)
    return root / "logs" / "exit_attribution.jsonl"
