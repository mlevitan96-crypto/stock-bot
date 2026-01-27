#!/usr/bin/env python3
"""
Build state/symbol_risk_features.json from historical price data (Alpaca).
Logs subsystem=phase2, event_type=symbol_risk_features_built. Run on droplet if missing.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.chdir(REPO)


def _load_env() -> None:
    env_file = REPO / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip("'\"").strip()
            if k:
                os.environ.setdefault(k, v)


def main() -> int:
    _load_env()

    from config.registry import StateFiles, read_json
    from structural_intelligence.symbol_risk_features import update_symbol_risk_features

    try:
        from utils.system_events import log_system_event
    except Exception:
        def log_system_event(*args, **kwargs):  # type: ignore
            pass

    # Alpaca API (same as bot)
    try:
        import alpaca_trade_api as tradeapi
        base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        api = tradeapi.REST(
            os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", ""),
            base_url=base,
            api_version="v2",
        )
    except Exception as e:
        log_system_event(
            "phase2", "symbol_risk_features_build_failed", "ERROR",
            details={"reason": "alpaca_init", "error": str(e)},
        )
        print(f"build_symbol_risk_features: Alpaca init failed: {e}", file=sys.stderr)
        return 1

    # Symbols: trade_universe_v2, then config, then default
    symbols: List[str] = []
    tu_path = REPO / "state" / "trade_universe_v2.json"
    if tu_path.exists():
        try:
            tu = read_json(tu_path, default={}) or {}
            univ = tu.get("universe") or tu.get("symbols")
            if isinstance(univ, list):
                symbols = [str(s) for s in univ if str(s).strip()][:80]
            elif isinstance(univ, dict):
                symbols = list(univ.keys())[:80]
        except Exception:
            pass
    if not symbols:
        from main import Config
        symbols = list(getattr(Config, "SYMBOL_UNIVERSE", [])) or list(getattr(Config, "SYMBOLS", [])) or []
    if not symbols:
        symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META", "AMZN"]

    out = update_symbol_risk_features(api, symbols=symbols, benchmark="SPY", refresh_hours=0.0)
    sym_data = out.get("symbols") or {}
    count = len(sym_data)

    try:
        log_system_event(
            "phase2", "symbol_risk_features_built", "INFO",
            details={"count": count, "symbols_sample": list(sym_data.keys())[:10]},
        )
    except Exception:
        pass

    print(f"build_symbol_risk_features: wrote {count} symbols to state/symbol_risk_features.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
