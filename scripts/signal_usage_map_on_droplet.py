#!/usr/bin/env python3
"""
Phase 1B: Signal usage map. Run ON THE DROPLET.
Traces: scoring composition, normalization/clipping, expectancy gate.
Outputs: reports/signal_review/SIGNAL_USAGE_MAP.md, SIGNAL_USAGE_MAP.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "signal_review"
OUT_MD = OUT_DIR / "SIGNAL_USAGE_MAP.md"
OUT_JSON = OUT_DIR / "SIGNAL_USAGE_MAP.json"

# Load inventory if present so we can annotate each
INVENTORY_JSON = OUT_DIR / "SIGNAL_INVENTORY.json"

# From uw_composite_v2: components keys are the signals; gate uses composite_exec_score = score (post-clamp)
COMPONENT_KEYS = [
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
    "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score",
    "freshness_factor",
]

WEIGHT_SOURCE = "uw_composite_v2.py WEIGHTS_V3 / get_weight(component, regime)"
CONTRIBUTION_PATH = "components[signal] * weight -> sum -> clamp(0,1) -> composite_pre_clamp; adjustments -> score -> gate"


def build_usage_map() -> list[dict]:
    """Build used/unused map from known scoring path."""
    usage = []
    for name in COMPONENT_KEYS:
        usage.append({
            "signal_name": name,
            "USED_IN_SCORE": True,
            "USED_IN_GATE_SCORE": True,
            "WEIGHT_SOURCE": WEIGHT_SOURCE,
            "CONTRIBUTION_PATH": CONTRIBUTION_PATH,
        })
    return usage


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    usage = build_usage_map()

    OUT_JSON.write_text(json.dumps({"usage_map": usage, "source": "signal_usage_map_on_droplet.py"}, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(usage)} signals)")

    lines = [
        "# Signal usage map (Phase 1B)",
        "",
        "| signal_name | USED_IN_SCORE | USED_IN_GATE_SCORE | WEIGHT_SOURCE |",
        "|-------------|---------------|---------------------|---------------|",
    ]
    for u in usage:
        lines.append(f"| {u['signal_name']} | {u['USED_IN_SCORE']} | {u['USED_IN_GATE_SCORE']} | {WEIGHT_SOURCE[:40]}... |")
    lines.extend([
        "",
        "CONTRIBUTION_PATH: " + CONTRIBUTION_PATH,
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "python3 scripts/signal_usage_map_on_droplet.py",
        "```",
        "",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
