#!/usr/bin/env python3
"""
Audit that every open position has at least one signal_strength_evaluated event in the last N minutes.

Reads logs/system_events.jsonl and state/signal_strength_cache.json (or Alpaca positions);
exits non-zero if any open position is missing a recent evaluation.

Usage:
  python scripts/audit_signal_propagation.py [--minutes 15] [--events path]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENTS = REPO_ROOT / "logs" / "system_events.jsonl"
DEFAULT_CACHE = REPO_ROOT / "state" / "signal_strength_cache.json"


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


def get_open_positions(repo_root: Path) -> list[tuple[str, str]]:
    """Return list of (symbol, side) for open positions. Prefer Alpaca; fallback to signal_strength_cache."""
    try:
        sys.path.insert(0, str(repo_root))
        from config.registry import APIConfig
        import os
        if not os.environ.get("APCA_API_KEY_ID") and not getattr(APIConfig, "ALPACA_KEY", None):
            raise RuntimeError("Alpaca not configured")
        from alpaca.trading.client import TradingClient
        from config.registry import APIConfig
        key = os.environ.get("APCA_API_KEY_ID") or getattr(APIConfig, "ALPACA_KEY", "")
        secret = os.environ.get("APCA_API_SECRET_KEY") or getattr(APIConfig, "ALPACA_SECRET", "")
        base = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        client = TradingClient(key, secret, url_override=base)
        positions = client.get_all_positions() or []
        out = []
        for p in positions:
            sym = getattr(p, "symbol", None)
            if not sym:
                continue
            qty = float(getattr(p, "qty", 0))
            side = "LONG" if qty > 0 else "SHORT"
            out.append((sym, side))
        return out
    except Exception:
        pass
    cache_path = repo_root / "state" / "signal_strength_cache.json"
    cache = _load_json(cache_path, {})
    if not cache:
        return []
    out = []
    for sym, data in cache.items():
        if isinstance(data, dict):
            side = (data.get("position_side") or "LONG").upper()
            if side not in ("LONG", "SHORT"):
                side = "LONG"
            out.append((sym, side))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit signal propagation for open positions")
    parser.add_argument("--minutes", type=float, default=15, help="Lookback minutes for signal_strength_evaluated events")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS, help="Path to system_events.jsonl")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help="Repo root")
    args = parser.parse_args()

    repo_root = args.repo.resolve()
    events_path = args.events if args.events.is_absolute() else repo_root / args.events
    since = datetime.now(timezone.utc) - timedelta(minutes=args.minutes)

    open_positions = get_open_positions(repo_root)
    if not open_positions:
        print("No open positions; audit passes (nothing to check).")
        return 0

    evaluated: dict[str, list[dict]] = {}
    trend_events: dict[str, list[dict]] = {}
    if events_path.exists():
        with events_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("subsystem") != "signals":
                    continue
                details = rec.get("details") or {}
                ts = _parse_ts(rec.get("timestamp") or details.get("timestamp"))
                if ts and ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts and ts < since:
                    continue
                sym = rec.get("symbol") or details.get("symbol")
                if not sym:
                    continue
                if rec.get("event_type") == "signal_strength_evaluated":
                    if sym not in evaluated:
                        evaluated[sym] = []
                    evaluated[sym].append({
                        "signal_strength": details.get("signal_strength"),
                        "timestamp": rec.get("timestamp") or details.get("timestamp"),
                        "position_side": details.get("position_side"),
                    })
                elif rec.get("event_type") == "signal_trend_evaluated":
                    if sym not in trend_events:
                        trend_events[sym] = []
                    trend_events[sym].append({
                        "signal_delta": details.get("signal_delta"),
                        "signal_trend": details.get("signal_trend"),
                        "timestamp": rec.get("timestamp") or details.get("timestamp"),
                    })

    rows = []
    all_ok = True
    trend_fail = False
    for symbol, side in open_positions:
        evals = evaluated.get(symbol, [])
        if not evals:
            status = "MISSING"
            all_ok = False
            last_strength = ""
            last_at = ""
        else:
            status = "OK"
            last = evals[-1]
            last_strength = str(last.get("signal_strength") if last.get("signal_strength") is not None else "")
            last_at = str(last.get("timestamp") or "")
            if symbol not in trend_events or not trend_events[symbol]:
                trend_fail = True
            elif len(evals) >= 2:
                has_delta = any(t.get("signal_delta") is not None for t in trend_events[symbol])
                if not has_delta:
                    trend_fail = True

        rows.append((symbol, side, last_strength, last_at, status))

    print("SIGNAL PROPAGATION AUDIT (last %.0f minutes)" % args.minutes)
    print("-" * 80)
    print(f"{'symbol':<12} {'side':<6} {'last_signal_strength':<20} {'last_evaluated_at':<28} status")
    print("-" * 80)
    for symbol, side, last_strength, last_at, status in rows:
        print(f"{symbol:<12} {side:<6} {last_strength:<20} {last_at:<28} {status}")
    print("-" * 80)
    if not all_ok:
        print("FAIL: At least one open position has no signal_strength_evaluated event in the window.")
        return 1
    if trend_fail:
        print("FAIL: For evaluated symbols, signal_trend_evaluated must exist; for symbols with >=2 evals, delta must be non-null.")
        return 1
    print("OK: All open positions have at least one signal_strength_evaluated and trend coverage in the window.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
