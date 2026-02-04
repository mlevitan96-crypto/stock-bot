"""
Strategy Comparison Engine: compare equity vs wheel, compute promotion readiness.

Read-only. Does not modify positions or trigger real trading.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence


def compute_sharpe_proxy(pnl_series: Sequence[float]) -> Optional[float]:
    """
    Sharpe-like ratio: mean(pnl) / std(pnl) * sqrt(252) proxy.
    Returns None if insufficient data or zero std.
    """
    if not pnl_series or len(pnl_series) < 2:
        return None
    vals = [float(x) for x in pnl_series]
    mean_pnl = sum(vals) / len(vals)
    variance = sum((x - mean_pnl) ** 2 for x in vals) / (len(vals) - 1)
    std = math.sqrt(variance) if variance > 0 else 0.0
    if std <= 0:
        return 0.0 if mean_pnl >= 0 else -10.0
    return mean_pnl / std


def compute_drawdown(pnl_series: Sequence[float]) -> Optional[float]:
    """
    Max drawdown as fraction of peak cumulative PnL.
    Returns None if insufficient data. Returns 0 if no peak.
    """
    if not pnl_series:
        return None
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in pnl_series:
        cumulative += float(pnl)
        if cumulative > peak:
            peak = cumulative
        if peak > 0:
            dd = (peak - cumulative) / peak
            if dd > max_dd:
                max_dd = dd
        elif cumulative < 0:
            max_dd = 1.0
    return max_dd


def compare_strategies(
    equity_report: dict,
    wheel_report: dict,
    combined_report: dict,
    equity_pnl_series: Optional[List[float]] = None,
    wheel_pnl_series: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Compare equity vs wheel strategies. Returns metrics and promotion_readiness_score.

    Args:
        equity_report: reports/YYYY-MM-DD_stock-bot_equity.json
        wheel_report: reports/YYYY-MM-DD_stock-bot_wheel.json
        combined_report: reports/YYYY-MM-DD_stock-bot_combined.json
        equity_pnl_series: Optional historical daily realized PnL for equity
        wheel_pnl_series: Optional historical daily realized PnL for wheel

    Returns:
        Dict with all comparison fields.
    """
    eq_realized = float(equity_report.get("realized_pnl") or 0)
    wh_realized = float(wheel_report.get("realized_pnl") or 0)
    eq_unrealized = float(equity_report.get("unrealized_pnl") or 0)
    wh_unrealized = float(wheel_report.get("unrealized_pnl") or 0)
    eq_drawdown = equity_report.get("max_drawdown")
    wh_drawdown = wheel_report.get("max_drawdown")

    eq_sharpe = compute_sharpe_proxy(equity_pnl_series or [eq_realized])
    wh_sharpe = compute_sharpe_proxy(wheel_pnl_series or [wh_realized])

    if equity_pnl_series and len(equity_pnl_series) >= 2:
        eq_drawdown = compute_drawdown(equity_pnl_series)
    if wheel_pnl_series and len(wheel_pnl_series) >= 2:
        wh_drawdown = compute_drawdown(wheel_pnl_series)

    eq_win_rate = None
    wh_win_rate = None
    wheel_yield = wheel_report.get("yield_per_period")
    if wheel_yield is not None:
        wheel_yield = float(wheel_yield)
    else:
        cap = float(wheel_report.get("capital_at_risk") or 0)
        prem = float(wheel_report.get("premium_collected") or 0)
        wheel_yield = (prem / cap) if cap > 0 else None

    account_equity = float(combined_report.get("account_equity") or 0)
    eq_cap = sum(float(p.get("market_value") or 0) for p in (equity_report.get("positions_by_symbol") or {}).values())
    wh_cap = sum(float(p.get("market_value") or 0) for p in (wheel_report.get("positions_by_symbol") or {}).values())
    wh_cap += float(wheel_report.get("capital_at_risk") or 0)
    total_cap = eq_cap + wh_cap
    capital_efficiency_equity = (eq_realized + eq_unrealized) / eq_cap if eq_cap > 0 else 0.0
    capital_efficiency_wheel = (wh_realized + wh_unrealized) / wh_cap if wh_cap > 0 else 0.0

    assignment_count = wheel_report.get("assignment_count", 0) or 0
    call_away_count = wheel_report.get("call_away_count", 0) or 0
    total_wheel_events = max(1, assignment_count + call_away_count)
    assignment_health = min(1.0, (call_away_count + 1) / (assignment_count + 1)) if assignment_count >= 0 else 0.5
    if assignment_count == 0 and call_away_count == 0:
        assignment_health = 0.5

    pnl_stability = 1.0
    if wheel_pnl_series and len(wheel_pnl_series) >= 2:
        std = (sum((x - sum(wheel_pnl_series) / len(wheel_pnl_series)) ** 2 for x in wheel_pnl_series) / (len(wheel_pnl_series) - 1)) ** 0.5
        mean_abs = abs(sum(wheel_pnl_series) / len(wheel_pnl_series))
        if mean_abs > 0 and std > 0:
            cv = std / mean_abs
            pnl_stability = max(0, 1.0 - cv)
        else:
            pnl_stability = 1.0

    dd_val = wh_drawdown if wh_drawdown is not None else 0.5
    dd_inverse = max(0, 1.0 - dd_val) if dd_val is not None else 0.5
    sharpe_norm = max(0, min(1.0, (wh_sharpe or 0) * 0.5 + 0.5))
    yield_norm = max(0, min(1.0, (wheel_yield or 0) * 20))

    promotion_readiness_score = round(
        yield_norm * 0.30
        + pnl_stability * 0.20
        + dd_inverse * 0.20
        + sharpe_norm * 0.20
        + assignment_health * 0.10,
        2
    ) * 100
    promotion_readiness_score = max(0, min(100, int(promotion_readiness_score)))

    return {
        "equity_realized_pnl": round(eq_realized, 2),
        "wheel_realized_pnl": round(wh_realized, 2),
        "equity_unrealized_pnl": round(eq_unrealized, 2),
        "wheel_unrealized_pnl": round(wh_unrealized, 2),
        "equity_drawdown": eq_drawdown,
        "wheel_drawdown": wh_drawdown,
        "equity_sharpe_proxy": round(eq_sharpe, 4) if eq_sharpe is not None else None,
        "wheel_sharpe_proxy": round(wh_sharpe, 4) if wh_sharpe is not None else None,
        "equity_win_rate": eq_win_rate,
        "wheel_win_rate": wh_win_rate,
        "wheel_yield_per_period": round(wheel_yield, 6) if wheel_yield is not None else None,
        "capital_efficiency_equity": round(capital_efficiency_equity, 6),
        "capital_efficiency_wheel": round(capital_efficiency_wheel, 6),
        "promotion_readiness_score": promotion_readiness_score,
        "assignment_health": round(assignment_health, 4),
    }


