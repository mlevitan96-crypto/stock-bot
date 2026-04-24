#!/usr/bin/env python3
"""
Paper PnL evaluation for second_chance_displacement.jsonl (Phase 4).

Joins reeval_result rows to BLOCKED_COUNTERFACTUAL_PNL_FULL.json per_row when available.

Usage (repo root):
  PYTHONPATH=. python3 scripts/audit/evaluate_second_chance_pnl.py \\
    --evidence-dir reports/daily/2026-04-01/evidence \\
    --second-chance-log logs/second_chance_displacement.jsonl
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _norm_ts(s: Optional[str]) -> Optional[str]:
    """Minute-precision join key fragment (matches blocked timestamp vs block_ts)."""
    if not s:
        return None
    t = str(s).strip().replace("+00:00", "Z")
    if len(t) >= 16:
        return t[:16]
    return t


def _join_key(symbol: str, ts: Optional[str]) -> str:
    return f"{str(symbol or '').upper().strip()}|{_norm_ts(ts) or ''}"


def _hour_bucket_utc(ts: Optional[str]) -> str:
    if not ts:
        return "unknown"
    try:
        t = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        h = dt.hour
        if h < 14:
            return "pre_14_utc"
        if h < 20:
            return "14_20_utc"
        return "post_20_utc"
    except Exception:
        return "unknown"


def _vol_bucket(atr_pct: Optional[float]) -> str:
    if atr_pct is None:
        return "unknown"
    try:
        x = float(atr_pct)
    except (TypeError, ValueError):
        return "unknown"
    if x < 0.002:
        return "low_atr_pct"
    if x < 0.006:
        return "mid_atr_pct"
    return "high_atr_pct"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-dir", type=Path, required=True)
    ap.add_argument("--second-chance-log", type=Path, default=Path("logs/second_chance_displacement.jsonl"))
    ap.add_argument("--counterfactual-json", type=Path, default=None)
    args = ap.parse_args()

    ev = args.evidence_dir
    cf_path = args.counterfactual_json or (ev / "BLOCKED_COUNTERFACTUAL_PNL_FULL.json")

    cf_by_key: Dict[str, Dict[str, Any]] = {}
    baseline_disp: List[float] = []
    if cf_path.exists():
        data = json.loads(cf_path.read_text(encoding="utf-8"))
        rows = data.get("per_row") or []
        for r in rows:
            if str(r.get("block_reason") or "") != "displacement_blocked":
                continue
            sym = str(r.get("symbol") or "").upper()
            bts = r.get("block_ts")
            k = _join_key(sym, str(bts) if bts else None)
            if k not in cf_by_key:
                cf_by_key[k] = r
            pva = r.get("pnl_variant_a_usd") or {}
            p60 = pva.get("pnl_60m")
            if p60 is not None:
                try:
                    baseline_disp.append(float(p60))
                except (TypeError, ValueError):
                    pass

    log_path = args.second_chance_log
    reevals: List[Dict[str, Any]] = []
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    j = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if j.get("event") == "reeval_result":
                    reevals.append(j)

    allowed = [r for r in reevals if r.get("reeval_outcome") == "allowed"]
    blocked = [r for r in reevals if r.get("reeval_outcome") == "blocked"]

    def attach_cf(row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        sym = str(row.get("symbol") or "").upper()
        ts = row.get("original_ts")
        k = _join_key(sym, str(ts) if ts else None)
        hit = cf_by_key.get(k)
        if hit:
            return hit, "exact_join"
        return None, "no_join"

    allowed_with_cf: List[Dict[str, Any]] = []
    pnl15: List[float] = []
    pnl30: List[float] = []
    pnl60: List[float] = []
    paper_realized_proxy: List[float] = []

    by_symbol: Dict[str, List[float]] = defaultdict(list)
    by_tod: Dict[str, List[float]] = defaultdict(list)
    by_vol: Dict[str, List[float]] = defaultdict(list)
    by_dir: Dict[str, List[float]] = defaultdict(list)

    for row in allowed:
        cf_row, join_how = attach_cf(row)
        rec = {"row": row, "cf": cf_row, "join": join_how}
        allowed_with_cf.append(rec)
        if not cf_row:
            continue
        pva = cf_row.get("pnl_variant_a_usd") or {}
        for key, bucket in [("pnl_15m", pnl15), ("pnl_30m", pnl30), ("pnl_60m", pnl60)]:
            v = pva.get(key)
            if v is None:
                continue
            try:
                fv = float(v)
                bucket.append(fv)
            except (TypeError, ValueError):
                pass
        p60v = pva.get("pnl_60m")
        if p60v is not None:
            try:
                fv60 = float(p60v)
                paper_realized_proxy.append(fv60)
                sym = str(row.get("symbol") or "").upper()
                by_symbol[sym].append(fv60)
                by_tod[_hour_bucket_utc(str(row.get("original_ts")))].append(fv60)
                atrp = cf_row.get("volatility_proxy_atr_pct")
                by_vol[_vol_bucket(float(atrp) if atrp is not None else None)].append(fv60)
                d = str(row.get("direction") or "unknown")
                by_dir[d].append(fv60)
            except (TypeError, ValueError):
                pass

    def mean(xs: List[float]) -> Optional[float]:
        return round(statistics.mean(xs), 6) if xs else None

    out: Dict[str, Any] = {
        "reeval_result_rows_total": len(reevals),
        "allowed_count": len(allowed),
        "blocked_count": len(blocked),
        "allowed_with_counterfactual_join": sum(1 for x in allowed_with_cf if x["cf"]),
        "paper_pnl_variant_a": {
            "allowed_n_with_cf": len(pnl60),
            "mean_pnl_usd_15m": mean(pnl15),
            "mean_pnl_usd_30m": mean(pnl30),
            "mean_pnl_usd_60m": mean(pnl60),
        },
        "comparison": {
            "original_blocked_outcome_usd": 0.0,
            "baseline_displacement_blocked_mean_pnl_60m_variant_a": mean(baseline_disp),
            "baseline_displacement_blocked_n": len(baseline_disp),
            "second_chance_allowed_mean_pnl_60m_when_joined": mean(pnl60),
        },
        "by_symbol_mean_60m": {k: mean(v) for k, v in sorted(by_symbol.items())},
        "by_time_of_day_mean_60m": {k: mean(v) for k, v in sorted(by_tod.items())},
        "by_volatility_bucket_mean_60m": {k: mean(v) for k, v in sorted(by_vol.items())},
        "by_direction_mean_60m": {k: mean(v) for k, v in sorted(by_dir.items())},
        "counterfactual_path": str(cf_path),
        "second_chance_log": str(log_path),
    }

    (ev / "SECOND_CHANCE_PNL_EVALUATION.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(ev / "SECOND_CHANCE_PNL_EVALUATION.json"), **{k: out[k] for k in ("reeval_result_rows_total", "allowed_count", "blocked_count")}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
