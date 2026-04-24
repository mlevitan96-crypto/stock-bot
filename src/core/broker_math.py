"""Broker reality helpers for side-aware Alpaca preflight."""
from __future__ import annotations

from typing import Any, Tuple


def required_buying_power(notional: float, side: str, *, short_margin_multiplier: float = 1.5) -> float:
    """Return local buying-power requirement for the order side."""
    value = abs(float(notional))
    return value * float(short_margin_multiplier) if str(side or "").lower() in ("sell", "short") else value


def validate_buying_power(
    *,
    notional: float,
    side: str,
    buying_power: float,
    short_margin_multiplier: float = 1.5,
) -> Tuple[bool, str]:
    """Fail closed on invalid BP and apply short margin to sell/short entries."""
    try:
        bp = float(buying_power)
    except (TypeError, ValueError):
        return False, "invalid_buying_power"
    if bp <= 0:
        return False, "invalid_buying_power"
    required = required_buying_power(
        notional,
        side,
        short_margin_multiplier=short_margin_multiplier,
    )
    if required > bp:
        return False, "insufficient_buying_power"
    return True, "buying_power_ok"


def validate_short_asset(asset: Any, *, htb_override: bool = False) -> Tuple[bool, str]:
    """Require Alpaca shortable and easy-to-borrow for short entries."""
    shortable = bool(getattr(asset, "shortable", False))
    if not shortable:
        return False, "asset_not_shortable"
    easy_to_borrow = bool(getattr(asset, "easy_to_borrow", False))
    if not easy_to_borrow and not htb_override:
        return False, "asset_hard_to_borrow"
    if not easy_to_borrow and htb_override:
        return True, "short_asset_ok_htb_override"
    return True, "short_asset_ok"
