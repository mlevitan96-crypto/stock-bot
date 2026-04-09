#!/usr/bin/env python3
"""
Alpaca Self-Healing Supervisor — architectural skeleton (Kraken parity target).

NOT WIRED into main.py or deploy_supervisor yet. Intended to converge on Kraken-style
``self_healing_supervisor`` behavior: quarantine bad symbols, orphan cleanup, SAFE MODE under stress.

Design notes (implementation TBD):
- **UW telemetry quarantine:** Symbols whose recent ``entry_uw`` lacks finite ``earnings_proximity``
  or ``sentiment_score`` (same contract as ``telemetry/alpaca_zero_tolerance_tripwire.py``) are
  candidates for a time-boxed quarantine list (e.g. ``state/alpaca_uw_quarantine.json``) so the
  engine skips new entries until telemetry recovers. Escalation: pair with governance Telegram.
- **Rate-limit SAFE MODE:** On Alpaca ``429`` / classified ``RATE_LIMIT`` (see ``alpaca_client.ErrorType``),
  flip a process-local or persisted SAFE MODE flag, widen backoff, pause discretionary order flow,
  and log structured rows to ``logs/self_healing.jsonl`` for SRE review.
- **Orphan cleanup:** Reconcile broker open orders vs internal position intent; cancel stale client
  order IDs; align with existing integrity tools (truth warehouse, strict gate).

This module exposes typed stubs only; callers will be added in a follow-on integration pass.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Sequence

logger = logging.getLogger(__name__)


class HealingAction(str, Enum):
    QUARANTINE_SYMBOL = "quarantine_symbol"
    CLEAR_QUARANTINE = "clear_quarantine"
    ENTER_SAFE_MODE = "enter_safe_mode"
    EXIT_SAFE_MODE = "exit_safe_mode"
    ORPHAN_CLEANUP = "orphan_cleanup"
    NOOP = "noop"


@dataclass
class QuarantineRecord:
    symbol: str
    reason: str
    quarantined_at_utc: str
    expires_at_utc: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafeModeState:
    active: bool = False
    reason: str = ""
    entered_at_utc: Optional[str] = None
    rate_limit_events_1h: int = 0


class AlpacaBrokerPort(Protocol):
    """Minimal broker surface for future orphan cleanup (stub)."""

    def list_open_orders(self) -> Sequence[Any]: ...
    def cancel_order(self, order_id: str) -> None: ...


class SelfHealingSupervisor:
    """
    Central coordinator (skeleton). Future: periodic tick from supervisor or main loop.
    """

    def __init__(self) -> None:
        self._quarantine: Dict[str, QuarantineRecord] = {}
        self._safe_mode = SafeModeState()

    @property
    def safe_mode(self) -> SafeModeState:
        return self._safe_mode

    def evaluate_uw_telemetry_for_symbol(self, symbol: str, entry_uw: Optional[Dict[str, Any]]) -> HealingAction:
        """
        If entry_uw is missing required finite scalars, recommend quarantine (no side effects here).
        """
        _ = symbol.upper()
        if not isinstance(entry_uw, dict):
            return HealingAction.QUARANTINE_SYMBOL
        ep = entry_uw.get("earnings_proximity")
        ss = entry_uw.get("sentiment_score")
        if ep is None or ss is None:
            return HealingAction.QUARANTINE_SYMBOL
        try:
            float(ep)
            float(ss)
        except (TypeError, ValueError):
            return HealingAction.QUARANTINE_SYMBOL
        return HealingAction.NOOP

    def on_alpaca_rate_limit(self, detail: str = "") -> HealingAction:
        """Signal from Alpaca client on 429; future: persist SAFE MODE + backoff policy."""
        logger.warning("SelfHealingSupervisor: rate limit observed — SAFE MODE stub (%s)", detail[:200])
        self._safe_mode.active = True
        self._safe_mode.reason = "rate_limit"
        self._safe_mode.entered_at_utc = datetime.now(timezone.utc).isoformat()
        self._safe_mode.rate_limit_events_1h += 1
        return HealingAction.ENTER_SAFE_MODE

    def quarantine_symbol(self, symbol: str, reason: str, *, ttl_sec: Optional[int] = None) -> None:
        """Placeholder: will persist quarantine + append self_healing.jsonl."""
        sym = symbol.upper().strip()
        now = datetime.now(timezone.utc).isoformat()
        exp: Optional[str] = None
        if ttl_sec is not None:
            exp = (datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)).isoformat()
        self._quarantine[sym] = QuarantineRecord(
            symbol=sym, reason=reason, quarantined_at_utc=now, expires_at_utc=exp
        )

    def list_quarantined_symbols(self) -> List[str]:
        return sorted(self._quarantine.keys())

    def run_orphan_cleanup_stub(self, _broker: Optional[AlpacaBrokerPort] = None) -> List[str]:
        """Placeholder: return would-be actions; no broker I/O."""
        return []


_default_supervisor: Optional[SelfHealingSupervisor] = None


def get_self_healing_supervisor() -> SelfHealingSupervisor:
    global _default_supervisor
    if _default_supervisor is None:
        _default_supervisor = SelfHealingSupervisor()
    return _default_supervisor
