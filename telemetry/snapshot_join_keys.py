"""
Canonical join keys for snapshot↔outcome attribution.
Used across: signal_snapshots*.jsonl, master_trade_log.jsonl,
exit_attribution.jsonl, blocked_trades.jsonl.

Gold standard trade identifier: ``build_trade_key`` from ``src.telemetry.alpaca_trade_key``
(symbol|LONG|SHORT|UTC_epoch_seconds). Legacy ``open_*``, ``live:SYMBOL:iso``, rounded
buckets, and bare ``position_id`` remain only as **deprecated fallbacks** when the
canonical key cannot be derived — do not add new writers that rely on them.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side


def _looks_like_canonical_trade_key(s: str) -> bool:
    parts = s.split("|")
    if len(parts) < 3:
        return False
    try:
        int(parts[-1])
    except ValueError:
        return False
    return True


def _round_ts_bucket(ts: str, bucket_sec: int = 60) -> str:
    """Round timestamp to bucket for join (e.g. 60s). **Deprecated** for primary joins."""
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
    *,
    trade_key: Optional[str] = None,
    canonical_trade_id: Optional[str] = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Build join_key for ENTRY-side snapshots.

    Precedence:
      1) Explicit ``trade_key`` / ``canonical_trade_id`` when they match the canonical pattern.
      2) **Deprecated:** ``live:``-prefixed ``trade_id`` (legacy Alpaca snapshot contract).
      3) **Deprecated:** surrogate bucket on ``timestamp_utc``.
    """
    symbol = str(symbol or "").upper()
    ts = timestamp_utc or ""
    tid = (trade_id or "").strip()
    side_n = (side or "long").lower()[:4]
    evt = (lifecycle_event or "ENTRY_DECISION")[:20]
    iid = (intent_id or "").strip()

    fields: Dict[str, Any] = {
        "symbol": symbol,
        "timestamp_utc": ts,
        "trade_id": tid or None,
        "side": side_n if side_n else None,
        "lifecycle_event": evt if evt else None,
    }

    for label, raw in (("trade_key", trade_key), ("canonical_trade_id", canonical_trade_id)):
        if raw and _looks_like_canonical_trade_key(str(raw).strip()):
            c = str(raw).strip()
            fields["join_source"] = "canonical_trade_key"
            fields[label] = c
            fields["trade_key"] = c
            return c, fields

    # DEPRECATED: live:SYMBOL:entry_ts — prefer emit/store trade_key from alpaca_trade_key instead.
    if tid and tid.startswith("live:") and ":" in tid:
        join_key = tid
        fields["join_source"] = "trade_id_live_prefix_deprecated"
        return join_key, fields

    rounded = _round_ts_bucket(ts, bucket_sec)
    if symbol and rounded:
        parts = [symbol, rounded, side_n, evt]
        if iid:
            parts.append(iid[:32])
        join_key = "|".join(p for p in parts if p)
        fields["join_source"] = "surrogate_ts_bucket_deprecated"
        fields["rounded_ts_bucket"] = rounded
        return join_key, fields

    fallback = f"{symbol}|{ts[:19]}" if symbol and ts else f"unknown|{ts[:19]}" if ts else "unknown"
    fields["join_source"] = "fallback_deprecated"
    return fallback, fields


