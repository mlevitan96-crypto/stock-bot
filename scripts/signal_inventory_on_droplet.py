#!/usr/bin/env python3
"""
Phase 1A: Signal inventory (static discovery). Run ON THE DROPLET.
Discovers signals from code: registries, WEIGHTS_V3, components dicts, compute_* patterns.
Outputs: reports/signal_review/SIGNAL_INVENTORY.md, SIGNAL_INVENTORY.json
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "signal_review"
OUT_MD = OUT_DIR / "SIGNAL_INVENTORY.md"
OUT_JSON = OUT_DIR / "SIGNAL_INVENTORY.json"

# Canonical list from uw_composite_v2.py components dict (single source of truth for scoring)
CANONICAL_COMPONENTS = [
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
    "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score",
    "freshness_factor",
]


def discover_from_uw_composite() -> list[dict]:
    """Parse uw_composite_v2.py for components and WEIGHTS_V3."""
    inv = []
    ucf = REPO / "uw_composite_v2.py"
    if not ucf.exists():
        return inv
    text = ucf.read_text(encoding="utf-8", errors="replace")
    # Find components = { ... } (around line 1186)
    for m in re.finditer(r'["\'](\w+)["\']\s*:\s*round\s*\(\s*\w+', text):
        name = m.group(1)
        if name not in [x["signal_name"] for x in inv]:
            inv.append({
                "signal_name": name,
                "source_file": "uw_composite_v2.py",
                "line_range": "components dict",
                "compute_entrypoint": "_compute_composite_score_core",
                "required_inputs": "enriched_data, regime, expanded_intel",
                "referenced_in_scoring": "uw_composite_v2.py (composite sum -> clamp)",
                "status": "USED_IN_SCORE",
            })
    # WEIGHTS_V3 keys (may use different names like options_flow)
    wei = re.search(r"WEIGHTS_V3\s*=\s*\{([^}]+)\}", text, re.DOTALL)
    if wei:
        for m in re.finditer(r'"([^"]+)"\s*:', wei.group(1)):
            wkey = m.group(1)
            if not any(x["signal_name"] == wkey for x in inv):
                inv.append({
                    "signal_name": wkey,
                    "source_file": "uw_composite_v2.py",
                    "line_range": "WEIGHTS_V3",
                    "compute_entrypoint": "get_weight(component, regime)",
                    "required_inputs": "regime",
                    "referenced_in_scoring": "uw_composite_v2.py (weight * value -> contribution)",
                    "status": "USED_IN_SCORE",
                })
    return inv


def discover_from_main() -> list[dict]:
    """main.py: signal_score_breakdown logs these names."""
    inv = []
    for name in CANONICAL_COMPONENTS:
        inv.append({
            "signal_name": name,
            "source_file": "main.py",
            "line_range": "signal_score_breakdown block",
            "compute_entrypoint": "composite_meta.components from cluster",
            "required_inputs": "c.composite_meta (from uw_composite_v2 result)",
            "referenced_in_scoring": "uw_composite_v2._compute_composite_score_core",
            "status": "USED_IN_SCORE",
        })
    return inv


def merge_inventory(from_uc: list[dict], from_main: list[dict]) -> list[dict]:
    """Merge by signal_name; prefer USED_IN_SCORE and richer source."""
    by_name: dict[str, dict] = {}
    for x in from_main:
        by_name[x["signal_name"]] = {**x, "status": "USED_IN_SCORE"}
    for x in from_uc:
        if x["signal_name"] not in by_name:
            by_name[x["signal_name"]] = x
        else:
            by_name[x["signal_name"]].update({k: v for k, v in x.items() if k != "signal_name"})
    return list(by_name.values())


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    from_uc = discover_from_uw_composite()
    from_main = discover_from_main()
    inventory = merge_inventory(from_uc, from_main)
    # Dedupe by signal_name keeping one row per name
    seen = set()
    unique = []
    for s in inventory:
        if s["signal_name"] in seen:
            continue
        seen.add(s["signal_name"])
        unique.append(s)
    inventory = unique

    # JSON
    OUT_JSON.write_text(json.dumps({"signals": inventory, "source": "signal_inventory_on_droplet.py"}, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(inventory)} signals)")

    # MD
    lines = [
        "# Signal inventory (Phase 1A)",
        "",
        f"Discovered **{len(inventory)}** signals. Source: uw_composite_v2.py components + main.py breakdown.",
        "",
        "| signal_name | source_file | compute_entrypoint | status |",
        "|-------------|-------------|--------------------|--------|",
    ]
    for s in sorted(inventory, key=lambda x: x["signal_name"]):
        lines.append(f"| {s['signal_name']} | {s.get('source_file', '')} | {s.get('compute_entrypoint', '')} | {s.get('status', 'DISCOVERED')} |")
    lines.extend([
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "python3 scripts/signal_inventory_on_droplet.py",
        "```",
        "",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
