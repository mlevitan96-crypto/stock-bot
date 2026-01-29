"""
Intraday OHLCV bars loader for counterfactuals and exit attribution.

- Load 1m, 5m, or 15m bars for symbols (e.g. from trade_intent / exit_attribution).
- Cache under data/bars/YYYY-MM-DD/<symbol>_<timeframe>.json.
- Use Alpaca Data API when ALPACA_API_KEY/SECRET are set; otherwise skip and log.
- If bars missing for a symbol: log and skip gracefully (bar freshness check).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BARS_DIR = DATA / "bars"
LOGS = ROOT / "logs"
TELEMETRY_DIR = ROOT / "telemetry"


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


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _alpaca_api() -> Any:
    """Return Alpaca REST client or None if env missing."""
    try:
        key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
        secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
        base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        if not key or not secret:
            return None
        from alpaca_trade_api import REST
        return REST(key, secret, base_url=base)
    except Exception:
        return None


def _fetch_bars_alpaca(
    symbol: str,
    date_str: str,
    timeframe: str = "1Min",
) -> List[Dict[str, Any]]:
    """
    Fetch full-day bars from Alpaca for date_str (US session ~13:30–20:00 UTC).
    Returns list of {t, o, h, l, c, v}.
    """
    api = _alpaca_api()
    if api is None:
        return []
    try:
        y, m, d = date_str.split("-")
        day_start = datetime(int(y), int(m), int(d), 13, 30, 0, tzinfo=timezone.utc)
        day_end = datetime(int(y), int(m), int(d), 20, 0, 0, tzinfo=timezone.utc)
        start_s = _iso(day_start)
        end_s = _iso(day_end)
        resp = api.get_bars(symbol, timeframe, start=start_s, end=end_s, limit=5000)
        df = getattr(resp, "df", None)
        if df is None or len(df) == 0:
            return []
        out = []
        for idx, row in df.iterrows():
            t = idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
            out.append({
                "t": t,
                "o": float(row.get("open", row.get("o", 0))),
                "h": float(row.get("high", row.get("h", 0))),
                "l": float(row.get("low", row.get("l", 0))),
                "c": float(row.get("close", row.get("c", 0))),
                "v": int(row.get("volume", row.get("v", 0))),
            })
        return out
    except Exception as e:
        _warn(f"bars_loader: fetch {symbol} {timeframe} {date_str}: {e}")
        return []


_log: Optional[Callable[[str], None]] = None


def set_logger(fn: Callable[[str], None]) -> None:
    global _log
    _log = fn


def _warn(msg: str) -> None:
    if _log:
        _log(msg)
    else:
        print(f"[bars_loader] {msg}", file=sys.stderr)


def get_alpaca_bar_health(date_str: str) -> Optional[Dict[str, Any]]:
    """
    Read telemetry/YYYY-MM-DD/alpaca_bar_health.json if present.
    Returns {symbol: {status, count, error?}, ...} or None if file missing.
    """
    path = TELEMETRY_DIR / date_str / "alpaca_bar_health.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "error" not in data and "warning" not in data:
            return data
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k not in ("error", "warning") and isinstance(v, dict)}
        return None
    except Exception:
        return None


def cache_path(symbol: str, date_str: str, timeframe: str = "1Min") -> Path:
    safe = symbol.replace("/", "_").strip() or "unknown"
    BARS_DIR.mkdir(parents=True, exist_ok=True)
    (BARS_DIR / date_str).mkdir(parents=True, exist_ok=True)
    return BARS_DIR / date_str / f"{safe}_{timeframe}.json"


def load_bars(
    symbol: str,
    date_str: str,
    timeframe: str = "1Min",
    start_ts: Optional[datetime] = None,
    end_ts: Optional[datetime] = None,
    use_cache: bool = True,
    fetch_if_missing: bool = True,
) -> List[Dict[str, Any]]:
    """
    Load intraday bars for symbol on date_str.
    - use_cache: read from data/bars/YYYY-MM-DD/<symbol>_<timeframe>.json when available.
    - fetch_if_missing: call Alpaca when cache miss; then write cache.
    - start_ts/end_ts: optional window; for full day use None.
    Returns list of {t, o, h, l, c, v}. Empty if missing; log and skip gracefully.
    """
    if not symbol or symbol == "?":
        return []
    path = cache_path(symbol, date_str, timeframe)
    if use_cache and path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            bars = data.get("bars", data) if isinstance(data, dict) else data
            if isinstance(bars, list):
                if start_ts or end_ts:
                    out = []
                    for b in bars:
                        t = b.get("t") or b.get("timestamp")
                        dt = _parse_ts(t)
                        if dt:
                            if start_ts and dt < start_ts:
                                continue
                            if end_ts and dt > end_ts:
                                continue
                        out.append(b)
                    return out
                return bars
        except Exception as e:
            _warn(f"bars_loader: read cache {path}: {e}")

    if not fetch_if_missing:
        return []
    health = get_alpaca_bar_health(date_str)
    if health and isinstance(health.get(symbol), dict):
        status = (health[symbol] or {}).get("status")
        if status in ("MISSING", "ERROR"):
            _warn(f"bars_loader: Alpaca bar health reports {status} for {symbol} 1Min {date_str}; trying 5m/15m fallback")
    bars = _fetch_bars_alpaca(symbol, date_str, timeframe)
    if not bars and timeframe == "1Min":
        for fallback_tf in ("5Min", "15Min"):
            bars = _fetch_bars_alpaca(symbol, date_str, fallback_tf)
            if bars:
                _warn(f"bars_loader: using {fallback_tf} fallback for {symbol} {date_str} ({len(bars)} bars)")
                path_fb = cache_path(symbol, date_str, fallback_tf)
                try:
                    path_fb.parent.mkdir(parents=True, exist_ok=True)
                    path_fb.write_text(
                        json.dumps({"symbol": symbol, "date": date_str, "timeframe": fallback_tf, "bars": bars}, indent=2),
                        encoding="utf-8",
                    )
                except Exception as e:
                    _warn(f"bars_loader: write fallback cache {path_fb}: {e}")
                if start_ts or end_ts:
                    out = []
                    for b in bars:
                        t = b.get("t") or b.get("timestamp")
                        dt = _parse_ts(t)
                        if dt:
                            if start_ts and dt < start_ts:
                                continue
                            if end_ts and dt > end_ts:
                                continue
                        out.append(b)
                    return out
                return bars
        _warn(f"bars_loader: NO_BARS for {symbol} {date_str} (1m/5m/15m all missing)")
        return []
    if not bars:
        _warn(f"bars_loader: no bars for {symbol} {timeframe} {date_str} (missing or skip)")
        return []
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"symbol": symbol, "date": date_str, "timeframe": timeframe, "bars": bars}, indent=2), encoding="utf-8")
    except Exception as e:
        _warn(f"bars_loader: write cache {path}: {e}")
    if start_ts or end_ts:
        out = []
        for b in bars:
            t = b.get("t") or b.get("timestamp")
            dt = _parse_ts(t)
            if dt:
                if start_ts and dt < start_ts:
                    continue
                if end_ts and dt > end_ts:
                    continue
            out.append(b)
        return out
    return bars


def price_at_time(bars: List[Dict], target_ts: datetime, default: Optional[float] = None) -> Optional[float]:
    """Close price at or just before target_ts."""
    if not bars:
        return default
    best = None
    for b in bars:
        t = b.get("t") or b.get("timestamp")
        dt = _parse_ts(t)
        if dt and dt <= target_ts:
            best = float(b.get("c") or b.get("close") or 0)
        elif dt and dt > target_ts:
            break
    return best if best is not None else default


def mfe_mae(
    bars: List[Dict],
    entry_ts: datetime,
    exit_ts: datetime,
    entry_price: float,
    side: str = "long",
) -> Tuple[Optional[float], Optional[float]]:
    """
    MFE and MAE over [entry_ts, exit_ts] from OHLC bars.
    - Long: MFE = max(high - entry), MAE = max(entry - low).
    - Short: MFE = max(entry - low), MAE = max(high - entry).
    Returns (mfe, mae) in price units; (None, None) if no bars.
    """
    if not bars or entry_price <= 0:
        return None, None
    is_long = (side or "long").lower() not in ("short", "sell")
    mfe = 0.0
    mae = 0.0
    any_bar = False
    for b in bars:
        t = b.get("t") or b.get("timestamp")
        dt = _parse_ts(t)
        if not dt or dt < entry_ts or dt > exit_ts:
            continue
        any_bar = True
        h = float(b.get("h") or b.get("high") or 0)
        l = float(b.get("l") or b.get("low") or 0)
        if is_long:
            mfe = max(mfe, h - entry_price)
            mae = max(mae, entry_price - l)
        else:
            mfe = max(mfe, entry_price - l)
            mae = max(mae, h - entry_price)
    if not any_bar:
        return None, None
    return round(mfe, 4), round(mae, 4)
