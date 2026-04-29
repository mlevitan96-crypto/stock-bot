#!/usr/bin/env python3
"""
Entry funnel ablation: compare hypothetical forward returns for AI-only, Flow-only, and
simple ensemble rules on historical ``trade_intent`` rows.

Usage (repo root):
  PYTHONPATH=. python scripts/research/entry_funnel_ablation.py --root . --date-from 2026-04-29 --date-to 2026-04-29

Outputs JSON summary to stdout and ``reports/research/entry_funnel_ablation_<date_to>.json``.
Read-only: ``logs/run.jsonl`` (+ rotations), ``data/bars_loader.py`` for forward prices.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _parse_ts(s: Any) -> Optional[datetime]:
    if s is None:
        return None
    try:
        if isinstance(s, (int, float)):
            return datetime.fromtimestamp(float(s), tz=timezone.utc)
        t = str(s).strip().replace("Z", "+00:00")
        d = datetime.fromisoformat(t)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None


def _side_bucket(side: Any) -> str:
    s = str(side or "").strip().lower()
    if s in ("sell", "short"):
        return "short"
    return "long"


def _signed_ret(entry: float, exit_px: float, bucket: str) -> Optional[float]:
    try:
        e = float(entry)
        x = float(exit_px)
        if e <= 0 or x <= 0 or not (math.isfinite(e) and math.isfinite(x)):
            return None
        raw = (x - e) / e
        return -raw if bucket == "short" else raw
    except (TypeError, ValueError):
        return None


def _bars_loader(root: Path):
    path = root / "data" / "bars_loader.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_bars_loader_ablation", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rotated_run_paths(root: Path) -> List[Path]:
    p = root / "logs" / "run.jsonl"
    out = [p] if p.is_file() else []
    for i in range(1, 40):
        q = root / "logs" / f"run.jsonl.{i}"
        if q.is_file():
            out.append(q)
    return out


def _iter_trade_intents(root: Path, d0: str, d1: str) -> Iterable[Dict[str, Any]]:
    for path in _rotated_run_paths(root):
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if "trade_intent" not in line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (o.get("event_type") or "") != "trade_intent":
                    continue
                ts = _parse_ts(o.get("ts") or o.get("timestamp"))
                if ts is None:
                    continue
                ds = ts.strftime("%Y-%m-%d")
                if ds < d0 or ds > d1:
                    continue
                yield o


def _pick_prices(
    bars: List[Dict[str, Any]],
    t0: datetime,
    t1: datetime,
) -> Tuple[Optional[float], Optional[float]]:
    entry = None
    exit_px = None
    for b in bars:
        dt = _parse_ts(b.get("t") or b.get("timestamp"))
        if dt is None:
            continue
        c = b.get("c")
        if c is None:
            c = b.get("close")
        try:
            close = float(c)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(close):
            continue
        if dt >= t0 and entry is None:
            entry = close
        if t0 <= dt <= t1:
            exit_px = close
    return entry, exit_px


def _flow(o: Dict[str, Any]) -> Optional[float]:
    x = o.get("alpha11_flow_strength")
    if x is None:
        uw = o.get("uw_flow_at_intent")
        if isinstance(uw, dict) and uw.get("flow_strength") is not None:
            try:
                return float(uw["flow_strength"])
            except (TypeError, ValueError):
                return None
    try:
        f = float(x)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _score(o: Dict[str, Any]) -> Optional[float]:
    for k in ("score", "composite_score"):
        v = o.get(k)
        if v is None:
            continue
        try:
            s = float(v)
            if math.isfinite(s):
                return s
        except (TypeError, ValueError):
            continue
    return None


@dataclass
class PolicyStats:
    label: str
    n: int = 0
    n_skipped: int = 0
    sum_r: float = 0.0

    def add(self, r: Optional[float]) -> None:
        if r is None:
            self.n_skipped += 1
            return
        self.n += 1
        self.sum_r += float(r)

    @property
    def mean_r(self) -> Optional[float]:
        return (self.sum_r / self.n) if self.n else None


def _percentile_linear(xs: List[float], pct: float) -> Optional[float]:
    """Linear interpolation percentile in [0,100]."""
    if not xs or not (0.0 <= pct <= 100.0):
        return None
    ys = sorted(float(x) for x in xs if math.isfinite(float(x)))
    if not ys:
        return None
    if len(ys) == 1:
        return float(ys[0])
    k = (len(ys) - 1) * (pct / 100.0)
    lo = int(math.floor(k))
    hi = min(lo + 1, len(ys) - 1)
    w = k - float(lo)
    return float(ys[lo]) * (1.0 - w) + float(ys[hi]) * w


def _eval_policy(
    rows: List[Dict[str, Any]],
    label: str,
    take: Any,
    load_bars: Any,
    horizon_min: int,
) -> Dict[str, Any]:
    st = PolicyStats(label=label)
    for o in rows:
        if not take(o):
            continue
        sym = str(o.get("symbol") or "").upper().strip()
        ts = _parse_ts(o.get("ts") or o.get("timestamp"))
        if not sym or ts is None:
            st.n_skipped += 1
            continue
        t_end = ts + timedelta(minutes=horizon_min)
        date_str = ts.strftime("%Y-%m-%d")
        side_b = _side_bucket(o.get("side"))
        try:
            bars = load_bars(
                sym,
                date_str,
                timeframe="1Min",
                start_ts=ts - timedelta(seconds=90),
                end_ts=t_end + timedelta(minutes=5),
                use_cache=True,
                fetch_if_missing=True,
            )
        except Exception:
            bars = []
        if not bars:
            st.n_skipped += 1
            continue
        entry, xit = _pick_prices(bars, ts, t_end)
        st.add(_signed_ret(entry, xit, side_b) if entry and xit else None)
    return {
        "label": st.label,
        "would_trade_count": st.n + st.n_skipped,
        "graded_n": st.n,
        "skipped": st.n_skipped,
        "mean_forward_return": st.mean_r,
        "sum_forward_return": st.sum_r if st.n else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--date-from", required=True)
    ap.add_argument("--date-to", required=True)
    ap.add_argument("--horizon-minutes", type=int, default=60)
    ap.add_argument("--ai-threshold", type=float, default=2.7, help="AI-only: score >= this")
    ap.add_argument("--flow-threshold", type=float, default=0.75, help="Flow-only: flow >= this")
    ap.add_argument("--ensemble-z", type=float, default=1.15, help="Ensemble: z(score)+z(flow) >= this (rough z)")
    args = ap.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root))
    try:
        from dotenv import load_dotenv

        load_dotenv(root / ".env")
    except Exception:
        pass

    bl = _bars_loader(root)
    if bl is None or not callable(getattr(bl, "load_bars", None)):
        print("ERROR: bars_loader missing", file=sys.stderr)
        return 2

    rows = list(_iter_trade_intents(root, args.date_from, args.date_to))
    if not rows:
        print(json.dumps({"error": "no_trade_intent_rows", "date_from": args.date_from, "date_to": args.date_to}))
        return 1

    # Blocked rows approximate "decision at gate"; include entered for completeness
    blocked = [r for r in rows if str(r.get("decision_outcome") or "").lower() == "blocked"]
    cohort = blocked if blocked else rows

    def z_score(s: Optional[float], arr: List[float]) -> float:
        if s is None or not arr:
            return 0.0
        m = sum(arr) / len(arr)
        v = sum((x - m) ** 2 for x in arr) / max(1, len(arr) - 1)
        sig = math.sqrt(v) if v > 1e-12 else 1.0
        return (float(s) - m) / sig

    sc_vals = [x for x in (_score(r) for r in cohort) if x is not None]
    fl_vals = [x for x in (_flow(r) for r in cohort) if x is not None]
    _ensemble_ok = len(sc_vals) >= 3 and len(fl_vals) >= 3

    def ai_only(o: Dict[str, Any]) -> bool:
        s = _score(o)
        return s is not None and s >= float(args.ai_threshold)

    def flow_only(o: Dict[str, Any]) -> bool:
        f = _flow(o)
        return f is not None and f >= float(args.flow_threshold)

    def ensemble(o: Dict[str, Any]) -> bool:
        if not _ensemble_ok:
            return False
        s = _score(o)
        f = _flow(o)
        if s is None or f is None:
            return False
        return z_score(s, sc_vals) + z_score(f, fl_vals) >= float(args.ensemble_z)

    h = max(1, int(args.horizon_minutes))

    # Joint-tail / ensemble-z deciles for nightly OFFENSE_SCORE_TIER1 hints (cron scaffold).
    auto_tune_hints: Dict[str, Any] = {"eligible": _ensemble_ok}
    if _ensemble_ok:
        z_rows: List[Dict[str, float]] = []
        joints: List[float] = []
        for r in cohort:
            s = _score(r)
            f = _flow(r)
            if s is None or f is None:
                continue
            zs = z_score(s, sc_vals) + z_score(f, fl_vals)
            if not (math.isfinite(zs) and math.isfinite(s) and math.isfinite(f)):
                continue
            z_rows.append({"z_sum": float(zs), "score": float(s), "flow": float(f)})
            joints.append(float(s) * float(f))
        z_list = [x["z_sum"] for x in z_rows]
        if z_list:
            p90z = _percentile_linear(z_list, 90.0)
            p50z = _percentile_linear(z_list, 50.0)
            p10z = _percentile_linear(z_list, 10.0)
            top_tail_scores = [x["score"] for x in z_rows if p90z is not None and x["z_sum"] >= p90z]
            med_top = _percentile_linear(top_tail_scores, 50.0) if top_tail_scores else None
            j_p90 = _percentile_linear(joints, 90.0) if joints else None
            suggested_tier = None
            if med_top is not None and math.isfinite(med_top):
                suggested_tier = max(4.0, round(float(med_top), 3))
            auto_tune_hints.update(
                {
                    "ensemble_z_p10": p10z,
                    "ensemble_z_p50": p50z,
                    "ensemble_z_p90": p90z,
                    "n_rows_with_score_and_flow": len(z_rows),
                    "joint_score_times_flow_p90": j_p90,
                    "score_median_in_top_ensemble_z_decile": med_top,
                    "suggested_OFFENSE_SCORE_TIER1": suggested_tier,
                    "suggested_OFFENSE_SIZE_MULT": 1.5,
                    "hint": "Set OFFENSE_SCORE_TIER1 in systemd/.env to suggested value after human sanity check",
                }
            )
        else:
            auto_tune_hints["reason"] = "no_joint_z_rows"

    out = {
        "date_from": args.date_from,
        "date_to": args.date_to,
        "horizon_minutes": h,
        "cohort": "blocked_trade_intent" if blocked else "all_trade_intent",
        "cohort_rows": len(cohort),
        "auto_tune_hints": auto_tune_hints,
        "policies": {
            "ai_only_gte": _eval_policy(cohort, f"ai_only_score>={args.ai_threshold}", ai_only, bl.load_bars, h),
            "flow_only_gte": _eval_policy(
                cohort, f"flow_only_flow>={args.flow_threshold}", flow_only, bl.load_bars, h
            ),
            "ensemble_z_sum": _eval_policy(
                cohort,
                f"ensemble_zscore_sum>={args.ensemble_z}" if _ensemble_ok else "ensemble_skipped_insufficient_n",
                ensemble,
                bl.load_bars,
                h,
            ),
        },
        "ensemble_z_eligible": _ensemble_ok,
        "notes": {
            "forward_return": "signed close-to-close over horizon from first 1m bar at/after intent ts",
            "ensemble": "crude z-sum on cohort distribution — replace with walk-forward logistic for production proof",
        },
    }
    rep = root / "reports" / "research" / f"entry_funnel_ablation_{str(args.date_to).replace('-', '')}.json"
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"\nWrote {rep}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
