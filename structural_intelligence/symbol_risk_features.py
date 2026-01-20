#!/usr/bin/env python3
"""
Symbol Risk Features (Structural Upgrade)
========================================

Adds risk-aware, selection-relevant per-symbol features:
- realized_vol_5d (annualized)
- realized_vol_20d (annualized)
- beta_vs_spy (rolling)

Constraints:
- Additive only (no scoring weight changes here)
- Best-effort, never blocks trading
- Wrapped with global_failure_wrapper("data")
- Logs failures + staleness to logs/system_events.jsonl
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from utils.system_events import global_failure_wrapper, log_system_event
except Exception:  # pragma: no cover
    def global_failure_wrapper(_subsystem):  # type: ignore
        def _d(fn):
            return fn
        return _d

    def log_system_event(*args, **kwargs):  # type: ignore
        return None

try:
    from config.registry import StateFiles, atomic_write_json, read_json
except Exception:  # pragma: no cover
    StateFiles = None  # type: ignore
    atomic_write_json = None  # type: ignore
    read_json = None  # type: ignore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def _std(xs: List[float]) -> float:
    if not xs:
        return 0.0
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / max(1, (len(xs) - 1))
    return math.sqrt(max(0.0, var))


def _cov(x: List[float], y: List[float]) -> float:
    n = min(len(x), len(y))
    if n < 2:
        return 0.0
    mx = sum(x[:n]) / n
    my = sum(y[:n]) / n
    return sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (n - 1)


def _var(x: List[float]) -> float:
    return _std(x) ** 2


def _pct_returns_from_closes(closes: List[float]) -> List[float]:
    rets: List[float] = []
    for i in range(1, len(closes)):
        a = _safe_float(closes[i - 1], 0.0)
        b = _safe_float(closes[i], 0.0)
        if a <= 0 or b <= 0:
            continue
        rets.append((b - a) / a)
    return rets


def _get_daily_closes(api, symbol: str, *, limit: int = 40) -> Tuple[List[float], Optional[str]]:
    """
    Best-effort daily close series. Returns (closes, last_bar_ts_iso).
    """
    try:
        # IMPORTANT: Some Alpaca environments return only the most recent bar when
        # `start/end` are omitted. We explicitly request a lookback window.
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=120)
        bars = api.get_bars(
            symbol,
            "1Day",
            start=start.isoformat(),
            end=end.isoformat(),
            limit=int(limit),
        )
        df = getattr(bars, "df", None)
        if df is None or df.empty:
            return [], None
        closes = []
        for _, row in df.iterrows():
            closes.append(_safe_float(row.get("close"), 0.0))
        # Timestamp of last bar
        ts_iso = None
        try:
            idx = df.index[-1]
            ts = idx.to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            ts_iso = ts.isoformat()
        except Exception:
            ts_iso = None
        return closes, ts_iso
    except Exception:
        return [], None


def _annualized_realized_vol(returns: List[float]) -> float:
    # Daily returns std * sqrt(252)
    return _std(returns) * math.sqrt(252.0)


def _beta(asset_rets: List[float], bench_rets: List[float]) -> float:
    n = min(len(asset_rets), len(bench_rets))
    if n < 5:
        return 0.0
    x = bench_rets[-n:]
    y = asset_rets[-n:]
    v = _var(x)
    if v <= 0:
        return 0.0
    return _cov(x, y) / v


def read_symbol_risk_features(default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if default is None:
        default = {}
    try:
        if StateFiles is None or not hasattr(StateFiles, "SYMBOL_RISK_FEATURES") or read_json is None:
            return dict(default)
        path = StateFiles.SYMBOL_RISK_FEATURES  # type: ignore[attr-defined]
        data = read_json(path, default=default)
        return data if isinstance(data, dict) else dict(default)
    except Exception:
        return dict(default)


def _cache_fresh(cache: Dict[str, Any], *, max_age_hours: float) -> bool:
    try:
        meta = cache.get("_meta", {}) if isinstance(cache, dict) else {}
        ts = meta.get("ts")
        if not ts:
            return False
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
        if age_hours > float(max_age_hours):
            return False

        # Guard: treat "all zeros" feature cache as invalid (e.g., not enough history returned).
        try:
            syms = cache.get("symbols", {}) if isinstance(cache, dict) else {}
            if isinstance(syms, dict) and syms:
                nonzero = 0
                for v in syms.values():
                    if not isinstance(v, dict):
                        continue
                    if _safe_float(v.get("realized_vol_20d"), 0.0) > 0.001 or _safe_float(v.get("beta_vs_spy"), 0.0) != 0.0:
                        nonzero += 1
                        break
                if nonzero == 0:
                    return False
        except Exception:
            pass
        return True
    except Exception:
        return False


@global_failure_wrapper("data")
def update_symbol_risk_features(
    api,
    *,
    symbols: List[str],
    benchmark: str = "SPY",
    refresh_hours: float = 6.0,
    min_returns_20d: int = 18,
) -> Dict[str, Any]:
    """
    Compute and persist per-symbol vol/beta features.
    """
    symbols_norm = sorted({str(s).upper().strip() for s in (symbols or []) if str(s).strip()})
    if not symbols_norm:
        return {"_meta": {"ts": _now_iso(), "note": "no_symbols"}, "symbols": {}}

    # Use cached values if fresh
    cache = read_symbol_risk_features(default={})
    if isinstance(cache, dict) and _cache_fresh(cache, max_age_hours=refresh_hours):
        return cache

    bench_closes, bench_ts = _get_daily_closes(api, benchmark, limit=45)
    bench_rets = _pct_returns_from_closes(bench_closes)

    out: Dict[str, Any] = {"_meta": {"ts": _now_iso(), "benchmark": benchmark, "benchmark_last_bar_ts": bench_ts}, "symbols": {}}
    ok = 0
    failed: List[str] = []

    for sym in symbols_norm:
        try:
            closes, last_ts = _get_daily_closes(api, sym, limit=45)
            rets = _pct_returns_from_closes(closes)
            # Rolling vols
            vol_5d = _annualized_realized_vol(rets[-5:]) if len(rets) >= 5 else 0.0
            vol_20d = _annualized_realized_vol(rets[-20:]) if len(rets) >= 20 else 0.0
            b = _beta(rets[-20:], bench_rets[-20:])
            # Guard: if insufficient returns, keep beta at 0.
            if len(rets) < min_returns_20d or len(bench_rets) < min_returns_20d:
                b = 0.0
            out["symbols"][sym] = {
                "realized_vol_5d": round(_safe_float(vol_5d), 6),
                "realized_vol_20d": round(_safe_float(vol_20d), 6),
                "beta_vs_spy": round(_safe_float(b), 6),
                "last_bar_ts": last_ts,
            }
            ok += 1
        except Exception:
            failed.append(sym)
            continue

    out["_meta"]["count"] = int(ok)
    out["_meta"]["failed_count"] = int(len(failed))
    if failed:
        out["_meta"]["failed_symbols"] = failed[:50]

    # Persist
    try:
        if StateFiles is not None and hasattr(StateFiles, "SYMBOL_RISK_FEATURES") and atomic_write_json is not None:
            atomic_write_json(StateFiles.SYMBOL_RISK_FEATURES, out)  # type: ignore[attr-defined]
    except Exception as e:
        try:
            log_system_event(
                subsystem="data",
                event_type="symbol_risk_features_persist_failed",
                severity="ERROR",
                details={"error": str(e)},
            )
        except Exception:
            pass

    # Log update summary (bounded)
    try:
        log_system_event(
            subsystem="data",
            event_type="symbol_risk_features_updated",
            severity="INFO",
            details={
                "count": int(ok),
                "failed_count": int(len(failed)),
                "benchmark": benchmark,
            },
        )
    except Exception:
        pass

    return out

