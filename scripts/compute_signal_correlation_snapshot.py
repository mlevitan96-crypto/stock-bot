#!/usr/bin/env python3
"""
Compute Pearson correlation of signal_strength across open positions over a rolling window.
Read-only analytics; not used for trading decisions.

Reads logs/system_events.jsonl (signal_strength_evaluated), builds per-symbol series,
computes pairwise correlation for open symbols (n>=6 overlapping points), writes
state/signal_correlation_cache.json and emits signal_correlation_snapshot.

Usage:
  python scripts/compute_signal_correlation_snapshot.py [--minutes 60] [--topk 20]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENTS = REPO_ROOT / "logs" / "system_events.jsonl"
DEFAULT_CACHE = REPO_ROOT / "state" / "signal_strength_cache.json"
CORRELATION_CACHE = REPO_ROOT / "state" / "signal_correlation_cache.json"

MIN_OVERLAP = 6
EVENT_SCHEMA_VERSION = 1


def _load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return default or {}


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        s = (ts or "").replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _minute_bucket(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M") if dt else ""


def get_open_symbols(repo_root: Path) -> list[str]:
    """Open symbols: Alpaca positions if available, else signal_strength_cache keys."""
    try:
        sys.path.insert(0, str(repo_root))
        import os
        from config.registry import APIConfig
        if os.environ.get("APCA_API_KEY_ID") or getattr(APIConfig, "ALPACA_KEY", None):
            from alpaca.trading.client import TradingClient
            key = os.environ.get("APCA_API_KEY_ID") or getattr(APIConfig, "ALPACA_KEY", "")
            secret = os.environ.get("APCA_API_SECRET_KEY") or getattr(APIConfig, "ALPACA_SECRET", "")
            base = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
            client = TradingClient(key, secret, url_override=base)
            positions = client.get_all_positions() or []
            return [getattr(p, "symbol", "") for p in positions if getattr(p, "symbol", "")]
    except Exception:
        pass
    cache = _load_json(repo_root / "state" / "signal_strength_cache.json", {})
    return [s for s in cache if isinstance(cache.get(s), dict)]


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < MIN_OVERLAP:
        return None
    n = len(x)
    sx = sum(x)
    sy = sum(y)
    sxx = sum(a * a for a in x)
    syy = sum(b * b for b in y)
    sxy = sum(a * b for a, b in zip(x, y))
    num = n * sxy - sx * sy
    den = (n * sxx - sx * sx) * (n * syy - sy * sy)
    if den <= 0:
        return None
    return num / (den ** 0.5)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute signal correlation snapshot (analytics only)")
    parser.add_argument("--minutes", type=float, default=60, help="Lookback window minutes")
    parser.add_argument("--topk", type=int, default=20, help="Max pairs to store")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS, help="system_events.jsonl path")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help="Repo root")
    parser.add_argument("--no-emit", action="store_true", help="Do not append event to system_events")
    args = parser.parse_args()

    repo_root = args.repo.resolve()
    events_path = args.events if args.events.is_absolute() else repo_root / args.events
    since = datetime.now(timezone.utc) - timedelta(minutes=args.minutes)

    open_symbols = get_open_symbols(repo_root)
    if len(open_symbols) < 2:
        out = {
            "as_of": datetime.now(timezone.utc).isoformat(),
            "window_minutes": args.minutes,
            "method": "pearson",
            "pairs": [],
            "top_symbols": {},
            "concentration_risk_score": 0,
            "message": "fallback: insufficient symbols",
        }
        CORRELATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
        CORRELATION_CACHE.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        print("Insufficient open symbols; wrote empty correlation cache.")
        return 0

    # Build per-symbol minute-bucketed series from signal_strength_evaluated
    series: dict[str, dict[str, float]] = defaultdict(dict)
    if not events_path.exists():
        out = {
            "as_of": datetime.now(timezone.utc).isoformat(),
            "window_minutes": args.minutes,
            "method": "pearson",
            "pairs": [],
            "top_symbols": {},
            "concentration_risk_score": 0,
            "message": "fallback: no events file",
        }
        CORRELATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
        CORRELATION_CACHE.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        print("No events file; wrote empty correlation cache.")
        return 0

    with events_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event_type") != "signal_strength_evaluated" or rec.get("subsystem") != "signals":
                continue
            details = rec.get("details") or {}
            sym = rec.get("symbol") or details.get("symbol")
            if not sym or sym not in open_symbols:
                continue
            ts = _parse_ts(rec.get("timestamp") or details.get("timestamp"))
            if ts and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if not ts or ts < since:
                continue
            strength = details.get("signal_strength")
            if strength is None:
                strength = rec.get("signal_strength")
            try:
                strength = float(strength)
            except (TypeError, ValueError):
                continue
            bucket = _minute_bucket(ts)
            if bucket:
                series[sym][bucket] = strength

    # Pairwise correlations (only open symbols with enough points)
    open_set = set(open_symbols)
    symbols_with_data = [s for s in open_symbols if len(series.get(s, {})) >= MIN_OVERLAP]
    pairs: list[dict] = []
    for i, a in enumerate(symbols_with_data):
        for b in symbols_with_data[i + 1 :]:
            buckets_a = set(series[a].keys())
            buckets_b = set(series[b].keys())
            common = sorted(buckets_a & buckets_b)
            if len(common) < MIN_OVERLAP:
                continue
            x = [series[a][t] for t in common]
            y = [series[b][t] for t in common]
            r = pearson(x, y)
            if r is not None:
                pairs.append({"a": a, "b": b, "corr": round(r, 4), "n": len(common)})

    pairs.sort(key=lambda p: abs(p["corr"]), reverse=True)
    pairs_topk = pairs[: args.topk]

    # Per-symbol concentration
    top_symbols: dict[str, dict] = {}
    for sym in open_symbols:
        corrs_for = [(p["corr"], p["a"] if p["b"] == sym else p["b"]) for p in pairs_topk if p["a"] == sym or p["b"] == sym]
        if not corrs_for:
            top_symbols[sym] = {"max_corr": None, "most_correlated_with": None, "avg_corr_topk": None}
            continue
        corrs_for.sort(key=lambda x: abs(x[0]), reverse=True)
        max_corr = corrs_for[0][0]
        most_with = corrs_for[0][1]
        avg_topk = sum(c[0] for c in corrs_for) / len(corrs_for) if corrs_for else None
        top_symbols[sym] = {
            "max_corr": round(max_corr, 4) if max_corr is not None else None,
            "most_correlated_with": most_with,
            "avg_corr_topk": round(avg_topk, 4) if avg_topk is not None else None,
        }

    as_of = datetime.now(timezone.utc).isoformat()
    concentration_risk_score = 0.0
    if pairs_topk:
        concentration_risk_score = round(sum(abs(p["corr"]) for p in pairs_topk[:10]), 4)
    out = {
        "as_of": as_of,
        "window_minutes": args.minutes,
        "method": "pearson",
        "pairs": pairs_topk,
        "top_symbols": top_symbols,
        "pair_count_considered": len(pairs),
        "concentration_risk_score": concentration_risk_score,
    }
    CORRELATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
    CORRELATION_CACHE.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {CORRELATION_CACHE} ({len(pairs_topk)} pairs, {len(top_symbols)} symbols)")

    if not args.no_emit:
        try:
            sys.path.insert(0, str(repo_root))
            from utils.system_events import log_system_event
            concentration_summary = {}
            if pairs_topk:
                concentration_summary["max_abs_corr"] = max(abs(p["corr"]) for p in pairs_topk)
                concentration_summary["avg_abs_corr"] = sum(abs(p["corr"]) for p in pairs_topk) / len(pairs_topk)
            log_system_event(
                "signals",
                "signal_correlation_snapshot",
                "INFO",
                as_of=as_of,
                window_minutes=args.minutes,
                pair_count_considered=len(pairs),
                pairs_topk=pairs_topk,
                concentration_summary=concentration_summary,
                event_schema_version=EVENT_SCHEMA_VERSION,
            )
        except Exception as e:
            print(f"Warning: could not emit event: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
