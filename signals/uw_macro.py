#!/usr/bin/env python3
"""
UW Macro Intelligence Extension

Scope:
- Extends UW daemon to fetch macro endpoints every 5 minutes (optional).
- Adds market/sector context to composite scoring.
- Fuses micro (flow/dark/insider) + macro (sector tide, short interest, greeks, ETF flows, ownership, seasonality).
- Reads live weights from data/uw_weights.json for adaptive learning.

New macro endpoints:
- Sector tides (bullish/bearish per sector)
- Short interest & FTDs (squeeze signals)
- Greeks & spot exposures (dealer positioning)
- ETF flows (institutional money flow)
- Institutional ownership (accumulation/distribution)
- Seasonality patterns (historical biases)

Files:
- data/uw_flow_cache.json (augmented with macro fields)
- data/uw_weights.json (live weights for learning)
- data/uw_macro.log.jsonl (macro daemon logs)
"""

import os
import json
import time
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import requests

from config.registry import CacheFiles, append_jsonl as registry_append_jsonl, atomic_write_json as registry_atomic_write_json, read_json as registry_read_json

CACHE_FILE = CacheFiles.UW_FLOW_CACHE
WEIGHTS_FILE = CacheFiles.UW_WEIGHTS
LOG_FILE = CacheFiles.UW_FLOW_CACHE_LOG  # reuse UW cache log sink for macro events

PRIMARY_WATCHLIST = ["AAPL", "MSFT", "NVDA", "QQQ", "SPY", "TSLA"]
DEFAULT_SECTORS = ["Technology", "Healthcare", "Financials", "Energy", "Consumer Discretionary", "Industrials"]
LOOKBACK_DAYS_SEASONALITY = int(os.getenv("LOOKBACK_DAYS_SEASONALITY", "365"))
SHORT_LOOKBACK_DAYS = int(os.getenv("SHORT_LOOKBACK_DAYS", "30"))

# Default weights for macro components
DEFAULT_WEIGHTS = {
    "W_FLOW": 3.00,
    "W_DARK": 1.25,
    "W_INSIDER": 0.75,
    "W_REGIME": 0.35,
    "W_SECTOR": 0.60,
    "W_SHORT": 0.50,
    "W_GREEKS": 0.50,
    "W_SPOT": 0.60,
    "W_ETF": 0.40,
    "W_INSTOWN": 0.40,
    "W_SEASON": 0.35
}


def now_ts() -> int:
    return int(time.time())


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    # Delegate to registry for consistent timestamps/format
    registry_append_jsonl(path, obj)


def atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    registry_atomic_write_json(path, obj)


def read_json(path: Path, default=None):
    return registry_read_json(path, default=default)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def log10_safe(x: float) -> float:
    return math.log10(max(1.0, x))


def load_live_weights(fallback: Dict[str, float]) -> Dict[str, float]:
    try:
        payload = json.loads(WEIGHTS_FILE.read_text())
        w = payload.get("weights") or {}
        out = fallback.copy()
        for k in out.keys():
            out[k] = float(w.get(k, out[k]))
        return out
    except Exception:
        return fallback


