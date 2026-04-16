"""
EOD-capped unmanaged forward returns for US equities (Alpaca ML cohort).

Computes:
  - ``target_ret_60m_rth``: log(close at horizon) - log(entry_price), horizon = min(entry + 60m, RTH close).
  - ``target_ret_eod_rth``: log(last RTH close same session) - log(entry_price).

Rules (institutional v1):
  - **RTH** uses ``America/New_York`` calendar day of ``entry_ts`` with session
    **[09:30, 16:00] ET inclusive** of minute bars. Hard cap at **16:00 ET** (no overnight).
  - Only bars whose timestamp falls in that window are used for forward prices.
  - ``entry_price`` is the trade reference (from cohort); forward prices use **1m bar close**.
  - If entry is **after** 16:00 ET on day ``d``, labels are undefined (after_rth_close).
  - If no usable bar exists for a horizon, returns NaN with a ``label_*_reason`` string.

Bar data: ``src.data.alpaca_bars_fetcher.fetch_bars_for_range`` (Alpaca Data API v2).

CLI (merge into flat cohort CSV without removing columns):
  PYTHONPATH=. python -m src.ml.alpaca_unmanaged_labels --csv reports/Gemini/alpaca_ml_cohort_flat.csv --out reports/Gemini/alpaca_ml_cohort_flat.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

_ET = ZoneInfo("America/New_York")
_RTH_OPEN = time(9, 30)
_RTH_CLOSE = time(16, 0)  # 4:00 PM ET — inclusive minute window through 15:59 bar; 16:00 is session end cap


def _parse_entry_ts(raw: Any) -> Optional[datetime]:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        dt = raw
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    s = str(raw).strip().replace("Z", "+00:00")
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _rth_bounds_et(d: date) -> Tuple[datetime, datetime]:
    """Return (rth_open_et, rth_close_et) for equity RTH on calendar date ``d`` (ET)."""
    o = datetime(d.year, d.month, d.day, _RTH_OPEN.hour, _RTH_OPEN.minute, tzinfo=_ET)
    c = datetime(d.year, d.month, d.day, _RTH_CLOSE.hour, _RTH_CLOSE.minute, tzinfo=_ET)
    return o, c


def _bar_dt_utc(bar: Dict[str, Any]) -> Optional[datetime]:
    t = bar.get("t")
    if not t:
        return None
    try:
        s = str(t).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _filter_rth_bars(bars: Iterable[Dict[str, Any]], session_open_et: datetime, session_close_et: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for b in bars:
        dtu = _bar_dt_utc(b)
        if dtu is None:
            continue
        et = dtu.astimezone(_ET)
        if et < session_open_et:
            continue
        # Strict: no bar strictly after 16:00 ET (use <= session_close_et for boundary)
        if et > session_close_et:
            continue
        out.append(b)
    out.sort(key=lambda x: _bar_dt_utc(x) or datetime.min.replace(tzinfo=timezone.utc))
    return out


def _last_close_at_or_before(bars: List[Dict[str, Any]], bound_et: datetime) -> Optional[float]:
    """Last 1m close with bar time (ET) <= ``bound_et``."""
    bound_utc = bound_et.astimezone(timezone.utc)
    best: Optional[Tuple[datetime, float]] = None
    for b in bars:
        dtu = _bar_dt_utc(b)
        if dtu is None or dtu > bound_utc:
            continue
        try:
            c = float(b.get("c") or b.get("close") or 0.0)
        except (TypeError, ValueError):
            continue
        if c <= 0:
            continue
        if best is None or dtu > best[0]:
            best = (dtu, c)
    return best[1] if best else None


def compute_unmanaged_rth_labels(
    *,
    symbol: str,
    entry_ts_utc: datetime,
    entry_price: float,
    bars: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Returns dict with target_ret_60m_rth, target_ret_eod_rth (float or NaN),
    label_60m_reason, label_eod_reason, label_session_date_et.
    """
    nan = float("nan")
    out: Dict[str, Any] = {
        "target_ret_60m_rth": nan,
        "target_ret_eod_rth": nan,
        "label_60m_reason": "",
        "label_eod_reason": "",
        "label_session_date_et": "",
    }
    if entry_price <= 0 or not math.isfinite(entry_price):
        out["label_60m_reason"] = out["label_eod_reason"] = "bad_entry_price"
        return out

    ent_utc = entry_ts_utc.astimezone(timezone.utc)
    ent_et = ent_utc.astimezone(_ET)
    d = ent_et.date()
    out["label_session_date_et"] = d.isoformat()
    rth_open_et, rth_close_et = _rth_bounds_et(d)

    if ent_et > rth_close_et:
        out["label_60m_reason"] = out["label_eod_reason"] = "after_rth_close"
        return out

    session_bars = _filter_rth_bars(bars, rth_open_et, rth_close_et)
    if not session_bars:
        out["label_60m_reason"] = out["label_eod_reason"] = "no_rth_bars"
        return out

    # T+60m in ET, capped at 4:00 PM ET same calendar day (no overnight). If raw T+60m is before
    # RTH open, evaluate at first RTH minute (forward session cap, not extended hours).
    t60_raw_et = ent_et + timedelta(minutes=60)
    horizon_60_et = min(max(t60_raw_et, rth_open_et), rth_close_et)

    px_60 = _last_close_at_or_before(session_bars, horizon_60_et)
    if px_60 is None or px_60 <= 0:
        out["label_60m_reason"] = "no_bar_lte_horizon_60"
    else:
        out["target_ret_60m_rth"] = math.log(px_60 / entry_price)
        out["label_60m_reason"] = "ok"

    px_eod = _last_close_at_or_before(session_bars, rth_close_et)
    if px_eod is None or px_eod <= 0:
        out["label_eod_reason"] = "no_bar_lte_rth_close"
    else:
        out["target_ret_eod_rth"] = math.log(px_eod / entry_price)
        out["label_eod_reason"] = "ok"

    return out


