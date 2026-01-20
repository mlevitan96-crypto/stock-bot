#!/usr/bin/env python3
"""
Sector-aware intelligence (v2, additive)
========================================

Contract:
- Sector profiles are config-driven (`config/sector_profiles.json`).
- Must be safe to import and must never raise during scoring.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple


ROOT = Path(__file__).resolve().parents[2]
SECTOR_PROFILES_PATH = ROOT / "config" / "sector_profiles.json"


def _load_profiles() -> Dict[str, Any]:
    try:
        return json.loads(SECTOR_PROFILES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"_meta": {"version": ""}, "UNKNOWN": {"flow_weight": 1.0, "darkpool_weight": 1.0, "earnings_weight": 1.0, "short_interest_weight": 1.0}}


def _heuristic_sector(symbol: str) -> str:
    s = (symbol or "").upper().strip()
    # Minimal heuristic map (expand later)
    tech = {"AAPL", "MSFT", "NVDA", "AMD", "META", "AMZN", "GOOGL", "GOOG", "TSLA", "PLTR", "COIN"}
    bio = {"MRNA", "BNTX", "GILD", "BIIB", "REGN"}
    fins = {"JPM", "BAC", "GS", "MS", "C", "XLF"}
    energy = {"XOM", "CVX", "XLE", "OXY"}
    if s in tech or s.endswith("Q") or s == "XLK":
        return "TECH"
    if s in bio or s == "XBI":
        return "BIOTECH"
    if s in fins:
        return "FINANCIALS"
    if s in energy:
        return "ENERGY"
    return "UNKNOWN"


def get_sector_profile_version() -> str:
    prof = _load_profiles()
    meta = prof.get("_meta") if isinstance(prof, dict) else {}
    return str((meta or {}).get("version") or "")


def get_sector(symbol: str) -> str:
    # Future: map from state/sector_tide_state.json if it becomes reliable.
    return _heuristic_sector(symbol)


def get_sector_multipliers(symbol: str) -> Tuple[str, Dict[str, float]]:
    """
    Returns (sector, multipliers) where multipliers keys:
    - flow_weight
    - darkpool_weight
    - earnings_weight
    - short_interest_weight
    """
    prof = _load_profiles()
    sector = get_sector(symbol)
    rec = prof.get(sector) if isinstance(prof, dict) else None
    base = prof.get("UNKNOWN") if isinstance(prof, dict) else None
    m = rec if isinstance(rec, dict) else (base if isinstance(base, dict) else {})
    def _f(k: str) -> float:
        try:
            return float(m.get(k, 1.0))
        except Exception:
            return 1.0
    return sector, {
        "flow_weight": _f("flow_weight"),
        "darkpool_weight": _f("darkpool_weight"),
        "earnings_weight": _f("earnings_weight"),
        "short_interest_weight": _f("short_interest_weight"),
    }

