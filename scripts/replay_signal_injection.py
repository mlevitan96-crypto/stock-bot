"""
Block 3G: Replay-time signal injection for backtest.
Computes raw signals at (symbol, timestamp) using historical bars and raw_signal_engine.
Used by run_30d_backtest_droplet.py to enrich attribution so Signal Edge Analysis
gets full per-signal, per-regime data without waiting for 30d of live Block 3E logs.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


# Keys we inject (must match Block 3E / ATTRIBUTION_SIGNAL_KEYS + regime_label, sector_momentum)
REPLAY_SIGNAL_KEYS = (
    "trend_signal",
    "momentum_signal",
    "volatility_signal",
    "regime_signal",
    "sector_signal",
    "reversal_signal",
    "breakout_signal",
    "mean_reversion_signal",
)
REPLAY_EXTRA_KEYS = ("regime_label", "sector_momentum")


def _default_load_bars(
    symbol: str,
    date_str: str,
    end_ts: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Load bars for one day; optionally filter to bars <= end_ts."""
    try:
        from data.bars_loader import load_bars
    except Exception:
        return []
    bars = load_bars(
        symbol,
        date_str,
        timeframe="1Min",
        use_cache=True,
        fetch_if_missing=True,
        end_ts=end_ts,
    )
    return bars if isinstance(bars, list) else []


def _bars_to_price_series(bars: List[Dict], event_ts: datetime) -> List[float]:
    """Extract close prices from bars up to event_ts, sorted by time."""
    out: List[tuple] = []
    for b in bars:
        t = b.get("t") or b.get("timestamp")
        dt = _parse_ts(t)
        if dt and dt <= event_ts:
            c = b.get("c") or b.get("close")
            if c is not None:
                try:
                    out.append((dt, float(c)))
                except (TypeError, ValueError):
                    pass
    out.sort(key=lambda x: x[0])
    return [c for _, c in out]


def compute_signals_for_timestamp(
    symbol: str,
    timestamp: Any,
    load_bars_fn: Optional[Callable[[str, str, Optional[datetime]], List[Dict]]] = None,
) -> Dict[str, Any]:
    """
    Block 3G: Compute all raw signals at (symbol, timestamp) for replay attribution.
    - Loads historical bars (multi-day up to timestamp), builds price series.
    - Calls raw_signal_engine.build_raw_signals(price_series, regime_label, sector_momentum).
    - regime_label/sector_momentum at replay time are unknown → use "" and 0.0.
    Returns dict of floats for REPLAY_SIGNAL_KEYS plus regime_label (str), sector_momentum (float).
    Missing data or errors → safe defaults (0.0, None) so attribution never crashes.
    """
    load = load_bars_fn or _default_load_bars
    event_dt = _parse_ts(timestamp)
    if not event_dt or not symbol or symbol == "?":
        return _safe_default_signals()

    # Load several days of bars so we have enough lookback (trend needs 26, etc.)
    # Chronological order: oldest first (day-10 .. day-0)
    all_bars: List[Dict] = []
    for day_offset in range(10, -1, -1):  # 10 days ago .. event day
        d = event_dt.date() - timedelta(days=day_offset)
        date_str = d.strftime("%Y-%m-%d")
        end_ts = event_dt if day_offset == 0 else None
        day_bars = load(symbol, date_str, end_ts)
        if day_bars:
            all_bars.extend(day_bars)

    price_series = _bars_to_price_series(all_bars, event_dt)
    regime_label = ""
    sector_momentum = 0.0

    try:
        from src.signals.raw_signal_engine import build_raw_signals  # type: ignore
    except Exception:
        return _safe_default_signals()

    if len(price_series) < 20:  # mean_reversion needs 20; trend needs 26
        return _safe_default_signals()

    try:
        raw = build_raw_signals(price_series, regime_label, sector_momentum)
        out: Dict[str, Any] = {}
        for k in REPLAY_SIGNAL_KEYS:
            v = raw.get(k)
            if v is not None and isinstance(v, (int, float)):
                out[k] = float(v)
            else:
                out[k] = 0.0
        out["regime_label"] = regime_label or None
        out["sector_momentum"] = float(sector_momentum)
        return out
    except Exception:
        return _safe_default_signals()


def _safe_default_signals() -> Dict[str, Any]:
    """Return dict of safe defaults when bars/signals unavailable."""
    out: Dict[str, Any] = {}
    for k in REPLAY_SIGNAL_KEYS:
        out[k] = 0.0
    out["regime_label"] = None
    out["sector_momentum"] = 0.0
    return out


def inject_signals_into_attribution_dict(
    payload: Dict[str, Any],
    symbol: str,
    timestamp: Any,
    load_bars_fn: Optional[Callable[[str, str, Optional[datetime]], List[Dict]]] = None,
) -> None:
    """
    Mutate payload in place: add signal fields from compute_signals_for_timestamp.
    Works for trade context or blocked_trade record. Field names match Block 3E.
    """
    signals = compute_signals_for_timestamp(symbol, timestamp, load_bars_fn=load_bars_fn)
    if "context" in payload and isinstance(payload["context"], dict):
        ctx = payload["context"]
        for k, v in signals.items():
            if v is not None or k in ("regime_label", "sector_momentum"):
                ctx[k] = v
    for k, v in signals.items():
        if v is not None or k in ("regime_label", "sector_momentum"):
            payload[k] = v
