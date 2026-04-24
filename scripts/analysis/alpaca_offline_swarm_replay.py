#!/usr/bin/env python3
"""
Offline Swarm Replay — equities research only.

Loads intraday bars from ``data/research_bars.db`` (see research_fetch_alpaca_bars.py),
walks forward in **New York regular session** only, builds a **synthetic** enrichment vector
from rolling OHLCV (so ``uw_composite_score_v2`` runs without live UW feeds), and runs **three**
weighting / signal variants in parallel with **spread + per-share fees** on round trips.

This does **not** import or modify the live trading loop; it silences ``emit_uw_attribution``
for the process so JSONL logs are not polluted.

Usage:
  PYTHONPATH=. python scripts/analysis/alpaca_offline_swarm_replay.py --db data/research_bars.db --symbols SPY
"""
from __future__ import annotations

import argparse
import math
import sqlite3
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


def _parse_bar_ts(s: str) -> datetime:
    s = str(s).strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_ny_regular_session(ts_utc: datetime) -> bool:
    """NYSE RTH Mon–Fri 09:30–16:00 America/New_York (no entries outside)."""
    local = ts_utc.astimezone(NY)
    if local.weekday() >= 5:
        return False
    m = local.hour * 60 + local.minute
    return (9 * 60 + 30) <= m < (16 * 60)


def _silence_uw_attribution_emit() -> None:
    try:
        import src.uw.uw_attribution as uwa

        uwa.emit_uw_attribution = lambda **kwargs: None  # type: ignore[assignment]
    except Exception:
        pass