class UWMacroClient:
    """Extended UW client for macro intelligence endpoints."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout_sec: int = 15):
        self.base_url = (base_url or os.getenv("UW_API_BASE", "")).rstrip("/")
        self.api_key = api_key or os.getenv("UW_API_KEY", "")
        if not self.base_url or not self.api_key:
            raise RuntimeError("UW client requires UW_API_BASE and UW_API_KEY.")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"})
        self.timeout = timeout_sec

    def fetch_sector_tide(self, sector: str) -> Dict[str, Any]:
        """Sector-wide bullish/bearish net premium."""
        url = f"{self.base_url}/api/market/sector-tide?sector={sector}"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        net = float(d.get("net_premium_usd", 0.0))
        return {
            "sector": sector,
            "bull_premium": float(d.get("bull_premium_usd", 0.0)),
            "bear_premium": float(d.get("bear_premium_usd", 0.0)),
            "net_premium": net,
            "sentiment": "BULLISH" if net > 0 else ("BEARISH" if net < 0 else "MIXED")
        }

    def fetch_top_net_impact(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Top symbols by net options premium impact."""
        url = f"{self.base_url}/api/market/top-net-impact?limit={limit}"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        out = []
        for row in d:
            net = float(row.get("net_premium_usd", 0.0))
            out.append({
                "symbol": row.get("symbol"),
                "net_premium_usd": net,
                "sentiment": "BULLISH" if net > 0 else ("BEARISH" if net < 0 else "MIXED")
            })
        return out

    def fetch_short_interest(self, symbol: str) -> Dict[str, Any]:
        """Short interest data including float utilization and borrow rate."""
        url = f"{self.base_url}/api/shorts/{symbol}/data?days={SHORT_LOOKBACK_DAYS}"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        si = float(d.get("short_interest", d.get("si", 0.0)))
        float_util = float(d.get("float_utilization", d.get("utilization", 0.0)))
        borrow_rate = float(d.get("borrow_rate", 0.0))
        return {
            "short_interest": si,
            "float_utilization": float_util,
            "borrow_rate": borrow_rate,
            "sentiment": "SQUEEZE_RISK" if float_util > 0.80 and borrow_rate > 10.0 else "NORMAL"
        }

    def fetch_ftds(self, symbol: str) -> Dict[str, Any]:
        """Fails-to-deliver data."""
        url = f"{self.base_url}/api/shorts/{symbol}/ftds?days={SHORT_LOOKBACK_DAYS}"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        total_ftd = sum([float(x.get("shares", 0)) for x in (d if isinstance(d, list) else [])])
        return {"total_ftd_shares": total_ftd}

    def fetch_greeks(self, symbol: str) -> Dict[str, Any]:
        """Options greeks (delta, gamma, vega, theta)."""
        url = f"{self.base_url}/api/stock/{symbol}/greeks"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        return {
            "delta": float(d.get("delta", 0.0)),
            "gamma": float(d.get("gamma", 0.0)),
            "vega": float(d.get("vega", 0.0)),
            "theta": float(d.get("theta", 0.0))
        }

    def fetch_spot_exposures(self, symbol: str) -> Dict[str, Any]:
        """Spot gamma exposures by strike (dealer positioning)."""
        url = f"{self.base_url}/api/stock/{symbol}/spot-exposures/strike"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        total_call = sum(float(x.get("call_notional_usd", 0.0)) for x in (d if isinstance(d, list) else []))
        total_put = sum(float(x.get("put_notional_usd", 0.0)) for x in (d if isinstance(d, list) else []))
        sentiment = "BULLISH" if total_call > total_put else ("BEARISH" if total_put > total_call else "MIXED")
        return {"call_notional_usd": total_call, "put_notional_usd": total_put, "sentiment": sentiment}

    def fetch_etf_flows(self, symbol: str) -> Dict[str, Any]:
        """ETF inflow/outflow data."""
        url = f"{self.base_url}/api/etfs/{symbol}/in_outflow"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        net_flow = float(d.get("net_flow_usd", 0.0))
        sentiment = "BULLISH" if net_flow > 0 else ("BEARISH" if net_flow < 0 else "MIXED")
        return {"net_flow_usd": net_flow, "sentiment": sentiment}

    def fetch_institutional_ownership(self, symbol: str) -> Dict[str, Any]:
        """Institutional ownership percentage and recent changes."""
        url = f"{self.base_url}/api/institution/{symbol}/ownership"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        inst_own = float(d.get("ownership_pct", 0.0))
        change_pct = float(d.get("ownership_change_pct", 0.0))
        sentiment = "ACCUMULATION" if change_pct > 0 else ("DISTRIBUTION" if change_pct < 0 else "FLAT")
        return {"ownership_pct": inst_own, "change_pct": change_pct, "sentiment": sentiment}

    def fetch_seasonality(self, symbol: str, days: int = LOOKBACK_DAYS_SEASONALITY) -> Dict[str, Any]:
        """Historical seasonality patterns."""
        url = f"{self.base_url}/api/seasonality/{symbol}/monthly?days={int(days)}"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        d = r.json().get("data", r.json())
        avg_ret = float(d.get("avg_monthly_return_pct", 0.0))
        best_month = d.get("best_month", "")
        worst_month = d.get("worst_month", "")
        sentiment = "BULLISH" if avg_ret > 0 else ("BEARISH" if avg_ret < 0 else "MIXED")
        return {"avg_monthly_return_pct": avg_ret, "best_month": best_month, "worst_month": worst_month, "sentiment": sentiment}


