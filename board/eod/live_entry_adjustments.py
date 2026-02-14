#!/usr/bin/env python3
"""
Live entry adjustments: survivorship, UW root-cause, constraint root-cause, correlation.
Apply BEFORE displacement and max_positions. Log all adjustments to JSONL.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SURVIVORSHIP_LOG = REPO_ROOT / "logs" / "survivorship_entry_adjustments.jsonl"
UW_ADJUSTMENTS_LOG = REPO_ROOT / "logs" / "uw_entry_adjustments.jsonl"
CONSTRAINT_OVERRIDES_LOG = REPO_ROOT / "logs" / "constraint_overrides.jsonl"

# Config: penalty/boost amounts (penalize_strong/boost_strong are stronger)
SURVIVORSHIP_PENALTY = 0.5
SURVIVORSHIP_PENALTY_STRONG = 0.5
SURVIVORSHIP_BOOST = 0.3
SURVIVORSHIP_BOOST_STRONG = 0.5
UW_QUALITY_WEIGHT = 0.1
UW_QUALITY_BOOST_STRONG = 0.75  # When uw_signal_quality_score >= 0.6
UW_QUALITY_LONGEVITY_BOOST = 0.15  # When uw_signal_quality_score >= 0.7
UW_QUALITY_PRE_FILTER_MIN = 0.25  # Reject candidates below this
UW_EDGE_REALIZATION_BOOST = 0.15
UW_EDGE_SUPPRESSION_PENALTY = 0.1
UW_EDGE_SUPPRESSION_STRONG_PENALTY = 0.2  # When uw_edge_suppression_rate > 0.8


def _append_jsonl(path: Path, rec: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        pass


def load_survivorship_adjustments(base: Path | None = None) -> dict[str, Any]:
    """Load state/survivorship_adjustments.json. Returns { adjustments: [{ symbol, action }], ... }."""
    base = base or REPO_ROOT
    path = base / "state" / "survivorship_adjustments.json"
    if not path.exists():
        return {"adjustments": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"adjustments": []}


def apply_survivorship_to_score(symbol: str, composite_score: float, base: Path | None = None) -> tuple[float, str]:
    """
    Apply survivorship adjustment. Returns (adjusted_score, action_applied).
    action_applied: "" | "penalize" | "penalize_strong" | "boost" | "boost_strong" | "penalize_decay"
    Also applies delta from src.intelligence.survivorship (chronic losers, consistent winners, decay-based).
    """
    data = load_survivorship_adjustments(base)
    delta = 0.0
    action = ""
    for adj in data.get("adjustments") or []:
        if adj.get("symbol") == symbol:
            action = (adj.get("action") or "").strip().lower()
            if action == "penalize_strong":
                delta += adj.get("score_penalty", SURVIVORSHIP_PENALTY_STRONG) or SURVIVORSHIP_PENALTY_STRONG
                delta = -abs(delta) if delta > 0 else delta
            elif action == "penalize":
                delta -= SURVIVORSHIP_PENALTY
            elif action == "penalize_decay":
                delta += adj.get("score_penalty", -0.1) or -0.1
            elif action == "boost_strong":
                delta += adj.get("score_boost", SURVIVORSHIP_BOOST_STRONG) or SURVIVORSHIP_BOOST_STRONG
            elif action == "boost":
                delta += SURVIVORSHIP_BOOST
            break
    if not action:
        try:
            from src.intelligence.survivorship import survivorship_score_delta
            delta += survivorship_score_delta(symbol, base)
        except Exception:
            pass
    if delta != 0:
        out = composite_score + delta
        _append_jsonl(SURVIVORSHIP_LOG, {"symbol": symbol, "action": action or "intelligence_delta", "delta": round(delta, 4), "score_before": composite_score, "score_after": out})
        return out, action or "intelligence_delta"
    return composite_score, ""


def load_uw_root_cause_latest(base: Path | None = None) -> dict[str, Any]:
    """Load latest uw_root_cause from board/eod/out/<latest_date>/uw_root_cause.json."""
    base = base or REPO_ROOT
    out_dir = base / "board" / "eod" / "out"
    if not out_dir.exists():
        return {}
    best: dict[str, Any] = {}
    best_date = ""
    for d in out_dir.iterdir():
        if d.is_dir() and len(d.name) == 10 and d.name[4] == "-":
            p = d / "uw_root_cause.json"
            if p.exists() and d.name > best_date:
                try:
                    best = json.loads(p.read_text(encoding="utf-8"))
                    best_date = d.name
                except Exception:
                    pass
    return best


def apply_uw_to_score(symbol: str, composite_score: float, base: Path | None = None) -> tuple[float, dict]:
    """
    Apply UW root-cause adjustments. Returns (adjusted_score, details).
    Pre-filter: reject (score -> -inf) when uw_signal_quality_score < 0.25.
    UW longevity: quality >= 0.7 -> +0.15; UW suppression: edge_suppression > 0.8 -> -0.2.
    Stronger boosts: quality >= 0.6 -> +0.75; override displacement if score gap > 0.1.
    """
    data = load_uw_root_cause_latest(base)
    details: dict[str, Any] = {}
    delta = 0.0
    quality = data.get("uw_signal_quality_score")
    supp = data.get("uw_edge_suppression_rate")
    real = data.get("uw_edge_realization_rate")

    # Per-candidate quality for pre-filter and longevity
    cand_quality: float | None = None
    for c in data.get("candidates") or []:
        if c.get("symbol") == symbol:
            details["candidate"] = c
            cand_quality = c.get("uw_signal_quality_score")
            if cand_quality is not None:
                cand_quality = float(cand_quality)
            break
    use_quality = cand_quality if cand_quality is not None else (float(quality) if quality is not None else None)
    if use_quality is not None and use_quality < UW_QUALITY_PRE_FILTER_MIN:
        details["uw_rejected_low_quality"] = True
        details["uw_signal_quality_score"] = use_quality
        _append_jsonl(UW_ADJUSTMENTS_LOG, {"symbol": symbol, "rejected": True, "quality": use_quality, "threshold": UW_QUALITY_PRE_FILTER_MIN})
        return float("-inf"), details

    if quality is not None:
        q = float(quality)
        details["uw_signal_quality_score"] = q
        if q >= 0.6:
            delta += UW_QUALITY_BOOST_STRONG
            details["uw_quality_boost_strong"] = True
            details["allow_displacement_override"] = True
            details["allow_max_positions_override"] = True
        else:
            delta += q * UW_QUALITY_WEIGHT
        if q >= 0.7:
            delta += UW_QUALITY_LONGEVITY_BOOST
            details["uw_longevity_boost"] = True
    if real is not None and real > 0.5:
        delta += UW_EDGE_REALIZATION_BOOST
    if supp is not None:
        details["uw_edge_suppression_rate"] = supp
        if float(supp) > 0.8:
            delta -= UW_EDGE_SUPPRESSION_STRONG_PENALTY
            details["uw_suppression_strong"] = True
        elif float(supp) > 0.5:
            delta -= UW_EDGE_SUPPRESSION_PENALTY
        details["allow_let_it_breathe"] = True
        details["override_displacement_if_score_gap"] = 0.1

    out = composite_score + delta
    if delta != 0 or details:
        if delta != 0:
            details["delta"] = delta
        _append_jsonl(UW_ADJUSTMENTS_LOG, {"symbol": symbol, "delta": delta, "score_before": composite_score, "score_after": out, "quality": quality, "edge_realization": real, "edge_suppression": supp, "details": details})
    return out, details


def load_constraint_root_cause_latest(base: Path | None = None) -> dict[str, Any]:
    """Load latest constraint_root_cause.json from board/eod/out."""
    base = base or REPO_ROOT
    out_dir = base / "board" / "eod" / "out"
    if not out_dir.exists():
        return {}
    best: dict[str, Any] = {}
    best_date = ""
    for d in out_dir.iterdir():
        if d.is_dir() and len(d.name) == 10 and d.name[4] == "-":
            p = d / "constraint_root_cause.json"
            if p.exists() and d.name > best_date:
                try:
                    best = json.loads(p.read_text(encoding="utf-8"))
                    best_date = d.name
                except Exception:
                    pass
    return best


def load_correlation_snapshot(base: Path | None = None) -> dict[str, Any]:
    """Load state/correlation_snapshot.json."""
    base = base or REPO_ROOT
    path = base / "state" / "correlation_snapshot.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def check_constraint_override_eligible(
    symbol: str,
    uw_details: dict | None,
    surv_action: str,
    variant_id: str | None,
    base: Path | None = None,
) -> tuple[bool, dict]:
    """
    Check if symbol qualifies for displacement/max_positions override.
    Returns (eligible, reason_dict).
    Eligible if: uw_signal_quality_score >= 0.6 OR survivorship boost active OR variant_id == "live_canary".
    """
    reasons: dict[str, Any] = {}
    if uw_details and uw_details.get("allow_displacement_override"):
        reasons["uw_quality_boost"] = True
    if surv_action in ("boost", "boost_strong"):
        reasons["survivorship_boost"] = surv_action
    if variant_id == "live_canary":
        reasons["variant_id"] = "live_canary"
    eligible = bool(reasons)
    if eligible:
        _append_jsonl(
            CONSTRAINT_OVERRIDES_LOG,
            {"symbol": symbol, "reasons": reasons, "allow_displacement_override": True, "allow_max_positions_burst": True},
        )
    return eligible, reasons


def apply_signal_quality_to_score(
    symbol: str,
    composite_score: float,
    market_context: dict | None = None,
    base: Path | None = None,
) -> float:
    """
    Apply signal-quality adjustment: smoothing, persistence, longevity, trend, volatility filter.
    market_context may contain: raw_signal (float), atr (float).
    Returns adjusted score. If no context, returns composite_score unchanged.
    """
    try:
        from src.intelligence.signal_quality import signal_quality_delta
    except Exception:
        return composite_score
    ctx = market_context or {}
    raw_signal = ctx.get("raw_signal")
    if raw_signal is None:
        raw_signal = composite_score
    atr = ctx.get("atr")
    fast_signal = ctx.get("fast_signal")
    slow_signal = ctx.get("slow_signal")
    regime_label = ctx.get("regime_label")
    sector_momentum = ctx.get("sector_momentum")
    delta = signal_quality_delta(
        symbol,
        raw_signal=float(raw_signal),
        atr=atr,
        fast_signal=fast_signal,
        slow_signal=slow_signal,
        regime_label=regime_label,
        sector_momentum=sector_momentum,
    )
    if delta == 0:
        return composite_score
    out = composite_score + delta
    try:
        _append_jsonl(
            REPO_ROOT / "logs" / "signal_quality_adjustments.jsonl",
            {"symbol": symbol, "delta": delta, "score_before": composite_score, "score_after": out},
        )
    except Exception:
        pass
    return out


def correlation_concentration_risk_multiplier(base: Path | None = None, threshold: float = 2.0) -> float:
    """
    If concentration_risk_score > threshold, return a multiplier < 1.0 for position size.
    Otherwise 1.0.
    """
    data = load_correlation_snapshot(base)
    score = data.get("concentration_risk_score")
    if score is None:
        return 1.0
    if float(score) > threshold:
        return max(0.5, 1.0 - (float(score) - threshold) * 0.1)
    return 1.0
