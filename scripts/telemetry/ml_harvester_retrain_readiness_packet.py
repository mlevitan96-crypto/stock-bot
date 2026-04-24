#!/usr/bin/env python3
"""
ML Performance Packet — Harvester-era strict cohort (Real Join = skip_neutral_no_join).

Reuses the same strict filter and cutoff semantics as scripts/telemetry_milestone_watcher.py:
  cutoff = max(TELEMETRY_MILESTONE_SINCE_DATE 00:00 UTC, STRICT_EPOCH_START)
  strict_scoreflow + skip_neutral_no_join=True

Syncs reports/Gemini/milestone_export_flat.csv as a copy of alpaca_ml_cohort_flat.csv (optional).

There is no scripts/generate_24h_comprehensive_analysis.py in this repo; this script is the
standard cohort performance audit for the Harvester flat export.

Usage (repo root):
  PYTHONPATH=. python3 scripts/telemetry/ml_harvester_retrain_readiness_packet.py --run-flattener
  PYTHONPATH=. python3 scripts/telemetry/ml_harvester_retrain_readiness_packet.py --csv reports/Gemini/alpaca_ml_cohort_flat.csv
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.ml.alpaca_cohort_train import (  # noqa: E402
    _entry_epoch_from_flat_row,
    load_and_filter,
)
from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START  # noqa: E402
from telemetry.ml_scoreflow_contract import mlf_scoreflow_component_column_names  # noqa: E402


def _strict_epoch_datetime_utc() -> datetime:
    return datetime.fromtimestamp(float(STRICT_EPOCH_START), tz=timezone.utc)


def _since_datetime_utc() -> datetime:
    floor = _strict_epoch_datetime_utc()
    raw = (os.environ.get("TELEMETRY_MILESTONE_SINCE_DATE") or "").strip()
    if not raw:
        return floor
    try:
        y, m, d = (int(x) for x in raw.split("-", 2))
        env_start = datetime(y, m, d, tzinfo=timezone.utc)
    except Exception:
        return floor
    return env_start if env_start >= floor else floor


def _run_flattener(root: Path) -> int:
    flat = REPO / "scripts" / "telemetry" / "alpaca_ml_flattener.py"
    cmd = [sys.executable, str(flat), "--root", str(root)]
    p = subprocess.run(cmd, cwd=str(root))
    return int(p.returncode)


def _copy_milestone_export(root: Path) -> None:
    src = root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv"
    dst = root / "reports" / "Gemini" / "milestone_export_flat.csv"
    if src.is_file():
        shutil.copy2(src, dst)


def _finite_float(x: Any) -> float | None:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _pearson(xs: List[float], ys: List[float]) -> float | None:
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = sum((a - mx) ** 2 for a in xs)
    dy = sum((b - my) ** 2 for b in ys)
    if dx <= 0 or dy <= 0:
        return None
    return num / math.sqrt(dx * dy)


def _cohort_since_cutoff(
    kept: List[Dict[str, str]], cutoff: datetime,
) -> List[Dict[str, str]]:
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    ts_cut = cutoff.timestamp()
    out: List[Dict[str, str]] = []
    for row in kept:
        ep = _entry_epoch_from_flat_row(row)
        if ep is None or ep < ts_cut:
            continue
        out.append(row)
    return out


def _metrics(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    pnls: List[float] = []
    for r in rows:
        v = _finite_float(r.get("realized_pnl_usd"))
        if v is not None:
            pnls.append(v)
    n = len(pnls)
    if n == 0:
        return {"n": 0}
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_win = sum(wins)
    gross_loss = sum(losses)
    win_rate = len(wins) / n
    pf = None
    if gross_loss < 0:
        pf = gross_win / abs(gross_loss)
    mean_p = sum(pnls) / n
    var = sum((p - mean_p) ** 2 for p in pnls) / max(n - 1, 1)
    std = math.sqrt(var) if var > 0 else 0.0
    sharpe_proxy = (mean_p / std * math.sqrt(n)) if std > 0 else None
    return {
        "n": n,
        "win_rate": win_rate,
        "profit_factor": pf,
        "mean_pnl_usd": mean_p,
        "std_pnl_usd": std,
        "sharpe_trade_proxy": sharpe_proxy,
        "gross_profit_usd": gross_win,
        "gross_loss_usd": gross_loss,
        "expectancy_per_trade_usd": mean_p,
    }


def _feature_columns(headers: Sequence[str]) -> Tuple[List[str], List[str]]:
    """Return (scoreflow mlf_*, auxiliary mlf_entry_uw_* or ecf_*)."""
    h = list(headers)
    sf = [c for c in mlf_scoreflow_component_column_names() if c in h]
    uw = [c for c in h if c.startswith("mlf_entry_uw_") and _is_numeric_candidate(c)]
    ecf = [c for c in h if c.startswith("ecf_") and _is_numeric_candidate(c)]
    aux = sorted(set(uw + ecf))
    return sf, aux


def _is_numeric_candidate(col: str) -> bool:
    low = col.lower()
    if "timestamp" in low or "ts_" in low or "iso" in low:
        return False
    return True


def _correlations(
    rows: List[Dict[str, str]], cols: List[str],
) -> List[Tuple[str, float | None, float | None]]:
    """Per column: corr with win (0/1), corr with pnl (aligned per row, finite feature only)."""
    out: List[Tuple[str, float | None, float | None]] = []
    for c in cols:
        xs: List[float] = []
        ys: List[float] = []
        ws: List[float] = []
        for r in rows:
            p = _finite_float(r.get("realized_pnl_usd"))
            if p is None:
                continue
            fv = _finite_float(r.get(c))
            if fv is None:
                continue
            xs.append(fv)
            ys.append(p)
            ws.append(1.0 if p > 0 else 0.0)
        if len(xs) < 8:
            out.append((c, None, None))
            continue
        out.append((c, _pearson(xs, ws), _pearson(xs, ys)))
    return out


def _rank_features(corr: List[Tuple[str, float | None, float | None]]) -> List[Tuple[str, float]]:
    scored: List[Tuple[str, float]] = []
    for name, cw, cp in corr:
        if cw is None and cp is None:
            continue
        score = 0.0
        if cw is not None:
            score = max(score, abs(cw))
        if cp is not None:
            score = max(score, abs(cp))
        if score > 0:
            scored.append((name, score))
    scored.sort(key=lambda t: -t[1])
    return scored


def main() -> int:
    ap = argparse.ArgumentParser(description="Harvester ML retrain readiness / performance packet")
    ap.add_argument("--root", type=Path, default=REPO, help="Repo root")
    ap.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Flat cohort CSV (default: reports/Gemini/alpaca_ml_cohort_flat.csv under --root)",
    )
    ap.add_argument(
        "--run-flattener",
        action="store_true",
        help="Run scripts/telemetry/alpaca_ml_flattener.py first",
    )
    ap.add_argument(
        "--copy-milestone-export",
        action="store_true",
        default=True,
        help="Copy alpaca_ml_cohort_flat.csv -> milestone_export_flat.csv (default: on)",
    )
    ap.add_argument(
        "--no-copy-milestone-export",
        action="store_false",
        dest="copy_milestone_export",
        help="Skip milestone_export_flat.csv copy",
    )
    ap.add_argument("--json-out", type=Path, default=None, help="Write full packet JSON to path")
    args = ap.parse_args()
    root = args.root.resolve()
    csv_path = (args.csv or (root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")).resolve()

    if args.run_flattener:
        code = _run_flattener(root)
        if code != 0:
            print(f"flattener failed exit={code}", file=sys.stderr)
            return code

    if args.copy_milestone_export:
        _copy_milestone_export(root)

    if not csv_path.is_file():
        print(f"Missing CSV: {csv_path}", file=sys.stderr)
        return 1

    cutoff = _since_datetime_utc()
    headers, kept_all, stats = load_and_filter(
        csv_path,
        feature_mode="strict_scoreflow",
        require_join_tier=None,
        skip_neutral_no_join=True,
    )
    cohort = _cohort_since_cutoff(kept_all, cutoff)
    metrics = _metrics(cohort)
    sf_cols, aux_cols = _feature_columns(headers)
    corr_sf = _correlations(cohort, sf_cols)
    corr_aux = _correlations(cohort, aux_cols) if aux_cols else []
    ranked = _rank_features(corr_sf + corr_aux)
    top3 = ranked[:3]

    packet: Dict[str, Any] = {
        "cutoff_utc": cutoff.isoformat(),
        "csv": str(csv_path),
        "strict_filter_stats_all_csv": stats,
        "real_join_rows_since_cutoff": len(cohort),
        "metrics": metrics,
        "scoreflow_correlations": [
            {"feature": n, "corr_win": cw, "corr_pnl": cp} for n, cw, cp in corr_sf
        ],
        "auxiliary_correlations": [
            {"feature": n, "corr_win": cw, "corr_pnl": cp} for n, cw, cp in corr_aux
        ],
        "top_features_by_abs_corr": [{"feature": n, "abs_corr_max": s} for n, s in top3],
    }

    n = metrics.get("n", 0)
    wr = metrics.get("win_rate")
    pf = metrics.get("profit_factor")
    sh = metrics.get("sharpe_trade_proxy")
    exp = metrics.get("expectancy_per_trade_usd")

    print("=== ML Performance Packet (Harvester Real-Join cohort) ===")
    print(f"csv: {csv_path}")
    print(f"milestone_export_flat.csv: {root / 'reports' / 'Gemini' / 'milestone_export_flat.csv'}")
    print(f"cutoff_utc (milestone watcher semantics): {cutoff.isoformat()}")
    print(f"real_join_rows_since_cutoff (skip_neutral_no_join): {len(cohort)}")
    print(f"strict ML-ready rows (all-time in CSV, same filter): {stats.get('kept')}")
    print()
    print("--- Performance (this cohort) ---")
    print(f"n_trades: {n}")
    if n:
        print(f"win_rate: {wr:.4f}  (null benchmark ~0.50 if no edge)")
        print(f"profit_factor: {pf if pf is not None else 'n/a (no losses or no wins)'}")
        print(f"mean_pnl_usd: {metrics.get('mean_pnl_usd')}")
        print(f"sharpe_trade_proxy (mean/std*sqrt(n)): {sh if sh is not None else 'n/a'}")
        print(f"expectancy_per_trade_usd: {exp}")
    print()
    print("--- Top 3 features (max of |corr(win)|, |corr(pnl)|) ---")
    for i, item in enumerate(packet["top_features_by_abs_corr"], 1):
        print(f"  {i}. {item['feature']}  score={item['abs_corr_max']:.4f}")
    if not top3:
        print("  (insufficient variance or columns — check flat CSV)")
    print()
    ready = len(cohort) >= 250 and n >= 250
    decay_hint = (
        pf is not None
        and pf < 1.0
        and wr is not None
        and wr < 0.45
        and n >= 100
    )
    print("--- Retrain readiness ---")
    print(f"Ready for Retrain (milestone / cohort size): {'YES' if ready else 'NO'}  (>=250 strict real-join rows since cutoff)")
    print(
        "Decay warning (heuristic: PF<1, WR<0.45, n>=100): "
        f"{'YES — live edge looks weak on this slice; retrain may help but is not guaranteed' if decay_hint else 'NO clear decay flag on these summary stats'}"
    )
    print(
        "Note: No frozen 'previous model' cohort is loaded here — feature drift vs an old model "
        "requires a saved baseline export."
    )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(packet, indent=2, default=str) + "\n", encoding="utf-8")
        print(f"\nWrote JSON: {args.json_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
