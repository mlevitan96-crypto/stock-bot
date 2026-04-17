"""
Level-1 Order Flow Imbalance (OFI) from consolidated quote updates.

Implements the standard bid/ask *price and size* event decomposition (Cont–Kukanov
style L1 OFI): at each quote, **e_t** aggregates changes on the bid side (buy-side
book pressure) and **f_t** on the ask side (sell-side book pressure); the increment is

    OFI_t = e_t - f_t

**Bid component e_t** (previous state b⁻ = (p_b⁻, q_b⁻), current b = (p_b, q_b)):

- If p_b > p_b⁻: e_t = q_b  (new best bid level; size at new quote)
- If p_b < p_b⁻: e_t = −q_b⁻  (bid dropped; liquidity removed at old price)
- If p_b = p_b⁻: e_t = q_b − q_b⁻  (depth change at unchanged price)

**Ask component f_t** (symmetric mirror for the ask, a⁻ → a):

- If p_a > p_a⁻: f_t = q_a
- If p_a < p_a⁻: f_t = −q_a⁻
- If p_a = p_a⁻: f_t = q_a − q_a⁻

Positive **OFI_t** indicates net pressure consistent with buyer-initiated flow on L1.
First quote for a symbol produces increment **0** (no prior reference).
"""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class _L1Quote:
    bid_px: float
    bid_sz: float
    ask_px: float
    ask_sz: float


def compute_l1_ofi_increment(
    prev: Optional[_L1Quote],
    bid_px: float,
    bid_sz: float,
    ask_px: float,
    ask_sz: float,
) -> Tuple[float, float, float, bool]:
    """
    Compute (e_bid, f_ask, ofi, updated) for one L1 update.

    Returns ``updated=False`` if the quote is invalid (non-finite or crossed book);
    caller should not advance ``prev`` in that case.
    """
    if prev is None:
        if not _valid_l1(bid_px, bid_sz, ask_px, ask_sz):
            return (0.0, 0.0, 0.0, False)
        return (0.0, 0.0, 0.0, True)

    if not _valid_l1(bid_px, bid_sz, ask_px, ask_sz):
        return (0.0, 0.0, 0.0, False)

    pbp, pbs = prev.bid_px, prev.bid_sz
    pap, pas = prev.ask_px, prev.ask_sz

    # Bid-side event e_t
    if bid_px > pbp:
        e_bid = bid_sz
    elif bid_px < pbp:
        e_bid = -pbs
    else:
        e_bid = bid_sz - pbs

    # Ask-side event f_t (symmetric)
    if ask_px > pap:
        f_ask = ask_sz
    elif ask_px < pap:
        f_ask = -pas
    else:
        f_ask = ask_sz - pas

    ofi = e_bid - f_ask
    return (float(e_bid), float(f_ask), float(ofi), True)


def _valid_l1(bp: float, bs: float, ap: float, sz_a: float) -> bool:
    try:
        if not (bp > 0.0 and ap > 0.0 and ap >= bp):
            return False
        if bs < 0.0 or sz_a < 0.0:
            return False
        if not all(math.isfinite(x) for x in (bp, bs, ap, sz_a)):
            return False
    except Exception:
        return False
    return True


class OFITracker:
    """
    Thread-safe L1 OFI: per-symbol increments from quotes + rolling sums (60s / 300s).

    Wall-clock windows use ``time.monotonic()`` at ingest so windows are stable under
    load (exchange timestamps can be used later for replay alignment).
    """

    def __init__(self, maxlen_ticks_per_symbol: int = 20_000) -> None:
        self._lock = threading.RLock()
        self._maxlen = max(256, int(maxlen_ticks_per_symbol))
        self._prev: Dict[str, _L1Quote] = {}
        # symbol -> deque of (mono_t, ofi_tick); ofi_tick excludes first-quote warmup
        self._hist: Dict[str, Deque[Tuple[float, float]]] = {}

    def on_quote(
        self,
        symbol: str,
        bid_px: float,
        bid_sz: float,
        ask_px: float,
        ask_sz: float,
        *,
        mono_t: Optional[float] = None,
    ) -> float:
        """
        Ingest one NBBO quote; returns the **OFI increment** for this message (0 on first
        valid quote for the symbol or on invalid/crossed data).
        """
        sym = str(symbol or "").upper().strip()
        if not sym:
            return 0.0
        t = float(time.monotonic() if mono_t is None else mono_t)
        bp, bs, ap, a_sz = float(bid_px), float(bid_sz), float(ask_px), float(ask_sz)

        with self._lock:
            prev = self._prev.get(sym)
            e_bid, f_ask, ofi, ok = compute_l1_ofi_increment(prev, bp, bs, ap, a_sz)
            if not ok:
                return 0.0
            cur = _L1Quote(bid_px=bp, bid_sz=bs, ask_px=ap, ask_sz=a_sz)
            self._prev[sym] = cur
            if prev is None:
                return 0.0
            dq = self._hist.get(sym)
            if dq is None:
                dq = deque(maxlen=self._maxlen)
                self._hist[sym] = dq
            dq.append((t, ofi))
            return ofi

    def rolling_sums(self, symbol: str) -> Tuple[float, float]:
        """Return (sum OFI over last 60s, sum over last 300s) for ``symbol``."""
        sym = str(symbol or "").upper().strip()
        if not sym:
            return (0.0, 0.0)
        now = time.monotonic()
        t60 = now - 60.0
        t300 = now - 300.0
        with self._lock:
            dq = self._hist.get(sym)
            if not dq:
                return (0.0, 0.0)
            s60 = 0.0
            s300 = 0.0
            # Iterate oldest→newest for clarity (small deques)
            for ts, tick in dq:
                if ts >= t300:
                    s300 += tick
                if ts >= t60:
                    s60 += tick
        return (float(s60), float(s300))

    def snapshot(self, symbol: str) -> Dict[str, float]:
        """Convenience: last rolling sums plus instantaneous mid/spread if known."""
        sym = str(symbol or "").upper().strip()
        s60, s300 = self.rolling_sums(sym)
        out = {"ofi_l1_roll_60s_sum": s60, "ofi_l1_roll_300s_sum": s300}
        with self._lock:
            q = self._prev.get(sym)
            if q is not None:
                out["l1_bid_px"] = q.bid_px
                out["l1_ask_px"] = q.ask_px
                out["l1_bid_sz"] = q.bid_sz
                out["l1_ask_sz"] = q.ask_sz
        return out
