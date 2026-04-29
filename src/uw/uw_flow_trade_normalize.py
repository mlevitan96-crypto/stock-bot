"""
Normalize Unusual Whales WebSocket ``flow-alerts`` payloads into the same per-trade
shape produced by ``GET /api/option-trades/flow-alerts`` so that:

- ``uw_flow_daemon._normalize_flow_data`` (premium / CALL|PUT rollups)
- ``uw_composite_v2`` sweep / premium helpers on ``flow_trades`` items

see a consistent schema. Without this, WS rows can omit ``type``/sweep flags the
composite expects, silently weakening flow features.
"""

from __future__ import annotations

import re
from typing import Any, Dict


def _to_float(v: Any) -> float:
    try:
        if v is None:
            return 0.0
        if isinstance(v, bool):
            return float(v)
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace(",", "")
        return float(s) if s else 0.0
    except (TypeError, ValueError):
        return 0.0


def _call_put_from_option_chain(chain: Any) -> str:
    """
    UW chains look like ``DIA241018C00415000`` (underlying + YYMMDD + C|P + strike).
    Returns ``CALL``, ``PUT``, or ``""`` if unknown.
    """
    if not isinstance(chain, str) or len(chain) < 8:
        return ""
    m = re.search(r"(\d{6})([CP])(\d)", chain.upper())
    if not m:
        return ""
    return "CALL" if m.group(2) == "C" else "PUT"


def normalize_ws_flow_alert_to_rest_trade(underlying: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a single WS ``flow-alerts`` object into a REST-style trade dict.

    Preserves unknown keys (shallow copy) then overwrites canonical fields so
    downstream code always sees ``premium`` / ``total_premium`` / ``type`` / timestamps.
    """
    out: Dict[str, Any] = dict(payload) if isinstance(payload, dict) else {}
    sym = str(underlying or "").strip().upper()
    if sym:
        out["symbol"] = sym
        out["ticker"] = sym

    prem = _to_float(
        out.get("total_premium")
        or out.get("premium")
        or out.get("totalPremium")
        or out.get("total_ask_side_prem")
        or out.get("total_bid_side_prem")
    )
    out["total_premium"] = prem
    out["premium"] = prem

    typ = str(out.get("type") or out.get("call_put") or out.get("option_type") or "").strip().upper()
    if typ in ("C", "CALL"):
        out["type"] = "CALL"
    elif typ in ("P", "PUT"):
        out["type"] = "PUT"
    else:
        oc = out.get("option_chain") or out.get("optionChain") or ""
        derived = _call_put_from_option_chain(oc)
        if derived:
            out["type"] = derived

    if out.get("has_sweep") is True:
        out["is_sweep"] = True
        out["sweep"] = True

    # Epoch ms from WS examples (`executed_at`, `start_time`, `end_time`)
    ts_ms = out.get("executed_at") or out.get("end_time") or out.get("start_time")
    if isinstance(ts_ms, (int, float)) and ts_ms > 1_000_000_000_000:
        out["timestamp"] = int(ts_ms // 1000)
    elif isinstance(ts_ms, (int, float)) and ts_ms > 1_000_000_000:
        out["timestamp"] = int(ts_ms)

    out["_ingest_source"] = "uw_ws_flow_alerts"
    return out
