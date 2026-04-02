#!/usr/bin/env python3
"""
Offline 1m-bar entry fill simulator for execution policy comparison.

NO broker / executor imports. Read-only JSONL bars + executed trade rows.

Policies (fixed, no tuning beyond TTL grid {1,2,3} for P1/P2):
  P0 MARKETABLE: next_bar_open + sign(side) * 0.5 * spread_proxy(decision_bar)
  P1 PASSIVE_MID: limit = decision_bar_close; fill first subsequent bar that touches
  P2 PASSIVE_THEN_CROSS: P1 then if unfilled, cross at open(bar after TTL wait) + sign * 0.5 * spread_proxy(that bar)

spread_proxy_usd = max(0.01, 0.10 * (high - low))  # same units as OHLC ($/share)
"""

from __future__ import annotations

import json
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]


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


def load_bars_jsonl(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Same shape as run_blocked_why_pipeline.load_bars — stdlib + pathlib only."""
    out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = payload.get("data") or {}
            bars = data.get("bars") or {}
            for sym, arr in bars.items():
                if not isinstance(arr, list):
                    continue
                su = str(sym).upper()
                for b in arr:
                    if not isinstance(b, dict):
                        continue
                    t = _parse_ts(b.get("t"))
                    if t is None:
                        continue
                    try:
                        o, h, low, c = float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    out[su].append({"t": t, "o": o, "h": h, "l": low, "c": c, "v": int(b.get("v") or 0)})
    for sym in out:
        out[sym].sort(key=lambda x: x["t"])
    return dict(out)


def spread_proxy_usd(bar: Dict[str, Any]) -> float:
    return max(0.01, 0.10 * (float(bar["h"]) - float(bar["l"])))


def _sign_entry(is_long: int) -> int:
    return 1 if is_long else -1


def decision_bar_index(bars: List[Dict[str, Any]], decision_ts: datetime) -> int:
    """1m bar open time == minute floor UTC of decision."""
    fk = decision_ts.astimezone(timezone.utc).replace(second=0, microsecond=0)
    times = [b["t"] for b in bars]
    i = bisect_left(times, fk)
    if i < len(times) and times[i] == fk:
        return i
    if i > 0:
        return i - 1
    return 0


def recompute_realized_pnl_usd(
    *,
    entry_fill: float,
    exit_price: float,
    qty: float,
    is_long: bool,
) -> float:
    if qty <= 0 or entry_fill <= 0 or exit_price <= 0:
        return float("nan")
    if is_long:
        return (exit_price - entry_fill) * qty
    return (entry_fill - exit_price) * qty


def slippage_vs_market_proxy_per_share(
    *,
    fill_price: float,
    decision_close: float,
    is_long: bool,
) -> float:
    """Positive = adverse vs decision_bar close."""
    if is_long:
        return fill_price - decision_close
    return decision_close - fill_price


def simulate_marketable(
    bars: List[Dict[str, Any]],
    decision_idx: int,
    is_long: bool,
) -> Tuple[str, Optional[datetime], Optional[float], Dict[str, Any]]:
    if decision_idx < 0 or decision_idx + 1 >= len(bars):
        return "NO_FILL", None, None, {"reason": "no_next_bar"}
    dec = bars[decision_idx]
    nxt = bars[decision_idx + 1]
    sp = spread_proxy_usd(dec)
    fp = float(nxt["o"]) + _sign_entry(is_long) * 0.5 * sp
    meta = {"spread_proxy_decision_bar": sp, "decision_bar_idx": decision_idx, "fill_bar_idx": decision_idx + 1}
    return "FILLED", nxt["t"], fp, meta


def simulate_passive_mid(
    bars: List[Dict[str, Any]],
    decision_idx: int,
    is_long: bool,
    ttl_minutes: int,
) -> Tuple[str, Optional[datetime], Optional[float], Dict[str, Any]]:
    if decision_idx < 0 or decision_idx >= len(bars):
        return "NO_FILL", None, None, {"reason": "bad_decision_idx"}
    limit = float(bars[decision_idx]["c"])
    ttl = max(1, int(ttl_minutes))
    for k in range(1, ttl + 1):
        j = decision_idx + k
        if j >= len(bars):
            return "NO_FILL", None, None, {"reason": "ran_out_of_bars", "limit": limit}
        b = bars[j]
        if is_long:
            if float(b["l"]) <= limit + 1e-12:
                return "FILLED", b["t"], limit, {"limit": limit, "fill_bar_idx": j}
        else:
            if float(b["h"]) >= limit - 1e-12:
                return "FILLED", b["t"], limit, {"limit": limit, "fill_bar_idx": j}
    return "NO_FILL", None, None, {"reason": "ttl_exhausted", "limit": limit}


def simulate_passive_then_cross(
    bars: List[Dict[str, Any]],
    decision_idx: int,
    is_long: bool,
    ttl_minutes: int,
) -> Tuple[str, Optional[datetime], Optional[float], Dict[str, Any]]:
    st, fts, fp, meta = simulate_passive_mid(bars, decision_idx, is_long, ttl_minutes)
    if st == "FILLED":
        meta = {**meta, "leg": "passive"}
        return st, fts, fp, meta
    ttl = max(1, int(ttl_minutes))
    cross_idx = decision_idx + ttl + 1
    if cross_idx >= len(bars):
        return "NO_FILL", None, None, {**meta, "reason": "no_cross_bar"}
    b = bars[cross_idx]
    sp = spread_proxy_usd(b)
    fill_px = float(b["o"]) + _sign_entry(is_long) * 0.5 * sp
    meta2 = {
        **meta,
        "leg": "cross",
        "cross_bar_idx": cross_idx,
        "spread_proxy_cross_bar": sp,
    }
    return "FILLED", b["t"], fill_px, meta2


def normalize_long(row: Dict[str, Any]) -> Optional[bool]:
    ps = str(row.get("position_side") or "").lower()
    if ps in ("long",):
        return True
    if ps in ("short",):
        return False
    s = str(row.get("side") or "").lower()
    if s in ("buy", "long"):
        return True
    if s in ("sell", "short"):
        return False
    return None


def simulate_trade_policies(
    row: Dict[str, Any],
    bars_map: Dict[str, List[Dict[str, Any]]],
    *,
    exit_price: float,
    qty: float,
) -> List[Dict[str, Any]]:
    """One row from exit_attribution + realized exit_price/qty → per-policy outcomes."""
    sym = str(row.get("symbol") or "").upper()
    decision_ts = _parse_ts(row.get("entry_timestamp"))
    is_long = normalize_long(row)
    out: List[Dict[str, Any]] = []
    if decision_ts is None or is_long is None:
        return out
    bars = bars_map.get(sym) or []
    if not bars:
        return out
    di = decision_bar_index(bars, decision_ts)
    dec_bar = bars[di] if 0 <= di < len(bars) else None
    if dec_bar is None:
        return out
    decision_close = float(dec_bar["c"])
    half_spread = 0.5 * spread_proxy_usd(dec_bar)

    def pack(policy_id: str, ttl: Optional[int], st: str, fts: Optional[datetime], fp: Optional[float], meta: Dict[str, Any]) -> Dict[str, Any]:
        slip = None
        if fp is not None:
            slip = slippage_vs_market_proxy_per_share(
                fill_price=fp, decision_close=decision_close, is_long=is_long
            )
        pnl = None
        if st == "FILLED" and fp is not None:
            pnl = recompute_realized_pnl_usd(
                entry_fill=fp, exit_price=exit_price, qty=qty, is_long=is_long
            )
        return {
            "policy_id": policy_id,
            "ttl_minutes": ttl,
            "fill_status": st,
            "fill_ts": fts.isoformat() if fts else None,
            "fill_price": fp,
            "slippage_vs_market_proxy_per_share": slip,
            "entry_cost_proxy_half_spread_per_share": half_spread,
            "sim_pnl_usd": pnl,
            "meta": meta,
        }

    # P0
    st0, t0, p0, m0 = simulate_marketable(bars, di, is_long)
    out.append(pack("P0_MARKETABLE", None, st0, t0, p0, m0))

    for ttl in (1, 2, 3):
        st1, t1, p1, m1 = simulate_passive_mid(bars, di, is_long, ttl)
        out.append(pack("P1_PASSIVE_MID", ttl, st1, t1, p1, m1))
        st2, t2, p2, m2 = simulate_passive_then_cross(bars, di, is_long, ttl)
        out.append(pack("P2_PASSIVE_THEN_CROSS", ttl, st2, t2, p2, m2))

    return out


def aggregate_metrics(
    policy_results: List[Dict[str, Any]],
    *,
    baseline_p0_pnls: List[float],
) -> Dict[str, Any]:
    """One policy across trades; baseline_p0_pnls[i] = P0 sim pnl for trade i (opportunity if this policy NO_FILL)."""
    filled_pnls: List[float] = []
    slips: List[float] = []
    no_fill = 0
    opp_loss = 0.0
    for i, r in enumerate(policy_results):
        if r.get("fill_status") != "FILLED":
            no_fill += 1
            if i < len(baseline_p0_pnls):
                try:
                    bp = float(baseline_p0_pnls[i])
                    if bp == bp:
                        opp_loss += bp
                except (TypeError, ValueError):
                    pass
            continue
        p = r.get("sim_pnl_usd")
        if p is not None and p == p:
            filled_pnls.append(float(p))
        s = r.get("slippage_vs_market_proxy_per_share")
        if s is not None and s == s:
            slips.append(float(s))

    def _p05(xs: List[float]) -> Optional[float]:
        if not xs:
            return None
        s = sorted(xs)
        k = max(0, int(0.05 * (len(s) - 1)))
        return round(s[k], 6)

    def _mdd(xs: List[float]) -> float:
        if not xs:
            return 0.0
        cum = 0.0
        peak = 0.0
        mdd = 0.0
        for x in xs:
            cum += x
            peak = max(peak, cum)
            mdd = min(mdd, cum - peak)
        return round(mdd, 6)

    n = len(policy_results)
    mean_pnl = sum(filled_pnls) / len(filled_pnls) if filled_pnls else None
    med_pnl = __import__("statistics").median(filled_pnls) if filled_pnls else None
    return {
        "filled_trade_count": len(filled_pnls),
        "fill_rate": round(len(filled_pnls) / n, 6) if n else 0.0,
        "mean_pnl_usd": round(mean_pnl, 6) if mean_pnl is not None else None,
        "median_pnl_usd": round(float(med_pnl), 6) if med_pnl is not None else None,
        "p05_pnl_per_trade": _p05(filled_pnls),
        "max_drawdown_proxy_usd": _mdd(filled_pnls),
        "mean_slippage_vs_market_proxy_per_share": round(sum(slips) / len(slips), 8) if slips else None,
        "no_fill_count": no_fill,
        "opportunity_loss_sum_baseline_p0_usd": round(opp_loss, 6),
    }


if __name__ == "__main__":
    print(json.dumps({"module": "exec_mode_fill_simulator", "repo": str(REPO)}))
