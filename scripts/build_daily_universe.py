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
try:
    from config.registry import DAILY_UNIVERSE_SCORING_V2
except Exception:  # pragma: no cover
    DAILY_UNIVERSE_SCORING_V2 = {}
from src.uw.uw_client import uw_get
from utils.state_io import read_json_self_heal

try:
    from utils.system_events import log_system_event
except Exception:  # pragma: no cover
    def log_system_event(*args, **kwargs):  # type: ignore
        return None


OUT_DAILY = Path("state/daily_universe.json")
OUT_CORE = Path("state/core_universe.json")
OUT_DAILY_V2 = Path("state/daily_universe_v2.json")


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


def _score_symbol_v2(sym: str, risk_feats: Dict[str, Any], *, regime_label: str) -> Tuple[float, Dict[str, float], Dict[str, Any]]:
    """
    Shadow-only universe scoring v2.
    Adds sector/regime alignment features while keeping v1 outputs unchanged.
    """
    vol = float(risk_feats.get("realized_vol_20d") or 0.0)
    w = (DAILY_UNIVERSE_SCORING_V2.get("weights") or {}) if isinstance(DAILY_UNIVERSE_SCORING_V2, dict) else {}
    vol_norm = max(0.0, min(1.0, (vol - 0.20) / 0.40)) if vol > 0 else 0.0
    w_vol = float(w.get("volatility", 0.25))

    try:
        from src.intel.sector_intel import get_sector
        sector = get_sector(sym)
    except Exception:
        sector = "UNKNOWN"

    # Very conservative alignment heuristics (bounded [0,1])
    r = str(regime_label or "NEUTRAL").upper()
    if r == "RISK_ON":
        sector_align = 1.0 if sector in ("TECH", "BIOTECH") else 0.25
        regime_align = 1.0
    elif r in ("RISK_OFF", "BEAR"):
        sector_align = 1.0 if sector in ("ENERGY", "FINANCIALS") else 0.25
        regime_align = 1.0
    elif r == "MIXED":
        sector_align = 0.5
        regime_align = 0.5
    else:
        sector_align = 0.25
        regime_align = 0.25

    w_sector = float(w.get("sector_alignment", 0.05))
    w_regime = float(w.get("regime_alignment", 0.05))
    score = (w_vol * vol_norm) + (w_sector * float(sector_align)) + (w_regime * float(regime_align))
    return float(score), {"volatility": float(w_vol * vol_norm), "sector_alignment": float(w_sector * sector_align), "regime_alignment": float(w_regime * regime_align)}, {"sector": sector, "regime_label": r}


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
    mode = "mock" if bool(mock) else "real"
    daily_out = {"_meta": {"ts": now, "version": DAILY_UNIVERSE_SCORING_V1.get("version"), "mode": mode}, "symbols": daily}
    core_out = {"_meta": {"ts": now, "version": DAILY_UNIVERSE_SCORING_V1.get("version"), "mode": mode}, "symbols": core}

    _atomic_write(OUT_DAILY, daily_out)
    _atomic_write(OUT_CORE, core_out)

    # Shadow-only v2 universe output (additive).
    try:
        from src.intel.regime_detector import write_regime_state, read_regime_state
        try:
            write_regime_state()
        except Exception:
            pass
        rs = read_regime_state()
        regime_label = str(rs.get("regime_label", "NEUTRAL") or "NEUTRAL")
    except Exception:
        regime_label = "NEUTRAL"

    try:
        scored_v2 = []
        for sym in sorted(cands):
            feats = rm.get(sym, {}) if isinstance(rm, dict) else {}
            sv2, bd2, ctx2 = _score_symbol_v2(sym, feats if isinstance(feats, dict) else {}, regime_label=regime_label)
            scored_v2.append({"symbol": sym, "score": float(round(sv2, 6)), "breakdown": bd2, "context": ctx2})
        scored_v2.sort(key=lambda r: float(r.get("score") or 0.0), reverse=True)
        daily_v2 = scored_v2[: max(1, int(args.max))]
        v2_ver = str((DAILY_UNIVERSE_SCORING_V2 or {}).get("version") or "")
        daily_out_v2 = {"_meta": {"ts": now, "version": v2_ver, "mode": mode, "regime_label": str(regime_label)}, "symbols": daily_v2}
        _atomic_write(OUT_DAILY_V2, daily_out_v2)
    except Exception:
        pass

    try:
        log_system_event(
            subsystem="uw",
            event_type="daily_universe_built",
            severity="INFO",
            details={
                "daily": len(daily),
                "core": len(core),
                "mode": mode,
                "version": DAILY_UNIVERSE_SCORING_V1.get("version"),
                "universe_scoring_v2_version": str((DAILY_UNIVERSE_SCORING_V2 or {}).get("version") or ""),
                "wrote_daily_universe_v2": OUT_DAILY_V2.exists(),
            },
        )
    except Exception:
        pass

    print(str(OUT_DAILY))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

