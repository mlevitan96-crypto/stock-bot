#!/usr/bin/env python3
"""
Apex omni-parameter sweep: strict-epoch exit cohort vs Alpaca 1m marks + adversarial friction.

**Quant:** Counterfactual USD PnL by shifting entry/exit on 1m closes (``alpaca_bars.jsonl`` first).
**Data engineer:** ``--fetch-bars-live`` merges missing minute marks via Alpaca REST (cached per symbol × ET day).

**Adversarial:** Default 2 bps × |qty × entry_px| on every grid cell except the reference cell:
``entry_delay_min==0``, ``exit_live``, ``alpha11_min_flow_floor==0.85`` (weakest filter / live timing only).

**Institutional metrics:** Markouts (T+1m / T+5m), capital velocity, displacement vs EOD shadow,
edge ratio (mean MFE / mean MAE), liquidity fill ratio.

Usage:
  PYTHONPATH=. python3 scripts/ml/apex_omni_parameter_sweep.py --root /root/stock-bot \\
    [--fetch-bars-live]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START  # noqa: E402
from src.governance.canonical_trade_count import iter_harvester_era_exit_records_for_csv  # noqa: E402

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    _ET = None

_TID_ENTRY_TS = re.compile(r"^open_[A-Z0-9]+_(.+)$")

# Reference grid cell: live timing + weakest UW floor (no adversarial friction).
REF_ALPHA_BASELINE = 0.85


def parse_ts(x: Any) -> Optional[datetime]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return datetime.fromtimestamp(float(x), tz=timezone.utc)
    s = str(x)
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except Exception:
        return None


def load_bars_jsonl(path: Path) -> Dict[str, List[Tuple[datetime, float]]]:
    bars: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
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
            b = data.get("bars") or {}
            for sym, arr in b.items():
                if not isinstance(arr, list):
                    continue
                su = str(sym).upper()
                for bar in arr:
                    t = parse_ts(bar.get("t"))
                    c = bar.get("c")
                    if t is None or c is None:
                        continue
                    bars[su].append((t, float(c)))
    for su in list(bars.keys()):
        bars[su].sort(key=lambda x: x[0])
    return dict(bars)


def merge_bar_points(
    bars: Dict[str, List[Tuple[datetime, float]]],
    sym: str,
    points: List[Tuple[datetime, float]],
) -> None:
    su = sym.upper()
    cur = bars.setdefault(su, [])
    seen = {t for t, _ in cur}
    for t, c in points:
        if t not in seen:
            cur.append((t, float(c)))
            seen.add(t)
    cur.sort(key=lambda x: x[0])


def bar_close_on_or_after(bars_list: List[Tuple[datetime, float]], ts: datetime) -> Optional[float]:
    for t, c in bars_list:
        if t >= ts:
            return c
    return None


def pnl_usd_long_short(entry_px: float, exit_px: float, qty: float, side: str) -> float:
    s = str(side or "long").lower()
    if s in ("sell", "short"):
        return (entry_px - exit_px) * qty
    return (exit_px - entry_px) * qty


def eod_utc_for_exit(exit_ts: datetime) -> datetime:
    if _ET is None:
        return exit_ts
    loc = exit_ts.astimezone(_ET).date()
    eod_local = datetime(loc.year, loc.month, loc.day, 16, 0, 0, tzinfo=_ET)
    return eod_local.astimezone(timezone.utc)


def _iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _et_day_str(ts: datetime) -> str:
    if _ET is None:
        return ts.astimezone(timezone.utc).strftime("%Y-%m-%d")
    return ts.astimezone(_ET).strftime("%Y-%m-%d")


def _session_utc_bounds_for_et_day(et_day: str) -> Tuple[datetime, datetime]:
    """RTH ~09:30–16:00 ET for calendar day ``et_day`` (YYYY-MM-DD)."""
    y, m, d = (int(x) for x in et_day.split("-"))
    if _ET is None:
        # Fallback: full UTC day (degraded)
        start = datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc)
        end = start + timedelta(days=1) - timedelta(seconds=1)
        return start, end
    open_local = datetime(y, m, d, 9, 30, 0, tzinfo=_ET)
    close_local = datetime(y, m, d, 16, 0, 0, tzinfo=_ET)
    return open_local.astimezone(timezone.utc), close_local.astimezone(timezone.utc)


def _alpaca_rest_client() -> Any:
    try:
        key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
        secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
        base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        if not key or not secret:
            return None
        from alpaca_trade_api import REST

        return REST(key, secret, base_url=base)
    except Exception:
        return None


@dataclass
class LiveBarCache:
    """
    In-memory cache: (symbol, ET trading date) -> list of (ts_utc, close).
    One REST round-trip per key during a sweep.
    """

    enabled: bool
    api: Any = None
    _by_sym_day: Dict[Tuple[str, str], List[Tuple[datetime, float]]] = field(default_factory=dict)
    rest_fetch_count: int = 0

    def __post_init__(self) -> None:
        if self.enabled:
            self.api = _alpaca_rest_client()

    def fetch_day_into(self, sym: str, ts: datetime, bars: Dict[str, List[Tuple[datetime, float]]]) -> None:
        if not self.api:
            return
        day = _et_day_str(ts)
        key = (sym.upper(), day)
        if key in self._by_sym_day:
            merge_bar_points(bars, sym, self._by_sym_day[key])
            return
        start_utc, end_utc = _session_utc_bounds_for_et_day(day)
        points: List[Tuple[datetime, float]] = []
        try:
            resp = self.api.get_bars(
                sym.upper(),
                "1Min",
                start=_iso_utc(start_utc),
                end=_iso_utc(end_utc + timedelta(minutes=1)),
                limit=10000,
            )
            df = getattr(resp, "df", None)
            if df is not None and len(df) > 0:
                for idx, row in df.iterrows():
                    tdt = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else datetime.fromisoformat(str(idx))
                    if tdt.tzinfo is None:
                        tdt = tdt.replace(tzinfo=timezone.utc)
                    else:
                        tdt = tdt.astimezone(timezone.utc)
                    c = float(row.get("close", row.get("c", 0)))
                    points.append((tdt, c))
            points.sort(key=lambda x: x[0])
        except Exception:
            points = []
        self._by_sym_day[key] = points
        self.rest_fetch_count += 1
        merge_bar_points(bars, sym, points)

    def close_on_or_after(
        self,
        sym: str,
        ts: datetime,
        bars: Dict[str, List[Tuple[datetime, float]]],
    ) -> Optional[float]:
        bl = bars.get(sym.upper()) or []
        px = bar_close_on_or_after(bl, ts)
        if px is not None:
            return px
        if not self.enabled or not self.api:
            return None
        self.fetch_day_into(sym, ts, bars)
        bl = bars.get(sym.upper()) or []
        return bar_close_on_or_after(bl, ts)


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if not math.isfinite(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def uw_flow_strength(rec: dict) -> Optional[float]:
    for path in (
        ("snapshot", "uw_flow_strength"),
        ("snapshot", "uw", "flow_strength"),
        ("uw_flow_strength",),
    ):
        cur: Any = rec
        ok = True
        for p in path:
            if not isinstance(cur, dict):
                ok = False
                break
            cur = cur.get(p)
        if ok and cur is not None:
            v = _safe_float(cur)
            if v is not None:
                return v
    return None


def mfe_fraction(rec: dict) -> Optional[float]:
    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
    for k in ("mfe_pct", "mfe", "mfe_pct_so_far"):
        v = _safe_float(snap.get(k) if k in snap else rec.get(k))
        if v is None:
            continue
        if abs(v) > 2.0:
            return v / 100.0
        return v
    return None


def mae_fraction(rec: dict) -> Optional[float]:
    eq = rec.get("exit_quality_metrics") if isinstance(rec.get("exit_quality_metrics"), dict) else {}
    for k in ("mae_pct", "mae"):
        v = _safe_float(eq.get(k))
        if v is not None:
            if abs(v) > 2.0:
                return abs(v / 100.0)
            return abs(v)
    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
    for k in ("mae_pct", "mae", "mae_pct_so_far"):
        v = _safe_float(snap.get(k) if k in snap else rec.get(k))
        if v is None:
            continue
        if abs(v) > 2.0:
            return abs(v / 100.0)
        return abs(v)
    return None


def realized_pnl_usd(rec: dict) -> Optional[float]:
    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
    for k in ("pnl", "realized_pnl_usd", "pnl_usd"):
        v = _safe_float(rec.get(k)) or _safe_float(snap.get(k))
        if v is not None:
            return v
    return None


def entry_fill_price(rec: dict) -> Optional[float]:
    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
    for k in ("entry_fill_price", "entry_price", "avg_entry_price"):
        v = _safe_float(rec.get(k)) or _safe_float(snap.get(k))
        if v is not None:
            return v
    return None


def hold_hours(rec: dict, entry_ts: Optional[datetime], exit_ts: Optional[datetime]) -> Optional[float]:
    v = _safe_float(rec.get("time_in_trade_minutes")) or _safe_float(
        (rec.get("snapshot") or {}).get("hold_minutes") if isinstance(rec.get("snapshot"), dict) else None
    )
    if v is not None:
        return max(1e-6, float(v) / 60.0)
    if entry_ts and exit_ts:
        return max(1e-6, (exit_ts - entry_ts).total_seconds() / 3600.0)
    return None


def intended_qty(rec: dict) -> Optional[float]:
    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
    return _safe_float(rec.get("intended_qty")) or _safe_float(snap.get("intended_qty"))


def filled_qty(rec: dict) -> Optional[float]:
    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
    return (
        _safe_float(rec.get("qty"))
        or _safe_float(snap.get("qty"))
        or _safe_float(rec.get("filled_qty"))
        or _safe_float(snap.get("filled_qty"))
    )


def record_has_displacement_close(rec: dict) -> bool:
    try:
        return "displacement_close" in json.dumps(rec, default=str).lower()
    except Exception:
        return False


def cohort_behavior_summary(rows: List[dict]) -> Dict[str, Any]:
    snap_pnl_pct = lambda s: _safe_float(s.get("pnl_pct"))

    win_mfe_minus_realized_pct_pts: List[float] = []
    lose_mae_pct_pts: List[float] = []
    lose_pnl_abs_usd: List[float] = []
    n_pnl = 0
    for rec in rows:
        pnl = realized_pnl_usd(rec)
        if pnl is None:
            continue
        n_pnl += 1
        snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
        mfe = mfe_fraction(rec)
        mae = mae_fraction(rec)
        pnl_pct = snap_pnl_pct(snap) or _safe_float(rec.get("pnl_pct"))
        if pnl > 0 and mfe is not None and pnl_pct is not None:
            mfe_pct_pts = float(mfe) * 100.0
            win_mfe_minus_realized_pct_pts.append(max(0.0, mfe_pct_pts - float(pnl_pct)))
        if pnl < 0:
            lose_pnl_abs_usd.append(abs(float(pnl)))
            if mae is not None:
                lose_mae_pct_pts.append(float(mae) * 100.0)

    def _mean(xs: List[float]) -> Optional[float]:
        return round(sum(xs) / len(xs), 4) if xs else None

    return {
        "rows_with_realized_pnl": n_pnl,
        "winners_with_mfe_and_pnl_pct": len(win_mfe_minus_realized_pct_pts),
        "opportunity_cost_of_impatience_proxy_mean_pct_pts": _mean(win_mfe_minus_realized_pct_pts),
        "losers_count": len(lose_pnl_abs_usd),
        "cost_of_stubbornness_mae_pct_mean": _mean(lose_mae_pct_pts),
        "losers_mean_abs_pnl_usd": _mean(lose_pnl_abs_usd),
        "note": "pct_pts = percentage points (MFE% headroom over realized pnl%).",
    }


def bar_resolution_probe_file_only(
    rows: List[dict],
    bars_static: Dict[str, List[Tuple[datetime, float]]],
    *,
    entry_delay_min: int = 5,
    exit_shift_min: int = 30,
) -> Dict[str, Any]:
    """Hit rate for shifted marks using only on-disk jsonl (before REST merges)."""
    n_in_bar = n_out_bar = n_used = 0
    for rec in rows:
        sym = str(rec.get("symbol") or "").upper()
        tid = str(rec.get("trade_id") or "")
        snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
        qty = filled_qty(rec)
        entry_ts = parse_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
        if entry_ts is None and tid:
            mte = _TID_ENTRY_TS.match(str(tid).strip())
            if mte:
                entry_ts = parse_ts(mte.group(1))
        exit_ts = parse_ts(rec.get("exit_ts") or rec.get("timestamp"))
        ep = entry_fill_price(rec)
        if not sym or entry_ts is None or exit_ts is None or qty is None or ep is None:
            continue
        t_in = entry_ts + timedelta(minutes=int(entry_delay_min))
        t_out = exit_ts + timedelta(minutes=int(exit_shift_min))
        bl = bars_static.get(sym) or []
        if bar_close_on_or_after(bl, t_in) is not None:
            n_in_bar += 1
        if bar_close_on_or_after(bl, t_out) is not None:
            n_out_bar += 1
        n_used += 1
    return {
        "entry_delay_min": entry_delay_min,
        "exit_shift_min": exit_shift_min,
        "trades_in_probe": n_used,
        "file_only_px_in_hit_rate": round(n_in_bar / n_used, 4) if n_used else None,
        "file_only_px_out_hit_rate": round(n_out_bar / n_used, 4) if n_used else None,
    }


def institutional_profit_matrix(
    rows: List[dict],
    bars: Dict[str, List[Tuple[datetime, float]]],
    cache: LiveBarCache,
) -> Dict[str, Any]:
    """
    Five institutional metrics on the realized cohort (not per grid cell).
    Markouts / EOD shadow use the same bar resolution path as the sweep.
    """
    mark_1m_bps: List[float] = []
    mark_5m_bps: List[float] = []
    cap_vel: List[float] = []
    mfes: List[float] = []
    maes: List[float] = []
    fill_gaps: List[float] = []
    disp_n = 0
    disp_shadow_minus_realized: List[float] = []
    early_exit_eod_bonus_usd: List[float] = []

    for rec in rows:
        sym = str(rec.get("symbol") or "").upper()
        tid = str(rec.get("trade_id") or "")
        side = str(rec.get("side") or rec.get("direction") or "long")
        entry_ts = parse_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
        if entry_ts is None and tid:
            mte = _TID_ENTRY_TS.match(str(tid).strip())
            if mte:
                entry_ts = parse_ts(mte.group(1))
        exit_ts = parse_ts(rec.get("exit_ts") or rec.get("timestamp"))
        ep = entry_fill_price(rec)
        qty = filled_qty(rec)
        if not sym or entry_ts is None or ep is None or qty is None:
            continue

        sdl = str(side or "long").lower()
        is_long = sdl not in ("short", "sell", "s")
        px1 = cache.close_on_or_after(sym, entry_ts + timedelta(minutes=1), bars)
        px5 = cache.close_on_or_after(sym, entry_ts + timedelta(minutes=5), bars)
        if px1 is not None:
            raw_ret = (px1 - ep) / ep * 10000.0
            mark_1m_bps.append(raw_ret if is_long else -raw_ret)
        if px5 is not None:
            raw_ret5 = (px5 - ep) / ep * 10000.0
            mark_5m_bps.append(raw_ret5 if is_long else -raw_ret5)

        pnl = realized_pnl_usd(rec)
        hh = hold_hours(rec, entry_ts, exit_ts)
        if pnl is not None and hh:
            notional = abs(float(qty) * float(ep))
            if notional > 0:
                pnl_bps = (float(pnl) / notional) * 10000.0
                cap_vel.append(float(pnl_bps) / float(hh))

        mfe = mfe_fraction(rec)
        mae = mae_fraction(rec)
        if mfe is not None:
            mfes.append(float(mfe))
        if mae is not None:
            maes.append(float(mae))

        intent = intended_qty(rec)
        fill = filled_qty(rec)
        if intent is not None and intent > 0 and fill is not None:
            fill_gaps.append(float(fill) / float(intent))

        if exit_ts and record_has_displacement_close(rec):
            eod_ts = eod_utc_for_exit(exit_ts)
            eod_px = cache.close_on_or_after(sym, eod_ts, bars)
            if eod_px is not None and pnl is not None:
                shadow = pnl_usd_long_short(float(ep), float(eod_px), float(qty), side)
                disp_n += 1
                disp_shadow_minus_realized.append(float(shadow) - float(pnl))

        if exit_ts and pnl is not None:
            eod_ts = eod_utc_for_exit(exit_ts)
            eod_px = cache.close_on_or_after(sym, eod_ts, bars)
            if eod_px is not None:
                shadow = pnl_usd_long_short(float(ep), float(eod_px), float(qty), side)
                b = float(shadow) - float(pnl)
                if b > 0:
                    early_exit_eod_bonus_usd.append(b)

    def _mean(xs: List[float]) -> Optional[float]:
        return round(sum(xs) / len(xs), 6) if xs else None

    mean_mfe = _mean(mfes)
    mean_mae = _mean(maes)
    edge_ratio = None
    if mean_mfe is not None and mean_mae is not None and mean_mae > 1e-12:
        edge_ratio = round(mean_mfe / mean_mae, 6)

    return {
        "markout_t_plus_1m_mean_bps": _mean(mark_1m_bps),
        "markout_t_plus_5m_mean_bps": _mean(mark_5m_bps),
        "markout_samples_1m": len(mark_1m_bps),
        "markout_samples_5m": len(mark_5m_bps),
        "markout_note": "Long: positive = favorable drift after entry; negative = adverse markout (toxicity).",
        "capital_velocity_mean_bps_per_hour": _mean(cap_vel),
        "capital_velocity_samples": len(cap_vel),
        "displacement_trades_with_eod_shadow": disp_n,
        "displacement_mean_shadow_minus_realized_usd": _mean(disp_shadow_minus_realized),
        "edge_ratio_mean_mfe_over_mean_mae": edge_ratio,
        "mean_mfe_fraction": mean_mfe,
        "mean_mae_fraction": mean_mae,
        "liquidity_mean_filled_over_intended": _mean(fill_gaps),
        "liquidity_samples": len(fill_gaps),
        "early_exit_eod_opportunity_sum_usd": round(sum(early_exit_eod_bonus_usd), 4),
        "early_exit_eod_opportunity_trades": len(early_exit_eod_bonus_usd),
    }


def cohort_rows(root: Path) -> List[dict]:
    return list(
        iter_harvester_era_exit_records_for_csv(
            root,
            floor_epoch=float(STRICT_EPOCH_START),
        )
    )


def blocked_intent_count(root: Path, t0: float, t1: float) -> int:
    p = root / "logs" / "run.jsonl"
    if not p.is_file():
        return 0
    n = 0
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(o.get("event_type") or "") != "trade_intent":
                continue
            if str(o.get("decision_outcome") or "").lower() != "blocked":
                continue
            ts = parse_ts(o.get("ts") or o.get("timestamp"))
            if ts is None:
                continue
            tsv = ts.timestamp()
            if t0 <= tsv <= t1:
                n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument(
        "--bars",
        type=Path,
        default=None,
        help="alpaca_bars.jsonl (default: <root>/artifacts/market_data/alpaca_bars.jsonl)",
    )
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--adversarial-bps", type=float, default=2.0, help="Friction bps × notional on non-baseline cells")
    ap.add_argument("--max-trades", type=int, default=0, help="Cap trades for dry runs (0 = all)")
    ap.add_argument(
        "--fetch-bars-live",
        action="store_true",
        help="Use Alpaca REST 1m when jsonl lacks a counterfactual minute (cached per symbol×ET day).",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    bars_path = args.bars or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")

    if bars_path.is_file():
        bars: Dict[str, List[Tuple[datetime, float]]] = load_bars_jsonl(bars_path)
    elif args.fetch_bars_live:
        bars = {}
        print("WARN: bars file missing; starting empty bar set, relying on --fetch-bars-live", file=sys.stderr)
    else:
        print("ERROR: bars file missing:", bars_path, file=sys.stderr)
        print("Use --fetch-bars-live or provide --bars", file=sys.stderr)
        return 1

    out_dir = args.out_dir or (root / "artifacts" / "apex_omni")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = cohort_rows(root)
    if args.max_trades and args.max_trades > 0:
        rows = rows[: int(args.max_trades)]

    cache = LiveBarCache(enabled=bool(args.fetch_bars_live))
    if args.fetch_bars_live and not cache.api:
        print("WARN: --fetch-bars-live set but Alpaca REST credentials missing; REST path disabled", file=sys.stderr)

    bars_static = {k: list(v) for k, v in bars.items()}
    cohort_behavior = cohort_behavior_summary(rows)
    bar_probe = bar_resolution_probe_file_only(rows, bars_static)
    inst_matrix = institutional_profit_matrix(rows, bars, cache)

    t0 = float(STRICT_EPOCH_START)
    t1 = datetime.now(timezone.utc).timestamp()
    blocked_n = blocked_intent_count(root, t0, t1)

    entry_delays = (0, 5, 15)
    exit_specs: List[Tuple[str, Any]] = [
        ("exit_m15", -15),
        ("exit_live", 0),
        ("exit_p30", 30),
        ("exit_eod", "eod"),
    ]
    alpha_floors = (0.85, 0.90, 0.95, 0.985)

    adv_frac = float(args.adversarial_bps) / 10000.0

    best: Optional[Dict[str, Any]] = None
    grid_results: List[Dict[str, Any]] = []

    for ed in entry_delays:
        for ex_label, ex_shift in exit_specs:
            for af in alpha_floors:
                total_raw = 0.0
                total_adv = 0.0
                used = 0
                skipped = 0
                worst_single: Optional[float] = None
                for rec in rows:
                    fs = uw_flow_strength(rec)
                    if fs is not None and fs < float(af):
                        skipped += 1
                        continue

                    sym = str(rec.get("symbol") or "").upper()
                    tid = str(rec.get("trade_id") or "")
                    side = str(rec.get("side") or rec.get("direction") or "long")
                    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
                    qty = filled_qty(rec)
                    entry_ts = parse_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
                    if entry_ts is None and tid:
                        mte = _TID_ENTRY_TS.match(str(tid).strip())
                        if mte:
                            entry_ts = parse_ts(mte.group(1))
                    exit_ts = parse_ts(rec.get("exit_ts") or rec.get("timestamp"))
                    ep = entry_fill_price(rec)
                    if not sym or entry_ts is None or exit_ts is None or qty is None or ep is None:
                        skipped += 1
                        continue

                    t_in = entry_ts + timedelta(minutes=int(ed))
                    if ex_shift == "eod":
                        t_out = eod_utc_for_exit(exit_ts)
                    else:
                        t_out = exit_ts + timedelta(minutes=int(ex_shift))
                    px_in = cache.close_on_or_after(sym, t_in, bars)
                    px_out = cache.close_on_or_after(sym, t_out, bars)
                    xp_live = _safe_float(rec.get("exit_price")) or _safe_float(snap.get("exit_price"))
                    if px_in is None:
                        px_in = ep
                    if px_out is None:
                        px_out = xp_live if xp_live is not None else ep
                    if px_in is None or px_out is None:
                        skipped += 1
                        continue

                    hypo = pnl_usd_long_short(px_in, px_out, float(qty), side)
                    notional = abs(float(qty) * px_in)
                    is_baseline_cell = ed == 0 and ex_label == "exit_live" and float(af) == float(REF_ALPHA_BASELINE)
                    friction = 0.0 if is_baseline_cell else adv_frac * notional
                    adv = hypo - friction
                    total_raw += hypo
                    total_adv += adv
                    used += 1
                    if worst_single is None or adv < worst_single:
                        worst_single = adv

                cell = {
                    "entry_delay_min": ed,
                    "exit_mode": ex_label,
                    "alpha11_min_flow_floor": af,
                    "trades_used": used,
                    "trades_skipped_filter_or_bars": skipped,
                    "sum_hypo_usd_raw": round(total_raw, 4),
                    "sum_hypo_usd_adversarial": round(total_adv, 4),
                    "worst_single_trade_adversarial_usd": (
                        round(float(worst_single), 4) if worst_single is not None else None
                    ),
                }
                grid_results.append(cell)
                if best is None or total_adv > best["sum_hypo_usd_adversarial"]:
                    best = dict(cell)

    raws = [float(c["sum_hypo_usd_raw"]) for c in grid_results]
    raw_spread = (max(raws) - min(raws)) if raws else 0.0
    degenerate_timing = raw_spread < 1e-6

    payload = {
        "root": str(root),
        "STRICT_EPOCH_START": STRICT_EPOCH_START,
        "REF_ALPHA_BASELINE": REF_ALPHA_BASELINE,
        "cohort_trades_loaded": len(rows),
        "blocked_trade_intents_in_strict_window": blocked_n,
        "bars_path": str(bars_path) if bars_path.is_file() else None,
        "bars_symbols": len(bars),
        "fetch_bars_live": bool(args.fetch_bars_live),
        "rest_day_fetch_count": cache.rest_fetch_count,
        "adversarial_bps": float(args.adversarial_bps),
        "institutional_profit_matrix": inst_matrix,
        "best_cell_adversarial_usd": best,
        "cohort_behavior_summary": cohort_behavior,
        "bar_resolution_probe_shifted_entry5m_exit30m_file_only": bar_probe,
        "grid_raw_usd_spread": round(raw_spread, 6),
        "timing_sweep_degenerate_all_raw_usd_identical": degenerate_timing,
        "grid": grid_results,
        "notes": [
            "Friction applies to every cell except entry_delay=0 + exit_live + alpha floor 0.85.",
            "Alpha11 floors filter on uw_flow_strength when present; missing → fail-open include.",
            "EOD exit uses 16:00 ET on exit calendar day.",
            "REST cache key: (symbol, ET date); one get_bars per key when a minute is missing from merged bars.",
        ],
    }
    outp = out_dir / "APEX_OMNI_PARAMETER_SWEEP.json"
    outp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Wrote", outp, flush=True)
    if best:
        print("BEST adversarial USD:", best["sum_hypo_usd_adversarial"], best, flush=True)
    print("REST day fetches:", cache.rest_fetch_count, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
