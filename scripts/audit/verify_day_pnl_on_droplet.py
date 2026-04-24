#!/usr/bin/env python3
"""
Verify Day P&L calculation on droplet.
Run from repo root on droplet (or via: ssh alpaca 'cd /root/stock-bot && python3 scripts/audit/verify_day_pnl_on_droplet.py').
- Reads state/daily_start_equity.json and Alpaca account.
- Reads logs/attribution.jsonl for today; sums pnl_usd (closed trades).
- Compares dashboard definition (equity change) vs attribution closed P&L sum.
Output: JSON to stdout and optional report path for audit.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    root = REPO
    state_dir = root / "state"
    logs_dir = root / "logs"

    # 1) Session baseline
    daily_start_path = state_dir / "daily_start_equity.json"
    daily_start_equity = None
    daily_start_date = None
    if daily_start_path.exists():
        try:
            data = json.loads(daily_start_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                daily_start_equity = data.get("equity")
                daily_start_date = data.get("date")
                if daily_start_equity is not None:
                    daily_start_equity = float(daily_start_equity)
        except Exception:
            pass

    # 2) Alpaca account (same as dashboard)
    equity_now = None
    last_equity = None
    try:
        from config.registry import Directories
        # Ensure we use repo paths
        if getattr(Directories, "ROOT", None) is None:
            Directories.ROOT = root
        import alpaca_trade_api as tradeapi
        key = os.getenv("ALPACA_KEY") or os.getenv("APCA_API_KEY_ID")
        secret = os.getenv("ALPACA_SECRET") or os.getenv("APCA_API_SECRET_KEY")
        base_url = os.getenv("ALPACA_BASE_URL") or os.getenv("APCA_API_BASE_URL")
        if key and secret and base_url:
            api = tradeapi.REST(key, secret, base_url)
            account = api.get_account()
            equity_now = float(getattr(account, "equity", 0) or 0)
            last_equity = float(getattr(account, "last_equity", 0) or 0)
    except Exception as e:
        equity_now = last_equity = None
        api_error = str(e)
    else:
        api_error = None

    # 3) Dashboard Day P&L (same logic as dashboard.py _api_positions_impl)
    day_pnl_dashboard = None
    if equity_now is not None:
        day_pnl_dashboard = equity_now - (last_equity or 0)
        if daily_start_equity is not None and str(daily_start_date) == today:
            day_pnl_dashboard = equity_now - daily_start_equity

    # 4) Attribution closed P&L for today (exits only)
    attr_path = logs_dir / "attribution.jsonl"
    attribution_closed_sum = 0.0
    attribution_count = 0
    if attr_path.exists():
        try:
            with attr_path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    ts = rec.get("ts") or rec.get("timestamp")
                    if not ts or not str(ts).startswith(today):
                        continue
                    pnl = float(rec.get("pnl_usd", 0) or 0)
                    attribution_closed_sum += pnl
                    attribution_count += 1
        except Exception:
            pass

    # 5) Build result
    result = {
        "date": today,
        "equity_now": round(equity_now, 2) if equity_now is not None else None,
        "last_equity": round(last_equity, 2) if last_equity is not None else None,
        "daily_start_equity": round(daily_start_equity, 2) if daily_start_equity is not None else None,
        "daily_start_date": daily_start_date,
        "day_pnl_dashboard": round(day_pnl_dashboard, 2) if day_pnl_dashboard is not None else None,
        "broker_day_pnl": round(equity_now - last_equity, 2) if (equity_now is not None and last_equity is not None) else None,
        "attribution_closed_pnl_sum": round(attribution_closed_sum, 2),
        "attribution_records_count": attribution_count,
        "api_error": api_error,
        "definition": (
            "Dashboard Day P&L = equity_now - daily_start_equity (when state/daily_start_equity.json exists for today), "
            "else equity_now - last_equity (broker). So it is TOTAL equity change for the day (realized + unrealized), "
            "NOT 'sum of exit P&L only'. Attribution closed sum = sum(pnl_usd) in logs/attribution.jsonl for today (exits)."
        ),
        "gap_dashboard_vs_attribution": (
            round(day_pnl_dashboard - attribution_closed_sum, 2)
            if day_pnl_dashboard is not None else None
        ),
    }
    print(json.dumps(result, indent=2))

    # Write to reports/audit for audit trail
    audit_dir = root / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    out_path = audit_dir / "DAY_PNL_VERIFICATION.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
