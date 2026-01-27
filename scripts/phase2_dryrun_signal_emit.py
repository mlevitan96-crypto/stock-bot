#!/usr/bin/env python3
"""
Phase-2 dry-run: emit trade_intent and exit_intent to logs/run.jsonl via the same
helpers as the live bot. No orders. Proves telemetry wiring when market is closed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Ensure we run from repo root (same as service)
os.chdir(REPO)


def main() -> int:
    # Load env exactly as service (EnvironmentFile=/root/stock-bot/.env)
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
    # Force Phase-2 telemetry on for dry-run (override .env)
    os.environ["PHASE2_TELEMETRY_ENABLED"] = "true"

    # Import same Config and emit helpers as live bot
    import main as main_mod
    Config = main_mod.Config
    _emit_trade_intent = main_mod._emit_trade_intent
    _emit_exit_intent = main_mod._emit_exit_intent

    # Minimal fake engine (market_context_v2, regime_posture_v2)
    class FakeEngine:
        market_context_v2: Dict[str, Any] = {}
        regime_posture_v2: Dict[str, Any] = {}

    engine = FakeEngine()
    market_regime = "mixed"

    # Symbol universe: config or default
    symbols: List[str] = list(getattr(Config, "SYMBOL_UNIVERSE", [])) or list(getattr(Config, "SYMBOLS", [])) or []
    if not symbols:
        symbols = ["SPY", "QQQ", "AAPL"]
    symbols = symbols[:3]

    # Fake cluster/comps per symbol
    for i, sym in enumerate(symbols):
        direction = "bullish" if i % 2 == 0 else "bearish"
        side = "buy" if direction == "bullish" else "sell"
        score = 3.0 + (i * 0.1)
        cluster = {"ticker": sym, "direction": direction, "source": "dryrun"}
        comps = {"flow_strength": 0.5, "dark_pool_bias": 0.0}
        _emit_trade_intent(
            symbol=sym,
            side=side,
            score=score,
            comps=comps,
            cluster=cluster,
            market_regime=market_regime,
            engine=engine,
            displacement_context=None,
            decision_outcome="entered",
            blocked_reason=None,
        )

    # Fake exit_intent per symbol
    for sym in symbols:
        info = {"entry_score": 3.0}
        _emit_exit_intent(
            symbol=sym,
            info=info,
            close_reason="dryrun_exit",
            metadata=None,
            thesis_break_reason="dryrun",
        )

    print("phase2_dryrun_signal_emit: emitted trade_intent and exit_intent for", symbols)
    return 0


if __name__ == "__main__":
    sys.exit(main())
