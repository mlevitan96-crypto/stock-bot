"""
Daily regime dictionary (shadow-only): GEX profile, dark-pool reference levels, sweep activity.

**Not used for live order gating.** Consume only from shadow telemetry paths.

**Architecture (Memory Bank §7.8):** ``UWRegimeMatrix`` **must not** call UW during scoring / shadow
attach paths. It **reads** a JSON snapshot written by ``scripts/run_uw_regime_matrix_refresh.py`` (cron /
premarket). Live REST pulls use ``uw_get`` **only** inside ``fetch_uw_regime_live_snapshot()`` which is
intended for batch jobs — not for ``attach_shadow_telemetry`` hot paths.

**Staleness / lookahead:** The snapshot is point-in-time at refresh; operators should schedule refresh
**before** RTH if shadow labels are used for same-session diagnostics. Dark-pool ``executed_at`` is
filtered by ``UW_REGIME_DP_MAX_AGE_HOURS`` when building the snapshot.
"""
from __future__ import annotations

import json
import logging
import math
import os
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_UW_REGIME_STATE_PATH = REPO_ROOT / "state" / "uw_regime_matrix.json"

# Proximity: price within this fractional band of a DP level counts as "support" (shadow flag only).
_DEFAULT_DP_PROXIMITY_FRAC = 0.003  # 0.3%

_UW_REGIME_POLICY = {
    "ttl_seconds": 120,
    "endpoint_name": "uw_regime_matrix_refresh",
    "max_calls_per_day": 50000,
}


def _safe_upper_ticker(ticker: str) -> str:
    return str(ticker or "").strip().upper()[:32]


def _is_momentum_strategy(intended_strategy: str) -> bool:
    s = str(intended_strategy or "").lower()
    return any(k in s for k in ("momentum", "trend", "breakout", "impulse"))


def _parse_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(str(x).replace(",", "").strip())
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _uw_get_regime(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Thin wrapper for tests; delegates to centralized UW client (retries + auth)."""
    try:
        from src.uw.uw_client import uw_get

        out = uw_get(endpoint, params=params or {}, cache_policy=_UW_REGIME_POLICY)
        return out if isinstance(out, dict) else {"data": []}
    except Exception as exc:
        _log.warning("uw_regime_matrix uw_get exception endpoint=%s err=%s", endpoint, exc)
        return {"data": [], "_uw_api_failure": True, "_exception": str(exc)[:200]}


def _uw_failure(resp: Dict[str, Any]) -> bool:
    return bool(resp.get("_uw_api_failure") or resp.get("_blocked"))


def _net_gamma_sign_from_greek_rows(rows: List[Dict[str, Any]]) -> str:
    """Latest row by ``date``: net call_gamma + put_gamma → positive / negative / neutral."""
    if not rows:
        return "neutral"
    best: Optional[Tuple[str, Dict[str, Any]]] = None
    for r in rows:
        if not isinstance(r, dict):
            continue
        d = str(r.get("date") or "")
        if best is None or d > best[0]:
            best = (d, r)
    if best is None:
        return "neutral"
    r = best[1]
    cg = _parse_float(r.get("call_gamma"))
    pg = _parse_float(r.get("put_gamma"))
    if cg is None and pg is None:
        return "neutral"
    net = (cg or 0.0) + (pg or 0.0)
    eps = 1e-6
    if net > eps:
        return "positive"
    if net < -eps:
        return "negative"
    return "neutral"


def _tickers_from_movers(resp: Dict[str, Any], *, cap: int) -> List[str]:
    out: List[str] = []
    if _uw_failure(resp):
        return out
    data = resp.get("data")
    if not isinstance(data, dict):
        return out
    ma = data.get("most_active")
    if not isinstance(ma, list):
        return out
    for item in ma:
        if not isinstance(item, dict):
            continue
        t = _safe_upper_ticker(str(item.get("ticker") or item.get("symbol") or ""))
        if t and t not in out:
            out.append(t)
        if len(out) >= cap:
            break
    return out


def _fallback_tickers() -> List[str]:
    raw = os.getenv("UW_REGIME_FALLBACK_TICKERS", "SPY,QQQ,AAPL,MSFT,NVDA").strip()
    return [_safe_upper_ticker(x) for x in raw.split(",") if _safe_upper_ticker(x)][:50]


def _aggregate_dark_pool_levels(
    trades: List[Dict[str, Any]],
    *,
    max_levels: int = 3,
    max_age_hours: int = 48,
) -> Dict[str, List[float]]:
    """Ticker → top ``max_levels`` prices by summed volume (recent window best-effort)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max(1, int(max_age_hours)))
    vol_by_ticker_price: Dict[str, Dict[float, float]] = {}
    for tr in trades:
        if not isinstance(tr, dict):
            continue
        sym = _safe_upper_ticker(str(tr.get("ticker") or ""))
        if not sym:
            continue
        ts = tr.get("executed_at")
        if ts:
            try:
                s = str(ts).replace("Z", "+00:00")
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    continue
            except Exception:
                pass
        px = _parse_float(tr.get("price"))
        if px is None or px <= 0:
            continue
        vol = _parse_float(tr.get("volume")) or _parse_float(tr.get("size")) or 0.0
        if vol < 0 or not math.isfinite(vol):
            vol = 0.0
        bucket = vol_by_ticker_price.setdefault(sym, {})
        bucket[round(px, 4)] = bucket.get(round(px, 4), 0.0) + float(vol)
    out: Dict[str, List[float]] = {}
    for sym, px_vol in vol_by_ticker_price.items():
        ranked = sorted(px_vol.items(), key=lambda kv: kv[1], reverse=True)
        out[sym] = [float(p) for p, _ in ranked[:max_levels]]
    return out


