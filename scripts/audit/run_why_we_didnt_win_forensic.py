#!/usr/bin/env python3
"""
WHY WE DIDN'T WIN — One-day forensic. Run ON DROPLET.
Uses exit_decision_trace, exit_attribution, blocked_trades, gate (optional), bars (optional).
Produces 6 board-grade artifacts. FAIL-CLOSED on missing required data.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"
DATE_STR = "2026-03-09"


def _parse_ts(v) -> float | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).replace("Z", "+00:00").strip()
        if len(s) > 32:
            s = s[:32]
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return None


def _day_start_end(date_str: str) -> tuple[float, float]:
    try:
        start = datetime.fromisoformat(date_str + "T00:00:00+00:00").timestamp()
        end = datetime.fromisoformat(date_str + "T23:59:59.999999+00:00").timestamp()
        return start, end
    except Exception:
        return 0.0, 0.0


def _load_jsonl(path: Path, date_str: str | None = None, date_key: str = "ts") -> list:
    out = []
    if not path.exists():
        return out
    start_ts, end_ts = _day_start_end(date_str) if date_str else (0, 1e12)
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if date_str:
                    ts = rec.get(date_key) or rec.get("timestamp") or rec.get("entry_timestamp")
                    t = _parse_ts(ts)
                    if t is None or not (start_ts <= t <= end_ts):
                        continue
                out.append(rec)
            except json.JSONDecodeError:
                continue
    return out


def phase0_sre(base: Path, date_str: str) -> tuple[dict, list]:
    """Return (status_dict, blockers_list). If blockers non-empty, caller should STOP."""
    trace_path = base / "reports" / "state" / "exit_decision_trace.jsonl"
    attr_path = base / "logs" / "exit_attribution.jsonl"
    blocked_path = base / "state" / "blocked_trades.jsonl"
    gate_path = base / "logs" / "gate.jsonl"
    blockers = []
    status = {
        "date": date_str,
        "exit_decision_trace_exists": trace_path.exists(),
        "exit_decision_trace_size": trace_path.stat().st_size if trace_path.exists() else 0,
        "exit_attribution_exists": attr_path.exists(),
        "blocked_trades_exists": blocked_path.exists(),
        "gate_exists": gate_path.exists(),
        "fail_closed": False,
    }
    if not status["exit_decision_trace_exists"]:
        blockers.append("exit_decision_trace.jsonl missing")
    if not status["exit_attribution_exists"]:
        blockers.append("exit_attribution.jsonl missing")
    if not status["blocked_trades_exists"]:
        blockers.append("blocked_trades.jsonl missing")
    if blockers:
        status["fail_closed"] = True
    return status, blockers


def phase1_portfolio_curve(base: Path, date_str: str) -> dict:
    """Build ts -> sum(unrealized_pnl), count_open; peak; drawdown; top trades at peak."""
    trace_path = base / "reports" / "state" / "exit_decision_trace.jsonl"
    start_ts, end_ts = _day_start_end(date_str)
    # ts_bucket -> { sum_pnl, count, by_trade: { trade_id: unrealized_pnl } }
    buckets: dict[float, dict] = defaultdict(lambda: {"sum_pnl": 0.0, "count": 0, "by_trade": {}})
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            ts = rec.get("ts") or rec.get("timestamp")
            t = _parse_ts(ts)
            if t is None or not (start_ts <= t <= end_ts):
                continue
            trade_id = rec.get("trade_id") or ""
            upnl = float(rec.get("unrealized_pnl") or 0)
            # bucket to minute
            bucket = int(t // 60) * 60.0
            buckets[bucket]["sum_pnl"] += upnl
            buckets[bucket]["by_trade"][trade_id] = upnl
        except Exception:
            continue
    # count open per bucket = len(by_trade)
    for b in buckets.values():
        b["count"] = len(b["by_trade"])
    if not buckets:
        return {"date": date_str, "curve": [], "peak_ts": None, "peak_unrealized": None, "drawdown_from_peak": None, "top_trades_at_peak": []}
    sorted_buckets = sorted(buckets.items())
    curve = [{"ts": k, "sum_unrealized_pnl": round(v["sum_pnl"], 4), "count_open": v["count"]} for k, v in sorted_buckets]
    peak_bucket = max(sorted_buckets, key=lambda x: x[1]["sum_pnl"])
    peak_ts = peak_bucket[0]
    peak_unrealized = peak_bucket[1]["sum_pnl"]
    top_trades = sorted(peak_bucket[1]["by_trade"].items(), key=lambda x: -x[1])[:20]
    last_pnl = sorted_buckets[-1][1]["sum_pnl"] if sorted_buckets else 0
    drawdown_from_peak = (peak_unrealized - last_pnl) if peak_unrealized is not None else None
    return {
        "date": date_str,
        "curve": curve,
        "peak_ts": peak_ts,
        "peak_unrealized_usd": round(peak_unrealized, 4) if peak_unrealized is not None else None,
        "drawdown_from_peak_usd": round(drawdown_from_peak, 4) if drawdown_from_peak is not None else None,
        "top_trades_at_peak": [{"trade_id": tid, "unrealized_pnl_usd": round(u, 4)} for tid, u in top_trades],
    }


def _normalize_trade_id(tid: str) -> str:
    """Canonical form for join: open_SYM_ISO with Z suffix. Handles live:SYM:ISO."""
    if not tid:
        return ""
    s = str(tid).strip()
    if s.startswith("live:"):
        parts = s.split(":", 2)
        if len(parts) >= 3:
            sym, iso = parts[1], parts[2]
            iso = iso.replace("+00:00", "Z").replace(" ", "T")
            if iso and not iso.endswith("Z") and "+" not in iso:
                iso = iso + "Z"
            return f"open_{sym}_{iso}"
    if not s.startswith("open_"):
        return s
    parts = s.split("_", 2)
    if len(parts) < 3:
        return s
    sym, iso = parts[1], parts[2]
    iso = str(iso).replace("+00:00", "Z").replace(" ", "T")
    if iso and not iso.endswith("Z") and "+" not in iso:
        iso = iso + "Z"
    return f"open_{sym}_{iso}"


def _trade_id_from_attribution(r: dict) -> str | None:
    tid = r.get("trade_id")
    if tid:
        return tid
    sym = (r.get("symbol") or "").upper()
    entry = r.get("entry_timestamp") or r.get("entry_ts")
    if sym and entry:
        entry_s = str(entry).replace(" ", "T")[:24]
        if not entry_s.endswith("Z") and "+" not in entry_s:
            entry_s += "Z"
        return f"open_{sym}_{entry_s}"
    return None


def _entry_ts_from_trade_id(tid: str) -> float | None:
    """Parse entry timestamp from open_SYM_ISO or live:SYM:ISO. Return Unix float or None."""
    if not tid:
        return None
    s = str(tid).strip()
    iso = None
    if s.startswith("live:"):
        parts = s.split(":", 2)
        if len(parts) >= 3:
            iso = parts[2]
    elif s.startswith("open_"):
        parts = s.split("_", 2)
        if len(parts) >= 3:
            iso = parts[2]
    if not iso:
        return None
    return _parse_ts(iso)


def _entry_bucket(ts: float, bucket_sec: int = 300) -> int:
    """Floor entry_ts to bucket (default 5m). Return bucket key (int seconds)."""
    if ts is None:
        return 0
    return int(ts // bucket_sec) * bucket_sec


def phase2_exit_lag(base: Path, date_str: str) -> tuple[dict, dict]:
    """Per trade: ts_peak, first eligibility ts, ts_exit, lag_minutes, classification. Plus join diagnostics."""
    trace_path = base / "reports" / "state" / "exit_decision_trace.jsonl"
    start_ts, end_ts = _day_start_end(date_str)
    BUCKET_SEC = 300  # 5m
    trade_samples: dict[str, list[dict]] = defaultdict(list)
    trace_by_fallback: dict[tuple[str, int], list[tuple[float, str]]] = defaultdict(list)  # (symbol, bucket) -> [(entry_ts, key)]
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            ts = rec.get("ts") or rec.get("timestamp")
            t = _parse_ts(ts)
            if t is None or not (start_ts <= t <= end_ts):
                continue
            trade_id = rec.get("trade_id") or ""
            if not trade_id:
                continue
            rec["_ts"] = t
            key = _normalize_trade_id(trade_id)
            trade_samples[key].append(rec)
            sym = (rec.get("symbol") or "").upper()
            entry_ts = _entry_ts_from_trade_id(trade_id)
            if sym and entry_ts is not None:
                bucket = _entry_bucket(entry_ts, BUCKET_SEC)
                trace_by_fallback[(sym, bucket)].append((entry_ts, key))
        except Exception:
            continue
    for tid in trade_samples:
        trade_samples[tid].sort(key=lambda x: x["_ts"])
    # Dedupe fallback: each (entry_ts, key) per (sym, bucket) - keep unique keys, prefer first
    for k in trace_by_fallback:
        seen = set()
        out = []
        for et, key in trace_by_fallback[k]:
            if key not in seen:
                seen.add(key)
                out.append((et, key))
        trace_by_fallback[k] = out

    attr_path = base / "logs" / "exit_attribution.jsonl"
    exits = _load_jsonl(attr_path, date_str, date_key="timestamp")
    if not exits:
        exits = _load_jsonl(attr_path, date_str, date_key="entry_timestamp")
    join_norm_count = 0
    join_fallback_count = 0
    ambiguous_count = 0
    still_no_trace_count = 0
    results = []
    for ex in exits:
        trade_id = _trade_id_from_attribution(ex)
        if not trade_id:
            continue
        lookup_key = _normalize_trade_id(trade_id)
        samples = trade_samples.get(lookup_key, [])
        join_method = "norm"
        fallback_ambiguous = False
        if not samples:
            attr_entry_ts = _parse_ts(ex.get("entry_timestamp") or ex.get("entry_ts")) or _entry_ts_from_trade_id(trade_id)
            sym = (ex.get("symbol") or "").upper()
            if attr_entry_ts is not None and sym:
                bucket = _entry_bucket(attr_entry_ts, BUCKET_SEC)
                candidates = trace_by_fallback.get((sym, bucket), [])
                if len(candidates) > 1:
                    best = min(candidates, key=lambda x: abs(x[0] - attr_entry_ts))
                    ties = [c for c in candidates if abs(c[0] - attr_entry_ts) == abs(best[0] - attr_entry_ts)]
                    fallback_ambiguous = len(ties) > 1
                    if fallback_ambiguous:
                        ambiguous_count += 1
                    lookup_key = best[1]
                    samples = trade_samples.get(lookup_key, [])
                    join_method = "fallback"
                elif len(candidates) == 1:
                    lookup_key = candidates[0][1]
                    samples = trade_samples.get(lookup_key, [])
                    join_method = "fallback"
            if not samples:
                still_no_trace_count += 1
        else:
            join_norm_count += 1

        ts_exit = _parse_ts(ex.get("timestamp") or ex.get("exit_timestamp"))
        realized_pnl = float(ex.get("pnl_usd") or ex.get("pnl") or 0)
        if join_method == "fallback" and samples:
            join_fallback_count += 1
        join_origin = "no_trace"
        if samples:
            join_origin = "fallback_ambiguous" if fallback_ambiguous else (join_method if join_method else "norm")

        if not samples:
            results.append({
                "trade_id": trade_id,
                "symbol": ex.get("symbol"),
                "ts_exit": ts_exit,
                "realized_pnl_usd": round(realized_pnl, 4),
                "classification": "NO_TRACE",
                "join_origin": "no_trace",
                "ts_peak_unrealized": None,
                "unrealized_at_peak": None,
                "first_eligibility_ts": None,
                "unrealized_pnl_at_first_eligibility": None,
                "first_firing_condition": None,
                "lag_minutes": None,
                "missed_capture_usd": None,
            })
            continue
        peak_sample = max(samples, key=lambda s: float(s.get("unrealized_pnl") or 0))
        unrealized_at_peak = float(peak_sample.get("unrealized_pnl") or 0)
        ts_peak = peak_sample["_ts"]
        first_eligibility_ts = None
        first_eligibility_sample = None
        for s in samples:
            if s["_ts"] > ts_exit:
                break
            exit_eligible = s.get("exit_eligible")
            cond = s.get("exit_conditions") or {}
            if exit_eligible is True or any(cond.get(k) for k in ("signal_decay", "flow_reversal", "stale_alpha", "risk_stop")):
                first_eligibility_ts = s["_ts"]
                first_eligibility_sample = s
                break
        unrealized_pnl_at_first_eligibility = float(first_eligibility_sample.get("unrealized_pnl") or 0) if first_eligibility_sample else None
        first_firing_condition = None
        if first_eligibility_sample:
            c = first_eligibility_sample.get("exit_conditions") or {}
            for k in ("signal_decay", "flow_reversal", "stale_alpha", "risk_stop"):
                if c.get(k):
                    first_firing_condition = k
                    break
            if first_firing_condition is None and first_eligibility_sample.get("exit_eligible"):
                first_firing_condition = "exit_eligible_no_condition"
        lag_sec = None
        missed = None
        if unrealized_at_peak <= 0:
            classification = "NEVER_GREEN"
        elif first_eligibility_ts is None:
            classification = "GREEN_REVERSAL"
        else:
            lag_sec = (ts_exit - first_eligibility_ts) if ts_exit else None
            lag_min = lag_sec / 60.0 if lag_sec is not None else None
            near_exit = next((s for s in reversed(samples) if s["_ts"] <= (ts_exit or 0)), None)
            unrealized_near_exit = float(near_exit.get("unrealized_pnl") or 0) if near_exit else None
            missed = (unrealized_at_peak - unrealized_near_exit) if unrealized_near_exit is not None else None
            if lag_min and lag_min > 0 and missed and missed > 0:
                classification = "ELIGIBLE_BUT_LATE"
            else:
                classification = "ELIGIBLE_AND_TIMELY"
        if fallback_ambiguous:
            classification = "AMBIGUOUS_TRACE"
        results.append({
            "trade_id": trade_id,
            "symbol": ex.get("symbol"),
            "ts_exit": ts_exit,
            "realized_pnl_usd": round(realized_pnl, 4),
            "classification": classification,
            "join_origin": join_origin,
            "ts_peak_unrealized": ts_peak,
            "unrealized_at_peak": round(unrealized_at_peak, 4),
            "first_eligibility_ts": first_eligibility_ts,
            "unrealized_pnl_at_first_eligibility": round(unrealized_pnl_at_first_eligibility, 4) if unrealized_pnl_at_first_eligibility is not None else None,
            "first_firing_condition": first_firing_condition,
            "lag_minutes": round(lag_sec / 60.0, 2) if lag_sec is not None else None,
            "missed_capture_usd": round(missed, 4) if missed is not None else None,
        })
    by_class = defaultdict(int)
    for r in results:
        by_class[r["classification"]] += 1
    lag_out = {
        "date": date_str,
        "trades": results,
        "classification_counts": dict(by_class),
        "summary": {
            "total_trades": len(results),
            "never_green": by_class["NEVER_GREEN"],
            "green_reversal": by_class["GREEN_REVERSAL"],
            "eligible_but_late": by_class["ELIGIBLE_BUT_LATE"],
            "eligible_and_timely": by_class["ELIGIBLE_AND_TIMELY"],
            "no_trace": by_class["NO_TRACE"],
            "ambiguous_trace": by_class["AMBIGUOUS_TRACE"],
        },
    }
    diagnostics = {
        "date": date_str,
        "join_norm_count": join_norm_count,
        "join_fallback_count": join_fallback_count,
        "ambiguous_count": ambiguous_count,
        "still_no_trace_count": still_no_trace_count,
        "total_attribution_trades": len(results),
    }
    return lag_out, diagnostics


def _load_bars_for_symbol(base: Path, date_str: str, symbol: str) -> list[dict]:
    """Load 1Min bars from data/bars/YYYY-MM-DD/SYM_1Min.json. Return list of {t, o, h, l, c, v} with t parsed to ts."""
    bars_dir = base / "data" / "bars" / date_str
    if not bars_dir.exists():
        return []
    safe = (symbol or "").replace("/", "_").strip().upper() or "UNKNOWN"
    for tf in ("1Min", "5Min", "15Min", "1min", "5min", "15min"):
        path = bars_dir / f"{safe}_{tf}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            bars = data.get("bars", data) if isinstance(data, dict) else data
            if not isinstance(bars, list):
                return []
            out = []
            for b in bars:
                t = b.get("t") or b.get("timestamp")
                ts = _parse_ts(t)
                if ts is not None:
                    out.append({
                        "ts": ts,
                        "o": float(b.get("o") or b.get("open") or 0),
                        "h": float(b.get("h") or b.get("high") or 0),
                        "l": float(b.get("l") or b.get("low") or 0),
                        "c": float(b.get("c") or b.get("close") or 0),
                        "v": int(b.get("v") or b.get("volume") or 0),
                    })
            out.sort(key=lambda x: x["ts"])
            return out
        except Exception:
            continue
    return []


def _counterfactual_pnl(entry_ts: float, entry_price: float, bars: list[dict], horizons_min: tuple[int, ...] = (30, 60, 120)) -> dict:
    """Given entry_ts and entry_price, find exit close at +30m, +60m, +120m. Return {pnl_30m, pnl_60m, pnl_120m} (1 share long)."""
    out = {}
    for m in horizons_min:
        target_ts = entry_ts + m * 60.0
        exit_price = None
        for b in bars:
            if b["ts"] >= target_ts:
                exit_price = b["c"]
                break
        if exit_price is not None and entry_price and entry_price > 0:
            out[f"pnl_{m}m"] = round(exit_price - entry_price, 4)
        else:
            out[f"pnl_{m}m"] = None
    return out


def phase3_blocked_counterfactuals(base: Path, date_str: str) -> dict:
    """Group blocked by reason/score; counterfactual PnL if bars available."""
    blocked_path = base / "state" / "blocked_trades.jsonl"
    blocked = _load_jsonl(blocked_path, date_str, date_key="timestamp")
    if not blocked:
        for line in (blocked_path.read_text(encoding="utf-8", errors="replace").splitlines() if blocked_path.exists() else []):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = rec.get("timestamp") or rec.get("ts")
                if ts and str(ts)[:10] == date_str:
                    blocked.append(rec)
            except Exception:
                continue
    by_reason = defaultdict(list)
    for r in blocked:
        reason = str(r.get("reason") or r.get("block_reason") or "unknown")
        score = r.get("score") or r.get("candidate_score")
        by_reason[reason].append({"symbol": r.get("symbol"), "score": score, "ts": r.get("timestamp") or r.get("ts")})
    reason_stats = {reason: {"count": len(items), "sample": items[:5]} for reason, items in by_reason.items()}
    bars_dir = base / "data" / "bars" / date_str
    bars_available = bars_dir.exists() and any(bars_dir.iterdir()) if bars_dir.exists() else False
    counterfactual_note = "Bars not loaded; counterfactual PnL at 30m/60m/120m not computed. Run with data/bars or Alpaca to enable."
    counterfactual_pnl_30m_60m_120m = None
    if bars_available and blocked:
        sample_size = min(200, len(blocked))
        step = max(1, len(blocked) // sample_size)
        sampled = [blocked[i] for i in range(0, len(blocked), step)][:sample_size]
        results_cf = []
        for r in sampled:
            sym = (r.get("symbol") or "").upper()
            if not sym:
                continue
            block_ts = _parse_ts(r.get("timestamp") or r.get("ts"))
            if block_ts is None:
                continue
            bars = _load_bars_for_symbol(base, date_str, sym)
            if not bars:
                continue
            entry_price = None
            for b in bars:
                if b["ts"] >= block_ts:
                    entry_price = b["o"]
                    break
            if entry_price is None or entry_price <= 0:
                continue
            pnls = _counterfactual_pnl(block_ts, entry_price, bars)
            results_cf.append({
                "symbol": sym,
                "block_ts": block_ts,
                "entry_price": round(entry_price, 4),
                **pnls,
            })
        if results_cf:
            counterfactual_note = f"Computed for {len(results_cf)} sampled blocked trades from data/bars/{date_str}."
            agg = defaultdict(list)
            for x in results_cf:
                for k in ("pnl_30m", "pnl_60m", "pnl_120m"):
                    if x.get(k) is not None:
                        agg[k].append(x[k])
            counterfactual_pnl_30m_60m_120m = {
                "sample_count": len(results_cf),
                "mean_30m": round(sum(agg["pnl_30m"]) / len(agg["pnl_30m"]), 4) if agg["pnl_30m"] else None,
                "mean_60m": round(sum(agg["pnl_60m"]) / len(agg["pnl_60m"]), 4) if agg["pnl_60m"] else None,
                "mean_120m": round(sum(agg["pnl_120m"]) / len(agg["pnl_120m"]), 4) if agg["pnl_120m"] else None,
                "top_5_30m": sorted(results_cf, key=lambda x: (x.get("pnl_30m") or -1e9), reverse=True)[:5],
            }
    return {
        "date": date_str,
        "blocked_count": len(blocked),
        "by_reason": reason_stats,
        "bars_available": bars_available,
        "counterfactual_note": counterfactual_note,
        "counterfactual_pnl_30m_60m_120m": counterfactual_pnl_30m_60m_120m,
    }


def phase4_board_and_verdict(
    base: Path,
    date_str: str,
    phase0: dict,
    curve: dict,
    lag: dict,
    blocked: dict,
) -> tuple[str, str, dict]:
    """Write INTRADAY_FORENSIC_FULL, INTRADAY_BOARD_PACKET, CSA_INTRADAY_VERDICT."""
    summary = lag.get("summary", {})
    never_green = summary.get("never_green", 0)
    green_reversal = summary.get("green_reversal", 0)
    eligible_but_late = summary.get("eligible_but_late", 0)
    total = summary.get("total_trades", 0)
    peak_usd = curve.get("peak_unrealized_usd")
    drawdown_usd = curve.get("drawdown_from_peak_usd")
    had_portfolio_edge = peak_usd is not None and peak_usd > 0
    why_not_captured = []
    if eligible_but_late > 0:
        why_not_captured.append("exit eligibility lag (ELIGIBLE_BUT_LATE)")
    if green_reversal > 0:
        why_not_captured.append("reversal before eligibility (GREEN_REVERSAL)")
    if never_green > 0 and total:
        why_not_captured.append(f"many trades never went green ({never_green}/{total})")
    verdict = "INCONCLUSIVE_DATA"
    if not phase0.get("exit_decision_trace_exists") or not phase0.get("exit_attribution_exists"):
        verdict = "INCONCLUSIVE_DATA"
    elif not had_portfolio_edge and total and never_green >= total * 0.5:
        verdict = "ENTRY_QUALITY_PRIMARY"
    elif had_portfolio_edge and eligible_but_late > green_reversal and eligible_but_late > 0:
        verdict = "EXIT_TIMING_PRIMARY"
    elif had_portfolio_edge and green_reversal >= eligible_but_late:
        verdict = "EXIT_TIMING_PRIMARY"  # reversal = we didn't exit in time
    elif blocked.get("blocked_count", 0) > 100 and not blocked.get("bars_available"):
        verdict = "GATING_PRIMARY"  # cannot rule out gating without counterfactual
    else:
        verdict = "ENTRY_QUALITY_PRIMARY" if never_green >= (total or 0) * 0.5 else "EXIT_TIMING_PRIMARY"

    full_md = [
        "# INTRADAY FORENSIC FULL — " + date_str,
        "",
        "**Source:** Droplet. exit_decision_trace + exit_attribution + blocked_trades.",
        "",
        "## 1) Portfolio-level unrealized edge",
        "",
        f"- **Peak unrealized (USD):** {peak_usd}",
        f"- **Drawdown from peak to EOD (USD):** {drawdown_usd}",
        f"- **Had intraday profit window:** " + ("Yes" if had_portfolio_edge else "No"),
        "",
        "## 2) Why wasn't it captured?",
        "",
        "Classifications: " + json.dumps(summary),
        "",
        "Attribution: " + "; ".join(why_not_captured) if why_not_captured else "N/A",
        "",
        "## 3) Displacement_blocked impact",
        "",
        f"- Blocked count: {blocked.get('blocked_count', 0)}",
        f"- Counterfactual: {blocked.get('counterfactual_note', 'N/A')}",
        "",
        "## 4) Single change that would have helped most",
        "",
        "EXIT_TIMING: earlier exit when eligible would have captured some green-reversal and eligible-but-late trades. ENTRY_QUALITY: reducing never-green entries would reduce loss. One day is insufficient for parameter change.",
        "",
        "## 5) What must NOT change based on one day",
        "",
        "Do not relax exit thresholds or gating (displacement_blocked) based on 2026-03-09 alone.",
        "",
    ]
    board_md = [
        "# INTRADAY BOARD PACKET — " + date_str,
        "",
        "## Was there portfolio-level unrealized edge?",
        "",
        ("Yes" if had_portfolio_edge else "No") + f" (peak {peak_usd} USD, drawdown to EOD {drawdown_usd} USD).",
        "",
        "## Why wasn't it captured?",
        "",
        "; ".join(why_not_captured) if why_not_captured else "No green trades or no trace.",
        "",
        "## Did displacement_blocked help or hurt?",
        "",
        f"Blocked count: {blocked.get('blocked_count', 0)}. Counterfactual PnL not computed (bars not used). Evidence inconclusive.",
        "",
        "## What single change would have helped most?",
        "",
        "Exit timing (capture at eligibility) for eligible-but-late and green-reversal trades. No tuning recommended from one day.",
        "",
        "## What must NOT change?",
        "",
        "Do not change exit thresholds or gating based on one day.",
        "",
    ]
    csa = {
        "date": date_str,
        "verdict": verdict,
        "had_portfolio_edge": had_portfolio_edge,
        "peak_unrealized_usd": peak_usd,
        "classification_summary": summary,
        "why_not_captured": why_not_captured,
        "blocked_count": blocked.get("blocked_count", 0),
        "data_integrity_fail_closed": phase0.get("fail_closed", True),
    }
    return "\n".join(full_md), "\n".join(board_md), csa


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=DATE_STR)
    ap.add_argument("--base-dir", default=None)
    ap.add_argument("--fail-if-no-trace-above", type=float, default=None, help="Exit 2 if no_trace ratio > this (e.g. 0.20)")
    args = ap.parse_args()
    date_str = args.date
    base = Path(args.base_dir) if args.base_dir else REPO
    AUDIT.mkdir(parents=True, exist_ok=True)
    BOARD.mkdir(parents=True, exist_ok=True)

    phase0, blockers = phase0_sre(base, date_str)
    if blockers:
        blocker_path = AUDIT / f"INTRADAY_FORENSIC_BLOCKERS_{date_str}.md"
        blocker_path.write_text(
            "# INTRADAY FORENSIC BLOCKERS\n\n**Date:** " + date_str + "\n\n**Blockers:**\n\n" + "\n".join("- " + b for b in blockers) + "\n\nSTOP. Resolve and re-run.",
            encoding="utf-8",
        )
        print("FAIL CLOSED:", blockers, file=sys.stderr)
        return 1

    curve = phase1_portfolio_curve(base, date_str)
    lag, join_diagnostics = phase2_exit_lag(base, date_str)
    blocked = phase3_blocked_counterfactuals(base, date_str)
    full_md, board_md, csa = phase4_board_and_verdict(base, date_str, phase0, curve, lag, blocked)

    (AUDIT / f"INTRADAY_PORTFOLIO_UNREALIZED_CURVE_{date_str}.json").write_text(json.dumps(curve, indent=2), encoding="utf-8")
    (AUDIT / f"INTRADAY_EXIT_LAG_AND_GIVEBACK_{date_str}.json").write_text(json.dumps(lag, indent=2), encoding="utf-8")
    (AUDIT / f"INTRADAY_JOIN_DIAGNOSTICS_{date_str}.json").write_text(json.dumps(join_diagnostics, indent=2), encoding="utf-8")
    (AUDIT / f"INTRADAY_BLOCKED_COUNTERFACTUALS_{date_str}.json").write_text(json.dumps(blocked, indent=2), encoding="utf-8")
    (AUDIT / f"INTRADAY_FORENSIC_FULL_{date_str}.md").write_text(full_md, encoding="utf-8")
    (BOARD / f"INTRADAY_BOARD_PACKET_{date_str}.md").write_text(board_md, encoding="utf-8")
    (AUDIT / f"CSA_INTRADAY_VERDICT_{date_str}.json").write_text(json.dumps(csa, indent=2), encoding="utf-8")

    if args.fail_if_no_trace_above is not None:
        total = join_diagnostics.get("total_attribution_trades") or lag.get("summary", {}).get("total_trades") or 0
        no_trace = join_diagnostics.get("still_no_trace_count") or lag.get("summary", {}).get("no_trace") or 0
        ratio = (no_trace / total) if total else 1.0
        if ratio > args.fail_if_no_trace_above:
            print(f"BLOCKER: join still broken (NO_TRACE ratio {ratio:.2f} > {args.fail_if_no_trace_above}). Fix join before interpreting economics.", file=sys.stderr)
            return 2
        print("PASS: join good enough to interpret exit timing + giveback.")

    print("Wrote 7 artifacts for", date_str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
