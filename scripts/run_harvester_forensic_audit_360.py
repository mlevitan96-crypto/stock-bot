#!/usr/bin/env python3
"""
360° Harvester forensic audit: veto gap, exit/MFE regret, mlf feature correlations & synergy buckets.

Reads:
  - telemetry.alpaca_strict_completeness_gate.STRICT_EPOCH_START (Harvester floor)
  - state/blocked_trades.jsonl (optional shadow: logs/shadow_blocked_trades.jsonl)
  - logs/exit_attribution.jsonl
  - reports/Gemini/alpaca_ml_cohort_flat.csv (Real Join subset for correlation / cohort alignment)

Usage (repo root):
  PYTHONPATH=. python3 scripts/run_harvester_forensic_audit_360.py
  PYTHONPATH=. python3 scripts/run_harvester_forensic_audit_360.py --json-out reports/Gemini/harvester_forensic_audit_360.json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.ml.alpaca_cohort_train import (  # noqa: E402
    _entry_epoch_from_flat_row,
    load_and_filter,
)
from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START  # noqa: E402

TID_OPEN = re.compile(r"^open_[A-Z0-9]+_(.+)$")


def _floor_ts() -> float:
    return float(STRICT_EPOCH_START)


def _parse_ts(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _iter_jsonl(path: Path) -> List[dict]:
    if not path.is_file():
        return []
    out: List[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
            if isinstance(o, dict):
                out.append(o)
        except json.JSONDecodeError:
            continue
    return out


def _blocked_ts(rec: dict) -> Optional[float]:
    return _parse_ts(rec.get("timestamp") or rec.get("ts") or rec.get("_dt"))


def _exit_ts(rec: dict) -> Optional[float]:
    return _parse_ts(rec.get("timestamp") or rec.get("exit_ts"))


def _trade_id(rec: dict) -> str:
    return str(rec.get("trade_id") or "").strip()


def audit_blocked(
    root: Path, floor_ts: float,
) -> Dict[str, Any]:
    paths = [root / "state" / "blocked_trades.jsonl", root / "logs" / "shadow_blocked_trades.jsonl"]
    by_reason: Dict[str, int] = defaultdict(int)
    by_source: Dict[str, int] = defaultdict(int)
    total = 0
    cf_sum = 0.0
    cf_count = 0
    positive_cf_trades = 0
    high_score_blocks = 0  # score >= 4 if present
    sample_fields: Set[str] = set()

    for src_path in paths:
        label = "blocked_trades" if "state" in str(src_path) else "shadow_blocked"
        rows = _iter_jsonl(src_path)
        if not rows:
            continue
        for rec in rows:
            ts = _blocked_ts(rec)
            if ts is None or ts < floor_ts:
                continue
            total += 1
            by_source[label] += 1
            reason = str(rec.get("reason") or rec.get("block_reason") or "unknown").strip()[:120]
            by_reason[reason] += 1
            if len(sample_fields) < 40:
                sample_fields.update(rec.keys())

            sc = rec.get("score") or rec.get("candidate_score")
            try:
                sf = float(sc) if sc is not None else None
            except (TypeError, ValueError):
                sf = None
            if sf is not None and sf >= 4.0:
                high_score_blocks += 1

            for key in (
                "counterfactual_pnl_usd",
                "theoretical_pnl_usd",
                "replay_pnl_usd",
                "estimated_pnl_usd",
                "counterfactual_pnl_30m",
                "counterfactual_pnl_15m",
            ):
                if key in rec and rec[key] is not None:
                    try:
                        cf_sum += float(rec[key])
                        cf_count += 1
                        if float(rec[key]) > 0:
                            positive_cf_trades += 1
                    except (TypeError, ValueError):
                        pass
            nested = rec.get("counterfactual") or rec.get("replay")
            if isinstance(nested, dict):
                for k, v in nested.items():
                    if "pnl" in k.lower() and v is not None:
                        try:
                            cf_sum += float(v)
                            cf_count += 1
                        except (TypeError, ValueError):
                            pass

    return {
        "harvester_floor_epoch": floor_ts,
        "blocked_rows_since_floor": total,
        "by_source_file": dict(by_source),
        "top_block_reasons": dict(sorted(by_reason.items(), key=lambda x: -x[1])[:25]),
        "high_score_blocked_count_gte_4": high_score_blocks,
        "counterfactual_numeric_observations": cf_count,
        "counterfactual_field_sum_usd_or_units": round(cf_sum, 4) if cf_count else None,
        "blocked_rows_with_positive_counterfactual_field": positive_cf_trades,
        "note": (
            "Opportunity cost in USD requires per-row counterfactual PnL in blocked JSONL or a bars replay "
            "(see scripts/blocked_expectancy_analysis.py). Many deployments only log reason/score without "
            "precomputed counterfactual_pnl_* — then only counts/by_reason are reliable here."
        ),
        "sample_field_names_seen": sorted(sample_fields)[:60],
    }


def _mfe_usd_guess(rec: dict) -> Tuple[Optional[float], Optional[float], str]:
    """Return (mfe_usd, realized_pnl_usd, method_note)."""
    eqm = rec.get("exit_quality_metrics")
    if not isinstance(eqm, dict):
        return None, None, "no_exit_quality_metrics"
    pnl = rec.get("realized_pnl_usd")
    if pnl is None:
        pnl = rec.get("pnl")
    try:
        pnl_f = float(pnl) if pnl is not None else None
    except (TypeError, ValueError):
        pnl_f = None
    qty_raw = rec.get("qty") or rec.get("quantity")
    try:
        qty = float(qty_raw) if qty_raw is not None else None
    except (TypeError, ValueError):
        qty = None
    mfe = eqm.get("mfe")
    rpp = eqm.get("realized_pnl_price")
    try:
        mfe_f = float(mfe) if mfe is not None else None
    except (TypeError, ValueError):
        mfe_f = None
    mfe_usd = eqm.get("mfe_usd")
    try:
        if mfe_usd is not None:
            return float(mfe_usd), pnl_f, "mfe_usd_field"
    except (TypeError, ValueError):
        pass
    if mfe_f is not None and qty and qty > 0:
        return mfe_f * qty, pnl_f, "mfe_times_qty"
    if mfe_f is not None and rpp is not None and qty and qty > 0:
        try:
            rpp_f = float(rpp)
            if mfe_f > 0 and rpp_f != 0:
                scale = pnl_f / (rpp_f * qty) if pnl_f is not None and (rpp_f * qty) != 0 else 1.0
                return mfe_f * qty * scale, pnl_f, "mfe_qty_scaled_by_realized_ratio"
        except (TypeError, ValueError):
            pass
    if mfe_f is not None and pnl_f is not None:
        return abs(mfe_f), abs(pnl_f), "fallback_abs_mfe_vs_abs_pnl_units_ambiguous"
    return None, pnl_f, "insufficient_mfe"


def audit_exits(
    root: Path,
    floor_ts: float,
    cohort_trade_ids: Optional[Set[str]],
) -> Dict[str, Any]:
    path = root / "logs" / "exit_attribution.jsonl"
    rows = _iter_jsonl(path)
    ratios: List[float] = []
    givebacks: List[float] = []
    n_with_eqm = 0
    n_cohort = 0
    for rec in rows:
        tid = _trade_id(rec)
        ts_exit = _exit_ts(rec)
        if ts_exit is None or ts_exit < floor_ts:
            continue
        if cohort_trade_ids is not None:
            if not tid or tid not in cohort_trade_ids:
                continue
        else:
            if tid:
                m = TID_OPEN.match(tid)
                if m:
                    open_ts = _parse_ts(m.group(1))
                    if open_ts is None or open_ts < floor_ts:
                        continue
        n_cohort += 1

        mfe_usd, pnl_f, _how = _mfe_usd_guess(rec)
        eqm = rec.get("exit_quality_metrics")
        if isinstance(eqm, dict):
            n_with_eqm += 1
            gb = eqm.get("profit_giveback")
            if gb is not None:
                try:
                    givebacks.append(float(gb))
                except (TypeError, ValueError):
                    pass
        if mfe_usd is not None and pnl_f is not None and mfe_usd > 1e-9:
            ratios.append(pnl_f / mfe_usd)

    return {
        "exit_attribution_path": str(path),
        "rows_in_cohort_window": n_cohort,
        "rows_with_exit_quality_metrics": n_with_eqm,
        "exit_efficiency_realized_over_mfe": {
            "n_comparable": len(ratios),
            "mean_ratio": round(sum(ratios) / len(ratios), 4) if ratios else None,
            "median_ratio": round(sorted(ratios)[len(ratios) // 2], 4) if ratios else None,
        },
        "profit_giveback": {
            "n": len(givebacks),
            "mean": round(sum(givebacks) / len(givebacks), 4) if givebacks else None,
        },
        "interpretation": (
            "Mean realized/MFE near 1 means exits capture most favorable excursion; "
            "low values suggest exit engine leaves money on table (if MFE is in comparable USD units)."
        ),
    }


def _finite(x: Any) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    n = len(xs)
    if n < 5 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = sum((a - mx) ** 2 for a in xs)
    dy = sum((b - my) ** 2 for b in ys)
    if dx <= 0 or dy <= 0:
        return None
    return num / math.sqrt(dx * dy)


def audit_mlf_synergy(root: Path, floor_ts: float) -> Dict[str, Any]:
    flat_path = root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv"
    if not flat_path.is_file():
        return {"error": f"missing {flat_path}"}

    cutoff = datetime.fromtimestamp(floor_ts, tz=timezone.utc)
    headers, kept, stats = load_and_filter(
        flat_path,
        feature_mode="strict_scoreflow",
        require_join_tier=None,
        skip_neutral_no_join=True,
    )
    cohort_rows: List[Dict[str, str]] = []
    for row in kept:
        ep = _entry_epoch_from_flat_row(row)
        if ep is None or ep < floor_ts:
            continue
        cohort_rows.append(row)

    feat_cols = [
        h
        for h in headers
        if (h.startswith("mlf_") or h.startswith("mlf_entry_uw_"))
        and "json" not in h.lower()
        and not h.endswith("_imputed")
    ]

    pnls: List[float] = []
    mat: Dict[str, List[float]] = {c: [] for c in feat_cols}
    for row in cohort_rows:
        p = _finite(row.get("realized_pnl_usd"))
        if p is None:
            continue
        pnls.append(p)
        for c in feat_cols:
            v = _finite(row.get(c))
            mat[c].append(v if v is not None else float("nan"))

    corrs: List[Tuple[str, float]] = []
    for c in feat_cols:
        xs = [mat[c][i] for i in range(len(pnls)) if not math.isnan(mat[c][i])]
        ys = [pnls[i] for i in range(len(pnls)) if not math.isnan(mat[c][i])]
        if len(xs) < 10:
            continue
        r = _pearson(xs, ys)
        if r is not None:
            corrs.append((c, r))
    corrs.sort(key=lambda t: -abs(t[1]))

    aligned: List[Tuple[Dict[str, str], float]] = []
    for row in cohort_rows:
        p = _finite(row.get("realized_pnl_usd"))
        if p is None:
            continue
        aligned.append((row, p))

    def med(name: str) -> float:
        vals = sorted(
            _finite(r.get(name)) for r, _ in aligned if _finite(r.get(name)) is not None
        )
        if not vals:
            return 0.0
        return vals[len(vals) // 2]

    m_cong = med("mlf_scoreflow_components_congress")
    m_smile = med("mlf_scoreflow_components_smile")
    m_sent = med("mlf_entry_uw_sentiment_score")

    clusters: List[Dict[str, Any]] = []
    specs = [
        ("congress_ge_median & sentiment_gt_0", lambda r: (_finite(r.get("mlf_scoreflow_components_congress")) or 0) >= m_cong and (_finite(r.get("mlf_entry_uw_sentiment_score")) or 0) > 0),
        ("congress_ge_median & smile_ge_median", lambda r: (_finite(r.get("mlf_scoreflow_components_congress")) or 0) >= m_cong and (_finite(r.get("mlf_scoreflow_components_smile")) or 0) >= m_smile),
        ("sentiment_gt_0 & smile_ge_median", lambda r: (_finite(r.get("mlf_entry_uw_sentiment_score")) or 0) > 0 and (_finite(r.get("mlf_scoreflow_components_smile")) or 0) >= m_smile),
        ("congress_ge_median only", lambda r: (_finite(r.get("mlf_scoreflow_components_congress")) or 0) >= m_cong),
        ("flow_ge_median & congress_ge_median", lambda r: (_finite(r.get("mlf_scoreflow_components_flow")) or 0) >= med("mlf_scoreflow_components_flow") and (_finite(r.get("mlf_scoreflow_components_congress")) or 0) >= m_cong),
        ("iv_skew_ge_median & congress_ge_median", lambda r: (_finite(r.get("mlf_scoreflow_components_iv_skew")) or 0) >= med("mlf_scoreflow_components_iv_skew") and (_finite(r.get("mlf_scoreflow_components_congress")) or 0) >= m_cong),
    ]
    for label, pred in specs:
        sub_p = [p for r, p in aligned if pred(r)]
        n = len(sub_p)
        if n < 15:
            clusters.append({"cluster": label, "n": n, "win_rate": None, "profit_factor": None})
            continue
        wr = sum(1 for p in sub_p if p > 0) / n
        gw = sum(p for p in sub_p if p > 0)
        gl = sum(p for p in sub_p if p < 0)
        pf = gw / abs(gl) if gl < 0 else None
        clusters.append(
            {
                "cluster": label,
                "n": n,
                "win_rate": round(wr, 4),
                "profit_factor": round(pf, 4) if pf is not None else None,
                "hits_60pct_win_bar": wr >= 0.60,
            }
        )
    clusters.sort(key=lambda d: (-(d.get("win_rate") or 0), -(d.get("n") or 0)))

    top3 = [c for c in clusters if c.get("win_rate") is not None][:3]
    top60 = [c for c in clusters if c.get("hits_60pct_win_bar")]

    return {
        "flat_cohort_strict_real_join_rows": len(cohort_rows),
        "load_and_filter_stats": stats,
        "top_mlf_correlations_with_pnl": [{"feature": a, "pearson_r": round(b, 4)} for a, b in corrs[:30]],
        "synergy_buckets_top_by_win_rate": top3,
        "clusters_with_win_rate_ge_60pct": top60,
        "median_thresholds_used": {
            "congress": m_cong,
            "smile": m_smile,
            "sentiment_score": m_sent,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Harvester 360° forensic audit")
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument(
        "--all-exits-since-floor",
        action="store_true",
        help="Exit/MFE over all exit_attribution since floor (default: Real-Join flat cohort only)",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    floor_ts = _floor_ts()

    cohort_ids: Optional[Set[str]] = None
    if args.all_exits_since_floor:
        cohort_ids = None
    else:
        flat_path = root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv"
        cohort_ids = set()
        if flat_path.is_file():
            _, kept, _ = load_and_filter(
                flat_path,
                feature_mode="strict_scoreflow",
                require_join_tier=None,
                skip_neutral_no_join=True,
            )
            for row in kept:
                ep = _entry_epoch_from_flat_row(row)
                if ep is None or ep < floor_ts:
                    continue
                tid = str(row.get("trade_id") or "").strip()
                if tid:
                    cohort_ids.add(tid)

    report = {
        "harvester_floor_utc": datetime.fromtimestamp(floor_ts, tz=timezone.utc).isoformat(),
        "blocked_veto_audit": audit_blocked(root, floor_ts),
        "exit_mfe_regret_audit": audit_exits(root, floor_ts, cohort_ids),
        "mlf_correlation_synergy_audit": audit_mlf_synergy(root, floor_ts),
    }

    # Verdict heuristics
    blocked = report["blocked_veto_audit"]
    exits = report["exit_mfe_regret_audit"]
    mlf = report["mlf_correlation_synergy_audit"]
    eff = exits.get("exit_efficiency_realized_over_mfe") or {}
    mean_eff = eff.get("mean_ratio")

    veto_signal = blocked.get("blocked_rows_since_floor", 0) > 100 and blocked.get("counterfactual_numeric_observations", 0) == 0
    exit_chokes = mean_eff is not None and mean_eff < 0.35

    if exit_chokes and not veto_signal:
        verdict = "Exit / veto balance: primary concern is EXIT ENGINE (low realized/MFE capture). Signal vetoes are secondary until MFE units are validated."
    elif veto_signal and not exit_chokes:
        verdict = "Exit / veto balance: large blocked volume without counterfactual PnL fields — run blocked_expectancy / bars replay to quantify veto gap; exit efficiency not clearly dominant."
    elif exit_chokes and veto_signal:
        verdict = "Exit / veto balance: BOTH paths need work — exits appear to leave alpha on table (if MFE scaling is correct) AND blocked-trade counterfactuals are not populated for opportunity-cost math."
    else:
        verdict = "Exit / veto balance: inconclusive from automated fields — verify MFE USD scaling in exit_quality_metrics and add counterfactual_pnl to blocked logs for a definitive split."

    report["final_verdict_signal_vs_exit"] = verdict

    print(json.dumps(report, indent=2, default=str))

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        print(f"\nWrote {args.json_out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