def assemble_macro_for_symbol(client: UWMacroClient, symbol: str) -> Dict[str, Any]:
    """Fetch all macro signals for a symbol (best-effort, graceful degradation)."""
    out: Dict[str, Any] = {}
    
    try:
        out["short_interest"] = client.fetch_short_interest(symbol)
    except Exception:
        out["short_interest"] = {"sentiment": "NORMAL"}

    try:
        out["ftds"] = client.fetch_ftds(symbol)
    except Exception:
        out["ftds"] = {"total_ftd_shares": 0}

    try:
        out["greeks"] = client.fetch_greeks(symbol)
    except Exception:
        out["greeks"] = {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0}

    try:
        out["spot_exposures"] = client.fetch_spot_exposures(symbol)
    except Exception:
        out["spot_exposures"] = {"call_notional_usd": 0.0, "put_notional_usd": 0.0, "sentiment": "MIXED"}

    try:
        out["etf_flows"] = client.fetch_etf_flows(symbol if symbol in ("SPY","QQQ","IWM") else "SPY")
    except Exception:
        out["etf_flows"] = {"net_flow_usd": 0.0, "sentiment": "MIXED"}

    try:
        out["institutional_ownership"] = client.fetch_institutional_ownership(symbol)
    except Exception:
        out["institutional_ownership"] = {"ownership_pct": 0.0, "change_pct": 0.0, "sentiment": "FLAT"}

    try:
        out["seasonality"] = client.fetch_seasonality(symbol)
    except Exception:
        out["seasonality"] = {"avg_monthly_return_pct": 0.0, "sentiment": "MIXED"}

    return out


def assemble_sector_tides(client: UWMacroClient, sectors: List[str]) -> Dict[str, Any]:
    """Fetch sector tide data for all sectors."""
    out: Dict[str, Any] = {}
    for sec in sectors:
        try:
            out[sec] = client.fetch_sector_tide(sec)
        except Exception:
            out[sec] = {"sector": sec, "net_premium": 0.0, "sentiment": "MIXED"}
    return out


def infer_sector(symbol: str) -> str:
    """Map symbol to sector (basic heuristic - replace with theme_map resolver)."""
    tech = {"AAPL","MSFT","NVDA","QQQ","TSLA","META","GOOGL","AMD","AVGO"}
    health = {"ISRG","UNH","PFE","MRNA"}
    energy = {"XOM","CVX"}
    if symbol in tech or symbol == "QQQ": return "Technology"
    if symbol in health: return "Healthcare"
    if symbol in energy: return "Energy"
    if symbol == "SPY": return "Industrials"
    return "Consumer Discretionary"


