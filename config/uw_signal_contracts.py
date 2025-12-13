#!/usr/bin/env python3
"""
Central UW Signal Contract Map
==============================
Single source of truth for mapping between:
- UW API endpoints and their response field names
- Internal signal component names
- Cache paths for data storage
- Consumer modules that use each signal

This file prevents dead references and ensures data flows properly
from UW API -> Cache -> Scoring -> Learning

CRITICAL: All field name translations MUST be defined here.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

SIGNAL_COMPONENTS = [
    "flow",               # Options flow sentiment
    "dark_pool",          # Dark pool activity
    "insider",            # Insider trading
    "iv_term_skew",       # IV term structure skew
    "smile_slope",        # Volatility smile slope
    "whale_persistence",  # Large player patterns (derived from motifs)
    "event_alignment",    # Event/earnings alignment
    "temporal_motif",     # Temporal patterns (staircase/burst)
    "toxicity_penalty",   # Signal staleness/crowding penalty
    "regime_modifier",    # Market regime adjustment
    "congress",           # Congress/politician trading
    "shorts_squeeze",     # Short interest/squeeze signals
    "institutional",      # Institutional activity
    "market_tide",        # Market-wide options sentiment
    "calendar_catalyst",  # Earnings/events calendar
    "greeks_gamma",       # Gamma exposure for squeeze
    "ftd_pressure",       # Fails-to-deliver pressure
    "iv_rank",            # IV rank percentile
    "oi_change",          # Open interest changes
    "etf_flow",           # ETF money flow
    "squeeze_score",      # Combined squeeze indicators
    "freshness_factor",   # Data recency factor
]

@dataclass
class EndpointContract:
    """Contract for a UW API endpoint"""
    endpoint: str
    method: str = "GET"
    required_params: List[str] = field(default_factory=list)
    response_fields: Dict[str, str] = field(default_factory=dict)
    cache_key: str = ""
    internal_fields: Dict[str, str] = field(default_factory=dict)
    signal_components: List[str] = field(default_factory=list)


UW_ENDPOINT_CONTRACTS = {
    "market_tide": EndpointContract(
        endpoint="/api/market/market-tide",
        response_fields={
            "net_call_premium": "float",
            "net_put_premium": "float",
            "net_volume": "int",
            "timestamp": "str",
            "date": "str",
        },
        internal_fields={
            "net_call_premium": "call_premium",
            "net_put_premium": "put_premium",
            "net_volume": "net_delta",
        },
        cache_key="_market_intel_cache.market_tide",
        signal_components=["market_tide"],
    ),
    
    "greek_exposure": EndpointContract(
        endpoint="/api/stock/{ticker}/greek-exposure",
        required_params=["ticker"],
        response_fields={
            "gamma_exposure": "float",
            "delta_exposure": "float",
            "gamma": "float",
            "delta": "float",
            "total_gamma": "float",
            "total_delta": "float",
            "gamma_max_strike": "float",
        },
        internal_fields={
            "gamma_exposure": "gamma_exposure",
            "total_gamma": "gamma_exposure",
            "gamma": "gamma_exposure",
            "delta_exposure": "delta_exposure",
            "total_delta": "delta_exposure",
            "delta": "delta_exposure",
            "gamma_max_strike": "gamma_wall",
            "gamma_wall": "gamma_wall",
        },
        cache_key="_greeks_cache",
        signal_components=["greeks_gamma"],
    ),
    
    "oi_change": EndpointContract(
        endpoint="/api/stock/{ticker}/oi-change",
        required_params=["ticker"],
        response_fields={
            "call_oi_change": "float",
            "put_oi_change": "float",
            "callOiChange": "float",
            "putOiChange": "float",
            "call_open_interest_change": "float",
            "put_open_interest_change": "float",
        },
        internal_fields={
            "call_oi_change": "call_oi_change",
            "callOiChange": "call_oi_change",
            "call_open_interest_change": "call_oi_change",
            "put_oi_change": "put_oi_change",
            "putOiChange": "put_oi_change",
            "put_open_interest_change": "put_oi_change",
        },
        cache_key="_oi_cache",
        signal_components=["oi_change"],
    ),
    
    "etf_inflow_outflow": EndpointContract(
        endpoint="/api/etfs/{ticker}/in-outflow",
        required_params=["ticker"],
        response_fields={
            "inflow": "float",
            "outflow": "float",
            "net_inflow": "float",
            "net_outflow": "float",
            "net_flow_usd": "float",
            "net_shares": "int",
            "in_flow": "float",
            "out_flow": "float",
        },
        internal_fields={
            "inflow": "inflow",
            "net_inflow": "inflow",
            "in_flow": "inflow",
            "outflow": "outflow",
            "net_outflow": "outflow",
            "out_flow": "outflow",
            "net_flow_usd": "net_flow",
            "net_shares": "net_flow",
        },
        cache_key="_etf_cache",
        signal_components=["etf_flow"],
    ),
    
    "iv_rank": EndpointContract(
        endpoint="/api/stock/{ticker}/iv-rank",
        required_params=["ticker"],
        response_fields={
            "iv_rank": "float",
            "ivRank": "float",
            "iv_percentile": "float",
            "ivPercentile": "float",
            "iv": "float",
            "implied_volatility": "float",
            "currentIV": "float",
        },
        internal_fields={
            "iv_rank": "iv_rank",
            "ivRank": "iv_rank",
            "iv_percentile": "iv_percentile",
            "ivPercentile": "iv_percentile",
            "iv": "current_iv",
            "implied_volatility": "current_iv",
            "currentIV": "current_iv",
        },
        cache_key="_iv_cache",
        signal_components=["iv_rank"],
    ),
    
    "shorts_ftds": EndpointContract(
        endpoint="/api/shorts/{ticker}/ftds",
        required_params=["ticker"],
        response_fields={
            "fail_to_deliver_qty": "float",
            "quantity": "float",
            "ftd_qty": "float",
            "shares": "float",
        },
        internal_fields={
            "fail_to_deliver_qty": "ftd_count",
            "quantity": "ftd_count",
            "ftd_qty": "ftd_count",
            "shares": "ftd_count",
        },
        cache_key="_ftd_cache",
        signal_components=["ftd_pressure"],
    ),
    
    "max_pain": EndpointContract(
        endpoint="/api/stock/{ticker}/max-pain",
        required_params=["ticker"],
        response_fields={
            "max_pain": "float",
            "maxPain": "float",
            "max_pain_strike": "float",
        },
        internal_fields={
            "max_pain": "max_pain",
            "maxPain": "max_pain",
            "max_pain_strike": "max_pain",
        },
        cache_key="_max_pain_cache",
        signal_components=["greeks_gamma"],
    ),
}


def translate_response_fields(response_data: Dict[str, Any], contract: EndpointContract) -> Dict[str, Any]:
    """
    Translate UW API response field names to internal field names.
    Tries each possible API field name and maps to the canonical internal name.
    """
    translated = {}
    
    for api_field, internal_field in contract.internal_fields.items():
        if api_field in response_data:
            value = response_data[api_field]
            if value is not None:
                if internal_field not in translated or translated[internal_field] in (None, 0, 0.0, ""):
                    translated[internal_field] = value
    
    return translated


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float, handling strings and None"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            cleaned = value.replace(",", "").strip()
            return float(cleaned) if cleaned else default
        except ValueError:
            return default
    return default


def parse_market_tide_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a market tide entry from UW API format to internal format.
    UW returns: net_call_premium, net_put_premium (as strings)
    We need: call_premium, put_premium (as floats)
    """
    return {
        "call_premium": safe_float(entry.get("net_call_premium", 0)),
        "put_premium": abs(safe_float(entry.get("net_put_premium", 0))),
        "net_volume": safe_float(entry.get("net_volume", 0)),
        "net_delta": safe_float(entry.get("net_volume", 0)),
        "sentiment": "BULLISH" if safe_float(entry.get("net_call_premium", 0)) > abs(safe_float(entry.get("net_put_premium", 0))) else "BEARISH",
        "timestamp": entry.get("timestamp", ""),
    }


