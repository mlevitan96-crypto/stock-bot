#!/usr/bin/env python3
"""
Shadow: Classify inventoried gates as alpha (scoring/signal) vs safety (exposure, kill, quota).
Alpha gates will be converted to weighted contributors; safety gates remain binary/unchanged.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SAFETY_PATTERNS = (
    "max_daily_loss", "max_open_positions", "max_notional", "max_new_positions",
    "disable_execution", "enable_intelligence_only", "canary_quota", "promotion_thresholds",
    "main_cycle_gate", "auto_rollback", "pnl_threshold_usd", "win_rate_threshold",
    "disable_if_canary", "live_safety",
)


def classify_one(gate: dict) -> str:
    key_path = (gate.get("key_path") or "").lower()
    source = (gate.get("source") or "").lower()
    for pat in SAFETY_PATTERNS:
        if pat.lower() in key_path or pat.lower() in source:
            return "safety"
    # Exit regimes: fire_sale/let_it_breathe thresholds are alpha (signal behavior)
    if "exit_regimes" in key_path or "exit_weights" in key_path:
        return "alpha"
    if "mode_governance" in source and ("enabled" in key_path or "sensitivity" in key_path):
        return "alpha"
    if "policy_variants" in source and "signal_decay" in key_path:
        return "alpha"
    if "policy_variants" in source and "blockers" in key_path:
        return "safety"
    if "uw_micro" in key_path:
        return "alpha"
    if "tuning" in key_path and "exit_weights" in key_path:
        return "alpha"
    if "tuning" in key_path and "entry_thresholds" in key_path:
        return "alpha"
    return "alpha"


def main() -> int:
    ap = argparse.ArgumentParser(description="Classify signal gates (alpha vs safety)")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.inventory)
    if not path.exists():
        print(f"Inventory missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    gates = data.get("gates", [])
    classified = []
    for g in gates:
        c = dict(g)
        c["classification"] = classify_one(g)
        classified.append(c)

    out = {
        "inventory_path": str(path),
        "gate_count": len(classified),
        "alpha_count": sum(1 for c in classified if c["classification"] == "alpha"),
        "safety_count": sum(1 for c in classified if c["classification"] == "safety"),
        "gates": classified,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Classified: alpha", out["alpha_count"], "safety", out["safety_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
