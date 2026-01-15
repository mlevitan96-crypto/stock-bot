#!/usr/bin/env python3
"""
PnL Reconciler (Institutional Remediation Phase 1)

Purpose:
- Perform a daily reconciliation between Alpaca broker "day PnL" (equity_now - last_equity)
  and internal attribution logs (logs/attribution.jsonl), and log the unreconciled gap.

Constraints:
- Does NOT modify core wallet computation logic.
- Purely observational: reads Alpaca account + attribution log, writes structured audit log.

Output:
- Appends to logs/pnl_reconciliation.jsonl via config.registry.append_jsonl(LogFiles.PNL_RECONCILIATION).
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import alpaca_trade_api as tradeapi

from config.registry import LogFiles, append_jsonl


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _load_attribution_sums(date_str: str) -> Dict[str, Any]:
    """
    Compute attribution sums for the provided date.
    - closed_pnl_sum_logged: sum(pnl_usd) for attribution records that look like closes/scales
    - all_pnl_sum_logged: sum(pnl_usd) for all attribution records that day (opens should be 0 anyway)
    """
    path = LogFiles.ATTRIBUTION
    closed_pnl_sum = 0.0
    all_pnl_sum = 0.0
    records = 0
    closed_records = 0

    if not path.exists():
        return {
            "attribution_path": str(path),
            "attribution_exists": False,
            "attribution_records_counted": 0,
            "attribution_closed_records_counted": 0,
            "attribution_pnl_sum_all_logged": 0.0,
            "attribution_pnl_sum_closed_logged": 0.0,
        }

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            ts = rec.get("ts") or rec.get("timestamp")
            if not ts or not str(ts).startswith(date_str):
                continue
            records += 1
            pnl = _safe_float(rec.get("pnl_usd"), 0.0)
            all_pnl_sum += pnl
            trade_id = str(rec.get("trade_id") or "")
            kind = trade_id.split("_", 1)[0].lower() if trade_id else ""
            if kind in ("close", "scale"):
                closed_records += 1
                closed_pnl_sum += pnl

    return {
        "attribution_path": str(path),
        "attribution_exists": True,
        "attribution_records_counted": records,
        "attribution_closed_records_counted": closed_records,
        "attribution_pnl_sum_all_logged": round(all_pnl_sum, 2),
        "attribution_pnl_sum_closed_logged": round(closed_pnl_sum, 2),
    }


def reconcile(date_str: Optional[str] = None, api: Optional[Any] = None) -> Dict[str, Any]:
    """
    Run reconciliation and append an audit record.
    """
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Alpaca API
    if api is None:
        key = os.getenv("ALPACA_KEY") or os.getenv("APCA_API_KEY_ID")
        secret = os.getenv("ALPACA_SECRET") or os.getenv("APCA_API_SECRET_KEY")
        base_url = os.getenv("ALPACA_BASE_URL") or os.getenv("APCA_API_BASE_URL")
        if not key or not secret or not base_url:
            raise RuntimeError("Missing Alpaca credentials in environment (ALPACA_KEY/ALPACA_SECRET/ALPACA_BASE_URL).")
        api = tradeapi.REST(key, secret, base_url)

    acct = api.get_account()
    equity_now = _safe_float(getattr(acct, "equity", None), 0.0)
    last_equity = _safe_float(getattr(acct, "last_equity", None), 0.0)
    broker_day_pnl = equity_now - last_equity

    attr = _load_attribution_sums(date_str)
    attribution_closed_pnl = _safe_float(attr.get("attribution_pnl_sum_closed_logged"), 0.0)
    unreconciled_gap = broker_day_pnl - attribution_closed_pnl

    payload: Dict[str, Any] = {
        "ts": _iso_now(),
        "event": "pnl_reconcile",
        "date": date_str,
        "equity_now": round(equity_now, 2),
        "last_equity": round(last_equity, 2),
        "broker_day_pnl": round(broker_day_pnl, 2),
        "attribution_closed_pnl_sum_logged": round(attribution_closed_pnl, 2),
        "unreconciled_gap_usd": round(unreconciled_gap, 2),
        "notes": [
            "broker_day_pnl = equity_now - last_equity (Alpaca broker day).",
            "attribution_closed_pnl_sum_logged = sum(pnl_usd) for close/scale attribution events on date.",
            "unreconciled_gap_usd highlights hidden slippage, fees, or attribution mismatches.",
        ],
        **attr,
    }

    append_jsonl(LogFiles.PNL_RECONCILIATION, payload)
    return payload


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=None, help="YYYY-MM-DD (UTC). Default: today.")
    args = p.parse_args()

    out = reconcile(date_str=args.date)
    # Print a compact one-liner for operators
    print(
        f"{out['date']} broker_day_pnl={out['broker_day_pnl']:.2f} "
        f"attribution_closed_pnl={out['attribution_closed_pnl_sum_logged']:.2f} "
        f"gap={out['unreconciled_gap_usd']:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

