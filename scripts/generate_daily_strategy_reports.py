#!/usr/bin/env python3
"""
Generate daily strategy reports: equity, wheel, combined.

Outputs:
- reports/YYYY-MM-DD_stock-bot_equity.json
- reports/YYYY-MM-DD_stock-bot_wheel.json
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
from typing import Any, Dict, List, Optional

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


def _compute_equity_report(day: str, all_attr: List[dict], positions: List[dict], equity_positions: List[dict]) -> dict:
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


def _compute_wheel_report(day: str, all_telemetry: List[dict], all_attr: List[dict], wheel_positions: List[dict]) -> dict:
    wheel_telem = _filter_by_strategy(all_telemetry, "wheel")
    wheel_attr = _filter_by_strategy(all_attr, "wheel")
    premium_collected = sum(float(r.get("premium") or 0) for r in wheel_telem + wheel_attr)
    positions_by_symbol = {}
    capital_at_risk = 0.0
    unrealized = 0.0
    for p in wheel_positions:
        sym = p.get("symbol", "")
        if not sym:
            continue
        qty = int(float(p.get("qty") or 0))
        mv = float(p.get("market_value") or 0)
        cost = float(p.get("cost_basis") or 0)
        positions_by_symbol[sym] = {"qty": qty, "market_value": mv, "cost_basis": cost}
        capital_at_risk += mv
        unrealized += mv - cost if cost else 0
    wheel_state = _load_json(ROOT / "state" / "wheel_state.json", {})
    open_csps = wheel_state.get("open_csps", {})
    for sym, lst in (open_csps or {}).items():
        for csp in lst if isinstance(lst, list) else [lst]:
            strike = float(csp.get("strike", 0))
            capital_at_risk += strike * 100
    realized = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in wheel_attr)

    # Count assignments and call-aways from telemetry for this day
    assignment_count = sum(1 for r in wheel_telem if r.get("assigned") is True)
    call_away_count = sum(1 for r in wheel_telem if r.get("called_away") is True)

    # Also check wheel_state csp_history/cc_history for assignments/callaways if not in daily telemetry
    csp_history = wheel_state.get("csp_history", []) or []
    cc_history = wheel_state.get("cc_history", []) or []
    for h in csp_history:
        if isinstance(h, dict) and h.get("assigned") and _day_utc(str(h.get("assigned_at") or h.get("ts") or "")) == day:
            assignment_count += 1
    for h in cc_history:
        if isinstance(h, dict) and h.get("called_away") and _day_utc(str(h.get("called_away_at") or h.get("ts") or "")) == day:
            call_away_count += 1

    yield_per_period = (premium_collected / capital_at_risk) if capital_at_risk > 0 else None

    return {
        "strategy_id": "wheel",
        "date": day,
        "realized_pnl": round(realized, 2),
        "unrealized_pnl": round(unrealized, 2),
        "premium_collected": round(premium_collected, 2),
        "capital_at_risk": round(capital_at_risk, 2),
        "assignment_count": assignment_count,
        "call_away_count": call_away_count,
        "yield_per_period": round(yield_per_period, 6) if yield_per_period is not None else None,
        "max_drawdown": None,
        "positions_by_symbol": positions_by_symbol,
        "exposure_by_sector": None,
        "iv_proxy": None,
        "earnings_proximity_flag": None,
    }


def _load_historical_pnl_series(reports_dir: Path, day: str, days_back: int) -> tuple:
    """Load equity and wheel realized PnL series for the last N days (chronological order)."""
    eq_series: List[float] = []
    wh_series: List[float] = []
    try:
        from datetime import timedelta
        d = datetime.strptime(day[:10], "%Y-%m-%d").date()
        for i in range(days_back - 1, -1, -1):
            dk = (d - timedelta(days=i)).strftime("%Y-%m-%d")
            eq_path = reports_dir / f"{dk}_stock-bot_equity.json"
            wh_path = reports_dir / f"{dk}_stock-bot_wheel.json"
            if eq_path.exists():
                eq = _load_json(eq_path, {})
                eq_series.append(float(eq.get("realized_pnl") or 0))
            if wh_path.exists():
                wh = _load_json(wh_path, {})
                wh_series.append(float(wh.get("realized_pnl") or 0))
    except Exception:
        pass
    return (eq_series if eq_series else None, wh_series if wh_series else None)


def _compute_combined_report(
    day: str,
    equity_report: dict,
    wheel_report: dict,
    account_equity: float,
    buying_power: float,
    reports_dir: Optional[Path] = None,
) -> dict:
    total_realized = (equity_report.get("realized_pnl") or 0) + (wheel_report.get("realized_pnl") or 0)
    total_unrealized = (equity_report.get("unrealized_pnl") or 0) + (wheel_report.get("unrealized_pnl") or 0)
    eq_pnl = (equity_report.get("realized_pnl") or 0) + (equity_report.get("unrealized_pnl") or 0)
    wh_pnl = (wheel_report.get("realized_pnl") or 0) + (wheel_report.get("unrealized_pnl") or 0)
    equity_cap = 0.0
    wheel_cap = 0.0
    for sym, p in (equity_report.get("positions_by_symbol") or {}).items():
        equity_cap += float(p.get("market_value") or 0)
    for sym, p in (wheel_report.get("positions_by_symbol") or {}).items():
        wheel_cap += float(p.get("market_value") or 0)
    wheel_cap += wheel_report.get("capital_at_risk") or 0
    total_cap = equity_cap + wheel_cap
    eq_frac = equity_cap / total_cap if total_cap > 0 else 0
    wh_frac = wheel_cap / total_cap if total_cap > 0 else 0

    out = {
        "date": day,
        "total_realized_pnl": round(total_realized, 2),
        "total_unrealized_pnl": round(total_unrealized, 2),
        "equity_strategy_pnl": round(eq_pnl, 2),
        "wheel_strategy_pnl": round(wh_pnl, 2),
        "capital_allocation": {"equity": round(eq_frac, 4), "wheel": round(wh_frac, 4)},
        "account_equity": round(account_equity, 2),
        "buying_power": round(buying_power, 2),
    }

    try:
        from strategies.strategy_comparison import compare_strategies, get_promotion_recommendation
        eq_series, wh_series = _load_historical_pnl_series(reports_dir or ROOT / "reports", day, 30)
        comparison = compare_strategies(equity_report, wheel_report, out, eq_series, wh_series)
        prom_cfg = {}
        try:
            import yaml
            cfg_path = ROOT / "config" / "strategies.yaml"
            if cfg_path.exists():
                cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
                prom_cfg = cfg.get("promotion", {}) or {}
        except Exception:
            pass
        rec = get_promotion_recommendation(comparison, prom_cfg)
        out["strategy_comparison"] = {**comparison, "recommendation": rec["recommendation"], "reasons": rec.get("reasons", [])}
    except Exception:
        out["strategy_comparison"] = {}

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    args = ap.parse_args()
    day = args.date.strip() or datetime.now(timezone.utc).date().isoformat()

    logs_dir = ROOT / "logs"
    state_dir = ROOT / "state"
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    all_attr = [r for r in _iter_jsonl(logs_dir / "attribution.jsonl") if _day_utc(str(r.get("ts") or r.get("timestamp") or "")) == day]
    all_telemetry = [r for r in _iter_jsonl(logs_dir / "telemetry.jsonl") if _day_utc(str(r.get("_dt") or r.get("ts") or r.get("timestamp") or "")) == day]
    equity_positions = []
    wheel_positions = []
    account_equity = 0.0
    buying_power = 0.0
    pos_meta = {}
    try:
        from config.registry import StateFiles, read_json
        pos_meta = read_json(getattr(StateFiles, "POSITION_METADATA", state_dir / "position_metadata.json"), default={}) or {}
    except Exception:
        pass
    wheel_state = _load_json(state_dir / "wheel_state.json", {})
    assigned = set((wheel_state.get("assigned_shares") or {}).keys())
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
                ac = str(getattr(p, "asset_class", "") or "").lower()
                if ac == "option":
                    wheel_positions.append({"symbol": sym, "qty": qty, "market_value": mv, "cost_basis": cb})
                elif sym in assigned:
                    wheel_positions.append({"symbol": sym, "qty": qty, "market_value": mv, "cost_basis": cb})
                else:
                    equity_positions.append({"symbol": sym, "qty": qty, "market_value": mv, "cost_basis": cb})
    except Exception:
        pass
    if not equity_positions and pos_meta:
        for sym, meta in pos_meta.items():
            if isinstance(meta, dict):
                qty = meta.get("qty", 0)
                entry = meta.get("entry_price", 0)
                equity_positions.append({"symbol": sym, "qty": qty, "market_value": 0, "cost_basis": entry * qty if entry else 0})

    equity_report = _compute_equity_report(day, all_attr, [], equity_positions)
    wheel_report = _compute_wheel_report(day, all_telemetry, all_attr, wheel_positions)
    combined_report = _compute_combined_report(day, equity_report, wheel_report, account_equity, buying_power, reports_dir)

    out_equity = reports_dir / f"{day}_stock-bot_equity.json"
    out_wheel = reports_dir / f"{day}_stock-bot_wheel.json"
    out_combined = reports_dir / f"{day}_stock-bot_combined.json"

    out_equity.write_text(json.dumps(equity_report, indent=2, default=str), encoding="utf-8")
    out_wheel.write_text(json.dumps(wheel_report, indent=2, default=str), encoding="utf-8")
    out_combined.write_text(json.dumps(combined_report, indent=2, default=str), encoding="utf-8")

    sc = combined_report.get("strategy_comparison") or {}
    if sc:
        try:
            from config.registry import LogFiles, append_jsonl
            telem_rec = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "run_date": day,
                "event": "strategy_comparison_snapshot",
                "strategy_comparison_snapshot": sc,
                "wheel_yield_per_period": sc.get("wheel_yield_per_period"),
                "wheel_assignment_health_score": sc.get("assignment_health"),
                "wheel_callaway_health_score": sc.get("assignment_health"),
                "equity_sharpe_proxy": sc.get("equity_sharpe_proxy"),
                "wheel_sharpe_proxy": sc.get("wheel_sharpe_proxy"),
            }
            append_jsonl(LogFiles.TELEMETRY, telem_rec)
        except Exception:
            pass

    print(f"Wrote {out_equity}")
    print(f"Wrote {out_wheel}")
    print(f"Wrote {out_combined}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
