#!/usr/bin/env python3
"""
Stock-Bot Entry Intelligence Population & Parity Auditor.

Memory Bank: §4 Signal Integrity; §7.2 Composite v2; §7.5–§7.7 Adaptive weights;
§7.8 UW Intelligence; §7.9 Attribution. Observability-only (NO tuning, NO gating).

Explains why composite v2 components default, identifies missing/miswired entry intelligence,
produces concrete plan to populate signals safely.

Output: reports/STOCK_ENTRY_INTELLIGENCE_PARITY_AND_GAPS_<DATE>.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Component -> expected input fields (from uw_composite_v2 + uw_enrichment_v2)
COMPONENT_INPUTS = {
    "flow": ["sentiment", "conviction", "trade_count", "flow_trades"],
    "dark_pool": ["dark_pool"],
    "insider": ["insider"],
    "iv_skew": ["iv_term_skew"],
    "smile": ["smile_slope"],
    "whale": ["motif_whale"],
    "event": ["event_alignment"],
    "motif_bonus": ["motif_staircase", "motif_burst"],
    "toxicity_penalty": ["toxicity"],
    "regime": ["regime"],
    "congress": ["congress"],
    "shorts_squeeze": ["shorts", "ftd"],
    "institutional": ["institutional"],
    "market_tide": ["market_tide"],
    "calendar": ["calendar"],
    "greeks_gamma": ["greeks"],
    "ftd_pressure": ["ftd", "shorts"],
    "iv_rank": ["iv", "iv_rank"],
    "oi_change": ["oi_change", "oi"],
    "etf_flow": ["etf_flow"],
    "squeeze_score": ["squeeze_score"],
    "freshness_factor": ["_last_update", "last_update"],
}

# Intended source per component
COMPONENT_SOURCES = {
    "flow": "uw_flow_cache (UW ingestion)",
    "dark_pool": "uw_flow_cache (UW ingestion)",
    "insider": "uw_flow_cache (UW ingestion)",
    "iv_skew": "uw_enrichment_v2 (computed from cache)",
    "smile": "uw_enrichment_v2 (computed from cache)",
    "whale": "uw_enrichment_v2 motif_whale (from cache history)",
    "event": "uw_enrichment_v2 (computed from cache)",
    "motif_bonus": "uw_enrichment_v2 motif_staircase/burst (from cache history)",
    "toxicity_penalty": "uw_enrichment_v2 (computed from cache)",
    "regime": "state/regime_state.json, regime_detector",
    "congress": "uw_flow_cache or data/uw_expanded_intel.json",
    "shorts_squeeze": "uw_flow_cache or expanded_intel",
    "institutional": "uw_flow_cache or expanded_intel",
    "market_tide": "uw_flow_cache or expanded_intel",
    "calendar": "uw_flow_cache or expanded_intel",
    "greeks_gamma": "uw_flow_cache (UW greeks endpoint)",
    "ftd_pressure": "uw_flow_cache (UW shorts/FTD)",
    "iv_rank": "uw_flow_cache (UW iv endpoint)",
    "oi_change": "uw_flow_cache (UW oi endpoint)",
    "etf_flow": "uw_flow_cache (UW etf endpoint)",
    "squeeze_score": "uw_flow_cache or computed",
    "freshness_factor": "uw_flow_cache _last_update",
}


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _has_data(obj: dict, keys: list[str]) -> tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, "not_dict"
    for k in keys:
        v = obj.get(k)
        if v is not None and v != "" and v != {} and v != []:
            return True, k
    return False, "missing"


def run(base_dir: Path, target_date: str) -> str:
    base_dir = base_dir.resolve()
    reports_dir = base_dir / "reports"
    data_dir = base_dir / "data"
    state_dir = base_dir / "state"
    logs_dir = base_dir / "logs"
    reports_dir.mkdir(parents=True, exist_ok=True)

    uw_cache = _load_json(data_dir / "uw_flow_cache.json")
    expanded_intel = _load_json(data_dir / "uw_expanded_intel.json")
    premarket = _load_json(state_dir / "premarket_intel.json")
    postmarket = _load_json(state_dir / "postmarket_intel.json")
    regime_state = _load_json(state_dir / "regime_state.json")
    symbol_risk = _load_json(state_dir / "symbol_risk_features.json")
    market_context = _load_json(state_dir / "market_context_v2.json")

    # Sample symbols from cache
    symbols = [k for k in (uw_cache or {}).keys() if not k.startswith("_")][:20]
    if not symbols:
        symbols = ["AAPL", "SPY", "QQQ"]

    # Phase 1: Presence check per component
    presence: dict[str, str] = {}
    for comp, inputs in COMPONENT_INPUTS.items():
        found = False
        for sym in symbols:
            data = (uw_cache or {}).get(sym, {})
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = {}
            exp_intel = (expanded_intel or {}).get(sym, {}) if isinstance(expanded_intel, dict) else {}
            combined = {**(data if isinstance(data, dict) else {}), **(exp_intel if isinstance(exp_intel, dict) else {})}
            ok, _ = _has_data(combined, inputs)
            if ok:
                found = True
                break
        if found:
            presence[comp] = "PRESENT"
        else:
            # Check if component has neutral default in uw_composite_v2
            if comp in ("iv_skew", "smile", "event", "congress", "shorts_squeeze", "institutional",
                        "market_tide", "calendar", "greeks_gamma", "ftd_pressure", "oi_change",
                        "etf_flow", "squeeze_score"):
                presence[comp] = "DEFAULTED"
            else:
                presence[comp] = "MISSING"

    # Phase 2: Source trace for MISSING/DEFAULTED
    failure_modes: dict[str, str] = {}
    for comp in presence:
        if presence[comp] in ("DEFAULTED", "MISSING"):
            src = COMPONENT_SOURCES.get(comp, "unknown")
            if "uw_flow_cache" in src and (not uw_cache or len([k for k in (uw_cache or {}).keys() if not k.startswith("_")]) == 0):
                failure_modes[comp] = "ingestion not running or cache empty"
            elif "expanded_intel" in src and (not expanded_intel or not isinstance(expanded_intel, dict)):
                failure_modes[comp] = "expanded_intel not populated"
            elif "uw_enrichment" in src:
                failure_modes[comp] = "enrichment computed from cache; cache may lack upstream fields"
            elif comp in ("congress", "shorts_squeeze", "institutional", "market_tide", "calendar",
                         "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow"):
                failure_modes[comp] = "UW expanded endpoints may not be polled or wired to cache"
            else:
                failure_modes[comp] = "wiring incomplete or intentionally disabled"

    # Phase 3: Applicability
    applicable = {c: "APPLICABLE to stock-bot" for c in COMPONENT_INPUTS}
    applicable["flow"] = "APPLICABLE (UW options flow for equities)"
    applicable["congress"] = "APPLICABLE (congress trading in equities)"
    applicable["squeeze_score"] = "APPLICABLE (FTD/SI squeeze in equities)"
    for c in ["greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow"]:
        applicable[c] = "APPLICABLE (options/ETF data for equity names)"
    applicable["regime"] = "REQUIRES STOCK-SPECIFIC SOURCE (regime_state/regime_detector)"
    # None are crypto-specific for stock-bot

    # Phase 4: Recommendations
    activate = [c for c in presence if presence[c] == "PRESENT"]
    adapt = [c for c in presence if presence[c] == "DEFAULTED" and "UW" in COMPONENT_SOURCES.get(c, "")]
    defer = []
    new_intel = []
    if not expanded_intel or not isinstance(expanded_intel, dict):
        new_intel.append("Populate data/uw_expanded_intel.json from UW expanded endpoints or premarket/postmarket intel")
    if not uw_cache or len([k for k in (uw_cache or {}).keys() if not k.startswith("_")]) == 0:
        new_intel.append("Ensure uw_flow_daemon runs and populates data/uw_flow_cache.json")

    now_iso = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Stock Entry Intelligence Population & Parity Audit",
        "",
        f"**Date:** {target_date}",
        f"**Generated:** {now_iso}",
        "",
        "## Memory Bank (cited)",
        "",
        "- **§4 Signal Integrity:** preserve signal_type, metadata; no \"unknown\" unless truly unknown.",
        "- **§7.2 Composite v2 scoring:** flow, dp, insider, iv_skew, smile, whale, event, motif, toxicity, regime, congress, shorts, inst, tide, calendar, greeks, ftd, iv_rank, oi, etf, squeeze.",
        "- **§7.5–§7.7 Adaptive weights & telemetry:** state/signal_weights.json; state/score_telemetry.json.",
        "- **§7.8 UW Intelligence Layer:** UW client, premarket/postmarket intel, expanded endpoints.",
        "- **§7.9 Attribution invariants:** append-only logs.",
        "- **Observability-only:** NO tuning, NO gating changes.",
        "",
        "---",
        "",
        "## Why 0% coverage (from prior audit)",
        "",
        "The signal contribution audit showed 0% coverage for all components in exit_attribution v2_exit_components.",
        "This indicates either: (1) v2_exit_components uses different keys than the audit expected, or (2) components",
        "are not being written to exit records. At entry, components are computed from enriched_data (uw_flow_cache",
        "+ uw_enrichment_v2 + expanded_intel). If uw_flow_cache is empty or UW daemon is not running, all flow-based",
        "components default. Expanded intel (congress, shorts, greeks, etc.) requires UW expanded endpoints to be",
        "polled and written to cache or uw_expanded_intel.json.",
        "",
        "---",
        "",
        "## Phase 1: Entry intelligence presence check",
        "",
        "| Component | Status | Expected inputs | Source |",
        "|-----------|--------|-----------------|--------|",
    ]
    for comp in sorted(COMPONENT_INPUTS.keys()):
        st = presence.get(comp, "UNKNOWN")
        inp = ", ".join(COMPONENT_INPUTS[comp][:3])
        src = COMPONENT_SOURCES.get(comp, "?")[:50]
        lines.append(f"| {comp} | {st} | {inp} | {src} |")

    lines.extend([
        "",
        "---",
        "",
        "## Phase 2: Source trace (MISSING/DEFAULTED)",
        "",
    ])
    for comp in sorted(failure_modes.keys()):
        lines.append(f"- **{comp}**: {failure_modes[comp]}")
    if not failure_modes:
        lines.append("- None (all PRESENT).")

    lines.extend([
        "",
        "---",
        "",
        "## Phase 3: Parity & applicability",
        "",
        "| Component | Applicability | Rationale |",
        "|-----------|---------------|-----------|",
    ])
    for comp in sorted(COMPONENT_INPUTS.keys()):
        app = applicable.get(comp, "APPLICABLE")
        lines.append(f"| {comp} | {app} | Stock-bot equities |")

    lines.extend([
        "",
        "---",
        "",
        "## Phase 4: Recommendations (NO-APPLY)",
        "",
        "### 1) Components to ACTIVATE (data already available)",
        "",
    ])
    for c in activate[:15]:
        lines.append(f"- **{c}**: Data present in cache. Evidence: sampled symbols. **STATUS: SHADOW — NOT APPLIED**")
    if not activate:
        lines.append("- None (no components have non-default data in sampled cache).")

    lines.extend([
        "",
        "### 2) Components to ADAPT (need stock-specific intel)",
        "",
    ])
    for c in adapt[:15]:
        lines.append(f"- **{c}**: Defaulting; wire UW expanded endpoints or premarket intel. **STATUS: SHADOW — NOT APPLIED**")
    if not adapt:
        lines.append("- None.")

    lines.extend([
        "",
        "### 3) Components to DEFER (not applicable)",
        "",
    ])
    for c in defer:
        lines.append(f"- **{c}**: Not applicable to stock-bot. **STATUS: SHADOW — NOT APPLIED**")
    if not defer:
        lines.append("- None (all components are applicable to equities).")

    lines.extend([
        "",
        "### 4) Minimal new intel sources to add first",
        "",
    ])
    for item in new_intel[:5]:
        lines.append(f"- {item} **STATUS: SHADOW — NOT APPLIED**")
    if not new_intel:
        lines.append("- Audit existing pipeline; ensure daemon and premarket/postmarket scripts run.")

    lines.extend([
        "",
        "---",
        "",
        "## Data source status",
        "",
        f"- **uw_flow_cache.json**: {'present' if uw_cache else 'missing'}; {len([k for k in (uw_cache or {}).keys() if not k.startswith('_')])} symbols",
        f"- **uw_expanded_intel.json**: {'present' if expanded_intel else 'missing'}",
        f"- **premarket_intel.json**: {'present' if premarket else 'missing'}",
        f"- **postmarket_intel.json**: {'present' if postmarket else 'missing'}",
        f"- **regime_state.json**: {'present' if regime_state else 'missing'}",
        f"- **symbol_risk_features.json**: {'present' if symbol_risk else 'missing'}",
        f"- **market_context_v2.json**: {'present' if market_context else 'missing'}",
        "",
        "---",
        "",
        "*Generated by scripts/entry_intelligence_parity_audit.py. Observability-only.*",
        "",
    ])

    out_path = reports_dir / f"STOCK_ENTRY_INTELLIGENCE_PARITY_AND_GAPS_{target_date}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    parser.add_argument("--base-dir", default=None)
    args = parser.parse_args()
    base_dir = Path(args.base_dir) if args.base_dir else REPO
    target_date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = run(base_dir, target_date)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
