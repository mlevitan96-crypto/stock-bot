#!/usr/bin/env python3
"""Emit one trade_intent row for forward-collection audit (no broker orders)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))
os.environ["PHASE2_TELEMETRY_ENABLED"] = "true"

from main import _emit_trade_intent  # noqa: E402


class _FakeEngine:
    market_context_v2: dict = {}
    regime_posture_v2: dict = {}


def main() -> int:
    _emit_trade_intent(
        "AUDIT_FWD_PROBE",
        "buy",
        3.25,
        {"flow_strength": 0.4, "dark_pool_bias": 0},
        {"ticker": "AUDIT_FWD_PROBE", "direction": "bullish"},
        "mixed",
        _FakeEngine(),
        decision_outcome="entered",
        blocked_reason=None,
    )
    print("emit_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
