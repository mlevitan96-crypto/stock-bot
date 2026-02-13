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
UW_EDGE_REALIZATION_BOOST = 0.15
UW_EDGE_SUPPRESSION_PENALTY = 0.1


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
    action_applied: "" | "penalize" | "penalize_strong" | "boost" | "boost_strong"
    """
    data = load_survivorship_adjustments(base)
    for adj in data.get("adjustments") or []:
        if adj.get("symbol") == symbol:
            action = (adj.get("action") or "").strip().lower()
            delta = 0.0
            if action == "penalize_strong":
                delta = adj.get("score_penalty", SURVIVORSHIP_PENALTY_STRONG) or SURVIVORSHIP_PENALTY_STRONG
                delta = -abs(delta)
            elif action == "penalize":
                delta = -SURVIVORSHIP_PENALTY
            elif action == "boost_strong":
                delta = adj.get("score_boost", SURVIVORSHIP_BOOST_STRONG) or SURVIVORSHIP_BOOST_STRONG
            elif action == "boost":
                delta = SURVIVORSHIP_BOOST
            if delta != 0:
                out = composite_score + delta
                _append_jsonl(SURVIVORSHIP_LOG, {"symbol": symbol, "action": action, "delta": delta, "score_before": composite_score, "score_after": out})
                return out, action
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
    Uses uw_signal_quality_score, uw_edge_realization_rate, uw_edge_suppression_rate and per-candidate data if present.
    Stronger boosts: quality >= 0.6 -> +0.75; edge_suppression > 0.5 -> allow let-it-breathe, override displacement if score gap > 0.1.
    """
    data = load_uw_root_cause_latest(base)
    details: dict[str, Any] = {}
    delta = 0.0
    quality = data.get("uw_signal_quality_score")
    supp = data.get("uw_edge_suppression_rate")
    real = data.get("uw_edge_realization_rate")

    if quality is not None:
        q = float(quality)
        if q >= 0.6:
            delta += UW_QUALITY_BOOST_STRONG
            details["uw_quality_boost_strong"] = True
            details["allow_displacement_override"] = True
            details["allow_max_positions_override"] = True
        else:
            delta += q * UW_QUALITY_WEIGHT
    if real is not None and real > 0.5:
        delta += UW_EDGE_REALIZATION_BOOST
    if supp is not None and supp > 0.5:
        delta -= UW_EDGE_SUPPRESSION_PENALTY
        details["uw_edge_suppression_rate"] = supp
        details["allow_let_it_breathe"] = True
        details["override_displacement_if_score_gap"] = 0.1

    for c in data.get("candidates") or []:
        if c.get("symbol") == symbol:
            details["candidate"] = c
            break
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
