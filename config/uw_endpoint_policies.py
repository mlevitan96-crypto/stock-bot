#!/usr/bin/env python3
"""
UW Endpoint Policies
====================

Contract:
- Defines *intended* cadence/TTL/cost per endpoint for the centralized UW client.
- Pure metadata (safe to import; no side effects).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional


Cadence = Literal["slow", "medium", "fast"]
SymbolScope = Literal["market", "sector", "symbol"]


@dataclass(frozen=True)
class UwEndpointPolicy:
    name: str
    path: str
    cadence: Cadence
    ttl_seconds: int
    max_calls_per_day: int
    symbol_scope: SymbolScope
    notes: str = ""


POLICIES: Dict[str, UwEndpointPolicy] = {
    # Slow (cache hard)
    "congress_trades": UwEndpointPolicy(
        name="congress_trades",
        path="/api/congress/trades",
        cadence="slow",
        ttl_seconds=6 * 3600,
        max_calls_per_day=200,
        symbol_scope="market",
        notes="Slow-changing; safe to cache hard.",
    ),
    "insider_trades": UwEndpointPolicy(
        name="insider_trades",
        path="/api/insider/trades",
        cadence="slow",
        ttl_seconds=6 * 3600,
        max_calls_per_day=200,
        symbol_scope="market",
        notes="Slow-changing; safe to cache hard.",
    ),
    "institutional_holdings": UwEndpointPolicy(
        name="institutional_holdings",
        path="/api/institutional/holdings",
        cadence="slow",
        ttl_seconds=24 * 3600,
        max_calls_per_day=100,
        symbol_scope="market",
        notes="Holdings update slowly; cache hard.",
    ),
    "short_interest": UwEndpointPolicy(
        name="short_interest",
        path="/api/short-interest",
        cadence="slow",
        ttl_seconds=24 * 3600,
        max_calls_per_day=200,
        symbol_scope="market",
        notes="Short interest updates slowly; cache hard.",
    ),
    "seasonality": UwEndpointPolicy(
        name="seasonality",
        path="/api/seasonality",
        cadence="slow",
        ttl_seconds=24 * 3600,
        max_calls_per_day=100,
        symbol_scope="market",
        notes="Seasonality is slow; cache hard.",
    ),
    "fda_calendar": UwEndpointPolicy(
        name="fda_calendar",
        path="/api/calendar/fda",
        cadence="slow",
        ttl_seconds=24 * 3600,
        max_calls_per_day=100,
        symbol_scope="market",
        notes="Calendar changes slowly; cache hard.",
    ),

    # Medium
    "earnings_calendar": UwEndpointPolicy(
        name="earnings_calendar",
        path="/api/calendar/earnings",
        cadence="medium",
        ttl_seconds=2 * 3600,
        max_calls_per_day=400,
        symbol_scope="market",
        notes="Refresh a few times/day.",
    ),
    "sector_flow": UwEndpointPolicy(
        name="sector_flow",
        path="/api/market/sector-flow",
        cadence="medium",
        ttl_seconds=15 * 60,
        max_calls_per_day=1000,
        symbol_scope="sector",
        notes="Sector rotation changes intraday.",
    ),
    "market_sentiment": UwEndpointPolicy(
        name="market_sentiment",
        path="/api/market/sentiment",
        cadence="medium",
        ttl_seconds=10 * 60,
        max_calls_per_day=1500,
        symbol_scope="market",
        notes="Market-wide; medium cadence.",
    ),
    "top_net_impact": UwEndpointPolicy(
        name="top_net_impact",
        path="/api/market/top-net-impact",
        cadence="medium",
        ttl_seconds=5 * 60,
        max_calls_per_day=2000,
        symbol_scope="market",
        notes="Used by universe builder.",
    ),

    # Fast (symbol-level)
    "options_flow_alerts": UwEndpointPolicy(
        name="options_flow_alerts",
        path="/api/option-trades/flow-alerts",
        cadence="fast",
        ttl_seconds=30,
        max_calls_per_day=7000,
        symbol_scope="symbol",
        notes="High-volume endpoint; short TTL.",
    ),
    "darkpool_symbol": UwEndpointPolicy(
        name="darkpool_symbol",
        path="/api/darkpool/{symbol}",
        cadence="fast",
        ttl_seconds=60,
        max_calls_per_day=3000,
        symbol_scope="symbol",
        notes="Symbol-level; short TTL.",
    ),
    "net_premium_ticks": UwEndpointPolicy(
        name="net_premium_ticks",
        path="/api/market/net-premium",
        cadence="fast",
        ttl_seconds=30,
        max_calls_per_day=3000,
        symbol_scope="market",
        notes="Fast market tick; short TTL.",
    ),
    "premarket_summary": UwEndpointPolicy(
        name="premarket_summary",
        path="/api/market/premarket",
        cadence="fast",
        ttl_seconds=120,
        max_calls_per_day=800,
        symbol_scope="market",
        notes="Premarket/after-hours summary.",
    ),
    "afterhours_summary": UwEndpointPolicy(
        name="afterhours_summary",
        path="/api/market/afterhours",
        cadence="fast",
        ttl_seconds=300,
        max_calls_per_day=400,
        symbol_scope="market",
        notes="Postmarket summary.",
    ),
}


def get_policy(name: str) -> Optional[UwEndpointPolicy]:
    return POLICIES.get(str(name))