def load_bars_from_db(conn: sqlite3.Connection, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT ts_utc, o, h, l, c, v FROM research_bars
        WHERE symbol = ? AND timeframe = ?
        ORDER BY ts_utc ASC
        """,
        (symbol.upper(), timeframe),
    )
    rows = []
    for ts_utc, o, h, l, c, v in cur.fetchall():
        rows.append({"t": ts_utc, "o": float(o), "h": float(h), "l": float(l), "c": float(c), "v": int(v)})
    return rows


def synthetic_enriched(
    closes: List[float],
    volumes: List[int],
    end_idx: int,
    window: int,
) -> Optional[Dict[str, Any]]:
    """Bar-only feature path for offline scoring (not production semantics)."""
    start = max(0, end_idx - window + 1)
    if end_idx - start < 10:
        return None
    wc = closes[start : end_idx + 1]
    wv = volumes[start : end_idx + 1]
    rets: List[float] = []
    for i in range(1, len(wc)):
        den = max(1e-12, abs(wc[i - 1]))
        rets.append((wc[i] - wc[i - 1]) / den)
    if len(rets) < 5:
        return None
    tail = rets[-20:]
    rv20 = math.sqrt(sum(r * r for r in tail) / max(1, len(tail)))
    drift5 = sum(rets[-5:])
    iv_term_skew = max(-1.0, min(1.0, math.tanh(drift5 * 4.0) * 0.35))
    try:
        vm = statistics.mean(wv)
        vs = statistics.pstdev(wv) if len(wv) > 1 else 0.0
    except statistics.StatisticsError:
        vm, vs = float(wv[-1]), 0.0
    vol_z = (float(wv[-1]) - vm) / (vs + 1e-9)
    conviction = max(0.0, min(1.0, 0.45 + 0.12 * vol_z))
    sentiment = "BULLISH" if rets[-1] > 0.0005 else ("BEARISH" if rets[-1] < -0.0005 else "NEUTRAL")
    toxicity = max(0.0, min(1.0, 0.25 + 0.18 * abs(vol_z)))
    smile_slope = max(-0.5, min(0.5, rets[-1] * 12.0))
    net_oi = max(-1.0, min(1.0, vol_z * 0.25))
    return {
        "sentiment": sentiment,
        "conviction": conviction,
        "trade_count": 14,
        "freshness": 1.0,
        "iv_term_skew": iv_term_skew,
        "smile_slope": smile_slope,
        "toxicity": toxicity,
        "event_alignment": 0.35,
        "realized_vol_20d": float(max(0.05, min(1.5, rv20 * 12.0))),
        "beta_vs_spy": 1.05,
        "dark_pool": {"sentiment": "NEUTRAL", "total_notional_1h": 2.5e6, "total_notional": 2.5e6},
        "insider": {"sentiment": "NEUTRAL", "conviction_modifier": 0.0},
        "oi_change": {"net_oi_change": net_oi},
        "motif_staircase": {"detected": False},
        "motif_sweep_block": {"detected": False},
        "motif_burst": {"detected": False},
        "motif_whale": {"detected": False},
    }


def variant_signal(result: Dict[str, Any], variant: str) -> float:
    """
    Map engine output to per-variant scalar used for entry/exit thresholds.

    **Variant A (Base):** final v2 score (default production stack).
    **Variant B (Flow-heavy):** rebalance core: 3× effective weight on ``iv_skew`` and ``oi_change``
    components vs their contribution in the core sum, and **zero** lagging structure proxies
    (``motif_bonus`` + ``smile`` terms in the core reconstruction).
    **Variant C (Costanza):** invert the scale for long-only: ``8 - score_A`` (weak scores → high signal).
    """
    comp = result.get("components") if isinstance(result.get("components"), dict) else {}
    base_s = float(result.get("base_score", result.get("score", 0.0)) or 0.0)
    score_v2 = float(result.get("score", 0.0) or 0.0)
    v2_total = 0.0
    va = result.get("v2_adjustments")
    if isinstance(va, dict):
        v2_total = float(va.get("total", 0.0) or 0.0)
    iv = float(comp.get("iv_skew", 0.0) or 0.0)
    oi = float(comp.get("oi_change", 0.0) or 0.0)
    motif = float(comp.get("motif_bonus", 0.0) or 0.0)
    smile = float(comp.get("smile", 0.0) or 0.0)
    if variant == "A":
        return max(0.0, min(8.0, score_v2))
    if variant == "B":
        # Flow-heavy: +2x incremental on iv_skew & oi_change contributions; strip motif+smile from core.
        core_adj = base_s + 2.0 * (iv + oi) - motif - smile
        return max(0.0, min(8.0, core_adj + v2_total))
    if variant == "C":
        return max(0.0, min(8.0, 8.0 - score_v2))
    return max(0.0, min(8.0, score_v2))


@dataclass
class VariantSim:
    name: str
    position: float = 0.0
    entry_px: float = 0.0
    cum_realized: float = 0.0
    fees_paid: float = 0.0
    trades: int = 0
    wins: int = 0
    peak_eq: float = 0.0
    max_dd: float = 0.0

    def _equity(self, mark_px: float) -> float:
        mtm = self.position * (mark_px - self.entry_px) if self.position else 0.0
        return self.cum_realized + mtm

    def mark_bar(self, close_px: float) -> None:
        eq = self._equity(close_px)
        if eq > self.peak_eq:
            self.peak_eq = eq
        dd = self.peak_eq - eq
        if dd > self.max_dd:
            self.max_dd = dd

    def enter(self, px: float, spread_cost: float, comm: float) -> None:
        self.position = 1.0
        self.entry_px = px + spread_cost + comm
        self.fees_paid += spread_cost + comm
        self.trades += 1

    def exit(self, px: float, spread_cost: float, comm: float) -> None:
        if not self.position:
            return
        exit_net = px - spread_cost - comm
        pnl = self.position * (exit_net - self.entry_px)
        self.cum_realized += pnl
        self.fees_paid += spread_cost + comm
        if pnl > 0:
            self.wins += 1
        self.position = 0.0
        self.entry_px = 0.0


def half_spread_dollars(px: float, spread_bps: float, shares: float) -> float:
    return shares * px * (spread_bps / 10_000.0) * 0.5


def _is_last_rth_bar_of_day(i: int, bars: List[Dict[str, Any]]) -> bool:
    ts_i = _parse_bar_ts(str(bars[i]["t"])).astimezone(NY)
    if i + 1 >= len(bars):
        return True
    ts_n = _parse_bar_ts(str(bars[i + 1]["t"])).astimezone(NY)
    if ts_n.date() != ts_i.date():
        return True
    return not is_ny_regular_session(ts_n)


def run_symbol(
    symbol: str,
    bars: List[Dict[str, Any]],
    *,
    entry_thr: float,
    exit_thr: float,
    spread_bps: float,
    commission_per_share: float,
    window: int,
) -> Dict[str, VariantSim]:
    _silence_uw_attribution_emit()
    import uw_composite_v2 as uw

    closes = [b["c"] for b in bars]
    vols = [b["v"] for b in bars]
    sims = {
        "A": VariantSim("A_Base"),
        "B": VariantSim("B_FlowHeavy"),
        "C": VariantSim("C_Costanza"),
    }
    for i in range(len(bars)):
        ts = _parse_bar_ts(str(bars[i]["t"]))
        px = float(bars[i]["c"])
        rth = is_ny_regular_session(ts)

        enriched = synthetic_enriched(closes, vols, i, window)
        if enriched is None:
            for s in sims.values():
                s.mark_bar(px)
            continue

        result = uw.compute_composite_score_v2(
            symbol,
            enriched,
            regime="NEUTRAL",
            market_context={"volatility_regime": "mid", "spy_overnight_ret": 0.0, "qqq_overnight_ret": 0.0},
            posture_state={"posture": "neutral", "regime_confidence": 0.55},
            expanded_intel={},
            use_adaptive_weights=False,
        )
        if not isinstance(result, dict):
            for s in sims.values():
                s.mark_bar(px)
            continue

        sig_a = variant_signal(result, "A")
        sig_b = variant_signal(result, "B")
        sig_c = variant_signal(result, "C")
        sigs = {"A": sig_a, "B": sig_b, "C": sig_c}

        last_rth = _is_last_rth_bar_of_day(i, bars) if rth else False

        for key, sim in sims.items():
            sig = sigs[key]
            hs_in = half_spread_dollars(px, spread_bps, 1.0)
            comm = commission_per_share

            if rth and sim.position > 0.0 and sig <= exit_thr:
                hs_out = half_spread_dollars(px, spread_bps, 1.0)
                sim.exit(px, hs_out, comm)
            elif rth and sim.position > 0.0 and last_rth:
                hs_out = half_spread_dollars(px, spread_bps, 1.0)
                sim.exit(px, hs_out, comm)
            if rth and sim.position == 0.0 and (not last_rth) and sig >= entry_thr:
                sim.enter(px, hs_in, comm)

            sim.mark_bar(px)

    return sims


def markdown_table(rows: List[Dict[str, Any]]) -> str:
    hdr = "| Variant | Total Trades | Win Rate | Simulated PnL (USD) | Max Drawdown (USD) |"
    sep = "|---------|-------------:|---------:|--------------------:|-------------------:|"
    lines = [hdr, sep]
    for r in rows:
        lines.append(
            f"| {r['name']} | {r['trades']} | {r['win_rate']:.2%} | {r['pnl']:.4f} | {r['max_dd']:.4f} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=REPO / "data" / "research_bars.db")
    ap.add_argument("--symbols", default="SPY", help="Comma-separated; must exist in DB")
    ap.add_argument("--timeframe", default="5Min", help="Must match rows in DB")
    ap.add_argument("--entry-thr", type=float, default=2.7)
    ap.add_argument("--exit-thr", type=float, default=2.0)
    ap.add_argument("--spread-bps", type=float, default=4.0, help="Full bid-ask width in bps; half applied each side")
    ap.add_argument("--commission-per-share", type=float, default=0.0, help="Per share, charged entry+exit (use 0 for typical Alpaca equity $0)")
    ap.add_argument("--window", type=int, default=36, help="Rolling bars for synthetic enrichment")
    args = ap.parse_args()

    if not args.db.is_file():
        print(f"DB not found: {args.db} — run research_fetch_alpaca_bars.py first.", file=sys.stderr)
        return 1

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    print("# Offline Swarm Replay — variant comparison\n")
    conn = sqlite3.connect(str(args.db))
    any_ok = False
    try:
        for sym in symbols:
            bars = load_bars_from_db(conn, sym, args.timeframe)
            if not bars:
                print(f"No bars for {sym} ({args.timeframe}) in {args.db}", file=sys.stderr)
                continue
            any_ok = True
            per = run_symbol(
                sym,
                bars,
                entry_thr=args.entry_thr,
                exit_thr=args.exit_thr,
                spread_bps=args.spread_bps,
                commission_per_share=args.commission_per_share,
                window=args.window,
            )
            out_rows = []
            for k in ("A", "B", "C"):
                s = per[k]
                wr = (s.wins / s.trades) if s.trades else 0.0
                out_rows.append(
                    {
                        "name": s.name,
                        "trades": s.trades,
                        "win_rate": wr,
                        "pnl": s.cum_realized,
                        "max_dd": s.max_dd,
                    }
                )
            print(f"## {sym} ({len(bars)} bars)\n")
            print(markdown_table(out_rows))
            print()
    finally:
        conn.close()

    if not any_ok:
        return 1

    print()
    print(
        f"_Settings:_ spread **{args.spread_bps:g}** bps (half per side), commission **{args.commission_per_share:g}**/share each way, "
        f"entry **≥ {args.entry_thr}**, exit **≤ {args.exit_thr}**, RTH NY only, 1 share notional.\n"
    )
    print("**Note:** Enrichment is **synthetic from OHLCV** so absolute PnL is not predictive of live UW+composite performance; "
          "use this harness to compare **relative** variant behavior under identical price paths.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
