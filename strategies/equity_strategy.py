"""
Equity strategy: UW-driven equity trading (existing behavior).

This module wraps the main.run_once flow with strategy_id="equity".
No logic changes; only strategy_id tagging.
"""

from typing import Any, Callable


def run(run_once_fn: Callable[[], Any]) -> Any:
    """
    Run equity strategy by invoking run_once under strategy_id=equity.

    Args:
        run_once_fn: The main run_once function (passed to avoid circular import).

    Returns:
        Result of run_once_fn().
    """
    from strategies.context import strategy_context

    with strategy_context("equity"):
        return run_once_fn()
