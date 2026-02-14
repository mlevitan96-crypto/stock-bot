#!/usr/bin/env python3
"""
Proactive root-cause analytics for the Board.
Produces: uw_root_cause.json, exit_causality_matrix.json, constraint_root_cause.json,
missed_money_numeric.json, survivorship_adjustments.json, correlation_snapshot.json.
Board MUST use these to explain WHY, identify WHICH, recommend HOW.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BOARD_EOD_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOARD_EOD_DIR.parent.parent


def _day_utc(ts: Any) -> str:
    s = str(ts or "")[:10]
    return s if len(s) == 10 and s[4] == "-" else ""


def _iter_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def _load_window(base: Path, date_str: str, window_days: int = 7) -> tuple[list[str], list[dict], list[dict], list[dict]]:
    try:
        t = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return [date_str], [], [], []
    start = t - timedelta(days=window_days - 1)
    days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(window_days)]
    attr = _iter_jsonl(base / "logs" / "attribution.jsonl")
    exit_attr = _iter_jsonl(base / "logs" / "exit_attribution.jsonl")
    blocked = _iter_jsonl(base / "state" / "blocked_trades.jsonl")
    attr = [r for r in attr if _day_utc(r.get("ts") or r.get("timestamp")) in days]
    exit_attr = [r for r in exit_attr if _day_utc(r.get("ts") or r.get("timestamp") or r.get("exit_ts")) in days]
    blocked = [r for r in blocked if _day_utc(r.get("ts") or r.get("timestamp")) in days]
    return days, attr, exit_attr, blocked


# --- 1) UW ROOT-CAUSE ---

def build_uw_root_cause(base: Path, date_str: str, window_days: int = 7) -> dict[str, Any]:
    """
    For each UW candidate (symbol): entry_score, realized_pnl, win_rate, avg_hold_minutes,
    exit_reason_distribution, decay_trigger_count, blocked_count.
    uw_signal_quality_score, uw_edge_realization_rate, uw_edge_suppression_rate.
    """
    days, attr, exit_attr, blocked = _load_window(base, date_str, window_days)
    by_symbol: dict[str, dict] = defaultdict(lambda: {
        "entry_scores": [], "pnls": [], "hold_minutes": [], "exit_reasons": [],
        "decay_count": 0, "blocked_count": 0,
    })
    blocked_by_sym: dict[str, int] = defaultdict(int)
    for r in blocked:
        sym = str(r.get("symbol") or r.get("ticker") or "UNKNOWN").strip() or "UNKNOWN"
        blocked_by_sym[sym] += 1
    for r in attr:
        sym = str(r.get("symbol") or r.get("ticker") or "UNKNOWN").strip() or "UNKNOWN"
        by_symbol[sym]["entry_scores"].append(float(r.get("score") or r.get("composite_score") or 0))
        by_symbol[sym]["pnls"].append(float(r.get("pnl_usd") or r.get("pnl") or 0))
        h = r.get("hold_minutes") or r.get("time_in_trade_minutes")
        if h is not None:
            try:
                by_symbol[sym]["hold_minutes"].append(float(h))
            except (TypeError, ValueError):
                pass
        reason = str(r.get("exit_reason") or r.get("close_reason") or "unknown")
        by_symbol[sym]["exit_reasons"].append(reason)
        if "signal_decay" in reason.lower():
            by_symbol[sym]["decay_count"] += 1
        by_symbol[sym]["blocked_count"] = blocked_by_sym.get(sym, 0)
    for r in exit_attr:
        sym = str(r.get("symbol") or r.get("ticker") or "UNKNOWN").strip() or "UNKNOWN"
        if sym not in by_symbol:
            by_symbol[sym] = {"entry_scores": [], "pnls": [], "hold_minutes": [], "exit_reasons": [], "decay_count": 0, "blocked_count": blocked_by_sym.get(sym, 0)}
        by_symbol[sym]["pnls"].append(float(r.get("pnl") or r.get("pnl_usd") or 0))
        h = r.get("time_in_trade_minutes")
        if h is not None:
            try:
                by_symbol[sym]["hold_minutes"].append(float(h))
            except (TypeError, ValueError):
                pass
        reason = str(r.get("exit_reason") or "unknown")
        by_symbol[sym]["exit_reasons"].append(reason)
        if "signal_decay" in reason.lower():
            by_symbol[sym]["decay_count"] += 1
    for sym in list(by_symbol.keys()):
        if sym in blocked_by_sym and by_symbol[sym]["blocked_count"] == 0:
            by_symbol[sym]["blocked_count"] = blocked_by_sym[sym]

    candidates: list[dict] = []
    total_candidates = 0
    expressed_edge = 0
    suppressed = 0
    for sym, d in by_symbol.items():
        scores = d["entry_scores"]
        pnls = d["pnls"]
        holds = d["hold_minutes"]
        reasons = d["exit_reasons"]
        entry_score = round(sum(scores) / len(scores), 4) if scores else 0.0
        realized_pnl = round(sum(pnls), 2)
        win_rate = round(sum(1 for p in pnls if p > 0) / len(pnls), 4) if pnls else 0.0
        avg_hold = round(sum(holds) / len(holds), 1) if holds else None
        exit_dist: dict[str, int] = defaultdict(int)
        for r in reasons:
            exit_dist[r] += 1
        total_candidates += 1
        if pnls and pnls[-1] and float(pnls[-1]) > 0:
            expressed_edge += 1
        if d["blocked_count"] > 0 or (reasons and "signal_decay" in str(reasons[-1]).lower() and realized_pnl < 0):
            suppressed += 1
        candidates.append({
            "symbol": sym,
            "entry_score": entry_score,
            "realized_pnl": realized_pnl,
            "win_rate": win_rate,
            "avg_hold_minutes": avg_hold,
            "exit_reason_distribution": dict(exit_dist),
            "decay_trigger_count": d["decay_count"],
            "blocked_count": d["blocked_count"],
        })

    uw_signal_quality_score = 0.0
    if candidates:
        # Weighted: entry_score * win_rate * (1 + pnl_normalized)
        components = []
        for c in candidates:
            wr = max(0, c["win_rate"])
            sc = max(0, min(5, c["entry_score"]))
            pnl_norm = max(-1, min(1, (c["realized_pnl"] or 0) / 100.0)) if c["realized_pnl"] else 0
            components.append(sc * wr * (1 + pnl_norm * 0.2))
        uw_signal_quality_score = round(sum(components) / len(components), 4) if components else 0.0

    uw_edge_realization_rate = round(expressed_edge / total_candidates, 4) if total_candidates else 0.0
    uw_edge_suppression_rate = round(suppressed / total_candidates, 4) if total_candidates else 0.0

    out = {
        "date": date_str,
        "window_days": window_days,
        "candidates": candidates,
        "uw_signal_quality_score": uw_signal_quality_score,
        "uw_edge_realization_rate": uw_edge_realization_rate,
        "uw_edge_suppression_rate": uw_edge_suppression_rate,
        "total_candidates": total_candidates,
    }
    return out


# --- 2) EXIT CAUSALITY MATRIX ---

CAUSE_OF_DECAY_OPTIONS = [
    "price_reversal", "volatility_spike", "sector_rotation", "correlation_cluster",
    "signal_noise", "entry_misclassification", "constraint_forced_exit", "unknown",
]


def _infer_cause_of_decay(rec: dict) -> str:
    """Infer cause_of_decay from exit record when possible."""
    delta = rec.get("score_deterioration") or rec.get("relative_strength_deterioration")
    if delta is not None:
        try:
            d = float(delta)
            if d < -0.5:
                return "signal_noise"
            if d < -0.2:
                return "entry_misclassification"
        except (TypeError, ValueError):
            pass
    if rec.get("exit_reason") and "constraint" in str(rec.get("exit_reason", "")).lower():
        return "constraint_forced_exit"
    return "unknown"


def build_exit_causality_matrix(base: Path, date_str: str, window_days: int = 7) -> dict[str, Any]:
    """
    For each exit: exit_reason, signal_strength_entry/exit, signal_delta, price_delta,
    pnl_at_exit, pnl_delta_5m/15m/60m, cause_of_decay.
    """
    days, attr, exit_attr, _ = _load_window(base, date_str, window_days)
    hold_longer_path = base / "logs" / "exit_hold_longer.jsonl"
    hold_longer: list[dict] = []
    if hold_longer_path.exists():
        for r in _iter_jsonl(hold_longer_path):
            if _day_utc(r.get("timestamp") or r.get("ts")) in days:
                hold_longer.append(r)

    rows: list[dict] = []
    for r in exit_attr + [x for x in attr if x.get("exit_reason") or x.get("close_reason")]:
        entry_price = r.get("entry_price")
        exit_price = r.get("exit_price")
        price_delta = None
        if entry_price and exit_price:
            try:
                ep, xp = float(entry_price), float(exit_price)
                if ep and ep != 0:
                    price_delta = round((xp - ep) / ep, 4)
            except (TypeError, ValueError):
                pass
        entry_score = r.get("score") or r.get("v2_exit_score") or r.get("composite_score")
        exit_score = r.get("v2_exit_score") or r.get("score_deterioration")
        if exit_score is not None and entry_score is not None:
            try:
                signal_delta = round(float(exit_score) - float(entry_score), 4)
            except (TypeError, ValueError):
                signal_delta = None
        else:
            signal_delta = r.get("score_deterioration")
            if signal_delta is not None:
                try:
                    signal_delta = round(float(signal_delta), 4)
                except (TypeError, ValueError):
                    signal_delta = None
        pnl = r.get("pnl") or r.get("pnl_usd")
        pnl_delta_5m = pnl_delta_15m = pnl_delta_60m = None
        sym = str(r.get("symbol") or r.get("ticker") or "")
        ts = r.get("timestamp") or r.get("exit_ts") or r.get("ts")
        for h in hold_longer:
            if str(h.get("symbol") or "") == sym and (h.get("timestamp") or h.get("ts")) == ts:
                pnl_delta_5m = h.get("pnl_delta_5m")
                pnl_delta_15m = h.get("pnl_delta_15m")
                pnl_delta_60m = h.get("pnl_delta_60m")
                break
        cause = _infer_cause_of_decay(r)
        rows.append({
            "symbol": sym,
            "exit_reason": str(r.get("exit_reason") or r.get("close_reason") or "unknown"),
            "signal_strength_entry": entry_score,
            "signal_strength_exit": r.get("v2_exit_score"),
            "signal_delta": signal_delta,
            "price_delta": price_delta,
            "pnl_at_exit": round(float(pnl), 2) if pnl is not None and not math.isnan(float(pnl)) else None,
            "pnl_delta_5m": round(float(pnl_delta_5m), 2) if pnl_delta_5m is not None else None,
            "pnl_delta_15m": round(float(pnl_delta_15m), 2) if pnl_delta_15m is not None else None,
            "pnl_delta_60m": round(float(pnl_delta_60m), 2) if pnl_delta_60m is not None else None,
            "cause_of_decay": cause,
        })

    by_cause: dict[str, int] = defaultdict(int)
    for row in rows:
        by_cause[row["cause_of_decay"]] += 1
    return {
        "date": date_str,
        "window_days": window_days,
        "exits": rows,
        "cause_counts": dict(by_cause),
        "cause_options": CAUSE_OF_DECAY_OPTIONS,
    }


# --- 3) CONSTRAINT ROOT-CAUSE ---

def build_constraint_root_cause(base: Path, date_str: str, window_days: int = 7) -> dict[str, Any]:
    """
    For each block reason: avg_candidate_score, avg_expected_value_usd, avg_rank,
    constraint_suppression_cost_usd, constraint_false_positive_rate (proxy).
    """
    _, _, _, blocked = _load_window(base, date_str, window_days)
    by_reason: dict[str, list[dict]] = defaultdict(list)
    for r in blocked:
        reason = str(r.get("block_reason") or r.get("reason") or "unknown").strip() or "unknown"
        by_reason[reason].append(r)

    reasons_list: list[dict] = []
    total_ev = 0.0
    for reason, recs in by_reason.items():
        scores = []
        evs = []
        ranks = []
        for r in recs:
            s = r.get("candidate_score") or r.get("score")
            if s is not None:
                try:
                    scores.append(float(s))
                except (TypeError, ValueError):
                    pass
            ev = r.get("expected_value_usd")
            if ev is not None:
                try:
                    evs.append(float(ev))
                except (TypeError, ValueError):
                    pass
            rank = r.get("candidate_rank")
            if rank is not None:
                try:
                    ranks.append(int(rank))
                except (TypeError, ValueError):
                    pass
        avg_score = round(sum(scores) / len(scores), 4) if scores else None
        avg_ev = round(sum(evs), 2) if evs else None
        avg_rank = round(sum(ranks) / len(ranks), 2) if ranks else None
        total_ev += sum(evs) if evs else 0
        reasons_list.append({
            "block_reason": reason,
            "count": len(recs),
            "avg_candidate_score": avg_score,
            "avg_expected_value_usd": avg_ev,
            "avg_rank": avg_rank,
        })
    return {
        "date": date_str,
        "window_days": window_days,
        "by_reason": reasons_list,
        "constraint_suppression_cost_usd": round(total_ev, 2),
        "constraint_false_positive_rate": None,  # requires simulation
    }


# --- 4) MISSED MONEY NUMERIC ---

def build_missed_money_numeric(base: Path, date_str: str, window_days: int = 7) -> dict[str, Any]:
    """
    Numeric only. Uses same inputs as bundle_writer.compute_missed_money; does not raise if unknown.
    Caller may FAIL EOD when all_numeric is False.
    """
    try:
        from board.eod.bundle_writer import compute_missed_money
    except Exception:
        return {"date": date_str, "blocked_trade_cost_usd": 0.0, "early_exit_cost_usd": 0.0, "correlation_cost_score": None, "all_numeric": False}
    mm = compute_missed_money(base, date_str, window_days=window_days)
    blocked = mm.get("blocked_trade_opportunity_cost") or {}
    early = mm.get("early_exit_opportunity_cost") or {}
    corr = mm.get("correlation_concentration_cost") or {}
    blocked_usd = 0.0
    if not blocked.get("unknown") and blocked.get("total_expected_value_usd") is not None:
        blocked_usd = float(blocked["total_expected_value_usd"])
    early_usd = 0.0
    if not early.get("unknown"):
        early_usd = float(early.get("pnl_delta_15m_total_usd") or 0) + float(early.get("pnl_delta_60m_total_usd") or 0)
    corr_score = None
    if not corr.get("unknown") and corr.get("concentration_risk_score") is not None:
        corr_score = float(corr["concentration_risk_score"])
    return {
        "date": date_str,
        "blocked_trade_cost_usd": round(blocked_usd, 2),
        "early_exit_cost_usd": round(early_usd, 2),
        "correlation_cost_score": corr_score,
        "all_numeric": blocked.get("unknown") is False and early.get("unknown") is False,
    }


# --- 5) SURVIVORSHIP ADJUSTMENTS ---

def build_survivorship_adjustments(base: Path, date_str: str, window_days: int = 7) -> dict[str, Any]:
    """
    chronic_losers (negative pnl_contribution_usd, high trade_count), consistent_winners.
    Penalize/boost recommendations; write to state/survivorship_adjustments.json.
    """
    try:
        from board.eod.rolling_windows import build_signal_survivorship
        surv = build_signal_survivorship(base, date_str, window_days=window_days)
    except Exception:
        surv = {"signals": {}}
    try:
        from src.intelligence.survivorship import (
            CHRONIC_LOSER_PENALTY,
            CONSISTENT_WINNER_BOOST,
            DECAY_EXIT_RATE_THRESHOLD,
            DECAY_EXIT_PENALTY,
        )
    except Exception:
        CHRONIC_LOSER_PENALTY = -0.15
        CONSISTENT_WINNER_BOOST = 0.10
        DECAY_EXIT_RATE_THRESHOLD = 0.70
        DECAY_EXIT_PENALTY = -0.10
    signals = surv.get("signals") or {}
    chronic_losers: list[dict] = []
    consistent_winners: list[dict] = []
    decay_penalties: list[dict] = []
    for sym, d in signals.items():
        if not isinstance(d, dict):
            continue
        pnl = d.get("pnl_contribution_usd") or 0
        count = d.get("trade_count") or 0
        wr = d.get("win_rate") or 0
        decay_count = d.get("decay_trigger_count") or 0
        decay_rate = (decay_count / count) if count else 0.0
        # Penalize chronic losers: pnl < -10, count >= 3 -> penalize_strong; extra -0.15 when win_rate < 0.25
        if count >= 3 and pnl < -10:
            penalty = -0.5 + (CHRONIC_LOSER_PENALTY if wr is not None and wr < 0.25 else 0)
            chronic_losers.append({
                "symbol": sym, "pnl_contribution_usd": pnl, "trade_count": count, "win_rate": wr,
                "action": "penalize_strong",
                "score_penalty": round(penalty, 2),
            })
        elif count >= 3 and pnl < -20:
            chronic_losers.append({"symbol": sym, "pnl_contribution_usd": pnl, "trade_count": count, "win_rate": wr, "action": "penalize"})
        # Boost consistent winners: win_rate > 0.55 gets extra +0.10
        if count >= 3 and pnl > 10 and wr >= 0.45:
            boost = 0.5 + (CONSISTENT_WINNER_BOOST if wr is not None and wr > 0.55 else 0)
            consistent_winners.append({
                "symbol": sym, "pnl_contribution_usd": pnl, "trade_count": count, "win_rate": wr,
                "action": "boost_strong",
                "score_boost": round(boost, 2),
            })
        elif count >= 3 and pnl > 20 and wr >= 0.5:
            consistent_winners.append({"symbol": sym, "pnl_contribution_usd": pnl, "trade_count": count, "win_rate": wr, "action": "boost"})
        # Decay-based survivorship: penalize symbols with >70% decay exits
        if count >= 2 and decay_rate > DECAY_EXIT_RATE_THRESHOLD:
            decay_penalties.append({
                "symbol": sym, "decay_trigger_count": decay_count, "trade_count": count,
                "decay_exit_rate": round(decay_rate, 4), "action": "penalize_decay",
                "score_penalty": DECAY_EXIT_PENALTY,
            })
    def adj_row(x: dict) -> dict:
        r = {"symbol": x["symbol"], "action": x["action"]}
        if x.get("score_penalty") is not None:
            r["score_penalty"] = x["score_penalty"]
        if x.get("score_boost") is not None:
            r["score_boost"] = x["score_boost"]
        return r

    out = {
        "date": date_str,
        "chronic_losers": chronic_losers,
        "consistent_winners": consistent_winners,
        "decay_penalties": decay_penalties,
        "adjustments": [adj_row(x) for x in chronic_losers + consistent_winners + decay_penalties],
    }
    state_path = base / "state" / "survivorship_adjustments.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# --- 6) CORRELATION SNAPSHOT ---

def build_correlation_snapshot(base: Path, date_str: str) -> dict[str, Any]:
    """
    Compute pairwise correlations, concentration_risk_score. Write state/correlation_snapshot.json.
    """
    path = base / "state" / "signal_correlation_cache.json"
    out: dict[str, Any] = {"date": date_str, "pairs": [], "concentration_risk_score": 0, "message": ""}
    if not path.exists():
        out["message"] = "fallback: signal_correlation_cache.json missing"
        state_path = base / "state" / "correlation_snapshot.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        pairs = data.get("pairs") or []
        out["pairs"] = pairs[:20]
        if data.get("concentration_risk_score") is not None:
            out["concentration_risk_score"] = float(data["concentration_risk_score"])
        elif pairs:
            abs_corrs = [abs(float(p.get("corr", 0))) for p in pairs[:10] if isinstance(p, dict)]
            out["concentration_risk_score"] = round(sum(abs_corrs), 4) if abs_corrs else 0
        state_path = base / "state" / "correlation_snapshot.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    except Exception as e:
        out["message"] = str(e)
    return out


# --- WRITE ALL TO EOD OUT ---

def write_all_root_cause_artifacts(base: Path, date_str: str, window_days: int = 7) -> dict[str, Path]:
    """Build and write all root-cause JSON files to board/eod/out/<date_str>/."""
    out_dir = base / "board" / "eod" / "out" / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    artifacts = [
        ("uw_root_cause.json", build_uw_root_cause(base, date_str, window_days)),
        ("exit_causality_matrix.json", build_exit_causality_matrix(base, date_str, window_days)),
        ("constraint_root_cause.json", build_constraint_root_cause(base, date_str, window_days)),
        ("survivorship_adjustments.json", build_survivorship_adjustments(base, date_str, window_days)),
    ]
    for name, data in artifacts:
        p = out_dir / name
        p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        written[name] = p
    try:
        mm = build_missed_money_numeric(base, date_str, window_days)
        p = out_dir / "missed_money_numeric.json"
        p.write_text(json.dumps(mm, indent=2), encoding="utf-8")
        written["missed_money_numeric.json"] = p
    except Exception:
        pass
    # Force correlation snapshot into EOD: run compute script before build
    try:
        import subprocess
        import sys
        subprocess.run(
            [sys.executable, str(base / "scripts" / "compute_signal_correlation_snapshot.py"),
             "--minutes", "1440", "--topk", "20"],
            cwd=str(base), capture_output=True, timeout=60,
        )
    except Exception:
        pass
    corr = build_correlation_snapshot(base, date_str)
    p = out_dir / "correlation_snapshot.json"
    p.write_text(json.dumps(corr, indent=2, default=str), encoding="utf-8")
    written["correlation_snapshot.json"] = p
    return written