def get_promotion_recommendation(
    comparison: Dict[str, Any],
    promotion_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get promotion recommendation: PROMOTE, WAIT, or DO NOT PROMOTE.
    Uses promotion config if provided; otherwise defaults.
    """
    cfg = promotion_config or {}
    min_score = cfg.get("min_score_to_promote", 75)
    min_weeks = cfg.get("min_weeks_of_data", 4)
    require_positive = cfg.get("require_positive_realized_pnl", True)
    require_dd_below = cfg.get("require_drawdown_below", 0.10)
    require_yield = cfg.get("require_yield_consistency", True)

    score = comparison.get("promotion_readiness_score", 0)
    wh_realized = comparison.get("wheel_realized_pnl", 0) or 0
    wh_drawdown = comparison.get("wheel_drawdown")
    wheel_yield = comparison.get("wheel_yield_per_period")

    reasons = []
    if score < min_score:
        reasons.append("promotion_readiness_score below threshold")
    if require_positive and wh_realized <= 0:
        reasons.append("wheel realized PnL not positive")
    if require_dd_below is not None and wh_drawdown is not None and wh_drawdown > require_dd_below:
        reasons.append("drawdown exceeds limit")
    if require_yield and (wheel_yield is None or wheel_yield <= 0):
        reasons.append("yield not consistent")

    if not reasons:
        recommendation = "PROMOTE"
    elif score >= min_score * 0.6:
        recommendation = "WAIT"
    else:
        recommendation = "DO NOT PROMOTE"

    return {
        "recommendation": recommendation,
        "promotion_readiness_score": score,
        "reasons": reasons,
        "yield_consistency": wheel_yield is not None and wheel_yield > 0,
        "drawdown_risk": wh_drawdown,
        "assignment_behavior": comparison.get("assignment_health"),
        "capital_efficiency": comparison.get("capital_efficiency_wheel"),
        "universe_health": None,
    }
