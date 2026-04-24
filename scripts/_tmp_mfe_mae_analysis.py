#!/usr/bin/env python3
"""
MFE/MAE cliff analysis for strict-complete Alpaca cohort (read-only).

Inputs:
  - logs/exit_attribution.jsonl (dedupe last row per trade_id)
  - telemetry/alpaca_strict_completeness_gate.evaluate_completeness(..., collect_complete_trade_ids=True)
  - logs/run_stitched.jsonl (optional sanity: event_type histogram for stitched window)

MFE uses exit_quality_metrics.mfe (price units) -> mfe_pct = mfe/entry*100 when present;
else high-water proxy max(0, (max(entry,exit)-entry)/entry*100) for long.

MAE: use exit_quality_metrics.mae when present; else exit-snapshot proxy for losers only:
mae_proxy_pct = min(0.0, float(pnl_pct)) (documented lower-bound; true intraday MAE needs bars).

Writes config/overlays/mfe_mae_exit_overlay.json when --write-overlay is passed.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _pctile(sorted_vals: List[float], p: float) -> Optional[float]:
    if not sorted_vals:
        return None
    xs = sorted_vals
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * (p / 100.0)
    f = int(math.floor(k))
    c = min(f + 1, len(xs) - 1)
    t = k - f
    return xs[f] * (1 - t) + xs[c] * t


def _stream_jsonl(path: Path):
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _dedupe_exit_by_trade_id(logs: Path) -> Dict[str, Dict[str, Any]]:
    """Last row wins per trade_id (matches strict gate semantics)."""
    by_tid: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for rec in _stream_jsonl(logs / "exit_attribution.jsonl"):
        tid = rec.get("trade_id")
        if not tid or not str(tid).startswith("open_"):
            continue
        tid = str(tid)
        if tid not in by_tid:
            order.append(tid)
        by_tid[tid] = rec
    return by_tid


def _side_long(rec: Dict[str, Any]) -> bool:
    s = str(rec.get("side") or "buy").lower()
    return s in ("buy", "long")


def _mfe_mae_pct(rec: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], str]:
    """
    Returns (mfe_pct, mae_pct, source_tag).
    mfe_pct >= 0 for long favorable excursion in % of entry.
    mae_pct <= 0 for long adverse (when known).
    """
    ep = rec.get("entry_price")
    xp = rec.get("exit_price")
    pnl_pct = rec.get("pnl_pct")
    try:
        epf = float(ep) if ep is not None else 0.0
        xpf = float(xp) if xp is not None else 0.0
    except (TypeError, ValueError):
        return None, None, "bad_prices"
    if epf <= 0:
        return None, None, "bad_entry"

    eq = rec.get("exit_quality_metrics") if isinstance(rec.get("exit_quality_metrics"), dict) else {}
    mfe_p = eq.get("mfe")
    mae_p = eq.get("mae")
    mfe_pct: Optional[float] = None
    mae_pct: Optional[float] = None
    src = []

    if mfe_p is not None:
        try:
            mf = float(mfe_p)
            mfe_pct = abs(mf) / epf * 100.0
            src.append("eq_mfe")
        except (TypeError, ValueError):
            pass
    if mfe_pct is None and _side_long(rec):
        mfe_pct = max(0.0, (max(epf, xpf) - epf) / epf * 100.0)
        src.append("proxy_max_entry_exit")
    elif mfe_pct is None:
        mfe_pct = max(0.0, (epf - min(epf, xpf)) / epf * 100.0)
        src.append("proxy_short")

    if mae_p is not None:
        try:
            ma = float(mae_p)
            mae_pct = ma / epf * 100.0
            src.append("eq_mae")
        except (TypeError, ValueError):
            pass
    if mae_pct is None and pnl_pct is not None:
        try:
            p = float(pnl_pct)
            if p < 0:
                mae_pct = min(0.0, p)
                src.append("mae_proxy_exit_pnl_losers")
        except (TypeError, ValueError):
            pass

    return mfe_pct, mae_pct, "+".join(src) if src else "none"


def _is_signal_decay_reason(exit_reason: str) -> bool:
    return "signal_decay" in (exit_reason or "").lower()


def _run_stitched_event_histogram(root: Path, sample_lines: int = 50_000) -> Dict[str, int]:
    path = root / "logs" / "run_stitched.jsonl"
    c: Counter[str] = Counter()
    n = 0
    for rec in _stream_jsonl(path):
        et = rec.get("event_type") or rec.get("type") or rec.get("msg") or "unknown"
        c[str(et)[:64]] += 1
        n += 1
        if n >= sample_lines:
            break
    return dict(c.most_common(32))


def _recommend_overlay(
    mfe_all: List[float],
    mfe_decay: List[float],
    mae_losers: List[float],
    pnl_losers: List[float],
) -> Dict[str, Any]:
    """Clip to production-safe bands; methodology is distribution-driven."""
    trail = None
    pt = None
    sl = None
    bear_pt = None
    bear_sl = None

    if mfe_all:
        # Trail: mfe_all is in **percent**; trailing_stop_pct in main is a price fraction (0.035 == 3.5%).
        # Map p65 MFE% -> trail fraction with sane floor/ceiling.
        trail_pct = _pctile(sorted(mfe_all), 65.0)
        trail = max(0.012, min(0.040, trail_pct / 100.0))
    if mfe_decay:
        # TP: p55 of MFE% among decay exits -> decimal return target for main.py
        pt_pct = _pctile(sorted(mfe_decay), 55.0)
        pt = max(0.005, min(0.018, pt_pct / 100.0))
    elif mfe_all:
        pt_pct = _pctile(sorted(mfe_all), 60.0)
        pt = max(0.005, min(0.018, pt_pct / 100.0))

    if mae_losers:
        # mae_losers values are already in **percent** (e.g. -0.5 == -0.5%). main.py compares
        # pnl_pct_decimal = pnl_pct/100 to stop_loss_pct as a decimal fraction (e.g. -0.01 == -1%).
        mae_sorted = sorted(mae_losers)  # ascending negative
        adv_pct = _pctile(mae_sorted, 20.0)  # e.g. -0.35 (%)
        sl_dec = adv_pct / 100.0
        sl = max(-0.025, min(-0.006, sl_dec))
    elif pnl_losers:
        pnl_sorted = sorted(pnl_losers)
        adv_pct = _pctile(pnl_sorted, 15.0)
        sl_dec = adv_pct / 100.0
        sl = max(-0.025, min(-0.006, sl_dec))

    if pt is None:
        pt = 0.0075
    if trail is None:
        trail = 0.028
    if sl is None:
        sl = -0.01

    bear_pt = min(0.012, round(pt * 1.25, 6))
    bear_sl = round(max(-0.012, sl * 1.15), 6)

    return {
        "trailing_stop_pct": round(trail, 6),
        "profit_target_decimal_default": round(pt, 6),
        "profit_target_decimal_bear": round(bear_pt, 6),
        "stop_loss_pct_default": round(sl, 6),
        "stop_loss_pct_bear": round(bear_sl, 6),
        "_method": {
            "trailing_stop_pct": "p65 mfe_pct (full strict cohort), clipped [1.2%, 4%]",
            "profit_target_decimal_default": "p55 mfe_pct (signal_decay subset) else p60 full, clipped [0.5%, 1.8%]",
            "stop_loss_pct_default": "p20 mae_pct losers (eq.mae) -> decimal; else p15 pnl_pct losers; max(-0.025, min(-0.006, sl_dec))",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--write-overlay", action="store_true", help="Write config/overlays/mfe_mae_exit_overlay.json")
    args = ap.parse_args()
    root = args.root.resolve()

    # Import gate evaluation (requires repo on PYTHONPATH).
    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    gate = evaluate_completeness(root, audit=False, collect_complete_trade_ids=True)
    if gate.get("LEARNING_STATUS") != "ARMED":
        print(json.dumps({"error": "strict_gate_not_armed", "gate": gate}, indent=2))
        return 2

    tids: List[str] = list(gate.get("complete_trade_ids") or [])
    by_tid = _dedupe_exit_by_trade_id(root / "logs")
    rows: List[Dict[str, Any]] = []
    missing: List[str] = []
    for tid in tids:
        rec = by_tid.get(tid)
        if not rec:
            missing.append(tid)
            continue
        rows.append(rec)

    mfe_all: List[float] = []
    mfe_decay: List[float] = []
    mfe_decay_winners: List[float] = []
    mae_losers: List[float] = []
    pnl_losers: List[float] = []
    giveback: List[float] = []

    decay_n = 0
    for rec in rows:
        mfe_pct, mae_pct, _src = _mfe_mae_pct(rec)
        if mfe_pct is not None:
            mfe_all.append(mfe_pct)
        er = str(rec.get("exit_reason") or "")
        pnl = rec.get("pnl")
        try:
            pnl_f = float(pnl) if pnl is not None else 0.0
        except (TypeError, ValueError):
            pnl_f = 0.0
        try:
            pnl_pct_f = float(rec.get("pnl_pct") or 0.0)
        except (TypeError, ValueError):
            pnl_pct_f = 0.0

        if pnl_pct_f < 0:
            pnl_losers.append(pnl_pct_f)

        if _is_signal_decay_reason(er):
            decay_n += 1
            if mfe_pct is not None:
                mfe_decay.append(mfe_pct)
            if pnl_f > 0 and mfe_pct is not None:
                mfe_decay_winners.append(mfe_pct)
                gb = mfe_pct - pnl_pct_f
                if gb > 0:
                    giveback.append(gb)

        if mae_pct is not None and mae_pct < -1e-6:
            mae_losers.append(mae_pct)

    def cliff_table(vals: List[float], label: str) -> Dict[str, Any]:
        if not vals:
            return {"label": label, "n": 0}
        s = sorted(vals)
        return {
            "label": label,
            "n": len(vals),
            "p50": _pctile(s, 50.0),
            "p75": _pctile(s, 75.0),
            "p90": _pctile(s, 90.0),
            "p95": _pctile(s, 95.0),
        }

    overlay = _recommend_overlay(mfe_all, mfe_decay, mae_losers, pnl_losers)

    # "Point of no return" heuristic: among losers, fraction with pnl <= q for q in grid.
    pnr_table: List[Dict[str, Any]] = []
    if pnl_losers:
        srt = sorted(pnl_losers)
        for q in (-0.25, -0.5, -0.75, -1.0, -1.5, -2.0):
            frac = sum(1 for x in srt if x <= q) / len(srt)
            pnr_table.append({"pnl_pct_threshold": q, "fraction_of_losers_at_or_below": round(frac, 4)})

    out: Dict[str, Any] = {
        "root": str(root),
        "strict_gate": {k: gate.get(k) for k in ("trades_seen", "trades_complete", "trades_incomplete", "LEARNING_STATUS")},
        "cohort_complete_trade_ids": len(tids),
        "exit_rows_matched": len(rows),
        "exit_rows_missing": len(missing),
        "signal_decay_exit_count": decay_n,
        "run_stitched_event_histogram_top": _run_stitched_event_histogram(root),
        "cliffs": {
            "mfe_pct_all_complete": cliff_table(mfe_all, "MFE % (strict complete)"),
            "mfe_pct_signal_decay": cliff_table(mfe_decay, "MFE % (exit_reason contains signal_decay)"),
            "mfe_pct_signal_decay_winners": cliff_table(mfe_decay_winners, "MFE % (decay exits, pnl_usd>0)"),
            "giveback_pct_mfe_minus_pnl_signal_decay_winners": cliff_table(giveback, "Giveback % (MFE%-pnl% decay winners)"),
            "mae_pct_losers_eq_mae_only": cliff_table(mae_losers, "MAE % (losers with eq.mae only)"),
            "pnl_pct_losers_proxy": cliff_table(pnl_losers, "Exit pnl% (losers)"),
        },
        "point_of_no_return_loser_histogram": pnr_table,
        "recommendations": overlay,
    }

    print(json.dumps(out, indent=2))

    if args.write_overlay:
        overlay_path = root / "config" / "overlays" / "mfe_mae_exit_overlay.json"
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "schema": "mfe_mae_exit_overlay_v1",
            "source": "scripts/_tmp_mfe_mae_analysis.py",
            "apply": {
                "trailing_stop_pct": overlay["trailing_stop_pct"],
                "profit_target_decimal_default": overlay["profit_target_decimal_default"],
                "profit_target_decimal_bear": overlay["profit_target_decimal_bear"],
                "stop_loss_pct_default": overlay["stop_loss_pct_default"],
                "stop_loss_pct_bear": overlay["stop_loss_pct_bear"],
            },
            "_method": overlay.get("_method"),
        }
        overlay_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        print(f"\nWrote {overlay_path}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