def extract_join_key_from_snapshot(rec: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Extract join_key from a snapshot record."""
    return build_join_key(
        symbol=rec.get("symbol"),
        timestamp_utc=rec.get("timestamp_utc"),
        trade_id=rec.get("trade_id"),
        side=None,
        lifecycle_event=rec.get("lifecycle_event"),
        trade_key=rec.get("trade_key"),
        canonical_trade_id=rec.get("canonical_trade_id"),
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
        trade_key=rec.get("trade_key"),
        canonical_trade_id=rec.get("canonical_trade_id"),
    )


def extract_join_key_from_exit_attribution(rec: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Extract join_key from exit_attribution record."""
    return build_join_key(
        symbol=rec.get("symbol"),
        timestamp_utc=rec.get("timestamp") or rec.get("exit_timestamp"),
        trade_id=rec.get("trade_id"),
        side=None,
        lifecycle_event="EXIT_DECISION",
        trade_key=rec.get("trade_key"),
        canonical_trade_id=rec.get("canonical_trade_id"),
    )


# -----------------------------------------------------------------------------
# EXIT_JOIN_KEY precedence (gold standard first):
#   a) trade_key / canonical_trade_id (symbol|LONG|SHORT|epoch) when present or buildable
#   b) **Deprecated:** position_id (broker scope; not stable across replays)
#   c) **Deprecated:** trade_id with ``live:`` prefix
#   d) **Deprecated:** surrogate rounded bucket + intent_id
# -----------------------------------------------------------------------------

EXIT_LIFECYCLE = frozenset({"EXIT_DECISION", "EXIT_FILL"})


def build_exit_join_key(
    symbol: str,
    entry_timestamp_utc: Optional[str] = None,
    exit_timestamp_utc: Optional[str] = None,
    position_id: Optional[str] = None,
    trade_id: Optional[str] = None,
    side: Optional[str] = None,
    intent_id: Optional[str] = None,
    bucket_sec: int = 60,
    *,
    trade_key: Optional[str] = None,
    canonical_trade_id: Optional[str] = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Build deterministic exit_join_key aligned to ``build_trade_key`` when possible.

    Legacy fallbacks (position_id, ``live:`` ids, time buckets) exist only for older rows;
    new instrumentation should always populate ``trade_key`` / ``canonical_trade_id`` on exit.
    """
    symbol = str(symbol or "").upper()
    pos_id = (position_id or "").strip()
    tid = (trade_id or "").strip()
    entry_ts = (entry_timestamp_utc or "").strip()
    exit_ts = (exit_timestamp_utc or "").strip()
    side_raw = side or "long"
    iid = (intent_id or "").strip()[:32]

    fields: Dict[str, Any] = {
        "symbol": symbol,
        "entry_timestamp_utc": entry_ts or None,
        "exit_timestamp_utc": exit_ts or None,
        "position_id": pos_id or None,
        "trade_id": tid or None,
        "side": (side_raw or "long").lower()[:4] if side_raw else None,
    }

    for label, raw in (("trade_key", trade_key), ("canonical_trade_id", canonical_trade_id)):
        if raw and _looks_like_canonical_trade_key(str(raw).strip()):
            c = str(raw).strip()
            fields["join_source"] = "canonical_trade_key"
            fields[label] = c
            fields["trade_key"] = c
            return c, fields

    if symbol and entry_ts:
        try:
            c = build_trade_key(symbol, normalize_side(side_raw), entry_ts)
            fields["join_source"] = "canonical_trade_key_built"
            fields["trade_key"] = c
            return c, fields
        except Exception:
            pass

    # DEPRECATED: Alpaca position UUID — useful for same-day broker joins, not replay-stable.
    if pos_id:
        fields["join_source"] = "position_id_deprecated"
        return pos_id, fields

    # DEPRECATED: live:SYMBOL:iso — superseded by build_trade_key / explicit trade_key on rows.
    if tid and tid.startswith("live:") and ":" in tid:
        fields["join_source"] = "trade_id_live_prefix_deprecated"
        return tid, fields

    rounded = _round_ts_bucket(entry_ts or exit_ts, bucket_sec)
    if symbol and rounded:
        parts = [symbol, rounded, (side_raw or "long").lower()[:4], "EXIT"]
        if iid:
            parts.append(iid)
        join_key = "|".join(p for p in parts if p)
        fields["join_source"] = "surrogate_ts_bucket_deprecated"
        fields["rounded_ts_bucket"] = rounded
        return join_key, fields

    fallback = (
        f"{symbol}|{entry_ts[:19] or exit_ts[:19]}|exit"
        if (symbol and (entry_ts or exit_ts))
        else (f"unknown|{exit_ts[:19]}" if exit_ts else "unknown")
    )
    fields["join_source"] = "fallback_deprecated"
    return fallback, fields


def extract_exit_join_key_from_snapshot(rec: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Extract exit_join_key from a snapshot (EXIT_DECISION or EXIT_FILL)."""
    jf = rec.get("join_key_fields") if isinstance(rec.get("join_key_fields"), dict) else {}
    tk = rec.get("trade_key") or rec.get("canonical_trade_id") or jf.get("trade_key")
    snap_side = jf.get("side") or rec.get("side")
    return build_exit_join_key(
        symbol=rec.get("symbol"),
        entry_timestamp_utc=rec.get("entry_timestamp_utc") or jf.get("entry_timestamp_utc"),
        exit_timestamp_utc=rec.get("timestamp_utc"),
        position_id=rec.get("position_id"),
        trade_id=rec.get("trade_id"),
        side=snap_side,
        trade_key=tk,
        canonical_trade_id=rec.get("canonical_trade_id"),
    )


def extract_exit_join_key_from_master_trade(rec: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Extract exit_join_key from master_trade_log (exited trade)."""
    entry_ts = rec.get("entry_ts") or rec.get("timestamp", "")
    return build_exit_join_key(
        symbol=rec.get("symbol"),
        entry_timestamp_utc=entry_ts,
        exit_timestamp_utc=rec.get("exit_ts"),
        position_id=rec.get("position_id"),
        trade_id=str(rec.get("trade_id") or "").strip() or None,
        side=rec.get("side"),
        trade_key=rec.get("trade_key"),
        canonical_trade_id=rec.get("canonical_trade_id"),
    )


def extract_exit_join_key_from_exit_attribution(rec: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Extract exit_join_key from exit_attribution record (prefer persisted trade_key / canonical)."""
    entry_ts = rec.get("entry_timestamp") or rec.get("entry_ts", "")
    return build_exit_join_key(
        symbol=rec.get("symbol"),
        entry_timestamp_utc=entry_ts,
        exit_timestamp_utc=rec.get("timestamp") or rec.get("exit_timestamp"),
        position_id=rec.get("position_id"),
        trade_id=str(rec.get("trade_id") or "").strip() or None,
        side=rec.get("position_side") or rec.get("side"),
        intent_id=rec.get("intent_id") or rec.get("decision_id"),
        trade_key=rec.get("trade_key"),
        canonical_trade_id=rec.get("canonical_trade_id"),
    )
