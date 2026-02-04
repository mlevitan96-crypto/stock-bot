"""
Multi-strategy support for stock-bot.

- equity: Existing UW-driven equity strategy (unchanged logic).
- wheel: Options wheel (CSP -> CC) strategy.
"""

from strategies.context import get_strategy_id, set_strategy_id, strategy_context

__all__ = [
    "get_strategy_id",
    "set_strategy_id",
    "strategy_context",
]
