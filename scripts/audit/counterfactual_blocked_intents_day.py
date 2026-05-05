#!/usr/bin/env python3
"""
Offline counterfactual: blocked trade_intent rows vs forward bar return.

Usage (droplet, repo root):
  PYTHONPATH=. python3 scripts/audit/counterfactual_blocked_intents_day.py --root /root/stock-bot --date 2026-04-29

Uses data/bars_loader.load_bars (Alpaca + cache). Entry = first 1Min close at/after intent
timestamp; exit = last 1Min close at/before intent + forward_minutes (default 60).
Signed return respects long vs short bucket.

CHOP-marginal cohort (Alpha 11): blocked_reason == alpha11_flow_strength_below_gate and
0.75 <= alpha11_flow_strength < 0.83 (would pass base floor 0.75 but fail CHOP-raised floor 0.83
when REGIME_ENGINE applies default ALPHA11_CHOP_FLOOR_ADD).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
    if s in ("buy", "long", "cover", "short_cover", "buy_to_cover"):
        return "long"
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
        if bucket == "short":
            return -raw
        return raw
    except (TypeError, ValueError):
        return None


def _bars_loader(root: Path):
    path = root / "data" / "bars_loader.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_bars_loader_cf", path)
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


def _load_intents(root: Path, day: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
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
                if (o.get("decision_outcome") or "").lower() != "blocked":
                    continue
                ts = _parse_ts(o.get("ts") or o.get("timestamp"))
                if ts is None or ts.strftime("%Y-%m-%d") != day:
                    continue
                rows.append(o)
    return rows


def _pick_prices(
    bars: List[Dict[str, Any]],
    t0: datetime,
    t1: datetime,
) -> Tuple[Optional[float], Optional[float]]:
    """First close at/after t0, last close at/before t1."""
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--date", required=True, help="UTC date prefix YYYY-MM-DD for run.jsonl filter")
    ap.add_argument("--forward-minutes", type=int, default=60)
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
        print("ERROR: data/bars_loader.py missing or invalid")
        return 2
    load_bars = bl.load_bars

    day = str(args.date).strip()
    intents = _load_intents(root, day)
    if not intents:
        print(json.dumps({"error": "no_blocked_trade_intent_rows", "date": day}, indent=2))
        return 1

    fwd = max(1, int(args.forward_minutes))

    def grade(rows: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
        rets: List[float] = []
        skips = Counter()
        for o in rows:
            sym = str(o.get("symbol") or "").upper().strip()
            if not sym:
                skips["no_symbol"] += 1
                continue
            ts = _parse_ts(o.get("ts"))
            if ts is None:
                skips["no_ts"] += 1
                continue
            t_end = ts + timedelta(minutes=fwd)
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
                skips["no_bars"] += 1
                continue
            entry, xit = _pick_prices(bars, ts, t_end)
            if entry is None or xit is None:
                skips["partial_bars"] += 1
                continue
            r = _signed_ret(entry, xit, side_b)
            if r is None:
                skips["bad_prices"] += 1
                continue
            rets.append(float(r))

        n = len(rets)
        wins = sum(1 for x in rets if x > 0)
        losses = sum(1 for x in rets if x < 0)
        flats = sum(1 for x in rets if x == 0)
        out: Dict[str, Any] = {
            "label": label,
            "n_intents": len(rows),
            "n_graded": n,
            "skip_reasons": dict(skips),
            "win_rate": (wins / n) if n else None,
            "mean_signed_return_60m": (sum(rets) / n) if n else None,
            "median_signed_return_60m": (sorted(rets)[n // 2]) if n else None,
            "wins": wins,
            "losses": losses,
            "flat": flats,
            "sum_signed_return": sum(rets) if n else None,
        }
        if n:
            out["min_ret"] = min(rets)
            out["max_ret"] = max(rets)
        return out

    # Full blocked cohort for the day
    full_stats = grade(intents, "all_blocked_today")

    # CHOP-marginal: would pass 0.75 floor but fail 0.83 CHOP floor
    chop_marginal: List[Dict[str, Any]] = []
    for o in intents:
        if (o.get("blocked_reason") or "") != "alpha11_flow_strength_below_gate":
            continue
        a = o.get("alpha11_flow_strength")
        try:
            fs = float(a) if a is not None else None
        except (TypeError, ValueError):
            fs = None
        if fs is None or not math.isfinite(fs):
            continue
        if 0.75 <= fs < 0.83:
            chop_marginal.append(o)

    chop_stats = grade(chop_marginal, "chop_marginal_alpha11_0.75_to_0.83")

    # Optional: label chop from feature snapshot (stricter narrative)
    chop_labeled = [
        o
        for o in chop_marginal
        if str((o.get("feature_snapshot") or {}).get("regime_label") or "").lower() == "chop"
    ]
    chop_labeled_stats = grade(chop_labeled, "chop_marginal_and_feature_regime_label_chop")

    report = {
        "date": day,
        "forward_minutes": fwd,
        "full_blocked_cohort": full_stats,
        "chop_marginal_alpha11_flow_band": chop_stats,
        "chop_marginal_plus_feature_chop_label": chop_labeled_stats,
        "interpretation": {
            "chop_defense": "If mean_signed_return_60m for chop_marginal cohort is negative, "
            "the raised floor avoided hypothetical losses on average; positive means opportunity cost.",
            "all_blocked": "Includes min_notional_floor and alpha11 <0.75; not CHOP-specific.",
        },
    }
    out_path = root / "reports" / "audit" / f"counterfactual_blocked_intents_{day.replace('-', '')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
