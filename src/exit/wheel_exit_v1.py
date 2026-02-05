"""Wheel exit policy v1: time + premium decay driven."""


def should_exit(position, market_context):
    """
    Wheel exits are time + premium decay driven.

    Args:
        position: Position object with days_to_expiry, premium_captured
        market_context: Market context (unused in v1)

    Returns:
        (bool, str|None): (should_exit, reason or None)
    """
    # Wheel exits are time + premium decay driven
    if position.days_to_expiry <= 3:
        return True, "expiry_close"
    if position.premium_captured >= 0.75:
        return True, "premium_target_hit"
    return False, None
