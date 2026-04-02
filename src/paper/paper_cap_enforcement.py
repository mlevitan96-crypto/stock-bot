"""
Paper-only capital caps for offline replay / audit. No broker imports.

Enable with PAPER_CAPS_ENABLED=1. Never call from live AlpacaExecutor order paths.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(float(v), tz=timezone.utc)
    s = str(v).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s.replace(" ", "T")[:32]).astimezone(timezone.utc)
    except Exception:
        return None


def load_paper_caps_from_env() -> Dict[str, Any]:
    def _f(k: str, d: str) -> float:
        try:
            return float(os.environ.get(k, d))
        except ValueError:
            return float(d)

    def _i(k: str, d: str) -> int:
        try:
            return int(os.environ.get(k, d))
        except ValueError:
            return int(d)

    return {
        "enabled": os.environ.get("PAPER_CAPS_ENABLED", "0") == "1",
        "fail_closed": os.environ.get("PAPER_CAP_FAIL_CLOSED", "1") == "1",
        "max_gross_usd": _f("PAPER_CAP_MAX_GROSS_USD", "25000"),
        "max_net_usd": _f("PAPER_CAP_MAX_NET_USD", "20000"),
        "max_per_symbol_usd": _f("PAPER_CAP_MAX_PER_SYMBOL_USD", "5000"),
        "max_orders_per_minute": _i("PAPER_CAP_MAX_ORDERS_PER_MINUTE", "30"),
        "max_new_positions_per_cycle": _i("PAPER_CAP_MAX_NEW_POSITIONS_PER_CYCLE", "6"),
        "hold_minutes_for_exposure": _i("PAPER_CAP_HOLD_MINUTES", "60"),
        "cycle_minutes": _i("PAPER_CAP_CYCLE_MINUTES", "1"),
    }


@dataclass
class _OpenLeg:
    symbol: str
    side: str
    notional_usd: float
    exit_ts: datetime


@dataclass
class PaperCapReplayState:
    """Simulated overlapping exposures for sequential replay."""

    legs: List[_OpenLeg] = field(default_factory=list)
    orders_in_minute: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    accepts_in_cycle: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    total_accepts: int = 0

    def prune(self, now: datetime) -> None:
        self.legs = [L for L in self.legs if L.exit_ts > now]

    def minute_key(self, t: datetime) -> str:
        return t.replace(second=0, microsecond=0).isoformat()

    def cycle_key(self, t: datetime, cycle_minutes: int) -> str:
        cm = max(1, int(cycle_minutes))
        sec = int(t.timestamp())
        return str(sec // (cm * 60))

    def exposures(self) -> Tuple[float, float, Dict[str, float]]:
        gross = 0.0
        net = 0.0
        per_sym: Dict[str, float] = defaultdict(float)
        for L in self.legs:
            gross += abs(L.notional_usd)
            delta = L.notional_usd if L.side == "long" else -L.notional_usd
            net += delta
            per_sym[L.symbol] += delta
        per_abs = {k: abs(v) for k, v in per_sym.items()}
        return gross, net, dict(per_abs)


def pretrade_key(symbol: str, side: str, ts_iso: str, notional: float) -> str:
    raw = f"{symbol}|{side}|{ts_iso}|{round(notional, 6)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def enforce_paper_caps(
    *,
    intent: Dict[str, Any],
    state: PaperCapReplayState,
    caps: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    intent: symbol, side (long/short), intended_notional_usd (>0), ts (datetime)
    Returns (passed, fail_reason_codes, diagnostics).
    """
    caps = caps or load_paper_caps_from_env()
    reasons: List[str] = []
    sym = str(intent.get("symbol") or "").upper().strip()
    side = str(intent.get("side") or "long").lower()
    if side in ("buy", "bull", "bullish"):
        side = "long"
    if side in ("sell", "bear", "bearish"):
        side = "short"
    try:
        n = float(intent.get("intended_notional_usd") or 0.0)
    except (TypeError, ValueError):
        n = 0.0
    now = intent.get("ts")
    if not isinstance(now, datetime):
        now = _parse_ts(intent.get("ts_iso"))
    if now is None:
        if caps.get("fail_closed"):
            return False, ["invalid_intent_ts"], {}
        return True, [], {"warning": "no_ts_skip_caps"}

    if not caps.get("enabled"):
        g, ne, ps = state.exposures()
        return True, [], {"caps_disabled": True, "current_gross_usd": g, "current_net_usd": ne, "per_symbol_usd": ps}

    try:
        state.prune(now)
        hold_m = int(caps.get("hold_minutes_for_exposure") or 60)
        cycle_m = int(caps.get("cycle_minutes") or 1)
        exit_ts = now + timedelta(minutes=hold_m)

        g, ne, per_sym = state.exposures()
        new_gross = g + abs(n)
        delta = n if side == "long" else -n
        new_net = ne + delta
        per_after = dict(per_sym)
        per_after[sym] = per_after.get(sym, 0.0) + delta
        sym_exposure_after = abs(per_after.get(sym, 0.0))

        mk = state.minute_key(now)
        ck = state.cycle_key(now, cycle_m)

        state.orders_in_minute[mk] += 1
        if state.orders_in_minute[mk] > int(caps["max_orders_per_minute"]):
            reasons.append("max_orders_per_minute")

        if new_gross > float(caps["max_gross_usd"]) + 1e-9:
            reasons.append("max_gross_usd")
        if abs(new_net) > float(caps["max_net_usd"]) + 1e-9:
            reasons.append("max_net_usd")
        if sym_exposure_after > float(caps["max_per_symbol_usd"]) + 1e-9:
            reasons.append("max_per_symbol_usd")

        if not reasons and state.accepts_in_cycle[ck] >= int(caps["max_new_positions_per_cycle"]):
            reasons.append("max_new_positions_per_cycle")

        diag = {
            "current_gross_usd": round(g, 6),
            "current_net_usd": round(ne, 6),
            "per_symbol_usd": {k: round(v, 6) for k, v in per_sym.items()},
            "intended_notional_usd": round(n, 6),
            "would_be_gross_usd": round(new_gross, 6),
            "would_be_net_usd": round(new_net, 6),
        }
        ok = len(reasons) == 0
        if ok:
            state.legs.append(_OpenLeg(symbol=sym, side=side, notional_usd=abs(n), exit_ts=exit_ts))
            state.accepts_in_cycle[ck] += 1
            state.total_accepts += 1
        return ok, reasons, diag
    except Exception as e:
        if caps.get("fail_closed"):
            return False, [f"cap_eval_error:{e}"], {}
        return True, [], {"error": str(e)}


def append_paper_cap_log(row: Dict[str, Any]) -> None:
    path = _repo_root() / "logs" / "paper_cap_decisions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")
