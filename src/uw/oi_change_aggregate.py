"""
Aggregate UW `/api/stock/{ticker}/oi-change` list payloads into ticker-level fields.

The official API returns `data` as a list of per-contract rows (see unusual_whales_api/api_spec.yaml).
Downstream ML and composite expect `net_oi_change`, `call_oi_change`, `put_oi_change`.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# OCC-style option symbol: ...YYMMDD[C|P]strike...
_OCC_CP = re.compile(r"(\d{6})([CP])(\d)")


def _side_from_option_symbol(option_symbol: str) -> Optional[str]:
    """Return 'C' or 'P' from OCC option ticker, or None."""
    if not option_symbol or not isinstance(option_symbol, str):
        return None
    m = _OCC_CP.search(option_symbol.upper())
    if not m:
        return None
    return m.group(2)


def aggregate_uw_stock_oi_change_list(rows: Any) -> Dict[str, Any]:
    """
    Sum OI deltas across all contracts; split call vs put using option_symbol when possible.
    """
    if not isinstance(rows, list) or not rows:
        return {}

    call_sum = 0
    put_sum = 0
    net_sum = 0
    used = 0

    for row in rows:
        if not isinstance(row, dict):
            continue
        diff = row.get("oi_diff_plain")
        if diff is None:
            try:
                co = int(row.get("curr_oi") or 0)
                lo = int(row.get("last_oi") or 0)
                diff = co - lo
            except (TypeError, ValueError):
                diff = 0
        try:
            d = int(diff or 0)
        except (TypeError, ValueError):
            d = 0
        net_sum += d
        used += 1
        side = _side_from_option_symbol(str(row.get("option_symbol") or ""))
        if side == "C":
            call_sum += d
        elif side == "P":
            put_sum += d

    out: Dict[str, Any] = {
        "net_oi_change": float(net_sum),
        "call_oi_change": float(call_sum),
        "put_oi_change": float(put_sum),
        "aggregated_contracts": int(used),
        "aggregation": "uw_stock_oi_change_list_v1",
    }
    return out
