#!/usr/bin/env python3
"""
Daily Dynamic Universe Builder (v2 intelligence layer)
======================================================

Outputs:
- state/daily_universe.json
- state/core_universe.json

Contract:
- Additive only (does not touch v1 trading behavior)
- Supports --mock and UW_MOCK=1 for regression
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.registry import DAILY_UNIVERSE_SCORING_V1
from src.uw.uw_client import uw_get
from utils.state_io import read_json_self_heal

try:
    from utils.system_events import log_system_event
except Exception:  # pragma: no cover
    def log_system_event(*args, **kwargs):  # type: ignore
        return None


OUT_DAILY = Path("state/daily_universe.json")
OUT_CORE = Path("state/core_universe.json")


def _atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _load_symbol_risk() -> Dict[str, Any]:
    return read_json_self_heal("state/symbol_risk_features.json", default={}, heal=True, mkdir=True)


def _risk_map(risk: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(risk, dict):
        return {}
    sy = risk.get("symbols")
    return sy if isinstance(sy, dict) else {}


def _mock_symbols() -> List[str]:
    return ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META", "AMZN", "COIN", "PLTR", "XLF", "XLE", "XLK"]


def _collect_candidates(mock: bool) -> Set[str]:
    # Universe sources: UW summary endpoints + existing core tickers (if present)
    if mock:
        return set(_mock_symbols())

    cands: Set[str] = set()
    try:
        # Use known market summary endpoints (policies define TTL/caps in the uw client)
        top_net = uw_get("/api/market/top-net-impact", params={"limit": 80}, cache_policy={"ttl_seconds": 300, "endpoint_name": "top_net_impact", "max_calls_per_day": 2000})
        for r in (top_net.get("data") or []):
            sym = r.get("symbol") or r.get("ticker")
            if sym:
                cands.add(str(sym).upper())
    except Exception:
        pass

    # Always include core ETFs
    for s in ("SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV"):
        cands.add(s)
    return cands


def _score_symbol(sym: str, risk_feats: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    # Very conservative first pass: use vol/beta only (UW and premarket are injected later by intel pass)
    vol = float(risk_feats.get("realized_vol_20d") or 0.0)
    beta = float(risk_feats.get("beta_vs_spy") or 0.0)

    w = (DAILY_UNIVERSE_SCORING_V1.get("weights") or {}) if isinstance(DAILY_UNIVERSE_SCORING_V1, dict) else {}
    w_vol = float(w.get("volatility", 0.30))
    # proxy: normalized vol in [0,1] around 0.20–0.60
    vol_norm = max(0.0, min(1.0, (vol - 0.20) / 0.40)) if vol > 0 else 0.0
    score = w_vol * vol_norm
    return float(score), {"volatility": float(score)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=200, help="Target daily universe size (150–250 recommended)")
    ap.add_argument("--core", type=int, default=60, help="Target core universe size")
    ap.add_argument("--mock", action="store_true", help="Mock mode (no UW calls)")
    args = ap.parse_args()

    mock = bool(args.mock) or str(os.getenv("UW_MOCK", "")).strip() in ("1", "true", "TRUE", "yes", "YES")

    risk = _load_symbol_risk()
    rm = _risk_map(risk)

    cands = _collect_candidates(mock=mock)
    # If risk store contains more symbols, allow them as candidates too (bounded)
    if isinstance(rm, dict) and rm:
        for s in list(rm.keys())[:500]:
            cands.add(str(s).upper())

    scored = []
    for sym in sorted(cands):
        feats = rm.get(sym, {}) if isinstance(rm, dict) else {}
        s, breakdown = _score_symbol(sym, feats if isinstance(feats, dict) else {})
        scored.append({"symbol": sym, "score": float(round(s, 6)), "breakdown": breakdown, "risk": feats})

    scored.sort(key=lambda r: float(r.get("score") or 0.0), reverse=True)
    daily = scored[: max(1, int(args.max))]
    core = scored[: max(1, int(args.core))]

    now = datetime.now(timezone.utc).isoformat()
    daily_out = {"_meta": {"ts": now, "version": DAILY_UNIVERSE_SCORING_V1.get("version"), "mock": mock}, "symbols": daily}
    core_out = {"_meta": {"ts": now, "version": DAILY_UNIVERSE_SCORING_V1.get("version"), "mock": mock}, "symbols": core}

    _atomic_write(OUT_DAILY, daily_out)
    _atomic_write(OUT_CORE, core_out)

    try:
        log_system_event(
            subsystem="uw",
            event_type="daily_universe_built",
            severity="INFO",
            details={"daily": len(daily), "core": len(core), "mock": mock, "version": DAILY_UNIVERSE_SCORING_V1.get("version")},
        )
    except Exception:
        pass

    print(str(OUT_DAILY))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