def compute_macro_score(symbol: str, uw_cache: Dict[str, Any], regime: str) -> Dict[str, Any]:
    """
    Compute macro contribution to composite score.
    
    Fuses:
    - Sector tide (market-wide sector sentiment)
    - Short interest (squeeze signals)
    - Greeks (dealer positioning)
    - Spot exposures (gamma pressure)
    - ETF flows (institutional money)
    - Institutional ownership (accumulation/distribution)
    - Seasonality (historical patterns)
    
    Returns macro delta (0-3 scale) to add to micro composite score.
    """
    weights = load_live_weights(DEFAULT_WEIGHTS)
    base = uw_cache.get(symbol, {}) or {}
    macro = base.get("macro", {}) or {}
    context = uw_cache.get("_macro_context", {}) or {}
    sector_tides = context.get("sector_tides", {}) or {}

    # Sector tide
    sector = infer_sector(symbol)
    sec = sector_tides.get(sector, {"net_premium": 0.0, "sentiment": "MIXED"})
    sec_sent = (sec.get("sentiment") or "MIXED").upper()
    sec_net = float(sec.get("net_premium", 0.0))
    sector_component = weights["W_SECTOR"] * (0.6 if sec_sent in ("BULLISH","BEARISH") else 0.3)
    sector_component += weights["W_SECTOR"] * min(0.65, log10_safe(abs(sec_net)+1)/7.0)

    # Short interest
    si = macro.get("short_interest", {})
    si_util = float(si.get("float_utilization", 0.0))
    si_borrow = float(si.get("borrow_rate", 0.0))
    short_component = weights["W_SHORT"] * (0.5 if si_util < 0.6 else 0.65 if si_util < 0.8 else 0.8)
    if si_util > 0.8 and si_borrow > 10.0:
        short_component += weights["W_SHORT"] * 0.2

    # Greeks
    g = macro.get("greeks", {})
    gamma = float(g.get("gamma", 0.0))
    greeks_component = weights["W_GREEKS"] * (0.5 + clamp(log10_safe(abs(gamma)+1)/10.0, 0.0, 0.25))

    # Spot exposures
    se = macro.get("spot_exposures", {})
    call_not = float(se.get("call_notional_usd", 0.0))
    put_not = float(se.get("put_notional_usd", 0.0))
    spot_bias = "BULLISH" if call_not > put_not else ("BEARISH" if put_not > call_not else "MIXED")
    spot_component = weights["W_SPOT"] * (0.6 if spot_bias in ("BULLISH","BEARISH") else 0.3)
    spot_component += weights["W_SPOT"] * clamp(log10_safe(call_not + put_not)/7.0, 0.0, 0.65)

    # ETF flows
    etf = macro.get("etf_flows", {})
    etf_net = float(etf.get("net_flow_usd", 0.0))
    etf_sent = (etf.get("sentiment") or "MIXED").upper()
    etf_component = weights["W_ETF"] * (0.55 if etf_sent in ("BULLISH","BEARISH") else 0.3)
    etf_component += weights["W_ETF"] * clamp(log10_safe(abs(etf_net)+1)/7.0, 0.0, 0.65)

    # Institutional ownership
    inst = macro.get("institutional_ownership", {})
    inst_chg = float(inst.get("change_pct", 0.0))
    inst_sent = (inst.get("sentiment") or "FLAT").upper()
    inst_component = weights["W_INSTOWN"] * (0.55 if inst_sent == "ACCUMULATION" else 0.45 if inst_sent == "DISTRIBUTION" else 0.35)
    inst_component += weights["W_INSTOWN"] * clamp(abs(inst_chg)/10.0, 0.0, 0.25)

    # Seasonality
    sea = macro.get("seasonality", {})
    sea_avg = float(sea.get("avg_monthly_return_pct", 0.0))
    sea_sent = (sea.get("sentiment") or "MIXED").upper()
    season_component = weights["W_SEASON"] * (0.5 if sea_sent in ("BULLISH","BEARISH") else 0.3)
    season_component += weights["W_SEASON"] * clamp(abs(sea_avg)/10.0, 0.0, 0.25)

    # Regime
    reg = (regime or "NEUTRAL").upper()
    regime_component = weights.get("W_REGIME", 0.35) * (0.05 if reg in ("RISK_ON","RISK_OFF") else 0.0)

    # Total macro delta
    macro_delta = sector_component + short_component + greeks_component + spot_component + etf_component + inst_component + season_component + regime_component
    macro_delta = clamp(macro_delta, 0.0, 3.0)

    return {
        "symbol": symbol,
        "macro_delta": round(macro_delta, 3),
        "contrib": {
            "sector": round(sector_component, 3),
            "short": round(short_component, 3),
            "greeks": round(greeks_component, 3),
            "spot": round(spot_component, 3),
            "etf": round(etf_component, 3),
            "inst_own": round(inst_component, 3),
            "season": round(season_component, 3),
            "regime": round(regime_component, 3),
        },
        "notes": f"sec={sector}:{sec_sent}(${int(sec_net):,}); short={si_util:.1%}@{si_borrow:.1f}%; spot={spot_bias}; etf={etf_sent}(${int(etf_net):,}); inst={inst_sent}({inst_chg:+.1f}%); season={sea_sent}({sea_avg:+.1f}%)"
    }
