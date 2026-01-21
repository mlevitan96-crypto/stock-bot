#!/usr/bin/env python3
"""
Pre-market Intelligence Pass (v2 intelligence layer)
====================================================

Inputs:
- state/daily_universe.json
- state/core_universe.json

Outputs:
- state/premarket_intel.json

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


OUT = Path("state/premarket_intel.json")


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
        "flow_strength": 0.6,
        "darkpool_bias": 0.1,
        "sentiment": "BULLISH",
        "earnings_proximity": 3,
        "sector_alignment": 0.1,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="Mock mode (no UW calls)")
    args = ap.parse_args()

    mock = bool(args.mock) or str(os.getenv("UW_MOCK", "")).strip() in ("1", "true", "TRUE", "yes", "YES")
    mode = "mock" if bool(mock) else "real"

    daily = _load_universe("state/daily_universe.json")
    core = _load_universe("state/core_universe.json")
    syms = sorted(set(daily + core))

    uw_cfg = (COMPOSITE_WEIGHTS_V2.get("uw") or {}) if isinstance(COMPOSITE_WEIGHTS_V2, dict) else {}
    uw_ver = str(uw_cfg.get("version", ""))

    symbols: Dict[str, Any] = {}
    for sym in syms:
        if mock:
            symbols[sym] = _mock_intel(sym)
            continue
        # Fast endpoints (symbol-level) are permitted ONLY for daily∪core universe.
        try:
            flow = uw_get(
                "/api/option-trades/flow-alerts",
                params={"symbol": sym, "limit": 50},
                cache_policy={"ttl_seconds": 30, "endpoint_name": "options_flow_alerts", "max_calls_per_day": 7000},
            )
        except Exception:
            flow = {"data": []}
        try:
            dp = uw_get(
                f"/api/darkpool/{sym}",
                params=None,
                cache_policy={"ttl_seconds": 60, "endpoint_name": "darkpool_symbol", "max_calls_per_day": 3000},
            )
        except Exception:
            dp = {"data": []}

        # Normalize into a minimal, stable schema for v2 scoring.
        try:
            flow_rows = flow.get("data") or []
            flow_strength = 0.0
            if isinstance(flow_rows, list) and flow_rows:
                # best-effort: use mean of flow_conv if present; else presence indicates some strength
                vals = []
                for r in flow_rows[:25]:
                    if isinstance(r, dict):
                        v = r.get("flow_conv") or r.get("flow_conviction") or r.get("conviction")
                        try:
                            vals.append(float(v))
                        except Exception:
                            continue
                flow_strength = sum(vals) / len(vals) if vals else 0.3
            dp_rows = dp.get("data") or []
            darkpool_bias = 0.0
            if isinstance(dp_rows, list) and dp_rows:
                # best-effort: compare off_lit_volume vs lit_volume if present
                r0 = dp_rows[0] if isinstance(dp_rows[0], dict) else {}
                offv = float((r0 or {}).get("off_lit_volume") or 0.0)
                litv = float((r0 or {}).get("lit_volume") or 0.0)
                tot = max(1.0, offv + litv)
                darkpool_bias = max(-1.0, min(1.0, (offv - litv) / tot))
        except Exception:
            flow_strength = 0.0
            darkpool_bias = 0.0

        symbols[sym] = {
            "flow_strength": float(round(flow_strength, 6)),
            "darkpool_bias": float(round(darkpool_bias, 6)),
            "sentiment": "NEUTRAL",
            "earnings_proximity": None,
            "sector_alignment": 0.0,
        }

    out = {
        "_meta": {"ts": datetime.now(timezone.utc).isoformat(), "uw_intel_version": uw_ver, "mode": mode},
        "symbols": symbols,
        "market": {},
    }
    _atomic_write(OUT, out)

    try:
        log_system_event(
            subsystem="uw",
            event_type="premarket_intel_ready",
            severity="INFO",
            details={"symbols": len(symbols), "mode": mode, "uw_intel_version": uw_ver},
        )
    except Exception:
        pass

    print(str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

