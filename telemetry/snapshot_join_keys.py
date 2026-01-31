"""
Canonical join keys for snapshot↔outcome attribution.
Used across: signal_snapshots*.jsonl, master_trade_log.jsonl,
exit_attribution.jsonl, blocked_trades.jsonl.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _round_ts_bucket(ts: str, bucket_sec: int = 60) -> str:
    """Round timestamp to bucket for join (e.g. 60s)."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        sec = int(dt.timestamp())
        bucketed = (sec // bucket_sec) * bucket_sec
        return datetime.fromtimestamp(bucketed, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return str(ts)[:19] if ts else ""


def build_join_key(
    symbol: str,
    timestamp_utc: Optional[str] = None,
    trade_id: Optional[str] = None,
    side: Optional[str] = None,
    lifecycle_event: Optional[str] = None,
    intent_id: Optional[str] = None,
    bucket_sec: int = 60,
) -> tuple[str, Dict[str, Any]]:
    """
    Build canonical join_key and join_key_fields.
    Prefer deterministic ids (trade_id). Fallback to surrogate.
    """
    symbol = str(symbol or "").upper()
    ts = timestamp_utc or ""
    tid = (trade_id or "").strip()
    side = (side or "long").lower()[:4]
    evt = (lifecycle_event or "ENTRY_DECISION")[:20]
    iid = (intent_id or "").strip()

    fields: Dict[str, Any] = {
        "symbol": symbol,
        "timestamp_utc": ts,
        "trade_id": tid or None,
        "side": side if side else None,
        "lifecycle_event": evt if evt else None,
    }

    if tid and tid.startswith("live:") and ":" in tid:
        join_key = tid
        fields["join_source"] = "trade_id"
        return join_key, fields

    rounded = _round_ts_bucket(ts, bucket_sec)
    if symbol and rounded:
        parts = [symbol, rounded, side, evt]
        if iid:
            parts.append(iid[:32])
        join_key = "|".join(p for p in parts if p)
        fields["join_source"] = "surrogate"
        fields["rounded_ts_bucket"] = rounded
        return join_key, fields

    fallback = f"{symbol}|{ts[:19]}" if symbol and ts else f"unknown|{ts[:19]}" if ts else "unknown"
    fields["join_source"] = "fallback"
    return fallback, fields


def extract_join_key_from_snapshot(rec: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Extract join_key from a snapshot record."""
    return build_join_key(
        symbol=rec.get("symbol"),
        timestamp_utc=rec.get("timestamp_utc"),
        trade_id=rec.get("trade_id"),
        side=None,
        lifecycle_event=rec.get("lifecycle_event"),
    )


def extract_join_key_from_master_trade(rec: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Extract join_key from master_trade_log record."""
    entry_ts = rec.get("entry_ts") or rec.get("timestamp")
    side = "long" if str(rec.get("side", "long")).lower() in ("long", "buy") else "short"
    return build_join_key(
        symbol=rec.get("symbol"),
        timestamp_utc=entry_ts,
        trade_id=rec.get("trade_id"),
        side=side,
        lifecycle_event="ENTRY_DECISION" if not rec.get("exit_ts") else "EXIT_DECISION",
    )


def extract_join_key_from_exit_attribution(rec: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Extract join_key from exit_attribution record."""
    return build_join_key(
        symbol=rec.get("symbol"),
        timestamp_utc=rec.get("timestamp") or rec.get("exit_timestamp"),
        trade_id=None,
        side=None,
        lifecycle_event="EXIT_DECISION",
    )
