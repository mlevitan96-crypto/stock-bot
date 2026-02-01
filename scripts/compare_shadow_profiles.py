#!/usr/bin/env python3
"""
Compare shadow tuning profiles and write reports/SHADOW_TUNING_COMPARISON.md.

Reads SHADOW_TUNING_baseline.json, SHADOW_TUNING_relaxed_displacement.json,
SHADOW_TUNING_higher_min_exec_score.json, SHADOW_TUNING_exit_tighten.json.
Outputs: which profile improved expectancy, reduced over-blocking, improved exit quality.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"

PROFILES = ["baseline", "relaxed_displacement", "higher_min_exec_score", "exit_tighten"]


def main() -> int:
    results: Dict[str, Dict] = {}
    for name in PROFILES:
        path = REPORTS / f"SHADOW_TUNING_{name}.json"
        if path.exists():
            try:
                results[name] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                results[name] = {}
        else:
            results[name] = {}

    base = results.get("baseline") or {}
    base_hyp = base.get("hypothetical") or {}
    base_pnl = base_hyp.get("net_pnl_usd")
    if base_pnl is None:
        base_pnl = (base.get("baseline") or {}).get("net_pnl_usd") or 0

    lines = [
        "# Shadow Tuning Comparison",
        "",
        "**Generated:** paper simulation only. NOT LIVE — no trading logic or config changed.",
        "",
        "## Profile results (hypothetical PnL vs baseline)",
        "",
        "| Profile | Hypothetical PnL (USD) | Δ vs baseline |",
        "|---------|-------------------------|--------------|",
    ]
    best_name = "baseline"
    best_pnl = float(base_pnl) if base_pnl is not None else 0.0
    for name in PROFILES:
        r = results.get(name) or {}
        hyp = r.get("hypothetical") or {}
        pnl = hyp.get("net_pnl_usd")
        if pnl is None:
            pnl = (r.get("baseline") or {}).get("net_pnl_usd")
        pnl = float(pnl) if pnl is not None else 0.0
        delta = pnl - float(base_pnl) if base_pnl is not None else 0
        delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
        lines.append(f"| {name} | {pnl:.2f} | {delta_str} |")
        if pnl > best_pnl:
            best_pnl = pnl
            best_name = name

    lines.extend([
        "",
        "## Summary",
        "",
        f"- **Best expectancy (hypothetical):** {best_name} (PnL {best_pnl:.2f} USD)",
        "",
        "- **Relaxed displacement:** Adds counterfactual PnL from blocked trades; improves if blocks were costly.",
        "- **Higher MIN_EXEC_SCORE:** Fewer trades (not simulated here); compare baseline vs fewer-entry scenario separately.",
        "- **Exit tighten:** Adds heuristic savings from reduced left-on-table; improves if exits were late.",
        "",
        "## NOT LIVE YET",
        "",
        "Any config change (displacement, MIN_EXEC_SCORE, trailing-stop, time-exit) must be:",
        "- CONFIG ONLY,",
        "- DISABLED by default,",
        "- Documented and applied only after human review.",
        "",
    ])

    out_path = REPORTS / "SHADOW_TUNING_COMPARISON.md"
    REPORTS.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
