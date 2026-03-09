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
        s = str(v).replace("Z", "+00:00")[:26]
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


def phase2_exit_lag(base: Path, date_str: str) -> dict:
    """Per trade: ts_peak, first eligibility ts, ts_exit, lag_minutes, classification."""
    trace_path = base / "reports" / "state" / "exit_decision_trace.jsonl"
    start_ts, end_ts = _day_start_end(date_str)
    # Load trace samples for date
    trade_samples: dict[str, list[dict]] = defaultdict(list)
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
            trade_samples[trade_id].append(rec)
        except Exception:
            continue
    for tid in trade_samples:
        trade_samples[tid].sort(key=lambda x: x["_ts"])
    # Load exits for date
    attr_path = base / "logs" / "exit_attribution.jsonl"
    exits = _load_jsonl(attr_path, date_str, date_key="timestamp")
    if not exits:
        exits = _load_jsonl(attr_path, date_str, date_key="entry_timestamp")
    results = []
    for ex in exits:
        trade_id = _trade_id_from_attribution(ex)
        if not trade_id:
            continue
        samples = trade_samples.get(trade_id, [])
        ts_exit = _parse_ts(ex.get("timestamp") or ex.get("exit_timestamp"))
        realized_pnl = float(ex.get("pnl_usd") or ex.get("pnl") or 0)
        if not samples:
            results.append({
                "trade_id": trade_id,
                "symbol": ex.get("symbol"),
                "ts_exit": ts_exit,
                "realized_pnl_usd": round(realized_pnl, 4),
                "classification": "NO_TRACE",
                "ts_peak_unrealized": None,
                "unrealized_at_peak": None,
                "first_eligibility_ts": None,
                "lag_minutes": None,
                "missed_capture_usd": None,
            })
            continue
        peak_sample = max(samples, key=lambda s: float(s.get("unrealized_pnl") or 0))
        unrealized_at_peak = float(peak_sample.get("unrealized_pnl") or 0)
        ts_peak = peak_sample["_ts"]
        first_eligibility_ts = None
        for s in samples:
            if s["_ts"] > ts_exit:
                break
            exit_eligible = s.get("exit_eligible")
            cond = s.get("exit_conditions") or {}
            if exit_eligible is True or any(cond.get(k) for k in ("signal_decay", "flow_reversal", "stale_alpha", "risk_stop")):
                first_eligibility_ts = s["_ts"]
                break
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
            results.append({
                "trade_id": trade_id,
                "symbol": ex.get("symbol"),
                "ts_exit": ts_exit,
                "realized_pnl_usd": round(realized_pnl, 4),
                "classification": classification,
                "ts_peak_unrealized": ts_peak,
                "unrealized_at_peak": round(unrealized_at_peak, 4),
                "first_eligibility_ts": first_eligibility_ts,
                "lag_minutes": round(lag_sec / 60.0, 2) if lag_sec is not None else None,
                "missed_capture_usd": round(missed, 4) if missed is not None else None,
            })
            continue
        results.append({
            "trade_id": trade_id,
            "symbol": ex.get("symbol"),
            "ts_exit": ts_exit,
            "realized_pnl_usd": round(realized_pnl, 4),
            "classification": classification,
            "ts_peak_unrealized": ts_peak,
            "unrealized_at_peak": round(unrealized_at_peak, 4),
            "first_eligibility_ts": first_eligibility_ts,
            "lag_minutes": None,
            "missed_capture_usd": None,
        })
    by_class = defaultdict(int)
    for r in results:
        by_class[r["classification"]] += 1
    return {
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
        },
    }


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
    # Bars: optional
    bars_dir = base / "data" / "bars"
    bars_available = bars_dir.exists() and any(bars_dir.iterdir()) if bars_dir.exists() else False
    counterfactual_note = "Bars not loaded; counterfactual PnL at 30m/60m/120m not computed. Run with data/bars or Alpaca to enable."
    return {
        "date": date_str,
        "blocked_count": len(blocked),
        "by_reason": reason_stats,
        "bars_available": bars_available,
        "counterfactual_note": counterfactual_note,
        "counterfactual_pnl_30m_60m_120m": None,
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
    lag = phase2_exit_lag(base, date_str)
    blocked = phase3_blocked_counterfactuals(base, date_str)
    full_md, board_md, csa = phase4_board_and_verdict(base, date_str, phase0, curve, lag, blocked)

    (AUDIT / f"INTRADAY_PORTFOLIO_UNREALIZED_CURVE_{date_str}.json").write_text(json.dumps(curve, indent=2), encoding="utf-8")
    (AUDIT / f"INTRADAY_EXIT_LAG_AND_GIVEBACK_{date_str}.json").write_text(json.dumps(lag, indent=2), encoding="utf-8")
    (AUDIT / f"INTRADAY_BLOCKED_COUNTERFACTUALS_{date_str}.json").write_text(json.dumps(blocked, indent=2), encoding="utf-8")
    (AUDIT / f"INTRADAY_FORENSIC_FULL_{date_str}.md").write_text(full_md, encoding="utf-8")
    (BOARD / f"INTRADAY_BOARD_PACKET_{date_str}.md").write_text(board_md, encoding="utf-8")
    (AUDIT / f"CSA_INTRADAY_VERDICT_{date_str}.json").write_text(json.dumps(csa, indent=2), encoding="utf-8")

    print("Wrote 6 artifacts for", date_str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