def _fetch_bars_bundle(
    symbol: str,
    day_et: date,
) -> List[Dict[str, Any]]:
    from src.data.alpaca_bars_fetcher import fetch_bars_for_range

    rth_o, rth_c = _rth_bounds_et(day_et)
    start_utc = rth_o.astimezone(timezone.utc) - timedelta(minutes=5)
    end_utc = rth_c.astimezone(timezone.utc) + timedelta(minutes=2)
    return fetch_bars_for_range(symbol.upper(), start_utc, end_utc, timeframe="1Min", limit=10000)


def _fmt_csv_float(v: float) -> str:
    if isinstance(v, float) and (math.isnan(v) or not math.isfinite(v)):
        return ""
    return f"{float(v):.10g}"


def merge_unmanaged_labels_into_csv(
    csv_in: Path,
    csv_out: Path,
    *,
    entry_price_col: str = "entry_price",
    entry_ts_col: str = "entry_ts",
    symbol_col: str = "symbol",
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Read flat cohort CSV, compute unmanaged labels per row, write ``csv_out`` with
    all original columns plus label columns (existing label columns overwritten if present).
    """
    csv_in = csv_in.resolve()
    csv_out = csv_out.resolve()
    if not csv_in.is_file():
        raise FileNotFoundError(str(csv_in))

    with csv_in.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        in_fields = list(reader.fieldnames or [])
        rows = list(reader)

    new_cols = [
        "target_ret_60m_rth",
        "target_ret_eod_rth",
        "label_60m_reason",
        "label_eod_reason",
        "label_session_date_et",
    ]
    out_fields = [c for c in in_fields if c not in new_cols] + [c for c in new_cols if c not in in_fields]

    # Prefetch bars once per (symbol, ET session date)
    keys_needed: set[Tuple[str, date]] = set()
    for r in rows:
        sym = (r.get(symbol_col) or "").strip().upper()
        ts = _parse_entry_ts(r.get(entry_ts_col))
        if sym and ts is not None:
            keys_needed.add((sym, ts.astimezone(_ET).date()))

    cache: Dict[Tuple[str, date], List[Dict[str, Any]]] = {}
    for sym, d_et in sorted(keys_needed):
        try:
            cache[(sym, d_et)] = _fetch_bars_bundle(sym, d_et)
        except Exception:
            cache[(sym, d_et)] = []

    stats = {"rows": len(rows), "prefetch_keys": len(cache), "errors": 0}

    for r in rows:
        sym = (r.get(symbol_col) or "").strip().upper()
        try:
            ep = float(r.get(entry_price_col) or 0.0)
        except (TypeError, ValueError):
            ep = 0.0
        ts = _parse_entry_ts(r.get(entry_ts_col))
        if not sym or ts is None:
            r["target_ret_60m_rth"] = r["target_ret_eod_rth"] = ""
            r["label_60m_reason"] = r["label_eod_reason"] = "missing_symbol_or_entry_ts"
            r["label_session_date_et"] = ""
            stats["errors"] += 1
            continue
        d_et = ts.astimezone(_ET).date()
        bars = cache.get((sym, d_et), [])
        lab = compute_unmanaged_rth_labels(symbol=sym, entry_ts_utc=ts, entry_price=ep, bars=bars)
        r["target_ret_60m_rth"] = _fmt_csv_float(float(lab["target_ret_60m_rth"]))
        r["target_ret_eod_rth"] = _fmt_csv_float(float(lab["target_ret_eod_rth"]))
        r["label_60m_reason"] = str(lab.get("label_60m_reason") or "")
        r["label_eod_reason"] = str(lab.get("label_eod_reason") or "")
        r["label_session_date_et"] = str(lab.get("label_session_date_et") or "")

    if dry_run:
        return stats

    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in out_fields})

    return stats


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Merge RTH-capped unmanaged labels into Alpaca ML flat CSV.")
    ap.add_argument("--csv", type=Path, required=True, help="Input cohort CSV (e.g. reports/Gemini/alpaca_ml_cohort_flat.csv).")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output CSV (default: overwrite --csv in place).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Do not write; print stats only.")
    args = ap.parse_args(argv)

    out_p = (args.out or args.csv).resolve()
    try:
        st = merge_unmanaged_labels_into_csv(args.csv.resolve(), out_p, dry_run=bool(args.dry_run))
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(json.dumps({**st, "out": str(out_p), "dry_run": bool(args.dry_run)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
