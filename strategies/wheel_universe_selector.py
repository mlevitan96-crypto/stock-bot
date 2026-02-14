"""
Wheel universe selector: rank by UW intelligence first, then apply liquidity/spread filters.

PATH B contract (UW-first):
- Step 1: Rank universe by UW composite score (from uw_flow_cache + uw_composite_v2).
- Step 2: Select top N candidates by UW rank.
- Step 3: Attach liquidity/OI/spread metrics for explainability; hard filters (spot/contract) run in wheel_strategy per-ticker.

Rules:
- UW composite score is primary sort key when cache available; else fallback to liquidity/IV/spread.
- Average daily volume, OI, spread used as secondary sort and for telemetry.
- Not in excluded sectors; not over-concentrated in portfolio.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[2]

# Sector mapping for universe tickers (non-tech focus)
SECTOR_MAP: Dict[str, str] = {
    "SPY": "Broad Market", "QQQ": "Technology", "DIA": "Broad Market", "IWM": "Broad Market",
    "XLF": "Financials", "XLE": "Energy", "XLI": "Industrials", "XLP": "Consumer Staples",
    "XLV": "Healthcare", "XLB": "Materials", "XLU": "Utilities", "XLY": "Consumer Discretionary",
    "SCHD": "Dividend", "VTV": "Value", "DVY": "Dividend", "VYM": "Dividend",
    "JPM": "Financials", "XOM": "Energy", "CVX": "Energy", "UNH": "Healthcare",
    "PG": "Consumer Staples", "KO": "Consumer Staples", "PEP": "Consumer Staples",
    "HD": "Consumer Discretionary", "MCD": "Consumer Discretionary", "WMT": "Consumer Staples",
    "ABBV": "Healthcare", "PFE": "Healthcare",
}

DEFAULT_EXCLUDED_SECTORS = ["Technology", "Communication Services"]


def _load_universe(config: dict) -> List[str]:
    """Load tickers from universe_source or universe_config."""
    uc = config.get("universe_source") or config.get("universe_config", "config/universe_wheel.yaml")
    path = Path(uc)
    if not path.is_absolute():
        _root = Path(__file__).resolve().parents[1]
        path = (_root / uc).resolve()
    if not path.exists():
        return ["SPY", "QQQ", "DIA", "IWM"]
    try:
        import yaml
        with path.open() as f:
            data = yaml.safe_load(f) or {}
        tickers = data.get("universe", {}).get("tickers", [])
        if isinstance(tickers, list) and tickers:
            return [str(t).strip() for t in tickers if t]
    except Exception as e:
        log.warning("Failed to load universe %s: %s", uc, e)
    return ["SPY", "QQQ", "DIA", "IWM"]


def _get_sector(symbol: str) -> str:
    return SECTOR_MAP.get(symbol.upper(), "Unknown")


def _get_avg_daily_volume(api, symbol: str, days: int = 20) -> float:
    """Fetch average daily volume from bars. Returns 0 on failure."""
    try:
        bars = api.get_bars(symbol, "1Day", limit=min(days + 5, 50))
        if hasattr(bars, "df") and bars.df is not None and not bars.df.empty:
            df = bars.df
            vol_col = "v" if "v" in df.columns else "volume"
            if vol_col in df.columns:
                return float(df[vol_col].mean())
        if isinstance(bars, list) and bars:
            vols = [float(b.get("v", b.get("volume", 0))) for b in bars if b]
            return sum(vols) / len(vols) if vols else 0.0
    except Exception as e:
        log.debug("get_bars for %s: %s", symbol, e)
    return 0.0


def _alpaca_options_request(api, method: str, path: str, params: Optional[dict] = None) -> Optional[dict]:
    """Call Alpaca options API. Avoids circular import with wheel_strategy."""
    try:
        import os
        import requests
        base = getattr(api, "_base_url", None) or os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY", "")
        secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET", "")
        url = base.rstrip("/") + path
        headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
        r = requests.request(method, url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        log.debug("Alpaca options request failed: %s", e)
    return None


def _get_option_open_interest(api, underlying: str) -> int:
    """Fetch max open interest across near-term put options. Returns 0 on failure."""
    try:
        today = datetime.now(timezone.utc).date()
        exp_gte = (today + timedelta(days=5)).strftime("%Y-%m-%d")
        exp_lte = (today + timedelta(days=45)).strftime("%Y-%m-%d")
        data = _alpaca_options_request(
            api, "GET", "/v2/options/contracts",
            params={
                "underlying_symbols": underlying,
                "type": "put",
                "expiration_date_gte": exp_gte,
                "expiration_date_lte": exp_lte,
            },
        )
        contracts = data.get("option_contracts", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not isinstance(contracts, list):
            return 0
        max_oi = 0
        for c in contracts[:50]:
            oi = int(c.get("open_interest", c.get("oi", 0)) or 0)
            max_oi = max(max_oi, oi)
        return max_oi
    except Exception as e:
        log.debug("options OI for %s: %s", underlying, e)
    return 0


def _get_spread_pct(api, symbol: str) -> Optional[float]:
    """Bid-ask spread as fraction of mid. Returns None on failure."""
    try:
        q = api.get_quote(symbol)
        if hasattr(q, "ap") and hasattr(q, "bp"):
            ask = float(q.ap or 0)
            bid = float(q.bp or 0)
        elif isinstance(q, dict):
            ask = float(q.get("ap", q.get("ask_price", 0)) or 0)
            bid = float(q.get("bp", q.get("bid_price", 0)) or 0)
        else:
            return None
        if ask <= 0 and bid <= 0:
            return None
        mid = (ask + bid) / 2 if (ask > 0 and bid > 0) else (ask or bid)
        if mid <= 0:
            return None
        spread = ask - bid
        return spread / mid
    except Exception as e:
        log.debug("get_quote for %s: %s", symbol, e)
    return None


def _check_earnings(symbol: str, window_days: int) -> bool:
    """True if earnings within window (skip). Stub: always False."""
    return False


def _get_iv_proxy(symbol: str) -> float:
    """IV proxy. Stub: return 0.25 (assume adequate IV)."""
    return 0.25


def _rank_by_uw_intelligence(tickers: List[str], config: dict) -> List[Tuple[str, float]]:
    """
    Rank tickers by UW composite score (from uw_flow_cache + uw_composite_v2).
    Returns list of (symbol, uw_composite_score) sorted by score descending.
    Symbols with no UW data get score -1e9 so they sort last.
    """
    try:
        from config.registry import CacheFiles, Directories
        import json
        cache_path = getattr(CacheFiles, "UW_FLOW_CACHE", None) or (Directories.DATA / "uw_flow_cache.json")
        if not cache_path.exists():
            return []
        cache = json.loads(cache_path.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(cache, dict):
            return []
    except Exception:
        return []
    regime = "mixed"
    try:
        from config.registry import StateFiles, read_json
        rp = getattr(StateFiles, "REGIME_POSTURE_STATE", None) or (Path(__file__).resolve().parents[1] / "state" / "regime_posture_state.json")
        if rp and Path(rp).exists():
            data = read_json(Path(rp), default={}) or {}
            regime = (data.get("regime_label") or data.get("regime") or "mixed") or "mixed"
    except Exception:
        pass
    try:
        import uw_composite_v2 as uw_v2
    except Exception:
        return []
    ranked: List[Tuple[str, float]] = []
    for symbol in tickers:
        enriched = cache.get(symbol) if isinstance(cache.get(symbol), dict) else None
        if not enriched:
            ranked.append((symbol, -1e9))
            continue
        try:
            composite = uw_v2.compute_composite_score_v2(symbol, enriched, regime)
            score = float(composite.get("score", 0) or 0) if composite else -1e9
            ranked.append((symbol, score))
        except Exception:
            ranked.append((symbol, -1e9))
    ranked.sort(key=lambda x: -x[1])
    return ranked


def select_wheel_candidates(
    date: str,
    market_data: Any,
    config: dict,
) -> List[Dict[str, Any]]:
    """
    Select and rank wheel candidates from universe.

    Args:
        date: Date string YYYY-MM-DD
        market_data: Alpaca API instance (or dict with api key) for bars/quotes/options
        config: Wheel config from strategies.yaml (universe_*, risk, etc.)

    Returns:
        Ranked list of dicts: symbol, liquidity_score, iv_score, spread_score,
        sector, wheel_suitability_score, and pass/fail reasons.
    """
    api = market_data.get("api") if isinstance(market_data, dict) else market_data
    if api is None:
        api = market_data

    def _get(k: str, default: Any) -> Any:
        return config.get(k, config.get("universe", {}).get(k, default))

    min_vol = _get("universe_min_liquidity_volume", 3_000_000)
    min_oi = _get("universe_min_open_interest", 5_000)
    max_spread = _get("universe_max_spread_pct", 0.005)
    min_iv = _get("universe_min_iv_proxy", 0.15)
    excluded = _get("universe_excluded_sectors", DEFAULT_EXCLUDED_SECTORS) or DEFAULT_EXCLUDED_SECTORS
    max_candidates = _get("universe_max_candidates", 10)

    tickers = _load_universe(config)
    avoid_earnings = config.get("risk", {}).get("avoid_earnings_window_days", 7)

    # Load wheel state for concentration check
    wheel_state = {}
    try:
        from config.registry import StateFiles, read_json
        wp = getattr(StateFiles, "WHEEL_STATE", None) or Path("state") / "wheel_state.json"
        wheel_state = read_json(wp, default={}) or {}
    except Exception:
        pass

    open_csps = wheel_state.get("open_csps", {})
    assigned = wheel_state.get("assigned_shares", {})
    max_per_symbol = config.get("risk", {}).get("max_positions_per_symbol", 2)

    # PATH B Step 1: Restrict to candidates that pass sector/earnings/count (no UW yet)
    candidate_tickers: List[str] = []
    for symbol in tickers:
        sector = _get_sector(symbol)
        if sector in (excluded or []):
            continue

        if _check_earnings(symbol, avoid_earnings):
            continue

        current_count = len(open_csps.get(symbol, []) or []) + (1 if symbol in assigned else 0)
        if current_count >= max_per_symbol:
            continue
        candidate_tickers.append(symbol)

    # PATH B Step 2: Rank by UW intelligence first (primary driver)
    uw_ranked = _rank_by_uw_intelligence(candidate_tickers, config)
    if uw_ranked:
        ordered_symbols = [s for s, _ in uw_ranked]
    else:
        ordered_symbols = candidate_tickers

    # UW quality floor and survivorship/decay filters (wheel_v2)
    uw_quality_min = _get("universe_uw_quality_min", 0.5)
    survivorship_min = 0.0
    decay_exit_rate_max = 0.80
    wheel_candidates_log = REPO_ROOT / "logs" / "wheel_candidates.jsonl"

    def _get_decay_exit_rate(sym: str) -> Optional[float]:
        try:
            from src.intelligence.survivorship import get_decay_exit_rate as _decay_rate
            return _decay_rate(sym, REPO_ROOT)
        except Exception:
            return None

    def _get_survivorship_score(sym: str) -> Optional[float]:
        try:
            from src.intelligence.survivorship import get_survivorship_score
            return get_survivorship_score(sym, REPO_ROOT)
        except Exception:
            return None

    results: List[Dict[str, Any]] = []
    uw_scores_map = {s: sc for s, sc in uw_ranked} if uw_ranked else {}
    for symbol in ordered_symbols:
        sector = _get_sector(symbol)
        vol = _get_avg_daily_volume(api, symbol)
        oi = _get_option_open_interest(api, symbol)
        spread_pct = _get_spread_pct(api, symbol)
        iv_proxy = _get_iv_proxy(symbol)

        pass_vol = vol >= min_vol
        pass_oi = oi >= min_oi
        pass_spread = spread_pct is None or spread_pct <= max_spread
        pass_iv = iv_proxy >= min_iv

        vol_norm = min(1.0, vol / min_vol) if min_vol > 0 else 0.5
        oi_norm = min(1.0, oi / min_oi) if min_oi > 0 else 0.5
        liquidity_score = 0.5 * vol_norm + 0.5 * oi_norm
        iv_score = min(1.0, iv_proxy / 0.5) if iv_proxy else 0.5
        spread_score = 1.0 - (spread_pct or 0) / max_spread if max_spread > 0 and spread_pct is not None else 1.0
        spread_score = max(0, min(1, spread_score))

        wheel_suitability_score = (
            liquidity_score * 0.4 + iv_score * 0.3 + spread_score * 0.3
        )

        uw_score = uw_scores_map.get(symbol)
        if uw_score is not None and uw_score <= -1e8:
            uw_score = None
        if uw_quality_min > 0 and (uw_score is None or uw_score < uw_quality_min):
            continue
        surv_score = _get_survivorship_score(symbol)
        if surv_score is not None and surv_score < survivorship_min:
            continue
        decay_rate = _get_decay_exit_rate(symbol)
        if decay_rate is not None and decay_rate > decay_exit_rate_max:
            continue

        passed = pass_vol and pass_oi and pass_spread and pass_iv
        rec = {
            "symbol": symbol,
            "variant_id": "wheel_v2",
            "uw_composite_score": round(uw_score, 4) if uw_score is not None else None,
            "liquidity_score": round(liquidity_score, 4),
            "iv_score": round(iv_score, 4),
            "spread_score": round(spread_score, 4),
            "sector": sector,
            "wheel_suitability_score": round(wheel_suitability_score, 4),
            "avg_daily_volume": int(vol),
            "open_interest": oi,
            "spread_pct": round(spread_pct, 6) if spread_pct is not None else None,
            "iv_proxy": iv_proxy,
            "pass_volume": pass_vol,
            "pass_oi": pass_oi,
            "pass_spread": pass_spread,
            "pass_iv": pass_iv,
            "passed": passed,
        }
        results.append(rec)
        try:
            wheel_candidates_log.parent.mkdir(parents=True, exist_ok=True)
            with wheel_candidates_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=str) + "\n")
        except Exception:
            pass

    # PATH B: Order already by UW rank; take top N (hard filters spot/contract run in wheel_strategy)
    selected = results[:max_candidates]
    return selected, results
