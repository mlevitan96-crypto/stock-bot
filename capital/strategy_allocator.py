"""
Fixed strategy capital allocator. Single source of truth for 25% wheel / 75% equity.
No strategy may consume the other's capital. Enforced at order time.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

log = logging.getLogger(__name__)

# Default allocation when config missing
DEFAULT_WHEEL_PCT = 25
DEFAULT_EQUITY_PCT = 75


def _load_capital_config(config: Optional[dict] = None) -> dict:
    """Load capital_allocation from config or strategies.yaml. Never raises."""
    if config and isinstance(config.get("capital_allocation"), dict):
        return config["capital_allocation"]
    try:
        import yaml
        path = Path("config") / "strategies.yaml"
        if not path.is_absolute():
            path = (Path(__file__).resolve().parents[2] / path).resolve()
        if path.exists():
            with path.open() as f:
                data = yaml.safe_load(f) or {}
            cap = data.get("capital_allocation") or {}
            if isinstance(cap, dict):
                return cap
    except Exception as e:
        log.debug("Load capital_allocation: %s", e)
    return {}


def _pct_for_strategy(cap_config: dict, strategy_id: str) -> float:
    """Return allocation_pct for strategy (0–100). Default: wheel 25, equity 75."""
    strategies = cap_config.get("strategies") or {}
    s = strategies.get(strategy_id) or strategies.get(strategy_id.lower())
    if s and isinstance(s.get("allocation_pct"), (int, float)):
        return float(s["allocation_pct"])
    if strategy_id == "wheel":
        return float(DEFAULT_WHEEL_PCT)
    if strategy_id == "equity":
        return float(DEFAULT_EQUITY_PCT)
    return 0.0


def get_wheel_used_from_state(wheel_state: dict) -> float:
    """Sum notional of all open CSPs in wheel_state. Used for wheel capital accounting."""
    open_csps = wheel_state.get("open_csps") or {}
    total = 0.0
    for symbol, entries in open_csps.items():
        for p in entries if isinstance(entries, list) else [entries]:
            if isinstance(p, dict):
                total += float(p.get("strike", 0) or 0) * 100 * int(p.get("qty", 1) or 1)
    return total


def can_allocate(
    strategy_id: str,
    required_notional: float,
    total_equity: float,
    wheel_state: Optional[dict] = None,
    capital_config: Optional[dict] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Single source of truth: can this strategy use required_notional?
    total_equity: from api.get_account().equity.
    wheel_state: from state/wheel_state.json (for wheel_used). If None, wheel_used=0.
    capital_config: optional capital_allocation dict; else loaded from config.

    Returns (allowed: bool, details: dict).
    details: strategy_budget, strategy_used, strategy_available, required_notional, decision_reason.
    """
    cap = capital_config or _load_capital_config()
    pct = _pct_for_strategy(cap, strategy_id) / 100.0
    strategy_budget = total_equity * pct
    strategy_used = 0.0
    if strategy_id == "wheel" and wheel_state is not None:
        strategy_used = get_wheel_used_from_state(wheel_state)
    strategy_available = max(0.0, strategy_budget - strategy_used)
    allowed = required_notional <= strategy_available and required_notional >= 0
    decision_reason = "ok" if allowed else "allocation_exceeded"
    details = {
        "strategy_budget": round(strategy_budget, 2),
        "strategy_used": round(strategy_used, 2),
        "strategy_available": round(strategy_available, 2),
        "required_notional": round(required_notional, 2),
        "decision_reason": decision_reason,
        "total_equity": round(total_equity, 2),
        "allocation_pct": pct * 100,
    }
    return (allowed, details)
