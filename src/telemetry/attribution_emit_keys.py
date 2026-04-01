"""
Append-only attribution join keys and economics placeholders (Alpaca).
Canonical import path: ``src.telemetry.attribution_emit_keys`` (droplet-safe).
Thread-safe enough for single-trading-thread; no strategy logic.
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_lock = threading.Lock()
_by_symbol: Dict[str, Dict[str, Any]] = {}

# Documented rule for deterministic joins (offline replay).
ATTRIBUTION_TIME_BUCKET_SECONDS = 300


def time_bucket_id_utc(when: Optional[datetime] = None) -> str:
    """
    Floor UTC unix time to ATTRIBUTION_TIME_BUCKET_SECONDS.
    ID format: "{seconds}s|{epoch_floor}" (UTC).
    """
    dt = when or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    epoch = int(dt.timestamp())
    flo = epoch - (epoch % ATTRIBUTION_TIME_BUCKET_SECONDS)
    return f"{ATTRIBUTION_TIME_BUCKET_SECONDS}s|{flo}"


def new_decision_event_id() -> str:
    return str(uuid.uuid4())


def _norm_sym(symbol: Any) -> str:
    return str(symbol or "").strip().upper()


def set_symbol_attribution_keys(symbol: Any, **kwargs: Any) -> None:
    sym = _norm_sym(symbol)
    if not sym:
        return
    with _lock:
        cur = dict(_by_symbol.get(sym, {}))
        for k, v in kwargs.items():
            if v is not None:
                cur[k] = v
        _by_symbol[sym] = cur


def get_symbol_attribution_keys(symbol: Any) -> Dict[str, Any]:
    sym = _norm_sym(symbol)
    if not sym:
        return {}
    with _lock:
        return dict(_by_symbol.get(sym, {}))


def clear_symbol_attribution_keys(symbol: Any) -> None:
    sym = _norm_sym(symbol)
    if not sym:
        return
    with _lock:
        _by_symbol.pop(sym, None)


def merge_attribution_keys_into_record(
    symbol: Any,
    rec: Dict[str, Any],
    *,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Merge canonical join keys from per-symbol store into record (additive unless overwrite)."""
    extra = get_symbol_attribution_keys(symbol)
    if not extra:
        return rec
    for k in (
        "canonical_trade_id",
        "decision_event_id",
        "symbol_normalized",
        "time_bucket_id",
    ):
        if k not in extra:
            continue
        if not overwrite and rec.get(k) is not None:
            continue
        rec[k] = extra[k]
    return rec


def uw_cache_probe() -> Dict[str, Any]:
    """Best-effort UW cache mtime for provenance (no API calls)."""
    out: Dict[str, Any] = {
        "uw_ingest_ts": None,
        "uw_staleness_seconds": None,
        "uw_missing_reason": None,
    }
    try:
        from config.registry import CacheFiles

        p = CacheFiles.UW_FLOW_CACHE
        if isinstance(p, Path) and p.exists():
            m = p.stat().st_mtime
            out["uw_ingest_ts"] = datetime.fromtimestamp(m, tz=timezone.utc).isoformat()
            out["uw_staleness_seconds"] = max(0.0, time.time() - m)
        else:
            out["uw_missing_reason"] = "uw_flow_cache_missing"
    except Exception:
        out["uw_missing_reason"] = "uw_cache_probe_error"
    return out


def slippage_bps_vs_mid(
    ref_mid: Optional[float],
    fill_price: Optional[float],
    side: Optional[str],
) -> tuple[Optional[float], Optional[str]]:
    """
    Slippage vs decision-time mid. side: buy/sell (Alpaca order side).
    buy: (fill - mid) / mid * 1e4; sell: (mid - fill) / mid * 1e4
    """
    try:
        m = float(ref_mid)
        f = float(fill_price)
        if m <= 0 or f <= 0:
            return None, None
    except (TypeError, ValueError):
        return None, None
    s = str(side or "").lower()
    if s == "buy":
        bps = (f - m) / m * 10000.0
    elif s == "sell":
        bps = (m - f) / m * 10000.0
    else:
        return None, None
    return round(bps, 4), "decision_time_mid"


def attach_paper_economics_defaults(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Additive economics schema for orders.jsonl.
    Fees: explicit exclusion on paper until Alpaca exposes per-fill fees on this surface.
    """
    e = dict(event)
    if "fee_excluded_reason" not in e and "fee_amount" not in e:
        e.setdefault("fee_excluded_reason", "ALPACA_PAPER_FILL_PAYLOAD_MISSING_FEE_FIELDS")
    e.setdefault("fee_amount", e.get("fee_amount"))
    e.setdefault("fee_currency", e.get("fee_currency"))
    # Slippage: fill when we have ref mid from attribution store
    sym = e.get("symbol")
    keys = get_symbol_attribution_keys(sym) if sym else {}
    ref_mid = keys.get("decision_slippage_ref_mid")
    fill_px = e.get("filled_avg_price")
    if fill_px is None:
        fill_px = e.get("filled_price")
    if fill_px is None:
        fill_px = e.get("price")
    side = e.get("side")
    bps, ref_type = slippage_bps_vs_mid(
        float(ref_mid) if ref_mid is not None else None,
        float(fill_px) if fill_px is not None else None,
        str(side) if side else None,
    )
    if bps is not None:
        e.setdefault("slippage_bps", bps)
        e.setdefault("slippage_ref_price_type", ref_type)
    else:
        e.setdefault("slippage_excluded_reason", e.get("slippage_excluded_reason") or "no_decision_mid_or_fill_price")
    e.setdefault("filled_at", e.get("filled_at") or e.get("ts"))
    e.setdefault("fill_qty", e.get("fill_qty", e.get("filled_qty", e.get("qty"))))
    e.setdefault("fill_price", e.get("fill_price", fill_px))
    return e
