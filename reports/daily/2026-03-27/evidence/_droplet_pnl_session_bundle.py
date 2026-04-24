#!/usr/bin/env/python3
"""Run on droplet: session PnL + hourly breakdown + strict gates (stdout JSON)."""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path("/root/stock-bot")
sys.path.insert(0, str(REPO))

ET = ZoneInfo("America/New_York")


def _num(x):
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _parse_iso(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def session_bounds_utc(d: date):
    start_et = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=ET)
    end_et = start_et + timedelta(days=1)
    return start_et.astimezone(timezone.utc), end_et.astimezone(timezone.utc)


def main():
    session = date(2026, 3, 27)
    u0, u1 = session_bounds_utc(session)
    close_et = datetime(session.year, session.month, session.day, 16, 0, 0, tzinfo=ET)
    exit_max = close_et.astimezone(timezone.utc).timestamp()

    from telemetry.alpaca_strict_completeness_gate import (
        STRICT_EPOCH_START,
        evaluate_completeness,
        market_open_epoch_today_et,
    )

    open_today = market_open_epoch_today_et()
    gate_dash = evaluate_completeness(REPO, open_ts_epoch=STRICT_EPOCH_START, audit=False)
    gate_session = evaluate_completeness(
        REPO,
        open_ts_epoch=open_today,
        exit_ts_max_epoch=exit_max,
        audit=False,
    )

    ex_path = REPO / "logs" / "exit_attribution.jsonl"
    pnls_pct: list[float] = []
    pnls_usd: list[float] = []
    sym_pnl: dict[str, float] = defaultdict(float)
    hour_pnl: dict[str, float] = defaultdict(float)
    hour_n: Counter = Counter()
    worst_trade = None
    worst_v = 0.0
    fees_session = 0.0
    fee_n = 0

    if ex_path.is_file():
        with ex_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = _parse_iso(str(r.get("timestamp") or ""))
                if not ts:
                    continue
                u = ts.astimezone(timezone.utc)
                if not (u0 <= u < u1):
                    continue
                if u.timestamp() > exit_max:
                    continue
                p_pct = _num(r.get("pnl_pct"))
                snap = r.get("snapshot") if isinstance(r.get("snapshot"), dict) else {}
                p_usd = _num(snap.get("pnl")) if snap else _num(r.get("pnl"))
                sym = str(r.get("symbol") or "?").upper()
                tid = str(r.get("trade_id") or "")
                if p_pct is not None:
                    pnls_pct.append(p_pct)
                if p_usd is not None:
                    pnls_usd.append(p_usd)
                    sym_pnl[sym] += p_usd
                    hk = u.astimezone(ET).strftime("%H")
                    hour_pnl[hk] += p_usd
                    hour_n[hk] += 1
                    if p_usd < worst_v:
                        worst_v = p_usd
                        worst_trade = {"trade_id": tid, "symbol": sym, "pnl_usd": p_usd}

    ord_path = REPO / "logs" / "orders.jsonl"
    if ord_path.is_file():
        with ord_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(o.get("type", "")).lower() != "order":
                    continue
                ts = _parse_iso(str(o.get("timestamp") or o.get("filled_at") or ""))
                if not ts:
                    continue
                u = ts.astimezone(timezone.utc)
                if not (u0 <= u < u1):
                    continue
                for k in ("commission", "fee", "fees"):
                    v = _num(o.get(k))
                    if v is not None:
                        fees_session += abs(v)
                        fee_n += 1
                        break

    wins = [p for p in pnls_pct if p > 0]
    losses = [p for p in pnls_pct if p < 0]
    gross_pct = sum(pnls_pct) if pnls_pct else None
    net_usd = sum(pnls_usd) if pnls_usd else None
    top_sym = sorted(sym_pnl.items(), key=lambda x: x[1], reverse=True)
    bot_sym = sorted(sym_pnl.items(), key=lambda x: x[1])

    worst_hour = min(hour_pnl.items(), key=lambda x: x[1]) if hour_pnl else None

    out = {
        "session_date_et": session.isoformat(),
        "integrity": {
            "exit_attribution_rows_session_window": len(pnls_pct),
            "strict_gate_session": {
                "trades_seen": gate_session.get("trades_seen"),
                "trades_complete": gate_session.get("trades_complete"),
                "trades_incomplete": gate_session.get("trades_incomplete"),
                "LEARNING_STATUS": gate_session.get("LEARNING_STATUS"),
                "learning_fail_closed_reason": gate_session.get("learning_fail_closed_reason"),
                "reason_histogram": gate_session.get("reason_histogram"),
                "exit_ts_max_utc_epoch": exit_max,
            },
            "dashboard_aligned_gate": {
                "provenance": "dashboard.py uses open_ts_epoch=STRICT_EPOCH_START",
                "STRICT_EPOCH_START": STRICT_EPOCH_START,
                "trades_seen": gate_dash.get("trades_seen"),
                "trades_complete": gate_dash.get("trades_complete"),
                "trades_incomplete": gate_dash.get("trades_incomplete"),
                "LEARNING_STATUS": gate_dash.get("LEARNING_STATUS"),
            },
        },
        "pnl": {
            "trade_count_exit_rows_session": len(pnls_pct),
            "gross_pnl_pct_sum": gross_pct,
            "net_realized_pnl_usd_sum": net_usd,
            "fees_usd_sum_orders_heuristic": round(fees_session, 4) if fees_session else 0.0,
            "fee_field_hits": fee_n,
            "win_rate_pct_basis": (len(wins) / len(pnls_pct) * 100) if pnls_pct else None,
            "avg_win_pct": (sum(wins) / len(wins)) if wins else None,
            "avg_loss_pct": (sum(losses) / len(losses)) if losses else None,
            "min_pct": min(pnls_pct) if pnls_pct else None,
            "max_pct": max(pnls_pct) if pnls_pct else None,
        },
        "hourly_pnl_usd_et_hour": dict(sorted(hour_pnl.items())),
        "hourly_trade_count": dict(sorted(hour_n.items())),
        "worst_hour_et": {"hour": worst_hour[0], "pnl_usd": worst_hour[1]} if worst_hour else None,
        "top_contributors_usd": [{"symbol": s, "pnl_usd": round(v, 4)} for s, v in top_sym[:12]],
        "worst_detractors_usd": [{"symbol": s, "pnl_usd": round(v, 4)} for s, v in bot_sym[:12]],
        "worst_trade": worst_trade,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
