"""
PDT Warden (scaffold) — reads risk limits from config and account/tier facts from stream_feed.

Rolling 5-business-day day-trade counts are broker-dependent; Alpaca has deprecated some account
fields. Callers should pass ``rolling_5d_day_trades`` when known (e.g. from Activity API / state
file) until a full implementation lands.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from src.alpaca.flow_toxicity_gate import entry_blocked_by_vpin_ofi
from src.alpaca.stream_feed import (
    account_data_tier_label,
    fetch_alpaca_account,
    resolve_stream_feed,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_risk_profile_path() -> Path:
    return _repo_root() / "config" / "alpaca_risk_profile.json"


@dataclass(frozen=True)
class AlpacaRiskProfile:
    pdt_mode: str
    min_equity_threshold: float
    rolling_5d_day_trade_limit: int
    wash_sale_buffer_days: int

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "AlpacaRiskProfile":
        return AlpacaRiskProfile(
            pdt_mode=str(data.get("pdt_mode", "strict")).strip().lower(),
            min_equity_threshold=float(data.get("min_equity_threshold", 25_000)),
            rolling_5d_day_trade_limit=int(data.get("rolling_5d_day_trade_limit", 3)),
            wash_sale_buffer_days=int(data.get("wash_sale_buffer_days", 31)),
        )


def load_alpaca_risk_profile(path: Optional[os.PathLike[str] | str] = None) -> AlpacaRiskProfile:
    p = Path(path) if path else _default_risk_profile_path()
    with open(p, encoding="utf-8") as f:
        return AlpacaRiskProfile.from_json(json.load(f))


def _parse_equity(account: Dict[str, Any]) -> float:
    for key in ("equity", "last_equity"):
        raw = account.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return 0.0


def _infer_rolling_day_trades(account: Dict[str, Any]) -> Optional[int]:
    """Return count only when the account payload exposes a usable integer field."""
    for key in ("daytrade_count", "day_trade_count", "day_trades_in_rolling_window"):
        raw = account.get(key)
        if raw is None:
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    return None


class PDTWarden:
    """
    Stub gate: uses ``config/alpaca_risk_profile.json``, account JSON from ``stream_feed``, and
    optional rolling day-trade count. ``data_tier`` / resolved feeds come from the same module
    used for SIP/IEX selection.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        trading_base_url: str,
        *,
        risk_profile_path: Optional[os.PathLike[str] | str] = None,
        rolling_5d_day_trades: Optional[int] = None,
    ) -> None:
        self._key = api_key
        self._secret = api_secret
        self._base = trading_base_url
        self._profile = load_alpaca_risk_profile(risk_profile_path)
        self._rolling_override = rolling_5d_day_trades
        self._cached_account: Optional[Dict[str, Any]] = None
        self._cached_tier: Optional[str] = None
        self._cached_feed_meta: Dict[str, Any] = {}

    def refresh_account(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        acct, err = fetch_alpaca_account(self._key, self._secret, self._base)
        self._cached_account = acct
        self._cached_tier = account_data_tier_label(acct) if acct else None
        _, _, meta = resolve_stream_feed(self._key, self._secret, trading_base_url=self._base)
        self._cached_feed_meta = dict(meta)
        return acct, err

    @property
    def data_tier(self) -> Optional[str]:
        if self._cached_tier is None and self._cached_account is None:
            self.refresh_account()
        return self._cached_tier

    def resolved_feed_meta(self) -> Dict[str, Any]:
        if not self._cached_feed_meta:
            self.refresh_account()
        return dict(self._cached_feed_meta)

    def can_trade(self, *, rolling_5d_day_trades: Optional[int] = None) -> bool:
        if self._profile.pdt_mode not in ("strict", "on", "true", "1"):
            return True

        acct, err = self.refresh_account()
        if err or not acct:
            return False

        equity = _parse_equity(acct)
        if equity >= self._profile.min_equity_threshold:
            return True

        count = rolling_5d_day_trades
        if count is None:
            count = self._rolling_override
        if count is None:
            inferred = _infer_rolling_day_trades(acct)
            count = inferred if inferred is not None else 0

        return count < self._profile.rolling_5d_day_trade_limit


def toxicity_blocks_entry(row: Mapping[str, Any], *, cfg: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[float]]:
    """Delegate to VPIN-ofi proxy (Sterling/Chen flow-toxicity lens)."""
    blocked, reason, spike = entry_blocked_by_vpin_ofi(row, cfg=cfg)
    return blocked, reason, spike


def allow_v2_threshold_relaxation(
    *,
    current_threshold: float,
    proposed_threshold: float,
    warden: PDTWarden,
    rolling_5d_day_trades: Optional[int] = None,
) -> Tuple[bool, str]:
    """
    Lowering the V2 probability threshold **increases** approval frequency (Bayesian / empirical
    tuning). Under PDT pressure that relaxation is blocked (Vane hard gate).
    """
    if proposed_threshold >= float(current_threshold) - 1e-12:
        return True, "no_relaxation_or_tightening_only"
    if not warden.can_trade(rolling_5d_day_trades=rolling_5d_day_trades):
        return False, "pdt_blocks_v2_threshold_relaxation"
    return True, "pdt_ok_v2_relaxation"
