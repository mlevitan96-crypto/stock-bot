"""
Strategy context: thread-local strategy_id for telemetry and order tagging.
"""

from contextvars import ContextVar
from typing import Optional

_strategy_id: ContextVar[Optional[str]] = ContextVar("strategy_id", default="equity")


def get_strategy_id() -> str:
    """Current strategy_id (default: equity)."""
    return _strategy_id.get() or "equity"


def set_strategy_id(sid: str) -> None:
    """Set current strategy_id."""
    _strategy_id.set(sid)


class strategy_context:
    """Context manager to run code under a given strategy_id."""

    def __init__(self, sid: str):
        self.sid = sid
        self._token = None

    def __enter__(self):
        self._token = _strategy_id.set(self.sid)
        return self

    def __exit__(self, *args):
        if self._token is not None:
            _strategy_id.reset(self._token)
        return False
