#!/usr/bin/env python3
"""
Phase-2 shadow dry-run: call run_shadow_variants with minimal mock candidates.
Emits shadow_variant_decision and shadow_variant_summary to logs/shadow.jsonl.
No orders. Proves shadow logging when market is closed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
os.chdir(REPO)


def main() -> int:
    env_file = REPO / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'\"").strip()
            if k:
                os.environ.setdefault(k, v)

    import main as main_mod
    from telemetry.shadow_experiments import run_shadow_variants

    Config = main_mod.Config

    class _FakeEngine:
        market_context_v2: dict = {}
        regime_posture_v2: dict = {}

    engine = _FakeEngine()
    experiments = getattr(Config, "SHADOW_EXPERIMENTS", None) or []
    if not experiments:
        experiments = [{"name": "dryrun_v1", "uw_flow_weight": 1}]

    live_ctx = {"market_regime": "mixed", "regime": "mixed", "engine": engine}
    candidates = [
        {"ticker": "SPY", "direction": "bullish", "composite_score": 3.1, "score": 3.1},
        {"ticker": "QQQ", "direction": "bearish", "composite_score": 2.9, "score": 2.9},
        {"ticker": "AAPL", "direction": "bullish", "composite_score": 3.2, "score": 3.2},
    ]
    positions: dict = {}

    out = run_shadow_variants(live_ctx, candidates=candidates, positions=positions,
                              experiments=experiments, max_variants_per_cycle=2)
    try:
        from utils.system_events import log_system_event
        log_system_event(
            "phase2", "shadow_variants_rotated", "INFO",
            details={"variants_run_this_cycle": out.get("variants_run", [])},
        )
    except Exception:
        pass
    print("phase2_shadow_dryrun: emitted shadow_variant_decision, shadow_variant_summary, shadow_variants_rotated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
