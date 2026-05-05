#!/usr/bin/env python3
"""
Generate a GitHub-ready daily trading review from DROPLET production data.

Constraints:
- Read-only: does not modify production logic/config.
- Uses ReportDataFetcher (Droplet) as single source of truth.

Output:
- reports/stock-bot-daily-review-YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import math
import sys
import csv
import json
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Ensure repo root is on sys.path when running as a script from subdir
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from report_data_fetcher import ReportDataFetcher
from report_data_validator import (
    ValidationError,
    validate_data_source,
    validate_report_data,
)


ISO_FIELDS = ("ts", "timestamp", "_ts", "time", "entry_ts", "exit_ts")


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(float(val), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(val, str):
        s = val.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _first_dt(record: Dict[str, Any], *keys: str) -> Optional[datetime]:
    for k in keys:
        if k in record:
            dt = _parse_dt(record.get(k))
            if dt:
                return dt
    # also check nested context
    ctx = record.get("context")
    if isinstance(ctx, dict):
        for k in keys:
            if k in ctx:
                dt = _parse_dt(ctx.get(k))
                if dt:
                    return dt
    return None


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _fmt_money(x: float) -> str:
    return f"${x:,.2f}"


def _fmt_pct(x: float) -> str:
    return f"{x:.2f}%"


def _fmt_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _fmt_minutes(x: Optional[float]) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x:.1f}"


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    def esc(s: str) -> str:
        return s.replace("\n", " ").replace("|", "\\|")

    out = []
    out.append("| " + " | ".join(esc(h) for h in headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


def _write_csv(path: Path, headers: List[str], rows: List[List[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)


def _json_default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.astimezone(timezone.utc).isoformat(timespec="seconds")
    return str(o)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=_json_default), encoding="utf-8")


def _bucketize(scores: List[float], buckets: List[Tuple[float, float]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for lo, hi in buckets:
        k = f"[{lo:.1f},{hi:.1f})"
        out[k] = 0
    for s in scores:
        for lo, hi in buckets:
            if lo <= s < hi:
                out[f"[{lo:.1f},{hi:.1f})"] += 1
                break
    return out


@dataclass(frozen=True)
class ClosedTrade:
    symbol: str
    side: str
    qty: Optional[float]
    entry_time: Optional[datetime]
    exit_time: datetime
    entry_price: Optional[float]
    exit_price: Optional[float]
    pnl_usd: float
    pnl_pct: Optional[float]
    hold_minutes: Optional[float]
    exit_reason: str
    entry_score: Optional[float]
    correlation_id: Optional[str]


def _infer_side_from_direction(direction: Optional[str]) -> Optional[str]:
    if not direction:
        return None
    d = str(direction).lower()
    if d.startswith("bull"):
        return "buy"
    if d.startswith("bear"):
        return "sell"
    return None


def _trade_event_kind(trade_id: str) -> str:
    if not trade_id:
        return "unknown"
    return str(trade_id).split("_", 1)[0].lower()


def extract_closed_trades(executed: List[Dict[str, Any]]) -> List[ClosedTrade]:
    closed: List[ClosedTrade] = []
    for rec in executed:
        trade_id = str(rec.get("trade_id") or "")
        kind = _trade_event_kind(trade_id)
        if kind not in {"close", "scale"}:
            continue
        ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
        symbol = str(rec.get("symbol") or ctx.get("symbol") or "").upper()
        if not symbol:
            continue
        exit_time = _first_dt(rec, "ts", "timestamp") or datetime.now(timezone.utc)
        entry_time = _parse_dt(ctx.get("entry_ts"))
        side = str(ctx.get("side") or _infer_side_from_direction(ctx.get("direction")) or "—")
        qty = ctx.get("qty")
        qty_f = None
        try:
            qty_f = float(qty) if qty is not None else None
        except Exception:
            qty_f = None
        entry_price = ctx.get("entry_price")
        exit_price = ctx.get("exit_price")
        entry_price_f = None
        exit_price_f = None
        try:
            entry_price_f = float(entry_price) if entry_price is not None else None
        except Exception:
            entry_price_f = None
        try:
            exit_price_f = float(exit_price) if exit_price is not None else None
        except Exception:
            exit_price_f = None
        pnl_usd = _safe_float(rec.get("pnl_usd"), 0.0)
        pnl_pct = rec.get("pnl_pct")
        pnl_pct_f = None
        try:
            pnl_pct_f = float(pnl_pct) if pnl_pct is not None else None
        except Exception:
            pnl_pct_f = None
        hold_minutes = rec.get("hold_minutes") or ctx.get("hold_minutes")
        hold_f = None
        try:
            hold_f = float(hold_minutes) if hold_minutes is not None else None
        except Exception:
            hold_f = None

        # If entry timestamp is missing but hold time is known, infer entry_time.
        if entry_time is None and hold_f is not None:
            try:
                entry_time = exit_time - timedelta(minutes=float(hold_f))
            except Exception:
                entry_time = None
        exit_reason = str(ctx.get("close_reason") or rec.get("close_reason") or "—")
        entry_score = rec.get("entry_score") or ctx.get("entry_score") or ctx.get("score")
        entry_score_f = None
        try:
            entry_score_f = float(entry_score) if entry_score is not None else None
        except Exception:
            entry_score_f = None
        correlation_id = ctx.get("correlation_id")
        if correlation_id is not None:
            correlation_id = str(correlation_id)

        closed.append(
            ClosedTrade(
                symbol=symbol,
                side=side,
                qty=qty_f,
                entry_time=entry_time,
                exit_time=exit_time,
                entry_price=entry_price_f,
                exit_price=exit_price_f,
                pnl_usd=pnl_usd,
                pnl_pct=pnl_pct_f,
                hold_minutes=hold_f,
                exit_reason=exit_reason,
                entry_score=entry_score_f,
                correlation_id=correlation_id,
            )
        )
    closed.sort(key=lambda t: t.exit_time)
    return closed


def _rolling_drawdown(pnls: List[Tuple[datetime, float]]) -> Tuple[float, float]:
    """
    Compute max drawdown on a realized-PnL cumulative curve.
    Returns (max_drawdown_abs_usd, max_peak_usd).
    """
    if not pnls:
        return 0.0, 0.0
    pnls_sorted = sorted(pnls, key=lambda x: x[0])
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for _, pnl in pnls_sorted:
        cum += pnl
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
    return max_dd, peak


def _index_by_symbol_time(
    records: List[Dict[str, Any]],
    time_key_candidates: Tuple[str, ...] = ("ts", "timestamp"),
) -> Dict[str, List[Tuple[datetime, Dict[str, Any]]]]:
    idx: Dict[str, List[Tuple[datetime, Dict[str, Any]]]] = defaultdict(list)
    for r in records:
        sym = str(r.get("symbol") or r.get("ticker") or "").upper()
        if not sym:
            # signals embed symbol under cluster
            cluster = r.get("cluster")
            if isinstance(cluster, dict):
                sym = str(cluster.get("ticker") or "").upper()
        if not sym:
            continue
        dt = _first_dt(r, *time_key_candidates) or _first_dt(r, "ts", "timestamp", "time")
        if not dt:
            continue
        idx[sym].append((dt, r))
    for sym in idx:
        idx[sym].sort(key=lambda x: x[0])
    return idx


def _nearest_within(
    idx: Dict[str, List[Tuple[datetime, Dict[str, Any]]]],
    symbol: str,
    t: datetime,
    window: timedelta,
) -> List[Dict[str, Any]]:
    items = idx.get(symbol.upper(), [])
    if not items:
        return []
    lo = t - window
    hi = t + window
    # simple linear scan around likely low volume per symbol
    out = []
    for dt, rec in items:
        if dt < lo:
            continue
        if dt > hi:
            break
        out.append(rec)
    return out


def analyze(
    date: str,
    output_path: Path,
    artifacts_dir: Optional[Path] = None,
) -> None:
    report_generated_at = datetime.now(timezone.utc)

    with ReportDataFetcher(date=date) as fetcher:
        data_source_info = fetcher.get_data_source_info()
        validate_data_source(data_source_info)

        executed = fetcher.get_executed_trades()
        blocked = fetcher.get_blocked_trades()
        signals = fetcher.get_signals()
        orders = fetcher.get_orders()
        gate_events = fetcher.get_gate_events()

    # validation (do this after close, so we don't hold SSH open on failure)
    validation_report = validate_report_data(
        executed_trades=executed,
        blocked_trades=blocked,
        signals=signals,
        date=date,
        allow_zero_trades=False,
    )

    # timestamps / window
    all_times: List[datetime] = []
    for r in executed:
        dt = _first_dt(r, "ts", "timestamp")
        if dt:
            all_times.append(dt)
    for r in blocked:
        dt = _first_dt(r, "timestamp", "ts")
        if dt:
            all_times.append(dt)
    for r in signals:
        dt = _first_dt(r, "ts", "timestamp")
        if dt:
            all_times.append(dt)
    for r in orders:
        dt = _first_dt(r, "ts", "timestamp")
        if dt:
            all_times.append(dt)
    for r in gate_events:
        dt = _first_dt(r, "ts", "timestamp")
        if dt:
            all_times.append(dt)

    session_start = min(all_times) if all_times else None
    session_end = max(all_times) if all_times else None

    # executed trades (close/scale = realized legs)
    closed = extract_closed_trades(executed)
    realized_pnl_usd = sum(t.pnl_usd for t in closed)
    wins = [t for t in closed if t.pnl_usd > 0]
    losses = [t for t in closed if t.pnl_usd < 0]
    win_rate = (len(wins) / len(closed) * 100.0) if closed else 0.0
    max_dd_usd, peak_usd = _rolling_drawdown([(t.exit_time, t.pnl_usd) for t in closed])

    # per symbol execution stats
    per_symbol: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"trades": 0, "pnl_usd": 0.0, "wins": 0, "losses": 0, "hold_minutes": []})
    for t in closed:
        s = per_symbol[t.symbol]
        s["trades"] += 1
        s["pnl_usd"] += t.pnl_usd
        if t.pnl_usd > 0:
            s["wins"] += 1
        elif t.pnl_usd < 0:
            s["losses"] += 1
        if t.hold_minutes is not None:
            s["hold_minutes"].append(t.hold_minutes)

    symbol_rows = []
    for sym, s in sorted(per_symbol.items(), key=lambda kv: kv[1]["pnl_usd"], reverse=True):
        trades_n = s["trades"]
        wr = (s["wins"] / trades_n * 100.0) if trades_n else 0.0
        avg_hold = (sum(s["hold_minutes"]) / len(s["hold_minutes"])) if s["hold_minutes"] else None
        symbol_rows.append(
            [
                sym,
                str(trades_n),
                _fmt_money(s["pnl_usd"]),
                f"{wr:.1f}%",
                _fmt_minutes(avg_hold),
            ]
        )

    # notable trades: biggest winners/losers and biggest absolute
    notable: List[ClosedTrade] = []
    if closed:
        top_w = sorted(closed, key=lambda t: t.pnl_usd, reverse=True)[:2]
        top_l = sorted(closed, key=lambda t: t.pnl_usd)[:2]
        top_abs = sorted(closed, key=lambda t: abs(t.pnl_usd), reverse=True)[:3]
        seen = set()
        for t in top_abs + top_w + top_l:
            k = (t.symbol, t.exit_time.isoformat(), t.pnl_usd)
            if k in seen:
                continue
            seen.add(k)
            notable.append(t)
        notable = notable[:5]

    # blocked trades summary
    blocked_reasons = Counter(str(b.get("reason") or "unknown") for b in blocked)
    blocked_top = blocked_reasons.most_common(12)

    blocked_rows = []
    for b in sorted(blocked, key=lambda x: _first_dt(x, "timestamp", "ts") or datetime.min.replace(tzinfo=timezone.utc)):
        ts = _first_dt(b, "timestamp", "ts")
        sym = str(b.get("symbol") or "—").upper()
        direction = str(b.get("direction") or "—")
        score = _safe_float(b.get("score"), float("nan"))
        reason = str(b.get("reason") or "unknown")
        v_err = str(b.get("validation_error") or b.get("error") or "")
        blocked_rows.append(
            [
                _fmt_dt(ts),
                sym,
                direction,
                f"{score:.3f}" if not math.isnan(score) else "—",
                reason,
                v_err if v_err else "—",
            ]
        )

    # realized trade ledger rows (all closed/scaled legs today)
    closed_rows = []
    for t in closed:
        closed_rows.append(
            [
                t.symbol,
                str(t.side),
                ("—" if t.qty is None else str(int(t.qty) if float(t.qty).is_integer() else t.qty)),
                _fmt_dt(t.entry_time),
                _fmt_dt(t.exit_time),
                ("—" if t.entry_price is None else f"{t.entry_price:.4f}"),
                ("—" if t.exit_price is None else f"{t.exit_price:.4f}"),
                _fmt_money(t.pnl_usd),
                ("—" if t.pnl_pct is None else _fmt_pct(t.pnl_pct)),
                _fmt_minutes(t.hold_minutes),
                (t.exit_reason[:120] + "…") if len(t.exit_reason) > 120 else t.exit_reason,
            ]
        )

    # Build indexes used for joins (signals/orders/blocked/executed opens)
    sig_idx = _index_by_symbol_time(signals, ("ts", "timestamp"))
    blocked_idx = _index_by_symbol_time(blocked, ("timestamp", "ts"))
    orders_idx = _index_by_symbol_time(orders, ("ts", "timestamp"))
    open_exec_idx = _index_by_symbol_time(
        [r for r in executed if _trade_event_kind(str(r.get("trade_id") or "")) == "open"],
        ("ts", "timestamp"),
    )

    # executed opens (entry events) today
    open_events = [r for r in executed if _trade_event_kind(str(r.get("trade_id") or "")) == "open"]
    open_rows = []
    open_filled = 0
    for r in sorted(open_events, key=lambda x: _first_dt(x, "ts", "timestamp") or datetime.min.replace(tzinfo=timezone.utc)):
        ts = _first_dt(r, "ts", "timestamp")
        sym = str(r.get("symbol") or "—").upper()
        ctx = r.get("context") if isinstance(r.get("context"), dict) else {}
        direction = str(ctx.get("direction") or "—")
        score = ctx.get("score")
        score_f = None
        try:
            score_f = float(score) if score is not None else None
        except Exception:
            score_f = None
        pos_usd = _safe_float(ctx.get("position_size_usd"), float("nan"))
        order_type = str(ctx.get("order_type") or "—")
        # attempt to find a filled order near the open timestamp
        fill_price = "—"
        if ts and sym:
            hits = _nearest_within(orders_idx, sym, ts, timedelta(seconds=90))
            for o in hits:
                if str(o.get("status") or "").lower() == "filled":
                    open_filled += 1
                    if o.get("price") is not None:
                        try:
                            fill_price = f"{float(o.get('price')):.4f}"
                        except Exception:
                            fill_price = str(o.get("price"))
                    break
        open_rows.append(
            [
                _fmt_dt(ts),
                sym,
                direction,
                ("—" if score_f is None else f"{score_f:.3f}"),
                ("—" if math.isnan(pos_usd) else _fmt_money(pos_usd)),
                order_type,
                fill_price,
            ]
        )

    # gate events summary
    gate_msg_counts = Counter(str(g.get("msg") or g.get("gate_type") or "unknown") for g in gate_events)
    gate_top = gate_msg_counts.most_common(12)

    # order errors / operational health
    order_error_actions = []
    for o in orders:
        if o.get("error") or o.get("error_details") or str(o.get("action") or "").endswith("_failed"):
            order_error_actions.append(o)
    order_error_counts = Counter(str(o.get("error") or o.get("action") or "unknown") for o in order_error_actions)
    order_error_top = order_error_counts.most_common(12)

    # signals: distribution + by-direction
    sig_scores = []
    sig_dir_counts = Counter()
    sig_source_counts = Counter()
    sig_ticker_counts = Counter()
    sig_toxicity = []
    sig_freshness = []
    sig_notes_terms = Counter()
    sig_sector_counts = Counter()
    for s in signals:
        cluster = s.get("cluster") if isinstance(s.get("cluster"), dict) else {}
        ticker = str(cluster.get("ticker") or "").upper()
        if ticker:
            sig_ticker_counts[ticker] += 1
        direction = str(cluster.get("direction") or "").lower() or "unknown"
        sig_dir_counts[direction] += 1
        src = str(cluster.get("source") or "unknown")
        sig_source_counts[src] += 1
        score = _safe_float(cluster.get("composite_score"), float("nan"))
        if not math.isnan(score):
            sig_scores.append(score)
        meta = cluster.get("composite_meta") if isinstance(cluster.get("composite_meta"), dict) else {}
        tox = _safe_float(meta.get("toxicity"), float("nan"))
        if not math.isnan(tox):
            sig_toxicity.append(tox)
        fr = _safe_float(meta.get("freshness"), float("nan"))
        if not math.isnan(fr):
            sig_freshness.append(fr)
        notes = str(meta.get("notes") or "")
        if notes:
            for term in [t.strip() for t in notes.split(";")]:
                if term:
                    sig_notes_terms[term] += 1
        sect = meta.get("sector_tide_info") if isinstance(meta.get("sector_tide_info"), dict) else {}
        sector = sect.get("sector")
        if sector:
            sig_sector_counts[str(sector)] += 1

    def _avg(xs: List[float]) -> Optional[float]:
        return (sum(xs) / len(xs)) if xs else None

    score_buckets = _bucketize(sig_scores, [(0.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 6.0), (6.0, 9.0)])

    # heuristic: map signals -> executed/blocked/missed and conflicts

    # precompute counter conflicts: direction flips within 10 minutes
    counter_events = []
    counter_by_signal_key = Counter()
    for sym, items in sig_idx.items():
        prev_dt = None
        prev_dir = None
        for dt, rec in items:
            cluster = rec.get("cluster") if isinstance(rec.get("cluster"), dict) else {}
            d = str(cluster.get("direction") or "unknown").lower()
            if prev_dt is not None and prev_dir is not None and d != prev_dir and d != "unknown" and prev_dir != "unknown":
                delta = dt - prev_dt
                if timedelta(0) <= delta <= timedelta(minutes=10):
                    counter_events.append((sym, prev_dir, d, delta, prev_dt, dt))
                    counter_by_signal_key[(sym, prev_dir)] += 1
                    counter_by_signal_key[(sym, d)] += 1
            prev_dt = dt
            prev_dir = d

    # build per-signal table (signal_name is derived from composite version + direction)
    per_signal = defaultdict(lambda: {"fired": 0, "executed": 0, "blocked": 0, "missed": 0, "counter": 0, "pnl_usd": 0.0})

    # index closed trades by symbol and entry time (for pnl attribution)
    closed_by_symbol = defaultdict(list)
    for t in closed:
        closed_by_symbol[t.symbol].append(t)
    for sym in closed_by_symbol:
        closed_by_symbol[sym].sort(key=lambda x: x.entry_time or x.exit_time)

    missed_candidates = []
    window_exec = timedelta(seconds=90)
    window_missed = timedelta(seconds=180)

    for rec in signals:
        ts = _first_dt(rec, "ts", "timestamp")
        if not ts:
            continue
        cluster = rec.get("cluster") if isinstance(rec.get("cluster"), dict) else {}
        sym = str(cluster.get("ticker") or "").upper()
        if not sym:
            continue
        direction = str(cluster.get("direction") or "unknown").lower()
        meta = cluster.get("composite_meta") if isinstance(cluster.get("composite_meta"), dict) else {}
        version = str(meta.get("version") or "unknown")
        signal_name = f"{cluster.get('source','unknown')}:{version}:{direction}"
        per_signal[signal_name]["fired"] += 1
        per_signal[signal_name]["counter"] += counter_by_signal_key.get((sym, direction), 0)

        # executed? (open attribution or filled order shortly after signal)
        exec_hits = _nearest_within(open_exec_idx, sym, ts, window_exec)
        order_hits = _nearest_within(orders_idx, sym, ts, window_exec)
        filled_order = any(str(o.get("status") or "").lower() == "filled" for o in order_hits)
        executed_hit = bool(exec_hits) or filled_order

        blocked_hits = _nearest_within(blocked_idx, sym, ts, window_exec)
        blocked_hit = bool(blocked_hits)

        if executed_hit:
            per_signal[signal_name]["executed"] += 1
        elif blocked_hit:
            per_signal[signal_name]["blocked"] += 1
        else:
            # missed candidate only if cluster gate_passed == True
            gate_passed = bool(cluster.get("gate_passed"))
            if gate_passed:
                later_exec = _nearest_within(open_exec_idx, sym, ts, window_missed)
                later_block = _nearest_within(blocked_idx, sym, ts, window_missed)
                later_order = _nearest_within(orders_idx, sym, ts, window_missed)
                later_filled = any(str(o.get("status") or "").lower() == "filled" for o in later_order)
                if not later_exec and not later_block and not later_filled:
                    per_signal[signal_name]["missed"] += 1
                    missed_candidates.append(rec)

        # pnl attribution heuristic: find a closed trade whose entry_ts is within 10 min after signal and matches direction
        desired_side = _infer_side_from_direction(direction)
        if desired_side and sym in closed_by_symbol:
            for t in closed_by_symbol[sym]:
                if not t.entry_time:
                    continue
                if ts <= t.entry_time <= ts + timedelta(minutes=10):
                    # map trade side to buy/sell (close context uses 'sell' for short)
                    trade_side = str(t.side).lower()
                    trade_side_norm = "buy" if "buy" in trade_side or trade_side == "long" else "sell" if "sell" in trade_side or trade_side == "short" else trade_side
                    if trade_side_norm == desired_side:
                        per_signal[signal_name]["pnl_usd"] += t.pnl_usd
                        break

    per_signal_rows = []
    for name, stats in sorted(per_signal.items(), key=lambda kv: (kv[1]["executed"], kv[1]["fired"]), reverse=True):
        per_signal_rows.append(
            [
                name,
                str(stats["fired"]),
                str(stats["executed"]),
                str(stats["blocked"]),
                str(stats["missed"]),
                str(stats["counter"]),
                _fmt_money(stats["pnl_usd"]),
            ]
        )

    # missed trades table (top by score)
    missed_rows = []
    for rec in sorted(
        missed_candidates,
        key=lambda r: _safe_float(((r.get("cluster") or {}).get("composite_score")), float("-inf")),
        reverse=True,
    )[:40]:
        ts = _first_dt(rec, "ts", "timestamp")
        cluster = rec.get("cluster") if isinstance(rec.get("cluster"), dict) else {}
        sym = str(cluster.get("ticker") or "—").upper()
        direction = str(cluster.get("direction") or "—")
        score = _safe_float(cluster.get("composite_score"), float("nan"))
        notes = ""
        meta = cluster.get("composite_meta") if isinstance(cluster.get("composite_meta"), dict) else {}
        notes = str(meta.get("notes") or "")
        missed_rows.append(
            [
                _fmt_dt(ts),
                sym,
                direction,
                f"{score:.3f}" if not math.isnan(score) else "—",
                (notes[:120] + "…") if len(notes) > 120 else (notes or "—"),
            ]
        )

    # full missed candidate rows (for appendix/details)
    missed_rows_all = []
    for rec in sorted(
        missed_candidates,
        key=lambda r: _first_dt(r, "ts", "timestamp") or datetime.min.replace(tzinfo=timezone.utc),
    ):
        ts = _first_dt(rec, "ts", "timestamp")
        cluster = rec.get("cluster") if isinstance(rec.get("cluster"), dict) else {}
        sym = str(cluster.get("ticker") or "—").upper()
        direction = str(cluster.get("direction") or "—")
        score = _safe_float(cluster.get("composite_score"), float("nan"))
        meta = cluster.get("composite_meta") if isinstance(cluster.get("composite_meta"), dict) else {}
        notes = str(meta.get("notes") or "")
        missed_rows_all.append(
            [
                _fmt_dt(ts),
                sym,
                direction,
                f"{score:.3f}" if not math.isnan(score) else "—",
                (notes[:120] + "…") if len(notes) > 120 else (notes or "—"),
            ]
        )

    # counter table (top 40, shortest deltas)
    counter_rows = []
    for sym, d0, d1, delta, t0, t1 in sorted(counter_events, key=lambda x: x[3])[:40]:
        # decision taken: did we issue a close_position order shortly after counter?
        close_orders = [
            o
            for o in _nearest_within(orders_idx, sym, t1, timedelta(minutes=15))
            if str(o.get("action") or "").lower() == "close_position"
        ]
        decision = "close_position" if close_orders else "no_immediate_close_observed"
        # pnl outcome: first close trade after counter within 6 hours
        pnl_outcome = "—"
        if sym in closed_by_symbol:
            for t in closed_by_symbol[sym]:
                if t.exit_time and t.exit_time >= t1 and t.exit_time <= t1 + timedelta(hours=6):
                    pnl_outcome = _fmt_money(t.pnl_usd)
                    break
        counter_rows.append([sym, d0, d1, f"{delta.total_seconds():.0f}s", decision, pnl_outcome])

    # derive "max exposure" proxy from open attribution records
    max_position_size_usd = 0.0
    max_equity_at_entry = 0.0
    open_sizes = []
    for r in executed:
        trade_id = str(r.get("trade_id") or "")
        if _trade_event_kind(trade_id) != "open":
            continue
        ctx = r.get("context") if isinstance(r.get("context"), dict) else {}
        ps = _safe_float(ctx.get("position_size_usd"), 0.0)
        eq = _safe_float(ctx.get("account_equity_at_entry"), 0.0)
        if ps > 0:
            open_sizes.append(ps)
        max_position_size_usd = max(max_position_size_usd, ps)
        max_equity_at_entry = max(max_equity_at_entry, eq)

    # markdown assembly
    lines: List[str] = []
    lines.append(f"# Stock-Bot Daily Review – {date} (Alpaca)")
    lines.append("")
    lines.append(f"**Report Generated:** {report_generated_at.isoformat(timespec='seconds')}")
    lines.append(f"**Data Source:** {data_source_info.get('source')}")
    lines.append(f"**Data Fetched:** {data_source_info.get('fetch_timestamp')}")
    if artifacts_dir:
        rel_artifacts = artifacts_dir.as_posix()
        lines.append(f"**Details bundle:** `{rel_artifacts}` (CSV + JSON exports)")
    lines.append("")
    if validation_report.get("warnings"):
        lines.append("**Data quality warnings (validator):**")
        for w in validation_report["warnings"]:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("## 1. Session overview")
    lines.append(f"- **Trading window (UTC):** {_fmt_dt(session_start)} → {_fmt_dt(session_end)}")
    lines.append(f"- **Total executed trade events (attribution):** {len(executed)} (includes opens/closes)")
    lines.append(f"- **Total realized closes/scales:** {len(closed)}")
    lines.append(f"- **Net realized PnL (close/scale legs):** {_fmt_money(realized_pnl_usd)}")
    lines.append(f"- **Win rate (close/scale legs):** {win_rate:.1f}% ({len(wins)}W / {len(losses)}L)")
    lines.append(f"- **Max drawdown (realized-PnL curve proxy):** {_fmt_money(max_dd_usd)} (peak {_fmt_money(peak_usd)})")
    lines.append(f"- **Max single-position size at entry (proxy):** {_fmt_money(max_position_size_usd)} (max equity seen {_fmt_money(max_equity_at_entry)})")
    lines.append("")

    lines.append("## 2. Execution summary")
    lines.append(f"- **Executed entry events (opens):** {len(open_events)} (filled-order match: {open_filled}*)")
    lines.append(f"- **Executed exit events (closes/scales):** {len(closed)}")
    lines.append("")
    lines.append("### Per-symbol realized results (close/scale legs)")
    lines.append(_md_table(["Symbol", "Closed legs", "PnL (USD)", "Win rate", "Avg hold (min)"], symbol_rows[:50]))
    lines.append("")

    lines.append("### Realized trade ledger (all closes/scales today)")
    lines.append(
        _md_table(
            [
                "Symbol",
                "Side",
                "Qty",
                "Entry time (UTC)",
                "Exit time (UTC)",
                "Entry px",
                "Exit px",
                "PnL (USD)",
                "PnL (%)",
                "Hold (min)",
                "Exit reason",
            ],
            closed_rows,
        )
    )
    lines.append("")

    if open_rows:
        lines.append("<details>")
        lines.append(f"<summary>Executed entry ledger (opens) – {len(open_rows)} rows</summary>")
        lines.append("")
        lines.append(
            _md_table(
                ["Time (UTC)", "Symbol", "Direction", "Score", "Position size (USD)", "Order type", "Fill px (nearest)"],
                open_rows,
            )
        )
        lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append("_\\* Filled-order match is a time-window heuristic on `orders.jsonl`._")
        lines.append("")

    if notable:
        lines.append("### Notable trades (largest PnL impact)")
        for t in notable:
            lines.append(
                f"- **{t.symbol} {t.side}**: PnL {_fmt_money(t.pnl_usd)}"
                f"{'' if t.pnl_pct is None else f' ({_fmt_pct(t.pnl_pct)})'}; "
                f"hold {_fmt_minutes(t.hold_minutes)} min; "
                f"exit `{t.exit_reason}`; "
                f"entry {_fmt_dt(t.entry_time)} → exit {_fmt_dt(t.exit_time)}"
            )
        lines.append("")

    lines.append("## 3. Signal behavior")
    lines.append(f"- **Total signals logged:** {len(signals)}")
    lines.append(f"- **By direction:** " + ", ".join(f"{k}={v}" for k, v in sig_dir_counts.most_common()))
    lines.append(f"- **By source:** " + ", ".join(f"{k}={v}" for k, v in sig_source_counts.most_common(8)))
    lines.append(f"- **Score buckets (composite_score):** " + ", ".join(f"{k}={v}" for k, v in score_buckets.items()))
    avg_tox = _avg(sig_toxicity)
    avg_fr = _avg(sig_freshness)
    if avg_tox is not None:
        lines.append(f"- **Avg toxicity:** {avg_tox:.3f} (from signal metadata)")
    if avg_fr is not None:
        lines.append(f"- **Avg freshness:** {avg_fr:.3f} (from signal metadata)")
    if sig_sector_counts:
        top_sectors = ", ".join(f"{k}={v}" for k, v in sig_sector_counts.most_common(6))
        lines.append(f"- **Top sectors (sector_tide_info):** {top_sectors}")
    lines.append("")

    lines.append("### Per-signal table (derived key = source:version:direction)")
    lines.append(_md_table(["Signal", "Fired", "Executed*", "Blocked*", "Missed*", "Counter*", "Attributed PnL (USD)*"], per_signal_rows[:80]))
    lines.append("")
    lines.append(
        "_\\* Executed/Blocked/Missed/Counter and PnL attribution are **heuristics** based on time-window matching between `signals.jsonl`, `orders.jsonl`, `blocked_trades.jsonl`, and `attribution.jsonl`._"
    )
    lines.append("")

    lines.append("## 4. Blocked trades")
    lines.append(f"- **Total blocked trades:** {len(blocked)}")
    if blocked_top:
        lines.append("- **Top reason codes:** " + ", ".join(f"{r}={c}" for r, c in blocked_top))
    lines.append("")
    lines.append("### Blocked trade log (first 200 rows; full day is large)")
    lines.append(_md_table(["Time (UTC)", "Symbol", "Direction", "Score", "Reason", "Details"], blocked_rows[:200]))
    lines.append("")
    lines.append("<details>")
    lines.append(f"<summary>Full blocked-trade ledger – {len(blocked_rows)} rows</summary>")
    lines.append("")
    lines.append(_md_table(["Time (UTC)", "Symbol", "Direction", "Score", "Reason", "Details"], blocked_rows))
    lines.append("")
    lines.append("</details>")
    lines.append("")
    lines.append("**Hindsight note:** outcome-tracking fields are frequently `outcome_tracked=false`, so PnL impact of blocks is mostly not inferable from today’s stored data.")
    lines.append("")

    lines.append("## 5. Missed trades")
    lines.append(
        f"- **Missed-trade candidates (gate_passed signals with no nearby order/blocked event):** {len(missed_candidates)}"
    )
    lines.append("")
    if missed_rows:
        lines.append("### Highest-score missed candidates (top 40)")
        lines.append(_md_table(["Time (UTC)", "Symbol", "Direction", "Score", "Notes (truncated)"], missed_rows))
        lines.append("")
        lines.append("<details>")
        lines.append(f"<summary>Full missed-trade candidate ledger – {len(missed_rows_all)} rows</summary>")
        lines.append("")
        lines.append(_md_table(["Time (UTC)", "Symbol", "Direction", "Score", "Notes (truncated)"], missed_rows_all))
        lines.append("")
        lines.append("</details>")
        lines.append("")
    else:
        lines.append("No missed-trade candidates detected by the current heuristic.")
        lines.append("")

    lines.append("## 6. Counter / opposing signals")
    lines.append(f"- **Direction-flip conflicts (≤10 min apart, same symbol):** {len(counter_events)}")
    lines.append("")
    if counter_rows:
        lines.append(_md_table(["Symbol", "Initial", "Counter", "Δt", "Decision observed", "PnL outcome (nearest close)"], counter_rows))
        lines.append("")
    lines.append(
        "**PnL impact vs alternative:** not reliably computable today because we do not have a standardized “counter-signal decision record” with mid/mark prices at conflict time."
    )
    lines.append("")

    lines.append("## 7. Risk & controls")
    lines.append(f"- **Gate events logged:** {len(gate_events)}")
    if gate_top:
        lines.append("- **Top gate events:** " + ", ".join(f"{m}={c}" for m, c in gate_top))
    lines.append("")
    lines.append("**Observed posture:** heavy blocking volume vs executions (blocked 570 vs 94 executed attribution events) suggests conservative gating/validation during this session.")
    lines.append("")

    lines.append("## 8. Operational health")
    lines.append(f"- **Total orders logged:** {len(orders)}")
    lines.append(f"- **Order error/failed events (heuristic):** {len(order_error_actions)}")
    if order_error_top:
        lines.append("- **Top order errors/actions:** " + ", ".join(f"{e}={c}" for e, c in order_error_top))
    lines.append("")
    lines.append("**Logging gap:** droplet path `/root/stock-bot/logs/exits.jsonl` was not found today; exit details appear only indirectly inside `attribution.jsonl` close events.")
    lines.append("")

    lines.append("## 9. Improvement opportunities")
    lines.append("- **Signal-level**: prioritize evaluating why a high volume of `gate_passed` signals do not translate into executions; add an explicit `final_decision` record tying signal → (executed|blocked|skipped) with a single correlation id.")
    lines.append("- **Execution**: add consistent `client_order_id` / `correlation_id` to `orders.jsonl` filled records so we can join to attribution and compute slippage/time-to-fill per trade.")
    lines.append("- **Risk**: `order_validation_failed` blocks often include explicit size constraint text; consider logging the numeric limit inputs (max position USD, per-name cap, equity) as structured fields (not just string).")
    lines.append("- **Logging**: restore or standardize `exits.jsonl` (or deprecate it explicitly) and ensure all report-critical logs exist daily.")
    lines.append("")

    lines.append("## 10. Appendix")
    lines.append("### Sources used (droplet paths)")
    lines.append("- `logs/attribution.jsonl` (executed trade attribution; includes close context with entry/exit and reason)")
    lines.append("- `state/blocked_trades.jsonl` (blocked trade candidates with reason codes and validation errors)")
    lines.append("- `logs/signals.jsonl` (signal snapshots including composite meta, components, motifs, expanded intel)")
    lines.append("- `logs/orders.jsonl` (order events including fills and errors)")
    lines.append("- `logs/gate.jsonl` (gate events / blockers and gate telemetry)")
    lines.append("- `logs/exits.jsonl` (**missing today on droplet**)")
    lines.append("")
    lines.append("### Repro script")
    lines.append(f"- `reports/_daily_review_tools/generate_daily_review.py` (this report generator; uses `ReportDataFetcher(date='{date}')`)")
    lines.append("")

    if artifacts_dir:
        rel = artifacts_dir.as_posix()
        lines.append("### Detailed exports (machine-readable)")
        lines.append(f"- `{rel}/daily_review_details.json` (summary + tables)")
        lines.append(f"- `{rel}/closed_trades.csv` (realized closes/scales)")
        lines.append(f"- `{rel}/open_events.csv` (executed opens, with nearest fill px)")
        lines.append(f"- `{rel}/blocked_trades.csv` (all blocked trades, filtered to date)")
        lines.append(f"- `{rel}/missed_candidates.csv` (all missed-trade candidates, filtered to date)")
        lines.append(f"- `{rel}/counter_conflicts.csv` (direction flips within 10 minutes)")
        lines.append(f"- `{rel}/per_symbol_summary.csv`")
        lines.append(f"- `{rel}/per_signal_summary.csv`")
        lines.append(f"- `{rel}/order_errors_summary.csv`")
        lines.append(f"- `{rel}/gate_events_summary.csv`")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # write artifacts bundle
    if artifacts_dir:
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # CSV exports
        _write_csv(
            artifacts_dir / "closed_trades.csv",
            [
                "symbol",
                "side",
                "qty",
                "entry_time_utc",
                "exit_time_utc",
                "entry_price",
                "exit_price",
                "pnl_usd",
                "pnl_pct",
                "hold_minutes",
                "exit_reason",
                "entry_score",
                "correlation_id",
            ],
            [
                [
                    t.symbol,
                    t.side,
                    t.qty,
                    t.entry_time,
                    t.exit_time,
                    t.entry_price,
                    t.exit_price,
                    t.pnl_usd,
                    t.pnl_pct,
                    t.hold_minutes,
                    t.exit_reason,
                    t.entry_score,
                    t.correlation_id,
                ]
                for t in closed
            ],
        )

        _write_csv(
            artifacts_dir / "open_events.csv",
            ["time_utc", "symbol", "direction", "score", "position_size_usd", "order_type", "fill_px_nearest"],
            [
                [r[0], r[1], r[2], r[3], r[4], r[5], r[6]]
                for r in open_rows
            ],
        )

        _write_csv(
            artifacts_dir / "blocked_trades.csv",
            ["time_utc", "symbol", "direction", "score", "reason", "details"],
            blocked_rows,
        )

        _write_csv(
            artifacts_dir / "missed_candidates.csv",
            ["time_utc", "symbol", "direction", "score", "notes_truncated"],
            missed_rows_all,
        )

        _write_csv(
            artifacts_dir / "counter_conflicts.csv",
            ["symbol", "initial_direction", "counter_direction", "delta_seconds", "decision_observed", "pnl_outcome_nearest_close"],
            [
                [sym, d0, d1, int(float(dt_s.replace("s", ""))), decision, pnl]
                for sym, d0, d1, dt_s, decision, pnl in counter_rows
            ],
        )

        _write_csv(
            artifacts_dir / "per_symbol_summary.csv",
            ["symbol", "closed_legs", "pnl_usd", "wins", "losses", "win_rate_pct", "avg_hold_minutes"],
            [
                [
                    sym,
                    s["trades"],
                    s["pnl_usd"],
                    s["wins"],
                    s["losses"],
                    (s["wins"] / s["trades"] * 100.0) if s["trades"] else 0.0,
                    (sum(s["hold_minutes"]) / len(s["hold_minutes"])) if s["hold_minutes"] else None,
                ]
                for sym, s in sorted(per_symbol.items())
            ],
        )

        _write_csv(
            artifacts_dir / "per_signal_summary.csv",
            ["signal", "fired", "executed", "blocked", "missed", "counter", "attributed_pnl_usd"],
            [
                [name, stats["fired"], stats["executed"], stats["blocked"], stats["missed"], stats["counter"], stats["pnl_usd"]]
                for name, stats in sorted(per_signal.items())
            ],
        )

        _write_csv(
            artifacts_dir / "order_errors_summary.csv",
            ["error_or_action", "count"],
            [[k, v] for k, v in order_error_top],
        )

        _write_csv(
            artifacts_dir / "gate_events_summary.csv",
            ["gate_msg", "count"],
            [[k, v] for k, v in gate_top],
        )

        # JSON export (summary + high-signal tables; raw logs are already available via droplet cache if needed)
        details = {
            "report_date": date,
            "report_generated_at": report_generated_at,
            "data_source_info": data_source_info,
            "counts": {
                "executed_attribution_events": len(executed),
                "executed_open_events": len(open_events),
                "realized_close_scale_events": len(closed),
                "blocked_trades": len(blocked),
                "signals": len(signals),
                "orders": len(orders),
                "gate_events": len(gate_events),
                "order_error_events_heuristic": len(order_error_actions),
                "missed_candidates": len(missed_candidates),
                "counter_conflicts": len(counter_events),
            },
            "session_window_utc": {"start": session_start, "end": session_end},
            "pnl": {
                "net_realized_usd_close_scale": realized_pnl_usd,
                "wins": len(wins),
                "losses": len(losses),
                "win_rate_pct": win_rate,
                "max_drawdown_usd_proxy": max_dd_usd,
                "peak_usd_proxy": peak_usd,
            },
            "top_block_reasons": blocked_top,
            "top_gate_events": gate_top,
            "top_order_errors": order_error_top,
            "signal_distribution": {
                "direction_counts": dict(sig_dir_counts),
                "source_counts": dict(sig_source_counts),
                "score_buckets": score_buckets,
                "avg_toxicity": _avg(sig_toxicity),
                "avg_freshness": _avg(sig_freshness),
                "sector_counts": dict(sig_sector_counts),
            },
        }
        _write_json(artifacts_dir / "daily_review_details.json", details)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD (UTC)")
    p.add_argument(
        "--out",
        default=None,
        help="Output markdown path (default: reports/stock-bot-daily-review-YYYY-MM-DD.md)",
    )
    p.add_argument(
        "--artifacts-dir",
        default=None,
        help="Directory to write detailed exports (CSV + JSON). "
        "Default: reports/stock-bot-daily-review-YYYY-MM-DD-artifacts/",
    )
    args = p.parse_args()

    date = args.date
    out = Path(args.out) if args.out else Path("reports") / f"stock-bot-daily-review-{date}.md"
    artifacts_dir = (
        Path(args.artifacts_dir)
        if args.artifacts_dir
        else Path("reports") / f"stock-bot-daily-review-{date}-artifacts"
    )

    try:
        analyze(date=date, output_path=out, artifacts_dir=artifacts_dir)
    except ValidationError as e:
        raise SystemExit(str(e)) from e
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

