#!/usr/bin/env python3
"""
Generate daily strategy reports: equity + combined (equity-only).

Outputs:
- reports/YYYY-MM-DD_stock-bot_equity.json
- reports/YYYY-MM-DD_stock-bot_combined.json

Run from repo root: python scripts/generate_daily_strategy_reports.py [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else datetime.now(timezone.utc).date().isoformat()


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
            if isinstance(rec, dict):
                yield rec
        except Exception:
            continue


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return default if default is not None else {}


def _filter_by_strategy(records: List[dict], strategy_id: str) -> List[dict]:
    return [r for r in records if (r.get("strategy_id") or "equity") == strategy_id]


def _compute_equity_report(day: str, all_attr: List[dict], equity_positions: List[dict]) -> dict:
    eq_attr = _filter_by_strategy(all_attr, "equity")
    realized = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in eq_attr)
    positions_by_symbol = {}
    unrealized = 0.0
    for p in equity_positions:
        sym = p.get("symbol", "")
        if not sym:
            continue
        qty = int(float(p.get("qty") or 0))
        mv = float(p.get("market_value") or 0)
        cost = float(p.get("cost_basis") or 0)
        positions_by_symbol[sym] = {"qty": qty, "market_value": mv, "cost_basis": cost}
        unrealized += mv - cost if cost else 0
    return {
        "strategy_id": "equity",
        "date": day,
        "realized_pnl": round(realized, 2),
        "unrealized_pnl": round(unrealized, 2),
        "max_drawdown": None,
        "positions_by_symbol": positions_by_symbol,
        "exposure_by_sector": None,
    }


def _compute_combined_report(
    day: str,
    equity_report: dict,
    account_equity: float,
    buying_power: float,
) -> dict:
    eq_pnl = (equity_report.get("realized_pnl") or 0) + (equity_report.get("unrealized_pnl") or 0)
    equity_cap = 0.0
    for _, p in (equity_report.get("positions_by_symbol") or {}).items():
        equity_cap += float(p.get("market_value") or 0)

    return {
        "date": day,
        "total_realized_pnl": round(equity_report.get("realized_pnl") or 0, 2),
        "total_unrealized_pnl": round(equity_report.get("unrealized_pnl") or 0, 2),
        "equity_strategy_pnl": round(eq_pnl, 2),
        "capital_allocation": {"equity": 1.0},
        "account_equity": round(account_equity, 2),
        "buying_power": round(buying_power, 2),
        "strategy_comparison": {},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    args = ap.parse_args()
    day = args.date.strip() or datetime.now(timezone.utc).date().isoformat()

    logs_dir = ROOT / "logs"
    state_dir = ROOT / "state"
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    all_attr = [
        r
        for r in _iter_jsonl(logs_dir / "attribution.jsonl")
        if _day_utc(str(r.get("ts") or r.get("timestamp") or "")) == day
    ]
    equity_positions: List[dict] = []
    account_equity = 0.0
    buying_power = 0.0
    pos_meta = {}
    try:
        from config.registry import StateFiles, read_json

        pos_meta = read_json(getattr(StateFiles, "POSITION_METADATA", state_dir / "position_metadata.json"), default={}) or {}
    except Exception:
        pass
    try:
        import alpaca_trade_api as tradeapi

        key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY", "")
        secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET", "")
        base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        if key and secret:
            api = tradeapi.REST(key, secret, base)
            acct = api.get_account()
            account_equity = float(getattr(acct, "equity", 0) or 0)
            buying_power = float(getattr(acct, "buying_power", 0) or 0)
            alpaca_pos = api.list_positions() or []
            for p in alpaca_pos:
                sym = getattr(p, "symbol", "")
                mv = float(getattr(p, "market_value", 0) or 0)
                cb = float(getattr(p, "cost_basis", 0) or 0)
                qty = int(float(getattr(p, "qty", 0) or 0))
                equity_positions.append({"symbol": sym, "qty": qty, "market_value": mv, "cost_basis": cb})
    except Exception:
        pass
    if not equity_positions and pos_meta:
        for sym, meta in pos_meta.items():
            if isinstance(meta, dict):
                qty = meta.get("qty", 0)
                entry = meta.get("entry_price", 0)
                equity_positions.append({"symbol": sym, "qty": qty, "market_value": 0, "cost_basis": entry * qty if entry else 0})

    equity_report = _compute_equity_report(day, all_attr, equity_positions)
    combined_report = _compute_combined_report(day, equity_report, account_equity, buying_power)

    out_equity = reports_dir / f"{day}_stock-bot_equity.json"
    out_combined = reports_dir / f"{day}_stock-bot_combined.json"

    out_equity.write_text(json.dumps(equity_report, indent=2, default=str), encoding="utf-8")
    out_combined.write_text(json.dumps(combined_report, indent=2, default=str), encoding="utf-8")

    print(f"Wrote {out_equity}")
    print(f"Wrote {out_combined}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
