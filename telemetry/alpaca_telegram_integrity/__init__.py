"""Alpaca-only Telegram + data integrity cycle (droplet-oriented). Read-only on logs."""

from .runner_core import run_integrity_cycle

__all__ = ["run_integrity_cycle"]
