#!/usr/bin/env python3
"""
Apex omni-parameter sweep (read-only): strict-epoch exit cohort vs 1m bars + adversarial friction.

**Scope (Quant):** Counterfactual USD PnL by shifting synthetic entry/exit marks on Alpaca 1m bars
(``artifacts/market_data/alpaca_bars.jsonl`` or ``--bars``). This is **not** a full engine replay:
Alpha 11 / Alpha 10 gates are applied as **filters** on per-row telemetry when present (fail-open when missing).

**Adversarial:** For any cell where entry delay ≠ 0 or exit shift ≠ 0, subtract ``ADVERSARIAL_BPS`` round-trip
from each trade's notional (default 2 bps = 0.0002 × |qty × entry_px|).

Outputs JSON under ``artifacts/apex_omni/`` (configurable).

Usage:
  PYTHONPATH=. python3 scripts/ml/apex_omni_parameter_sweep.py --root /root/stock-bot \\
    --bars artifacts/market_data/alpaca_bars.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

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
    """US equity regular session end ~16:00 America/New_York on calendar day of exit."""
    if _ET is None:
        return exit_ts
    loc = exit_ts.astimezone(_ET).date()
    eod_local = datetime(loc.year, loc.month, loc.day, 16, 0, 0, tzinfo=_ET)
    return eod_local.astimezone(timezone.utc)


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
    for k in ("mfe_pct", "mfe"):
        v = _safe_float(snap.get(k) if k in snap else rec.get(k))
        if v is None:
            continue
        if abs(v) > 2.0:
            return v / 100.0
        return v
    return None


def cohort_rows(root: Path) -> List[dict]:
    rows = list(
        iter_harvester_era_exit_records_for_csv(
            root,
            floor_epoch=float(STRICT_EPOCH_START),
        )
    )
    return rows


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
    ap.add_argument("--adversarial-bps", type=float, default=2.0, help="Friction round-trip bps on shifted paths")
    ap.add_argument("--max-trades", type=int, default=0, help="Cap trades for dry runs (0 = all)")
    args = ap.parse_args()
    root = args.root.resolve()
    bars_path = args.bars or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")
    if not bars_path.is_file():
        print("ERROR: bars file missing:", bars_path, file=sys.stderr)
        print("Provide --bars or ingest 1m Alpaca bars into artifacts/market_data/alpaca_bars.jsonl", file=sys.stderr)
        return 1

    out_dir = args.out_dir or (root / "artifacts" / "apex_omni")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = cohort_rows(root)
    if args.max_trades and args.max_trades > 0:
        rows = rows[: int(args.max_trades)]

    bars = load_bars_jsonl(bars_path)
    t0 = float(STRICT_EPOCH_START)
    t1 = datetime.now(timezone.utc).timestamp()
    blocked_n = blocked_intent_count(root, t0, t1)

    entry_delays = (0, 5, 15, 30)
    exit_specs: List[Tuple[str, Any]] = [
        ("exit_m15", -15),
        ("exit_live", 0),
        ("exit_p30", 30),
        ("exit_p60", 60),
        ("exit_eod", "eod"),
    ]
    alpha_floors = (0.85, 0.90, 0.95)
    mfe_gates = (0.0, 0.005, 0.01)

    adv_frac = float(args.adversarial_bps) / 10000.0

    best: Optional[Dict[str, Any]] = None

    grid_results: List[Dict[str, Any]] = []

    for ed in entry_delays:
        for ex_label, ex_shift in exit_specs:
            for af in alpha_floors:
                for mf in mfe_gates:
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
                        mfev = mfe_fraction(rec)
                        if mfev is not None and mfev < float(mf):
                            skipped += 1
                            continue

                        sym = str(rec.get("symbol") or "").upper()
                        tid = str(rec.get("trade_id") or "")
                        side = str(rec.get("side") or rec.get("direction") or "long")
                        snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
                        qty = _safe_float(rec.get("qty")) or _safe_float(snap.get("qty"))
                        entry_ts = parse_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
                        exit_ts = parse_ts(rec.get("exit_ts") or rec.get("timestamp"))
                        ep = _safe_float(rec.get("entry_price")) or _safe_float(snap.get("entry_price"))
                        if not sym or entry_ts is None or exit_ts is None or qty is None or ep is None:
                            skipped += 1
                            continue
                        bl = bars.get(sym)
                        if not bl:
                            skipped += 1
                            continue

                        t_in = entry_ts + timedelta(minutes=int(ed))
                        if ex_shift == "eod":
                            t_out = eod_utc_for_exit(exit_ts)
                        else:
                            t_out = exit_ts + timedelta(minutes=int(ex_shift))
                        px_in = bar_close_on_or_after(bl, t_in)
                        px_out = bar_close_on_or_after(bl, t_out)
                        if px_in is None or px_out is None:
                            skipped += 1
                            continue

                        hypo = pnl_usd_long_short(px_in, px_out, float(qty), side)
                        notional = abs(float(qty) * px_in)
                        is_baseline = ed == 0 and ex_label == "exit_live"
                        friction = 0.0 if is_baseline else adv_frac * notional
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
                        "mfe_gate_fraction": mf,
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

    payload = {
        "root": str(root),
        "STRICT_EPOCH_START": STRICT_EPOCH_START,
        "cohort_trades_loaded": len(rows),
        "blocked_trade_intents_in_strict_window": blocked_n,
        "bars_path": str(bars_path),
        "bars_symbols": len(bars),
        "adversarial_bps": float(args.adversarial_bps),
        "best_cell_adversarial_usd": best,
        "grid": grid_results,
        "notes": [
            "Alpha11 floors filter on uw_flow_strength when present; missing → fail-open include.",
            "MFE gate compares snapshot mfe_pct (auto /100 if >2).",
            "EOD exit uses 16:00 ET on exit calendar day.",
            "worst_single_trade_adversarial_usd is the worst per-trade mark in the cell (not full MAE path).",
        ],
    }
    outp = out_dir / "APEX_OMNI_PARAMETER_SWEEP.json"
    outp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Wrote", outp, flush=True)
    if best:
        print("BEST adversarial USD:", best["sum_hypo_usd_adversarial"], best, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
