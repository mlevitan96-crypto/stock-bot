"""
Pillar 4 — Volume Adjusted Mid-Price (VAMP) pegging (shadow / analytics).

VAMP (microstructure mid with size weights):

    VAMP = (bid_price * ask_size + ask_price * bid_size) / (bid_size + ask_size)

When ``bid_size + ask_size == 0``, or inputs are non-finite, VAMP is undefined (``None``)
to avoid division by zero.

``calculate_pegged_limit`` applies a **shadow-only** nudge: when 1m OFI strongly opposes the
resting side, move the theoretical maker limit a small fraction toward the **aggressive**
touch (buy → ask; sell → bid). Neutral / weak OFI returns exactly ``vamp``.
"""
from __future__ import annotations

import math
from typing import Any, Optional, Tuple


def nbbo_from_alpaca_quote(q: Any) -> Tuple[float, float, float, float]:
    """
    Best-effort (bp, bs, ap, as_) from ``alpaca_trade_api`` quote objects across naming variants.
    """
    if q is None:
        return (0.0, 0.0, 0.0, 0.0)

    def _f(name: str, alt: str = "") -> float:
        for k in (name, alt):
            if not k:
                continue
            v = getattr(q, k, None)
            if v is None and isinstance(q, dict):
                v = q.get(k)
            if v is None:
                continue
            try:
                x = float(v)
                return x if math.isfinite(x) else 0.0
            except (TypeError, ValueError):
                continue
        return 0.0

    bp = _f("bp", "bid_price") or _f("bidprice", "bid_price")
    ap = _f("ap", "ask_price") or _f("askprice", "ask_price")
    bs = _f("bs", "bid_size") or _f("bid_size", "bidsize")
    a_s = _f("as", "ask_size") or _f("ask_size", "asksize")
    return (bp, bs, ap, a_s)


class VAMPCalculator:
    """Volume-adjusted mid (VAMP) + optional OFI-aware shadow peg."""

    @staticmethod
    def volume_adjusted_mid(
        bid_price: float,
        bid_size: float,
        ask_price: float,
        ask_size: float,
    ) -> Optional[float]:
        try:
            bs0 = float(bid_size)
            a0 = float(ask_size)
        except (TypeError, ValueError):
            return None
        if not (math.isfinite(bs0) and math.isfinite(a0)):
            return None
        if bs0 < 0.0 or a0 < 0.0:
            return None
        bs = max(0.0, bs0)
        a_s = max(0.0, a0)
        den = bs + a_s
        if den <= 0.0:
            return None
        bp = float(bid_price)
        ap = float(ask_price)
        if not (math.isfinite(bp) and math.isfinite(ap)):
            return None
        if bp <= 0.0 or ap <= 0.0 or ap < bp:
            return None
        num = bp * a_s + ap * bs
        if not math.isfinite(num):
            return None
        v = num / den
        return v if math.isfinite(v) else None

    @staticmethod
    def calculate_pegged_limit(
        side: str,
        vamp: float,
        ofi_1m: float,
        *,
        half_spread: float,
        oppose_abs: float = 500.0,
        nudge_fraction: float = 0.15,
    ) -> float:
        """
        Shadow peg: at VAMP when ``|ofi_1m| < oppose_abs``.

        - **Buy / long:** strong *negative* OFI (sell flow) → nudge **up** toward the ask (aggressive lift).
        - **Sell / short:** strong *positive* OFI (buy flow) → nudge **down** toward the bid.
        """
        v = float(vamp)
        if not math.isfinite(v):
            return v
        hs = max(float(half_spread), 1e-9)
        nudge = min(abs(float(nudge_fraction)) * hs, hs * 0.99)
        thr = max(float(oppose_abs), 0.0)
        o = float(ofi_1m)
        if not math.isfinite(o) or thr <= 0.0:
            return v
        s = str(side or "").lower()
        if s in ("sell", "short"):
            if o > thr:
                return v - nudge
            return v
        # buy / long default
        if o < -thr:
            return v + nudge
        return v
