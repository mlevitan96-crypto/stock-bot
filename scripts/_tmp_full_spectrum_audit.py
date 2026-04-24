#!/usr/bin/env python3
"""
Full-spectrum board audit: exit_attribution + run_stitched (read-only).

Produces reports/board_audit_report.json with executive summary, toxic/alpha clusters,
fee & slippage drag, sector/time concurrency, and ML-architect verdict (Alpha 10 RF lineage).

Remote:
  PYTHONPATH=/root/stock-bot python3 scripts/_tmp_full_spectrum_audit.py --root /root/stock-bot

Optional deep row export (can be large):
  --per-trade-jsonl reports/board_audit_per_trade.jsonl
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
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


def _f(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _parse_ts(s: Any) -> Optional[datetime]:
    if not s or not isinstance(s, str):
        return None
    try:
        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _et_local(dt: datetime) -> Optional[datetime]:
    if _ET is None:
        return None
    return dt.astimezone(_ET)


def _session_segment_et(dt_et: Optional[datetime]) -> str:
    if dt_et is None:
        return "unknown"
    h, m = dt_et.hour, dt_et.minute
    wd = dt_et.weekday()  # 0=Mon
    if wd >= 5:
        return "weekend_et"
    tod = h * 60 + m
    open_m = 9 * 60 + 30
    close_m = 16 * 60
    last_start = close_m - 60
    if tod < open_m:
        return "premarket_et"
    if tod >= close_m:
        return "postmarket_et"
    if tod < open_m + 60:
        return "open_first_hour_et"
    if tod >= last_start:
        return "last_hour_et"
    return "regular_et"


def _sector_from_rec(rec: Dict[str, Any]) -> str:
    esp = rec.get("entry_sector_profile")
    if isinstance(esp, dict):
        s = str(esp.get("sector") or "").strip().upper()
        if s and s not in ("UNKNOWN", "NONE", ""):
            return s[:32]
    return "UNKNOWN"


def _regime_from_rec(rec: Dict[str, Any], which: str) -> str:
    k = "entry_regime" if which == "entry" else "exit_regime"
    v = rec.get(k)
    return str(v or "UNKNOWN").strip().upper()[:24] or "UNKNOWN"


def _exit_pathology(exit_reason: str, exit_reason_code: str) -> str:
    s = f"{exit_reason or ''} {exit_reason_code or ''}".lower()
    if "displac" in s:
        return "displacement"
    if "stop" in s and "trail" not in s:
        return "stop_loss"
    if "trail" in s:
        return "trailing_stop"
    if "profit" in s or "target" in s or "scale" in s:
        return "take_profit_scale"
    if "signal_decay" in s or "decay" in s:
        return "signal_decay"
    if "stale" in s:
        return "stale_time"
    if "time_exit" in s or "time exit" in s:
        return "time_exit"
    return "other_mixed"


def _dedupe_last_wins(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    by_tid: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for rec in rows:
        tid = str(rec.get("trade_id") or "").strip()
        if not tid:
            continue
        if tid not in by_tid:
            order.append(tid)
        by_tid[tid] = rec
    return [by_tid[t] for t in order], len(rows) - len(by_tid)


def _deep_features(rec: Dict[str, Any]) -> Dict[str, Any]:
    entry_ts = _parse_ts(rec.get("entry_timestamp"))
    exit_ts = _parse_ts(rec.get("timestamp"))
    dt_et = _et_local(entry_ts) if entry_ts else None
    dow = dt_et.strftime("%a") if dt_et else "unknown"
    dow_i = dt_et.weekday() if dt_et else None
    hour_et = dt_et.hour if dt_et else None
    session = _session_segment_et(dt_et)
    sector = _sector_from_rec(rec)
    er = _regime_from_rec(rec, "entry")
    xr = _regime_from_rec(rec, "exit")
    pnl = _f(rec.get("pnl")) or 0.0
    pnl_pct = _f(rec.get("pnl_pct")) or 0.0
    hold = _f(rec.get("time_in_trade_minutes"))
    fees = abs(_f(rec.get("fees_usd")) or 0.0)
    ex_slip = _f(rec.get("exit_slippage_bps"))
    en_slip = _f(rec.get("entry_slippage_bps"))
    eq = rec.get("exit_quality_metrics") if isinstance(rec.get("exit_quality_metrics"), dict) else {}
    mfe = _f(eq.get("mfe"))
    mae = _f(eq.get("mae"))
    giveback = _f(eq.get("profit_giveback"))
    ep = _f(rec.get("entry_price")) or 0.0
    qty = abs(_f(rec.get("qty")) or 0.0)
    notional = ep * qty if ep > 0 and qty > 0 else None
    slip_drag_usd = None
    if notional and ex_slip is not None:
        slip_drag_usd = notional * (ex_slip / 10000.0)
    cliff_proxy_min = None
    if hold and hold > 0 and mfe is not None and mfe > 0:
        cliff_proxy_min = hold * (1.0 - (giveback or 0.0)) * (mfe / (mfe + abs(mae or 0.0) + 1e-9))
    sym = str(rec.get("symbol") or "?").upper()[:12]
    return {
        "trade_id": rec.get("trade_id"),
        "symbol": sym,
        "entry_ts_utc": entry_ts.isoformat() if entry_ts else None,
        "exit_ts_utc": exit_ts.isoformat() if exit_ts else None,
        "dow_et": dow,
        "dow_index": dow_i,
        "hour_et": hour_et,
        "session_segment_et": session,
        "sector": sector,
        "entry_regime": er,
        "exit_regime": xr,
        "regime_shift": f"{er}->{xr}",
        "pnl_usd": round(pnl, 6),
        "pnl_pct": round(pnl_pct, 6),
        "hold_minutes": hold,
        "fees_usd": round(fees, 6),
        "exit_slippage_bps": ex_slip,
        "entry_slippage_bps": en_slip,
        "slip_drag_usd_est": round(slip_drag_usd, 6) if slip_drag_usd is not None else None,
        "mfe_price": mfe,
        "mae_price": mae,
        "profit_giveback": giveback,
        "alpha_persistence_cliff_proxy_min": round(cliff_proxy_min, 4) if cliff_proxy_min is not None else None,
        "exit_pathology": _exit_pathology(str(rec.get("exit_reason") or ""), str(rec.get("exit_reason_code") or "")),
        "variant_id": str(rec.get("variant_id") or "")[:48] or None,
        "sector_5m_calendar_bucket_opens_including_self": None,
        "sector_5m_calendar_bucket_other_opens": None,
    }


def _max_peers_same_sector_5m(entry_epochs: List[Tuple[float, str]]) -> Dict[str, float]:
    """For each (t, sector) approximate max count in [t-300, t] including self — O(n log n) per sector."""
    by_sec: DefaultDict[str, List[float]] = defaultdict(list)
    for t, sec in entry_epochs:
        if t > 0:
            by_sec[sec].append(t)
    out: Dict[str, float] = {}
    window = 300.0
    for sec, ts in by_sec.items():
        ts.sort()
        j = 0
        mx = 0
        for i, t0 in enumerate(ts):
            while j < len(ts) and ts[j] - t0 <= window:
                j += 1
            while j > i and ts[j - 1] - t0 > window:
                j -= 1
            mx = max(mx, j - i)
        out[sec] = float(mx)
    return out


def _same_bucket_opens_including_self(t0: float, sector: str, by_bucket: Dict[Tuple[str, int], int]) -> int:
    """Count opens in identical sector + 5-minute UTC calendar bucket (floor epoch/300)."""
    b = int(t0 // 300)
    return int(by_bucket.get((sector, b), 0))


def _load_stitched_entered(root: Path, cap: int = 200_000) -> Tuple[List[Dict[str, Any]], Counter]:
    path = root / "logs" / "run_stitched.jsonl"
    entered: List[Dict[str, Any]] = []
    hist: Counter[str] = Counter()
    n = 0
    for rec in _iter_jsonl(path):
        et = rec.get("event_type") or rec.get("msg") or ""
        hist[str(et)[:48]] += 1
        if str(et) != "trade_intent":
            continue
        if str(rec.get("decision_outcome") or "").lower() != "entered":
            continue
        sym = str(rec.get("symbol") or "").upper().strip()
        if not sym:
            continue
        ts = _parse_ts(rec.get("ts") or rec.get("timestamp"))
        snap = rec.get("feature_snapshot") if isinstance(rec.get("feature_snapshot"), dict) else {}
        reg = str(snap.get("regime_label") or snap.get("regime") or rec.get("regime_label") or "UNKNOWN")[:32]
        sec = "UNKNOWN"
        if isinstance(snap.get("sector_profile"), dict):
            sec = str(snap["sector_profile"].get("sector") or "UNKNOWN").upper()[:32]
        entered.append(
            {
                "symbol": sym,
                "ts_utc": ts.isoformat() if ts else None,
                "epoch": ts.timestamp() if ts else None,
                "regime_label": reg,
                "sector": sec,
            }
        )
        n += 1
        if n >= cap:
            break
    return entered, hist


def _toxic_cover_80(
    buckets: List[Tuple[str, float, int, float]],
) -> Tuple[List[Dict[str, Any]], float]:
    """
    buckets: (key, bucket_total_pnl_usd, n, win_rate)
    Greedy cover by most negative bucket totals until 80% of gross loss mass across all losing USD.
    """
    neg_total = sum(-min(0.0, b[1]) for b in buckets if b[1] < 0)
    if neg_total <= 0:
        return [], 0.0
    sorted_b = sorted((b for b in buckets if b[1] < 0), key=lambda x: x[1])
    target = 0.8 * neg_total
    acc = 0.0
    out: List[Dict[str, Any]] = []
    for key, pnl_sum, n, wr in sorted_b:
        mass = -pnl_sum
        out.append(
            {
                "cluster_key": key,
                "bucket_pnl_usd": round(pnl_sum, 2),
                "trade_count": n,
                "win_rate": round(wr, 4),
            }
        )
        acc += mass
        if acc >= target:
            break
    return out, neg_total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=Path("reports/board_audit_report.json"))
    ap.add_argument("--per-trade-jsonl", type=Path, default=None, help="Optional append one JSON object per trade")
    ap.add_argument("--no-dedupe", action="store_true", help="Use every exit row (not recommended)")
    args = ap.parse_args()
    root = args.root.resolve()
    exit_path = root / "logs" / "exit_attribution.jsonl"

    raw_rows = list(_iter_jsonl(exit_path))
    if args.no_dedupe:
        trades = [r for r in raw_rows if r.get("trade_id")]
        dup_removed = 0
    else:
        trades, dup_removed = _dedupe_last_wins(raw_rows)

    deep_rows: List[Dict[str, Any]] = []
    entry_epochs: List[Tuple[float, str]] = []
    for rec in trades:
        d = _deep_features(rec)
        deep_rows.append(d)
        et = _parse_ts(rec.get("entry_timestamp"))
        if et:
            entry_epochs.append((et.timestamp(), d["sector"]))

    by_bucket_count: Dict[Tuple[str, int], int] = defaultdict(int)
    for t, sec in entry_epochs:
        by_bucket_count[(sec, int(t // 300))] += 1

    crowded: List[int] = []
    for rec, d in zip(trades, deep_rows):
        et = _parse_ts(rec.get("entry_timestamp"))
        if not et:
            crowded.append(0)
            continue
        crowded.append(_same_bucket_opens_including_self(et.timestamp(), d["sector"], dict(by_bucket_count)))
    if crowded:
        sc = sorted(crowded)
        p95_crowd = float(sc[int(0.95 * (len(sc) - 1))]) if len(sc) > 1 else float(sc[0])
    else:
        p95_crowd = 0.0

    for d, c in zip(deep_rows, crowded):
        c = int(c)
        d["sector_5m_calendar_bucket_opens_including_self"] = c
        d["sector_5m_calendar_bucket_other_opens"] = max(0, c - 1)

    agg: DefaultDict[str, Dict[str, Any]] = defaultdict(
        lambda: {"n": 0, "wins": 0, "pnl": 0.0, "fees": 0.0, "slip_bps": []}
    )
    agg_sym_regime: DefaultDict[str, Dict[str, Any]] = defaultdict(
        lambda: {"n": 0, "wins": 0, "pnl": 0.0, "fees": 0.0, "slip_bps": []}
    )

    def add_key(
        store: DefaultDict[str, Dict[str, Any]], key: str, pnl: float, fee: float, win: bool, slip: Optional[float]
    ) -> None:
        b = store[key]
        b["n"] += 1
        if win:
            b["wins"] += 1
        b["pnl"] += pnl
        b["fees"] += fee
        if slip is not None:
            b["slip_bps"].append(slip)

    for rec, d in zip(trades, deep_rows):
        pnl = float(d["pnl_usd"])
        win = pnl > 0
        fee = float(d["fees_usd"])
        slip = d.get("exit_slippage_bps")
        sym = d["symbol"]
        slip_v = slip if isinstance(slip, (int, float)) else None
        # Primary (disjoint per trade): one key per closed trade — avoids double-count in toxic 80% cover.
        primary = f"sym|{sym}|sess|{d['session_segment_et']}|er|{d['entry_regime']}"
        add_key(agg, primary, pnl, fee, win, slip_v)
        # Symbol × entry regime across all sessions (for alpha mining; each trade counted once here too).
        sym_r = f"sym_all_sess|{sym}|er|{d['entry_regime']}"
        add_key(agg_sym_regime, sym_r, pnl, fee, win, slip_v)
        # Secondary exploratory keys (may overlap across trades — for tear-sheet only, not loss-mass sums).
        for k in (
            f"dow|{d['dow_et']}|sess|{d['session_segment_et']}|er|{d['entry_regime']}",
            f"sector|{d['sector']}|sess|{d['session_segment_et']}",
            f"hour|{d['hour_et']}|er|{d['entry_regime']}",
            f"path|{d['exit_pathology']}|sess|{d['session_segment_et']}",
        ):
            add_key(agg, "XREF|" + k, pnl, fee, win, slip_v)

    bucket_rows_primary: List[Tuple[str, float, int, float]] = []
    bucket_rows_xref: List[Tuple[str, float, int, float]] = []
    for k, b in agg.items():
        n = int(b["n"])
        if n < 5:
            continue
        wr = b["wins"] / n if n else 0.0
        row = (k, float(b["pnl"]), n, wr)
        if k.startswith("XREF|"):
            bucket_rows_xref.append(row)
        else:
            bucket_rows_primary.append(row)

    sym_reg_rows: List[Tuple[str, float, int, float]] = []
    for k, b in agg_sym_regime.items():
        n = int(b["n"])
        if n < 20:
            continue
        wr = b["wins"] / n if n else 0.0
        sym_reg_rows.append((k, float(b["pnl"]), n, wr))

    toxic_list, _neg_mass_buckets = _toxic_cover_80(bucket_rows_primary)

    alpha_list = []
    for k, pnl, n, wr in sorted(sym_reg_rows, key=lambda x: -x[3]):
        if wr >= 0.60 and pnl > 0:
            alpha_list.append({"cluster_key": k, "pnl_usd_sum": round(pnl, 2), "trade_count": n, "win_rate": round(wr, 4)})
    alpha_list = sorted(alpha_list, key=lambda x: -x["win_rate"])[:40]

    total_pnl = sum(float(d["pnl_usd"]) for d in deep_rows)
    total_fees = sum(float(d["fees_usd"]) for d in deep_rows)
    wins = sum(1 for d in deep_rows if float(d["pnl_usd"]) > 0)
    n_tr = len(deep_rows)
    win_rate = wins / n_tr if n_tr else 0.0
    gross_win = sum(max(0.0, float(d["pnl_usd"])) for d in deep_rows)
    fees_vs_gross = (total_fees / gross_win) if gross_win > 0 else None
    slips = [float(d["exit_slippage_bps"]) for d in deep_rows if d.get("exit_slippage_bps") is not None]
    slip_est_usd = sum(float(d["slip_drag_usd_est"] or 0) for d in deep_rows)
    slip_cov = sum(1 for d in deep_rows if d.get("exit_slippage_bps") is not None)

    stitched_entered, stitched_hist = _load_stitched_entered(root)
    sec_peer_max = _max_peers_same_sector_5m([(e["epoch"], e["sector"]) for e in stitched_entered if e.get("epoch")])

    pathology = Counter(d["exit_pathology"] for d in deep_rows)

    # ML Architect verdict heuristics
    total_loss_mass = abs(sum(min(0.0, float(d["pnl_usd"])) for d in deep_rows))
    toxic_loss_covered = sum(-min(0.0, t["bucket_pnl_usd"]) for t in toxic_list)
    concentration = toxic_loss_covered / max(1e-9, total_loss_mass)
    toxic_unique_bucket_count = len(toxic_list)
    toxic_frac_of_buckets = toxic_unique_bucket_count / max(1, len(bucket_rows_primary))

    if concentration > 0.55 and toxic_frac_of_buckets > 0.25:
        ml_verdict = "hard_reset_recommended"
        ml_rationale = (
            "Loss mass is concentrated in a few overlapping bucket definitions covering a large fraction of trades; "
            "RF (Alpha 10) likely memorized regime×session noise. Cold-start retrain with segment-blocked negatives "
            "or weighted loss is safer than fine-tune."
        )
    elif concentration > 0.45:
        ml_verdict = "fine_tune_with_reweight"
        ml_rationale = (
            "Material but not total concentration: keep RF architecture, freeze trees n_estimators low, "
            "retrain with sample_weight down-weighting toxic cluster rows and up-weighting alpha_segment rows."
        )
    else:
        ml_verdict = "fine_tune_or_refresh_features"
        ml_rationale = (
            "Losses diffuse across buckets: model drift is moderate. Prefer feature refresh (MFE/MAE truth), "
            "new labels from bar-backed excursions, and incremental fine-tune before full reset."
        )

    blocklist = []
    for t in toxic_list[:25]:
        blocklist.append(
            {
                "cluster_key": t["cluster_key"],
                "action": "BLOCK_OR_HARD_CAP",
                "bucket_pnl_usd": t.get("bucket_pnl_usd"),
                "rationale": "Top toxic mass contributor for 48h defensive posture (paper/live per governance).",
            }
        )

    report: Dict[str, Any] = {
        "schema": "board_audit_report_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "exit_attribution": str(exit_path),
            "run_stitched": str(root / "logs" / "run_stitched.jsonl"),
        },
        "universe": {
            "exit_rows_raw": len(raw_rows),
            "trades_deduped_by_trade_id": n_tr,
            "duplicate_rows_removed_estimate": dup_removed,
            "note": "Counts are from this host's logs/exit_attribution.jsonl (last row wins per trade_id). A higher 'full history' count elsewhere usually means merged shards or no dedupe.",
        },
        "executive_summary": {
            "total_pnl_usd": round(total_pnl, 2),
            "win_rate": round(win_rate, 4),
            "wins": wins,
            "losses": n_tr - wins,
            "total_fees_usd": round(total_fees, 2),
            "fees_as_fraction_of_gross_win_usd": round(fees_vs_gross, 4) if fees_vs_gross is not None else None,
            "exit_slippage_bps_mean_when_present": round(statistics.mean(slips), 4) if slips else None,
            "exit_slippage_bps_median_when_present": round(statistics.median(slips), 4) if slips else None,
            "exit_slippage_coverage_rows": slip_cov,
            "estimated_exit_slippage_drag_usd_sum": round(slip_est_usd, 2),
            "dominant_exit_pathology": pathology.most_common(5),
            "median_hold_minutes": round(statistics.median([float(d["hold_minutes"] or 0) for d in deep_rows]), 2)
            if deep_rows
            else None,
        },
        "fee_drag": {
            "note": "fees_usd from exit rows; slippage $ = exit_slippage_bps/1e4 * entry_notional when both known.",
            "total_fees_usd": round(total_fees, 2),
            "estimated_slippage_usd_sum": round(slip_est_usd, 2),
            "combined_friction_proxy_usd": round(total_fees + slip_est_usd, 2),
        },
        "toxic_segment": {
            "negative_pnl_mass_usd_approx": round(total_loss_mass, 2),
            "primary_disjoint_key": "sym|SYMBOL|sess|SEGMENT|er|ENTRY_REGIME",
            "clusters_explaining_80pct_of_loss_mass_primary_disjoint": toxic_list,
            "concentration_ratio_toxic_clusters_to_total_trade_loss_mass": round(min(1.0, concentration), 4),
            "exploratory_xref_buckets_top_negative_sample": sorted(
                [{"cluster_key": k, "bucket_pnl_usd": round(p, 2), "n": n, "win_rate": round(wr, 4)} for k, p, n, wr in bucket_rows_xref if p < 0],
                key=lambda x: x["bucket_pnl_usd"],
            )[:15],
        },
        "alpha_segment": {
            "clusters_win_rate_ge_0p60_min_n_20_sym_all_sessions": alpha_list[:25],
            "note": "Buckets are sym_all_sess|SYMBOL|er|ENTRY_REGIME (all ET session segments pooled per symbol).",
        },
        "correlation_sector_time": {
            "exit_attribution_same_sector_calendar_5m_bucket_opens_including_self_p95": float(p95_crowd),
            "stitched_entered_intents_loaded": len(stitched_entered),
            "stitched_max_concurrent_same_sector_5m_window": dict(sorted(sec_peer_max.items(), key=lambda x: -x[1])[:20]),
            "run_stitched_event_histogram_top": stitched_hist.most_common(24),
        },
        "blocklist_recommendations_48h": blocklist,
        "strategy_board_48h": {
            "risk": "Enforce blocklist caps on toxic cluster keys; reduce size in symbols/sessions appearing in toxic list.",
            "quant": "Tighten execution on rows with high exit_slippage_bps; review take-profit vs pathology mix.",
            "sre": "Verify exit_attribution completeness; retain stitched logs for concurrency forensics.",
            "ml_architect": {
                "alpha10_rf_lineage_note": "Repository ships Alpha 10 RandomForest exit-MFE gate (models/alpha10_rf_mfe.joblib); no separate Alpha 11 bundle found — verdict applies to that lineage.",
                "verdict": ml_verdict,
                "rationale": ml_rationale,
            },
        },
        "deep_feature_schema": {
            "fields": list(deep_rows[0].keys()) if deep_rows else [],
            "per_trade_export": str(args.per_trade_jsonl) if args.per_trade_jsonl else None,
        },
        "per_trade_sample": deep_rows[:8],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(args.out), "trades": n_tr}, indent=2))

    if args.per_trade_jsonl:
        args.per_trade_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.per_trade_jsonl.open("w", encoding="utf-8") as wf:
            for d in deep_rows:
                wf.write(json.dumps(d, default=str) + "\n")
        print(json.dumps({"per_trade_jsonl": str(args.per_trade_jsonl), "lines": len(deep_rows)}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
