#!/usr/bin/env python3
"""
Droplet-native FULL END-OF-DAY TRADE REVIEW
==========================================

This script is intended to be executed ON the droplet, where local logs/state
are the production source of truth.

Writes:
  reports/END_OF_DAY_REVIEW_<DATE>.md

Inputs (droplet paths):
  logs/run.jsonl
  logs/orders.jsonl
  logs/exit.jsonl
  logs/shadow.jsonl
  logs/system_events.jsonl
  state/market_context_v2.json
  state/regime_posture_state.json
  state/symbol_risk_features.json
  state/shadow_positions.json

Env:
  REPORT_DATE=YYYY-MM-DD (required)
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path("/root/stock-bot")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _parse_dt(x: Any) -> Optional[datetime]:
    if x is None:
        return None
    if isinstance(x, datetime):
        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    if isinstance(x, (int, float)):
        try:
            return datetime.fromtimestamp(float(x), tz=timezone.utc)
        except Exception:
            return None
    try:
        s = str(x).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict):
                    out.append(r)
    except Exception:
        return []
    return out


def _session_window(date_str: str) -> Tuple[datetime, datetime]:
    # Regular session 14:30–21:00 UTC per mandate.
    d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start = d.replace(hour=14, minute=30, second=0, microsecond=0)
    end = d.replace(hour=21, minute=0, second=0, microsecond=0)
    return start, end


def _in_window(ts: Any, start: datetime, end: datetime) -> bool:
    dt = _parse_dt(ts)
    return bool(dt and start <= dt <= end)


def _date_match(ts: Any, date_str: str) -> bool:
    dt = _parse_dt(ts)
    return bool(dt and dt.date().isoformat() == date_str)


def _infer_side_from_direction(direction: Any) -> str:
    d = str(direction or "").strip().lower()
    if d == "bearish":
        return "short"
    return "long"


def _infer_side_from_order_side(side: Any) -> str:
    s = str(side or "").strip().lower()
    if s == "sell":
        return "short"
    return "long"


def _fmt_money(x: float) -> str:
    return f"{x:,.2f}"


def _fmt_pct(x: float) -> str:
    return f"{(x * 100.0):.2f}%"


def _table(headers: List[str], rows: List[List[str]]) -> str:
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def _load_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    except Exception:
        pass
    return env


def _alpaca_daily_bar(symbol: str, date_str: str, env: Dict[str, str]) -> Optional[Dict[str, float]]:
    """
    Best-effort: returns dict(open, close) for the given date (UTC date) using Alpaca.
    If credentials or library missing, returns None.
    """
    try:
        from alpaca_trade_api import REST  # type: ignore
    except Exception:
        return None
    key = env.get("ALPACA_KEY") or env.get("ALPACA_API_KEY") or ""
    secret = env.get("ALPACA_SECRET") or env.get("ALPACA_API_SECRET") or ""
    base_url = env.get("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets"
    if not key or not secret:
        return None
    try:
        api = REST(key_id=key, secret_key=secret, base_url=base_url)
        bars = api.get_bars(symbol, "1Day", start=date_str, end=date_str, limit=5)
        df = getattr(bars, "df", None)
        if df is None or df.empty:
            return None
        row = df.iloc[-1]
        o = _safe_float(row.get("open"), 0.0)
        c = _safe_float(row.get("close"), 0.0)
        if o <= 0 or c <= 0:
            return None
        return {"open": o, "close": c}
    except Exception:
        return None


def main() -> int:
    date = os.getenv("REPORT_DATE", "").strip()
    if not date:
        raise SystemExit("REPORT_DATE is required (YYYY-MM-DD)")

    start, end = _session_window(date)
    generated = _now_utc().isoformat()

    # Load raw logs/state
    run = _read_jsonl(ROOT / "logs/run.jsonl")
    orders = _read_jsonl(ROOT / "logs/orders.jsonl")
    exits = _read_jsonl(ROOT / "logs/exit.jsonl")
    shadow = _read_jsonl(ROOT / "logs/shadow.jsonl")
    system_events = _read_jsonl(ROOT / "logs/system_events.jsonl")

    market_context_v2 = _read_json(ROOT / "state/market_context_v2.json", {})
    regime_posture = _read_json(ROOT / "state/regime_posture_state.json", {})
    risk_features = _read_json(ROOT / "state/symbol_risk_features.json", {})
    shadow_ledger = _read_json(ROOT / "state/shadow_positions.json", {"positions": []})

    # Filter to date + session window (where possible)
    run_day = [r for r in run if _date_match(r.get("ts") or r.get("timestamp"), date)]
    orders_day = [r for r in orders if _date_match(r.get("ts") or r.get("timestamp"), date)]
    exits_day = [r for r in exits if _date_match(r.get("ts") or r.get("timestamp"), date)]
    shadow_day = [r for r in shadow if _date_match(r.get("ts") or r.get("timestamp"), date)]
    se_day = [r for r in system_events if _date_match(r.get("timestamp") or r.get("ts"), date)]

    # Real trades: reconstruct from attribution events in system_events? We use `attribution.jsonl` indirectly is not listed;
    # but bot’s report contract uses it elsewhere. Here we reconstruct from orders+exit+system_events best-effort.
    # We will instead use shadow audit approach: pull executed trades from attribution if present.
    attribution_path = ROOT / "logs/attribution.jsonl"
    real_attrib = _read_jsonl(attribution_path) if attribution_path.exists() else []
    real_attrib_day = [r for r in real_attrib if _date_match(r.get("ts"), date)]

    # Index orders by symbol and approximate fill prices
    order_fills: Dict[str, List[Tuple[datetime, str, float, int]]] = {}
    for o in orders_day:
        ts = _parse_dt(o.get("ts") or o.get("timestamp"))
        if not ts or not _in_window(ts, start, end):
            continue
        sym = str(o.get("symbol") or "").upper()
        if not sym:
            continue
        side = str(o.get("side") or "").lower() or "buy"
        qty = _safe_int(o.get("qty") or o.get("filled_qty") or 0, 0)
        px = _safe_float(o.get("filled_avg_price") or o.get("avg_fill_price") or o.get("price") or 0.0, 0.0)
        if qty <= 0:
            continue
        order_fills.setdefault(sym, []).append((ts, side, px, qty))

    # Build REAL_TRADES by trade_id from attribution (most reliable for PnL)
    trades_by_id: Dict[str, Dict[str, Any]] = {}
    for r in real_attrib_day:
        tid = str(r.get("trade_id") or "")
        if not tid:
            continue
        ts = _parse_dt(r.get("ts"))
        if not ts:
            continue
        # We keep first seen and last seen to approximate entry/exit time.
        rec = trades_by_id.get(tid) or {"trade_id": tid}
        sym = str(r.get("symbol") or "").upper()
        rec["symbol"] = sym
        rec.setdefault("first_ts", ts)
        rec["last_ts"] = ts
        rec["pnl_usd"] = _safe_float(r.get("pnl_usd"), rec.get("pnl_usd", 0.0))
        ctx = r.get("context") if isinstance(r.get("context"), dict) else {}
        rec["direction"] = ctx.get("direction") or rec.get("direction")
        rec["position_size_usd"] = _safe_float(ctx.get("position_size_usd"), rec.get("position_size_usd", 0.0))
        rec["account_equity_at_entry"] = _safe_float(ctx.get("account_equity_at_entry"), rec.get("account_equity_at_entry", 0.0))
        # entry/exit prices may not exist; try pull from context
        rec["entry_price"] = _safe_float(ctx.get("entry_price"), rec.get("entry_price", 0.0))
        rec["exit_price"] = _safe_float(ctx.get("exit_price"), rec.get("exit_price", 0.0))
        rec["score"] = _safe_float(ctx.get("score"), rec.get("score", 0.0))
        trades_by_id[tid] = rec

    # Augment entry price from earliest order fill
    for tid, rec in trades_by_id.items():
        sym = str(rec.get("symbol") or "")
        if not sym:
            continue
        fills = sorted(order_fills.get(sym, []), key=lambda x: x[0])
        if fills:
            ts0, side0, px0, qty0 = fills[0]
            if _safe_float(rec.get("entry_price"), 0.0) <= 0 and px0 > 0:
                rec["entry_price"] = px0
            rec["qty"] = rec.get("qty") or qty0
            rec["side"] = _infer_side_from_order_side(side0)
        else:
            rec["side"] = _infer_side_from_direction(rec.get("direction"))
            rec["qty"] = rec.get("qty") or 0

    # Exit events can provide exit price; index by symbol
    exit_by_symbol: Dict[str, Tuple[datetime, float, str]] = {}
    for e in exits_day:
        ts = _parse_dt(e.get("ts") or e.get("timestamp"))
        if not ts:
            continue
        sym = str(e.get("symbol") or e.get("ticker") or "").upper()
        if not sym:
            continue
        px = _safe_float(e.get("exit_price") or e.get("price") or e.get("fill_price") or 0.0, 0.0)
        reason = str(e.get("reason") or e.get("exit_reason") or e.get("msg") or "")
        if px > 0:
            # keep latest
            prev = exit_by_symbol.get(sym)
            if prev is None or ts > prev[0]:
                exit_by_symbol[sym] = (ts, px, reason)

    real_rows: List[List[str]] = []
    real_total_pnl = 0.0
    real_total_notional = 0.0
    real_syms: set[str] = set()
    real_long = real_short = 0
    real_pnl_by_symbol: Dict[str, float] = {}
    real_notional_by_symbol: Dict[str, float] = {}
    real_trade_count_by_symbol: Dict[str, int] = {}
    real_score_by_symbol: Dict[str, List[float]] = {}
    real_flow_premium_by_symbol: Dict[str, List[float]] = {}
    real_flow_count_by_symbol: Dict[str, List[float]] = {}
    for rec in sorted(trades_by_id.values(), key=lambda r: r.get("first_ts") or datetime.min.replace(tzinfo=timezone.utc)):
        sym = str(rec.get("symbol") or "").upper()
        if not sym:
            continue
        entry_ts = rec.get("first_ts")
        if not entry_ts or not _in_window(entry_ts, start, end):
            continue
        exit_ts = rec.get("last_ts")
        entry_px = _safe_float(rec.get("entry_price"), 0.0)
        qty = _safe_int(rec.get("qty"), 0)
        side = str(rec.get("side") or _infer_side_from_direction(rec.get("direction")))
        pnl = _safe_float(rec.get("pnl_usd"), 0.0)
        real_total_pnl += pnl
        notional = _safe_float(rec.get("position_size_usd"), 0.0)
        if notional <= 0 and entry_px > 0 and qty > 0:
            notional = entry_px * qty
        real_total_notional += max(0.0, notional)
        real_syms.add(sym)
        real_pnl_by_symbol[sym] = real_pnl_by_symbol.get(sym, 0.0) + pnl
        real_notional_by_symbol[sym] = real_notional_by_symbol.get(sym, 0.0) + max(0.0, notional)
        real_trade_count_by_symbol[sym] = real_trade_count_by_symbol.get(sym, 0) + 1
        sc = _safe_float(rec.get("score"), 0.0)
        if sc:
            real_score_by_symbol.setdefault(sym, []).append(sc)
        ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
        comps = ctx.get("components") if isinstance(ctx.get("components"), dict) else {}
        fp = _safe_float(comps.get("flow_premium"), 0.0)
        fc = _safe_float(comps.get("flow_count"), 0.0)
        if fp:
            real_flow_premium_by_symbol.setdefault(sym, []).append(fp)
        if fc:
            real_flow_count_by_symbol.setdefault(sym, []).append(fc)
        if side == "short":
            real_short += 1
        else:
            real_long += 1

        # exit price best-effort
        exit_px = _safe_float(rec.get("exit_price"), 0.0)
        if exit_px <= 0 and sym in exit_by_symbol:
            exit_px = exit_by_symbol[sym][1]
        # MFE/MAE not reconstructible without full intraday tape; explicitly mark N/A.
        real_rows.append(
            [
                sym,
                side,
                str(qty),
                entry_ts.isoformat(),
                exit_ts.isoformat() if exit_ts else "",
                f"{entry_px:.4f}" if entry_px > 0 else "",
                f"{exit_px:.4f}" if exit_px > 0 else "",
                _fmt_money(pnl),
                "N/A",
                "N/A",
            ]
        )

    # Shadow trades
    shadow_exec = [r for r in shadow_day if str(r.get("event_type") or "") == "shadow_executed"]
    shadow_exit = [r for r in shadow_day if str(r.get("event_type") or "") == "shadow_exit"]
    shadow_pnl_updates = [r for r in shadow_day if str(r.get("event_type") or "") == "shadow_pnl_update"]

    # latest unrealized per symbol
    unreal_by_sym: Dict[str, float] = {}
    for r in shadow_pnl_updates:
        sym = str(r.get("symbol") or "").upper()
        if sym:
            unreal_by_sym[sym] = _safe_float(r.get("unrealized_pnl_usd"), 0.0)

    shadow_rows: List[List[str]] = []
    shadow_total_realized = 0.0
    shadow_total_unreal = sum(unreal_by_sym.values()) if unreal_by_sym else 0.0
    shadow_total_notional = 0.0
    shadow_syms: set[str] = set()
    shadow_long = shadow_short = 0
    shadow_notional_by_symbol: Dict[str, float] = {}
    shadow_trade_count_by_symbol: Dict[str, int] = {}
    shadow_realized_by_symbol: Dict[str, float] = {}
    shadow_unreal_by_symbol: Dict[str, float] = dict(unreal_by_sym)

    for r in sorted(shadow_exec, key=lambda x: str(x.get("ts") or "")):
        ts = _parse_dt(r.get("ts"))
        if not ts or not _in_window(ts, start, end):
            continue
        sym = str(r.get("symbol") or "").upper()
        qty = _safe_int(r.get("qty"), 0)
        entry_px = _safe_float(r.get("entry_price"), 0.0)
        side = _infer_side_from_order_side(r.get("side"))
        shadow_syms.add(sym)
        if side == "short":
            shadow_short += 1
        else:
            shadow_long += 1
        if qty > 0 and entry_px > 0:
            n = qty * entry_px
            shadow_total_notional += n
            shadow_notional_by_symbol[sym] = shadow_notional_by_symbol.get(sym, 0.0) + n
        shadow_trade_count_by_symbol[sym] = shadow_trade_count_by_symbol.get(sym, 0) + 1

        shadow_rows.append(
            [
                sym,
                side,
                str(qty),
                ts.isoformat(),
                "",
                f"{entry_px:.4f}" if entry_px > 0 else "",
                "",
                _fmt_money(0.0),
                "N/A",
                "N/A",
            ]
        )

    # Apply realized exits
    for r in shadow_exit:
        sym = str(r.get("symbol") or "").upper()
        rp = _safe_float(r.get("realized_pnl_usd"), 0.0)
        shadow_total_realized += rp
        if sym:
            shadow_realized_by_symbol[sym] = shadow_realized_by_symbol.get(sym, 0.0) + rp

    shadow_total_pnl = shadow_total_realized + shadow_total_unreal

    overlap = sorted(real_syms & shadow_syms)
    real_only = sorted(real_syms - shadow_syms)
    shadow_only = sorted(shadow_syms - real_syms)

    # Risk features map
    feat_by_sym: Dict[str, Dict[str, float]] = {}
    try:
        for k, v in (risk_features.get("symbols") or {}).items():
            if isinstance(v, dict):
                feat_by_sym[str(k).upper()] = {
                    "realized_vol_5d": _safe_float(v.get("realized_vol_5d"), 0.0),
                    "realized_vol_20d": _safe_float(v.get("realized_vol_20d"), 0.0),
                    "beta_vs_spy": _safe_float(v.get("beta_vs_spy"), 0.0),
                }
    except Exception:
        feat_by_sym = {}

    # Buy-and-hold tech benchmark
    env = _load_env_file(ROOT / ".env") if (ROOT / ".env").exists() else {}
    basket = ["AAPL", "MSFT", "NVDA", "META", "TSLA", "AMD"]
    bench_parts: List[Tuple[str, Optional[float]]] = []
    for s in basket:
        bar = _alpaca_daily_bar(s, date, env)
        if not bar:
            bench_parts.append((s, None))
            continue
        ret = (bar["close"] - bar["open"]) / bar["open"] if bar["open"] > 0 else 0.0
        bench_parts.append((s, ret))
    bench_valid = [r for _, r in bench_parts if r is not None]
    bench_ret = sum(bench_valid) / len(bench_valid) if bench_valid else 0.0

    bot_real_ret = (real_total_pnl / real_total_notional) if real_total_notional > 0 else 0.0
    bot_shadow_ret = (shadow_total_pnl / shadow_total_notional) if shadow_total_notional > 0 else 0.0

    # Regime/posture (latest snapshot only; timeline reconstruction depends on event stream)
    posture = str((regime_posture or {}).get("posture") or "")
    regime_label = str((regime_posture or {}).get("regime_label") or "")
    vol_regime = str((market_context_v2 or {}).get("volatility_regime") or "")
    market_trend = str((market_context_v2 or {}).get("market_trend") or "")

    # Compose report
    lines: List[str] = []
    lines.append(f"# END_OF_DAY_REVIEW_{date}")
    lines.append("")
    lines.append("## Data source (production)")
    lines.append("- **source**: `Droplet local logs/state (/root/stock-bot)`")
    lines.append(f"- **generated_utc**: `{generated}`")
    lines.append(f"- **session_window_utc**: `{start.isoformat()}` → `{end.isoformat()}`")
    lines.append("")

    lines.append("## Executive verdict (brutally honest)")
    lines.append(f"- **Real (v1) PnL**: `${_fmt_money(real_total_pnl)}` on notional `${_fmt_money(real_total_notional)}` → `{_fmt_pct(bot_real_ret)}`")
    lines.append(f"- **Shadow (v2) PnL**: `${_fmt_money(shadow_total_pnl)}` (realized `${_fmt_money(shadow_total_realized)}`, unrealized `${_fmt_money(shadow_total_unreal)}`) on notional `${_fmt_money(shadow_total_notional)}` → `{_fmt_pct(bot_shadow_ret)}`")
    lines.append(f"- **Buy & hold tech basket** ({', '.join(basket)}): `{_fmt_pct(bench_ret)}` (computed from Alpaca daily bars where available)")
    lines.append("")
    lines.append("### YES/NO answers")
    lines.append(f"- **Did v2 outperform v1 today (PnL)?**: `{'YES' if shadow_total_pnl > real_total_pnl else 'NO'}`")
    lines.append(f"- **Did v1 beat buy-and-hold tech today?**: `{'YES' if bot_real_ret > bench_ret else 'NO'}`")
    lines.append(f"- **Did v2 beat buy-and-hold tech today?**: `{'YES' if bot_shadow_ret > bench_ret else 'NO'}`")
    lines.append("")

    lines.append("## Market context (latest snapshot)")
    lines.append(f"- **regime_label**: `{regime_label}` | **posture**: `{posture}`")
    lines.append(f"- **market_trend**: `{market_trend}` | **volatility_regime**: `{vol_regime}`")
    lines.append("")

    lines.append("## Canonical tables")
    lines.append("### REAL_TRADES (best-effort reconstruction)")
    lines.append(_table(
        ["symbol", "side", "qty", "entry_time", "exit_time", "entry_price", "exit_price", "realized_pnl_usd", "MFE", "MAE"],
        real_rows if real_rows else [["(none)", "", "", "", "", "", "", "", "", ""]],
    ))
    lines.append("")
    lines.append("### SHADOW_TRADES (v2 hypothetical)")
    lines.append(_table(
        ["symbol", "side", "qty", "entry_time", "exit_time", "entry_price", "exit_price", "realized_pnl_shadow_usd", "MFE_shadow", "MAE_shadow"],
        shadow_rows if shadow_rows else [["(none)", "", "", "", "", "", "", "", "", ""]],
    ))
    lines.append("")

    lines.append("## Real vs shadow PnL and symbol selection")
    lines.append(f"- **real_symbols**: `{len(real_syms)}`")
    lines.append(f"- **shadow_symbols**: `{len(shadow_syms)}`")
    lines.append(f"- **overlap_symbols**: `{len(overlap)}`")
    lines.append(f"- **real_only_symbols**: `{len(real_only)}`")
    lines.append(f"- **shadow_only_symbols**: `{len(shadow_only)}`")
    lines.append("")
    if real_only:
        lines.append("### REAL_ONLY symbols")
        lines.append("- " + ", ".join(real_only[:50]))
        lines.append("")
    if shadow_only:
        lines.append("### SHADOW_ONLY symbols")
        lines.append("- " + ", ".join(shadow_only[:50]))
        lines.append("")

    # Per-symbol PnL comparison table
    lines.append("### Per-symbol PnL (real vs shadow)")
    pnl_rows: List[List[str]] = []
    for sym in sorted(real_syms | shadow_syms):
        rf = feat_by_sym.get(sym, {})
        real_p = real_pnl_by_symbol.get(sym, 0.0)
        shadow_p = shadow_realized_by_symbol.get(sym, 0.0) + shadow_unreal_by_symbol.get(sym, 0.0)
        pnl_rows.append(
            [
                sym,
                str(real_trade_count_by_symbol.get(sym, 0)),
                str(shadow_trade_count_by_symbol.get(sym, 0)),
                _fmt_money(real_p),
                _fmt_money(shadow_p),
                f"{_safe_float(rf.get('realized_vol_20d'), 0.0):.4f}" if rf else "",
                f"{_safe_float(rf.get('beta_vs_spy'), 0.0):.3f}" if rf else "",
            ]
        )
    lines.append(_table(["symbol", "real_trades", "shadow_trades", "real_pnl_usd", "shadow_pnl_usd", "vol_20d", "beta"], pnl_rows if pnl_rows else [["(none)", "", "", "", "", "", ""]]))
    lines.append("")

    # Category performance: real-only vs shadow-only
    def _avg(vals: List[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    real_only_pnls = [real_pnl_by_symbol.get(s, 0.0) for s in real_only]
    shadow_only_pnls = [(shadow_realized_by_symbol.get(s, 0.0) + shadow_unreal_by_symbol.get(s, 0.0)) for s in shadow_only]
    lines.append("### Category outcome (today)")
    lines.append(f"- **REAL_ONLY avg PnL/symbol**: `${_fmt_money(_avg(real_only_pnls))}` across `{len(real_only)}` symbols")
    lines.append(f"- **SHADOW_ONLY avg PnL/symbol**: `${_fmt_money(_avg(shadow_only_pnls))}` across `{len(shadow_only)}` symbols")
    lines.append(f"- **Did shadow-only symbols outperform real-only symbols today?**: `{'YES' if _avg(shadow_only_pnls) > _avg(real_only_pnls) else 'NO'}`")
    lines.append("")

    lines.append("## Volatility / beta exposure (from symbol risk features state)")
    rows_vb: List[List[str]] = []
    all_syms = sorted(real_syms | shadow_syms)
    for sym in all_syms:
        f = feat_by_sym.get(sym, {})
        rows_vb.append([
            sym,
            f"{_safe_float(f.get('realized_vol_20d'), 0.0):.4f}" if f else "",
            f"{_safe_float(f.get('beta_vs_spy'), 0.0):.3f}" if f else "",
            "1" if sym in real_syms else "0",
            "1" if sym in shadow_syms else "0",
        ])
    lines.append(_table(["symbol", "realized_vol_20d", "beta_vs_spy", "real_traded?", "shadow_traded?"], rows_vb if rows_vb else [["(none)", "", "", "", ""]]))
    lines.append("")

    # Vol/Beta quartile slice (best-effort)
    vols = [feat_by_sym.get(s, {}).get("realized_vol_20d", 0.0) for s in all_syms if feat_by_sym.get(s)]
    betas = [feat_by_sym.get(s, {}).get("beta_vs_spy", 0.0) for s in all_syms if feat_by_sym.get(s)]
    vols = sorted([_safe_float(v, 0.0) for v in vols if _safe_float(v, 0.0) > 0])
    betas = sorted([_safe_float(b, 0.0) for b in betas if _safe_float(b, 0.0) > 0])
    if vols and betas:
        qv_hi = vols[int(0.75 * (len(vols) - 1))]
        qv_lo = vols[int(0.25 * (len(vols) - 1))]
        qb_hi = betas[int(0.75 * (len(betas) - 1))]
        qb_lo = betas[int(0.25 * (len(betas) - 1))]

        def _is_high(sym: str) -> bool:
            f = feat_by_sym.get(sym, {})
            return _safe_float(f.get("realized_vol_20d"), 0.0) >= qv_hi and _safe_float(f.get("beta_vs_spy"), 0.0) >= qb_hi

        def _is_low(sym: str) -> bool:
            f = feat_by_sym.get(sym, {})
            return _safe_float(f.get("realized_vol_20d"), 0.0) <= qv_lo and _safe_float(f.get("beta_vs_spy"), 0.0) <= qb_lo

        high = [s for s in all_syms if _is_high(s)]
        low = [s for s in all_syms if _is_low(s)]

        def _sum_map(m: Dict[str, float], syms: List[str]) -> float:
            return sum(m.get(s, 0.0) for s in syms)

        lines.append("### High-vol/high-beta vs low-vol/low-beta slice (top/bottom quartile, best-effort)")
        lines.append(f"- thresholds: vol_hi≥{qv_hi:.4f}, beta_hi≥{qb_hi:.3f} | vol_lo≤{qv_lo:.4f}, beta_lo≤{qb_lo:.3f}")
        lines.append(f"- **real notional** high: `${_fmt_money(_sum_map(real_notional_by_symbol, high))}` | low: `${_fmt_money(_sum_map(real_notional_by_symbol, low))}`")
        lines.append(f"- **shadow notional** high: `${_fmt_money(_sum_map(shadow_notional_by_symbol, high))}` | low: `${_fmt_money(_sum_map(shadow_notional_by_symbol, low))}`")
        lines.append(f"- **real PnL** high: `${_fmt_money(_sum_map(real_pnl_by_symbol, high))}` | low: `${_fmt_money(_sum_map(real_pnl_by_symbol, low))}`")
        lines.append(f"- **shadow PnL** high: `${_fmt_money(_sum_map(shadow_unreal_by_symbol, high) + _sum_map(shadow_realized_by_symbol, high))}` | low: `${_fmt_money(_sum_map(shadow_unreal_by_symbol, low) + _sum_map(shadow_realized_by_symbol, low))}`")
        lines.append("")

    lines.append("## Long vs short posture")
    lines.append(f"- **real_long_trades**: `{real_long}` | **real_short_trades**: `{real_short}`")
    lines.append(f"- **shadow_long_trades**: `{shadow_long}` | **shadow_short_trades**: `{shadow_short}`")
    lines.append("")

    lines.append("## Divergence analysis (v2 vs v1)")
    divs = [r for r in shadow_day if str(r.get("event_type") or "") == "divergence"]
    lines.append(f"- **divergence_events**: `{len(divs)}`")
    if divs:
        rows_d: List[List[str]] = []
        for r in divs[:40]:
            ts = str(r.get("ts") or "")
            sym = str(r.get("symbol") or "").upper()
            real_sym_pnl = real_pnl_by_symbol.get(sym, 0.0)
            shadow_sym_pnl = shadow_realized_by_symbol.get(sym, 0.0) + shadow_unreal_by_symbol.get(sym, 0.0)
            rows_d.append([
                ts,
                sym,
                f"{_safe_float(r.get('v1_score'), 0.0):.3f}",
                f"{_safe_float(r.get('v2_score'), 0.0):.3f}",
                "PASS" if bool(r.get("v1_pass")) else "SKIP",
                "PASS" if bool(r.get("v2_pass")) else "SKIP",
                _fmt_money(real_sym_pnl),
                _fmt_money(shadow_sym_pnl),
            ])
        lines.append(_table(["time", "symbol", "v1_score", "v2_score", "decision_v1", "decision_v2", "real_pnl_sym", "shadow_pnl_sym"], rows_d))
        lines.append("")

    lines.append("## Brutal conclusions (decision-ready)")
    lines.append("- **What we can prove from today’s logs**:")
    lines.append("  - Shadow executed trades exist and have entry prices (v2 hypothetical).")
    lines.append("  - Shadow PnL updates are present when shadow positions exist (unrealized PnL reconstruction).")
    lines.append("- **What we cannot prove reliably from current telemetry**:")
    lines.append("  - Intraday MFE/MAE without a full price series per trade (not stored in logs today).")
    lines.append("  - Full UW/premarket per-symbol context unless explicitly logged per symbol at entry.")
    lines.append("")

    lines.append("## Minimal, contract-respecting improvements (if underperforming buy-and-hold)")
    lines.append("- If **v2 underperforms** despite better symbol selection, consider:")
    lines.append("  - Increasing v2 volatility/beta weighting *only within v2*, and keep shadow-first rollout.")
    lines.append("  - Strengthening regime/posture alignment penalties for misaligned directions.")
    lines.append("- If **v1 underperforms** vs buy-and-hold tech, the bot may be over-filtering or trading too small; validate notional and gate pressure.")
    lines.append("")

    out_path = ROOT / "reports" / f"END_OF_DAY_REVIEW_{date}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

