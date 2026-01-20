#!/usr/bin/env python3
"""
Post-market Intelligence Pass (v2 intelligence layer)
=====================================================

Inputs:
- state/daily_universe.json
- state/core_universe.json

Outputs:
- state/postmarket_intel.json

Contract:
- Additive only
- Mock-safe (no UW calls when --mock or UW_MOCK=1)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.registry import COMPOSITE_WEIGHTS_V2
from src.uw.uw_client import uw_get
from utils.state_io import read_json_self_heal

try:
    from utils.system_events import log_system_event
except Exception:  # pragma: no cover
    def log_system_event(*args, **kwargs):  # type: ignore
        return None


OUT = Path("state/postmarket_intel.json")


def _atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _load_universe(path: str) -> List[str]:
    d = read_json_self_heal(path, default={}, heal=True, mkdir=True)
    out: List[str] = []
    for r in (d.get("symbols") or []) if isinstance(d, dict) else []:
        if isinstance(r, dict) and r.get("symbol"):
            out.append(str(r["symbol"]).upper())
    return out


def _mock_intel(sym: str) -> Dict[str, Any]:
    return {
        "flow_strength": 0.55,
        "darkpool_bias": 0.05,
        "sentiment": "NEUTRAL",
        "earnings_proximity": None,
        "sector_alignment": 0.05,
        "institutional_blocks": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="Mock mode (no UW calls)")
    args = ap.parse_args()

    mock = bool(args.mock) or str(os.getenv("UW_MOCK", "")).strip() in ("1", "true", "TRUE", "yes", "YES")

    daily = _load_universe("state/daily_universe.json")
    core = _load_universe("state/core_universe.json")
    syms = sorted(set(daily + core))

    uw_cfg = (COMPOSITE_WEIGHTS_V2.get("uw") or {}) if isinstance(COMPOSITE_WEIGHTS_V2, dict) else {}
    uw_ver = str(uw_cfg.get("version", ""))

    # Market-level postmarket context (fetch once)
    market: Dict[str, Any] = {}
    if not mock:
        try:
            after = uw_get(
                "/api/earnings/afterhours",
                params=None,
                cache_policy={"ttl_seconds": 300, "endpoint_name": "earnings_afterhours", "max_calls_per_day": 400},
            )
            market["afterhours_earnings_present"] = bool(after.get("data"))
        except Exception:
            market["afterhours_earnings_present"] = False

    symbols: Dict[str, Any] = {}
    for sym in syms:
        if mock:
            symbols[sym] = _mock_intel(sym)
            continue
        # Minimal per-symbol record (we can enrich later with specific endpoints)
        symbols[sym] = {
            "flow_strength": 0.0,
            "darkpool_bias": 0.0,
            "sentiment": "NEUTRAL",
            "earnings_proximity": None,
            "sector_alignment": 0.0,
            "institutional_blocks": 0,
            "afterhours_summary_present": bool(market.get("afterhours_earnings_present")),
        }

    out = {
        "_meta": {"ts": datetime.now(timezone.utc).isoformat(), "uw_intel_version": uw_ver, "mock": mock},
        "symbols": symbols,
        "market": market,
    }
    _atomic_write(OUT, out)

    try:
        log_system_event(
            subsystem="uw",
            event_type="postmarket_intel_ready",
            severity="INFO",
            details={"symbols": len(symbols), "mock": mock, "uw_intel_version": uw_ver},
        )
    except Exception:
        pass

    print(str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