def fetch_uw_regime_live_snapshot(tickers: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Batch UW pull for GEX, dark pool levels, and qualifying sweep flow-alerts.

    **Call only from offline jobs** (refresh script / labs), not from ``attach_shadow_telemetry``.
    Uses ``uw_get`` (``UW_API_KEY`` / ``APIConfig``). Never raises; returns possibly empty dicts.
    """
    gex: Dict[str, str] = {}
    dp_levels: Dict[str, List[float]] = {}
    sweeps: Dict[str, bool] = {}

    cap = int(os.getenv("UW_REGIME_GEX_TICKER_CAP", "40") or "40")
    cap = max(3, min(100, cap))
    sleep_s = float(os.getenv("UW_REGIME_INTER_CALL_SLEEP_S", "0.18") or "0.18")
    if not math.isfinite(sleep_s) or sleep_s < 0:
        sleep_s = 0.18

    if tickers:
        tickers_use = [_safe_upper_ticker(t) for t in tickers if _safe_upper_ticker(t)][:cap]
    else:
        movers = _uw_get_regime("/api/market/movers", None)
        tickers_use = _tickers_from_movers(movers, cap=cap)
        if not tickers_use:
            tickers_use = _fallback_tickers()[:cap]

    dp_resp = _uw_get_regime("/api/darkpool/recent", {"limit": 200})
    if not _uw_failure(dp_resp):
        raw = dp_resp.get("data")
        trades_list: List[Dict[str, Any]] = []
        if isinstance(raw, list):
            trades_list = [x for x in raw if isinstance(x, dict)]
        elif isinstance(raw, dict):
            trades_list = [raw]
        try:
            hours = int(os.getenv("UW_REGIME_DP_MAX_AGE_HOURS", "48") or "48")
        except (TypeError, ValueError):
            hours = 48
        dp_levels = _aggregate_dark_pool_levels(trades_list, max_levels=3, max_age_hours=hours)
    time.sleep(sleep_s)

    min_prem = int(os.getenv("UW_REGIME_SWEEP_MIN_PREMIUM", "100000") or "100000")
    for sym in tickers_use:
        path = f"/api/stock/{urllib.parse.quote(sym)}/greek-exposure"
        gresp = _uw_get_regime(path, None)
        if not _uw_failure(gresp):
            gd = gresp.get("data")
            rows: List[Dict[str, Any]] = []
            if isinstance(gd, list):
                rows = [x for x in gd if isinstance(x, dict)]
            elif isinstance(gd, dict):
                rows = [gd]
            sign = _net_gamma_sign_from_greek_rows(rows)
            if sign != "neutral" or rows:
                gex[sym] = sign
        time.sleep(sleep_s)

        fresp = _uw_get_regime(
            "/api/option-trades/flow-alerts",
            {
                "ticker_symbol": sym,
                "min_premium": min_prem,
                "is_sweep": True,
                "is_ask_side": True,
                "is_otm": True,
                "limit": 50,
            },
        )
        if not _uw_failure(fresp):
            fd = fresp.get("data")
            hits: List[Any] = []
            if isinstance(fd, list):
                hits = fd
            elif isinstance(fd, dict):
                inner = fd.get("data")
                if isinstance(inner, list):
                    hits = inner
            for h in hits:
                if isinstance(h, dict) and h.get("has_sweep") is True:
                    tp = _parse_float(h.get("total_premium")) or 0.0
                    if tp >= float(min_prem):
                        sweeps[sym] = True
                        break
        time.sleep(sleep_s)

    return {
        "gex_profile": gex,
        "dark_pool_levels": dp_levels,
        "recent_sweeps": sweeps,
    }


def save_uw_regime_matrix_state(path: Path, snapshot: Dict[str, Any], *, source: str = "uw_regime_refresh") -> None:
    """Atomic JSON write for daemon/cron consumption."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "written_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(source)[:120],
        "gex_profile": dict(snapshot.get("gex_profile") or {}),
        "dark_pool_levels": dict(snapshot.get("dark_pool_levels") or {}),
        "recent_sweeps": dict(snapshot.get("recent_sweeps") or {}),
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    tmp.replace(path)


class UWRegimeMatrix:
    """
    In-memory regime snapshot loaded from ``state/uw_regime_matrix.json`` when present;
    otherwise deterministic mock data (dev / tests).
    """

    def __init__(self) -> None:
        self.gex_profile: Dict[str, str] = {}
        self.dark_pool_levels: Dict[str, List[float]] = {}
        self.recent_sweeps: Dict[str, bool] = {}
        self._source = "uninitialized"
        self._last_live_error: Optional[str] = None
        self._state_path = Path(os.getenv("UW_REGIME_MATRIX_STATE_PATH", str(DEFAULT_UW_REGIME_STATE_PATH)))
        self._load_from_disk_or_mock()

    def _apply_state_payload(self, raw: Dict[str, Any]) -> bool:
        gp = raw.get("gex_profile")
        dp = raw.get("dark_pool_levels")
        sw = raw.get("recent_sweeps")
        if not isinstance(gp, dict) or not isinstance(dp, dict) or not isinstance(sw, dict):
            return False
        gex_out: Dict[str, str] = {}
        for k, v in gp.items():
            sym = _safe_upper_ticker(str(k))
            if not sym:
                continue
            s = str(v or "neutral").strip().lower()
            if s not in ("positive", "negative", "neutral"):
                s = "neutral"
            gex_out[sym] = s
        dp_out: Dict[str, List[float]] = {}
        for k, v in dp.items():
            sym = _safe_upper_ticker(str(k))
            if not sym or not isinstance(v, list):
                continue
            levels: List[float] = []
            for item in v[:12]:
                fv = _parse_float(item)
                if fv is not None and fv > 0:
                    levels.append(float(fv))
            if levels:
                dp_out[sym] = levels[:8]
        sw_out: Dict[str, bool] = {}
        for k, v in sw.items():
            sym = _safe_upper_ticker(str(k))
            if not sym:
                continue
            sw_out[sym] = bool(v)

        self.gex_profile = gex_out
        self.dark_pool_levels = dp_out
        self.recent_sweeps = sw_out
        src = raw.get("source")
        self._source = str(src) if isinstance(src, str) and src.strip() else "cache_file"
        self._last_live_error = None
        return bool(gex_out or dp_out or sw_out)

    def _load_from_disk_or_mock(self) -> None:
        self._last_live_error = None
        try:
            p = self._state_path
            if p.is_file():
                raw = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and self._apply_state_payload(raw):
                    return
        except Exception as exc:
            self._last_live_error = str(exc)[:400]
            _log.warning("uw_regime_matrix cache read failed path=%s err=%s", self._state_path, exc)
        self._refresh_daily_regime_mock()

    def _refresh_daily_regime_mock(self) -> None:
        """Deterministic dummy regime rows for tests and shadow dry-runs."""
        self._last_live_error = None
        self.gex_profile = {
            "AAPL": "negative",
            "MSFT": "positive",
            "SPY": "neutral",
            "QQQ": "positive",
        }
        self.dark_pool_levels = {
            "AAPL": [175.0, 174.5],
            "MSFT": [380.0, 381.25],
            "SPY": [500.0],
        }
        self.recent_sweeps = {
            "AAPL": True,
            "MSFT": False,
            "SPY": False,
            "QQQ": True,
        }
        self._source = "mock_daily_refresh"

    def refresh_from_disk(self) -> None:
        """Re-read JSON snapshot (cheap; safe inside shadow attach)."""
        self._load_from_disk_or_mock()

    def refresh(self) -> None:
        """Alias: reload snapshot from disk (or mock if missing)."""
        self.refresh_from_disk()

    def evaluate_trade_conviction(
        self,
        ticker: str,
        intended_strategy: str,
        current_price: float,
    ) -> Dict[str, Any]:
        """
        Shadow query contract. Never raises: returns a dict with ``regime_conviction`` in
        {``veto``, ``high_conviction_boost``, ``neutral``} and auxiliary flags.

        Rules (first match wins):
        - Positive GEX + momentum strategy → ``veto``
        - Negative GEX + recent sweeps → ``high_conviction_boost``
        - Else if dark-pool proximity → ``dark_pool_support`` flag; ``regime_conviction`` stays ``neutral`` unless above matched
        """
        try:
            return self._evaluate_trade_conviction_inner(ticker, intended_strategy, current_price)
        except Exception as exc:  # pragma: no cover — belt-and-suspenders vs shadow bleed
            return {
                "regime_conviction": "neutral",
                "dark_pool_support": False,
                "gex_read": "unknown",
                "sweeps_recent": False,
                "dark_pool_min_distance_frac": None,
                "intended_strategy_norm": str(intended_strategy or "")[:200],
                "ticker": _safe_upper_ticker(ticker),
                "current_price": float(current_price) if math.isfinite(float(current_price)) else None,
                "regime_matrix_source": self._source,
                "shadow_uw_regime_error": str(exc)[:200],
            }

    def _evaluate_trade_conviction_inner(
        self,
        ticker: str,
        intended_strategy: str,
        current_price: float,
    ) -> Dict[str, Any]:
        sym = _safe_upper_ticker(ticker)
        strat = str(intended_strategy or "neutral_default")
        try:
            px = float(current_price)
        except (TypeError, ValueError):
            px = float("nan")
        if not math.isfinite(px):
            px = 0.0

        gex = str(self.gex_profile.get(sym) or "neutral").strip().lower()
        if gex not in ("positive", "negative", "neutral"):
            gex = "neutral"

        sweeps = bool(self.recent_sweeps.get(sym, False))
        momentum = _is_momentum_strategy(strat)

        levels = self.dark_pool_levels.get(sym) or []
        min_frac: Optional[float] = None
        prox_frac = float(os.getenv("UW_REGIME_DP_PROXIMITY_FRAC", str(_DEFAULT_DP_PROXIMITY_FRAC)) or _DEFAULT_DP_PROXIMITY_FRAC)
        if not math.isfinite(prox_frac) or prox_frac <= 0:
            prox_frac = _DEFAULT_DP_PROXIMITY_FRAC

        if levels and px > 0.0 and math.isfinite(px):
            den = max(abs(px), 1e-12)
            for lvl in levels:
                try:
                    lv = float(lvl)
                except (TypeError, ValueError):
                    continue
                if not math.isfinite(lv) or lv <= 0:
                    continue
                frac_dist = abs(px - lv) / den
                if math.isfinite(frac_dist):
                    min_frac = frac_dist if min_frac is None else min(min_frac, frac_dist)

        dp_support = bool(min_frac is not None and min_frac <= prox_frac)

        conviction = "neutral"
        if gex == "positive" and momentum:
            conviction = "veto"
        elif gex == "negative" and sweeps:
            conviction = "high_conviction_boost"

        out: Dict[str, Any] = {
            "regime_conviction": conviction,
            "dark_pool_support": dp_support,
            "gex_read": gex,
            "sweeps_recent": sweeps,
            "momentum_strategy": momentum,
            "dark_pool_min_distance_frac": None if min_frac is None else round(float(min_frac), 8),
            "dark_pool_proximity_threshold_frac": round(float(prox_frac), 8),
            "intended_strategy_norm": strat[:200],
            "ticker": sym or "UNKNOWN",
            "current_price": round(float(px), 6) if px > 0.0 and math.isfinite(px) else None,
            "regime_matrix_source": self._source,
            "regime_matrix_state_path": str(self._state_path),
        }
        if self._last_live_error:
            out["regime_matrix_last_error"] = self._last_live_error[:200]
        return out


_MATRIX: Optional[UWRegimeMatrix] = None


def get_uw_regime_matrix() -> UWRegimeMatrix:
    global _MATRIX
    if _MATRIX is None:
        _MATRIX = UWRegimeMatrix()
    return _MATRIX


def reset_uw_regime_matrix_for_tests() -> None:
    global _MATRIX
    _MATRIX = None