def aggregate_market_tide(tide_entries: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate multiple market tide entries into a single sentiment reading.
    Takes the most recent entries and computes overall sentiment.
    """
    if not tide_entries:
        return {
            "call_premium": 0.0,
            "put_premium": 0.0,
            "net_delta": 0.0,
            "sentiment": "NEUTRAL",
        }
    
    recent = tide_entries[:5]
    total_call = sum(safe_float(e.get("net_call_premium", 0)) for e in recent)
    total_put = sum(abs(safe_float(e.get("net_put_premium", 0))) for e in recent)
    
    if total_call + total_put == 0:
        sentiment = "NEUTRAL"
    elif total_call > total_put * 1.2:
        sentiment = "BULLISH"
    elif total_put > total_call * 1.2:
        sentiment = "BEARISH"
    else:
        sentiment = "NEUTRAL"
    
    return {
        "call_premium": total_call,
        "put_premium": total_put,
        "net_delta": total_call - total_put,
        "sentiment": sentiment,
    }


def validate_signal_activation() -> Dict[str, Any]:
    """
    Validate that all signal components are receiving non-zero data.
    Returns a report of which signals are active vs inactive.
    """
    from config.registry import CacheFiles, read_json
    
    report = {
        "active": [],
        "inactive": [],
        "missing_data": [],
    }
    
    expanded_intel = read_json(CacheFiles.UW_EXPANDED_INTEL)
    if not expanded_intel:
        report["missing_data"] = SIGNAL_COMPONENTS
        return report
    
    cache_stats = expanded_intel.get("_cache_stats", {})
    
    signal_checks = {
        "greeks_gamma": cache_stats.get("greeks", 0) > 0,
        "oi_change": cache_stats.get("oi", 0) > 0,
        "etf_flow": cache_stats.get("etf", 0) > 0,
        "market_tide": len(expanded_intel.get("_global", {}).get("market_tide", [])) > 0,
        "ftd_pressure": cache_stats.get("ftd", 0) > 0,
        "iv_rank": cache_stats.get("iv", 0) > 0,
        "congress": cache_stats.get("congress", 0) > 0,
        "shorts_squeeze": cache_stats.get("shorts", 0) > 0,
        "insider": cache_stats.get("insider", 0) > 0,
    }
    
    for signal, has_data in signal_checks.items():
        if has_data:
            report["active"].append(signal)
        else:
            report["inactive"].append(signal)
    
    return report


if __name__ == "__main__":
    print("=== UW Signal Contract Validation ===")
    report = validate_signal_activation()
    print(f"\nActive signals ({len(report['active'])}): {report['active']}")
    print(f"Inactive signals ({len(report['inactive'])}): {report['inactive']}")
    print(f"Missing data ({len(report['missing_data'])}): {report['missing_data']}")
