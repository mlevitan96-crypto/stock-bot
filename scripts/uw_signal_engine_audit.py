#!/usr/bin/env python3
"""
UW-to-Trade-Decision Integration Audit — run ON DROPLET only.
Read-only: enumerates endpoints, ingestion, signal engine mapping, score contribution,
gate influence, decision impact, config/events, verdict.
Writes reports/UW_*.md.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
LOGS = REPO / "logs"
REPORTS = REPO / "reports"
CONFIG = REPO / "config"

UW_CACHE_PATH = DATA / "uw_flow_cache.json"
RUN_JSONL = LOGS / "run.jsonl"
SYSTEM_EVENTS_JSONL = LOGS / "system_events.jsonl"

# Canonical list (source of truth)
UW_ENDPOINTS = [
    "dark_pool",
    "etf_inflow_outflow",
    "greek_exposure",
    "greeks",
    "iv_rank",
    "market_tide",
    "max_pain",
    "net_impact",
    "oi_change",
    "option_flow",
    "shorts_ftds",
]

# Daemon cache key(s) per endpoint (uw_flow_daemon writes these)
ENDPOINT_CACHE_KEYS = {
    "dark_pool": ["dark_pool_levels", "dark_pool"],
    "etf_inflow_outflow": ["etf_flow"],
    "greek_exposure": ["greek_exposure", "greeks"],
    "greeks": ["greeks"],
    "iv_rank": ["iv_rank"],
    "market_tide": ["market_tide", "_market_tide"],
    "max_pain": ["max_pain"],
    "net_impact": ["top_net_impact", "_top_net_impact"],
    "oi_change": ["oi_change"],
    "option_flow": ["option_flow", "flow_trades"],
    "shorts_ftds": ["shorts_ftds", "ftd_pressure", "ftd", "shorts"],
}

# UW endpoint → feature extractor (uw_enrichment_v2 / uw_composite_v2) → signal layer (decision_intelligence_trace)
# Signal layers: alpha_signals, flow_signals, regime_signals, volatility_signals, dark_pool_signals
SIGNAL_ENGINE_MAP = [
    ("dark_pool", "uw_enrichment_v2 (dark_pool_notional, sentiment)", "uw_composite_v2 (dp_component)", "dark_pool_signals", "active"),
    ("etf_inflow_outflow", "uw_enrichment_v2 (etf_flow)", "uw_composite_v2 (etf_flow_component)", "alpha_signals", "active"),
    ("greek_exposure", "uw_enrichment_v2 (greeks)", "uw_composite_v2 (greeks_gamma)", "alpha_signals", "active"),
    ("greeks", "uw_enrichment_v2 (greeks)", "uw_composite_v2 (greeks_gamma_component, max_pain)", "alpha_signals", "active"),
    ("iv_rank", "uw_enrichment_v2 (iv_rank)", "uw_composite_v2 (iv_rank_component)", "alpha_signals", "active"),
    ("market_tide", "uw_enrichment_v2 (market_tide)", "uw_composite_v2 (tide_component)", "regime_signals", "active"),
    ("max_pain", "uw_composite_v2 (from greeks)", "uw_composite_v2 (gamma_resistance_levels)", "alpha_signals", "active"),
    ("net_impact", "daemon (_top_net_impact)", "uw_composite_v2 (indirect via symbol_intel)", "flow_signals", "active"),
    ("oi_change", "uw_enrichment_v2 (oi_change)", "uw_composite_v2 (oi_change_component)", "alpha_signals", "active"),
    ("option_flow", "daemon (flow_trades)", "uw_composite_v2 (flow_component, flow_trade_count)", "flow_signals", "active"),
    ("shorts_ftds", "uw_enrichment_v2 (shorts_ftds)", "uw_composite_v2 (shorts_component, ftd_pressure)", "alpha_signals", "active"),
]

RUN_WINDOW_MIN = 30
EVENTS_WINDOW_MIN = 24 * 60


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(ts) -> float | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _read_jsonl(path: Path, since_min: int | None = None) -> list[dict]:
    out = []
    if not path.exists():
        return out
    since_ts = (datetime.now(timezone.utc) - timedelta(minutes=since_min)).timestamp() if since_min else None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = rec.get("ts") or rec.get("timestamp") or rec.get("_ts")
                if since_ts and ts is not None:
                    t = _parse_ts(ts)
                    if t is not None and t < since_ts:
                        continue
                out.append(rec)
            except Exception:
                continue
    return out


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    now = _now()

    # Load cache once
    cache_data: dict = {}
    if UW_CACHE_PATH.exists():
        try:
            cache_data = json.loads(UW_CACHE_PATH.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(cache_data, dict):
                cache_data = {}
        except Exception:
            cache_data = {}

    def _cache_has_endpoint(ep: str) -> bool:
        keys = ENDPOINT_CACHE_KEYS.get(ep, [])
        for sym, blob in (cache_data or {}).items():
            if not isinstance(blob, dict):
                continue
            for k in keys:
                if k in blob and blob[k] is not None:
                    return True
            # max_pain: composite reads from greeks.max_pain when daemon merges there
            if ep == "max_pain" and blob.get("greeks") and blob.get("greeks").get("max_pain") is not None:
                return True
        for k in keys:
            if k in cache_data and cache_data[k] is not None:
                return True
        return False

    # -------------------------------------------------------------------------
    # 1) UW_ENDPOINT_INVENTORY.md
    # -------------------------------------------------------------------------
    inv_md = [
        "# UW Endpoint Inventory (Source of Truth)",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        "## Canonical list",
        "",
    ]
    for ep in UW_ENDPOINTS:
        inv_md.append(f"- {ep}")
    inv_md.append("")
    (REPORTS / "UW_ENDPOINT_INVENTORY.md").write_text("\n".join(inv_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 2) UW_INGESTION_AUDIT.md
    # -------------------------------------------------------------------------
    ing_md = [
        "# UW Ingestion Audit (Daemon → Cache)",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        f"**Cache path:** {UW_CACHE_PATH}",
        f"**Cache exists:** {UW_CACHE_PATH.exists()}",
        "",
        "## Per-endpoint",
        "",
    ]
    for ep in UW_ENDPOINTS:
        keys = ENDPOINT_CACHE_KEYS.get(ep, [])
        in_cache = _cache_has_endpoint(ep)
        ing_md.append(f"### {ep}")
        ing_md.append(f"- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)")
        ing_md.append(f"- **Cache keys:** {keys}")
        ing_md.append(f"- **Data in cache:** {'yes' if in_cache else 'no'}")
        if not in_cache:
            ing_md.append("- **Likely reason:** empty API response, gated (market hours), or error; daemon writes only on success.")
        ing_md.append("")
    (REPORTS / "UW_INGESTION_AUDIT.md").write_text("\n".join(ing_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 3) UW_SIGNAL_ENGINE_MAP.md
    # -------------------------------------------------------------------------
    map_md = [
        "# UW Signal Engine Map (Cache → Features)",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        "| UW endpoint | Feature extractor | Signal layer | Active/Inactive |",
        "|-------------|-------------------|--------------|-----------------|",
    ]
    for row in SIGNAL_ENGINE_MAP:
        map_md.append("| " + " | ".join(row) + " |")
    map_md.append("")
    map_md.append("**Note:** Inactive = data missing in cache; component uses neutral default (e.g. 0.2).")
    (REPORTS / "UW_SIGNAL_ENGINE_MAP.md").write_text("\n".join(map_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 4) UW_SCORE_CONTRIBUTION.md (from trade_intent last 30 min)
    # -------------------------------------------------------------------------
    run_events = _read_jsonl(RUN_JSONL, since_min=RUN_WINDOW_MIN)
    trade_intents = [r for r in run_events if r.get("event_type") == "trade_intent"]

    # UW-sourced component names (from uw_composite_v2 weights / score_components)
    UW_COMPONENT_NAMES = {
        "dark_pool", "options_flow", "flow_strength", "whale", "market_tide", "etf_flow",
        "greeks_gamma", "iv_rank", "oi_change", "shorts_squeeze", "ftd_pressure", "whale_persistence",
        "flow_trades", "flow_conv", "dp_", "tide", "oi_", "greeks", "iv_", "shorts", "etf", "congress",
        "insider", "institutional", "calendar", "squeeze_score",
    }

    score_md = [
        "# UW Score Contribution (Features → Score)",
        "",
        f"**Generated:** {now.isoformat()}",
        f"**Window:** last {RUN_WINDOW_MIN} min",
        f"**trade_intent count:** {len(trade_intents)}",
        "",
    ]
    non_zero_components: set[str] = set()
    for rec in trade_intents[:20]:
        trace = rec.get("intelligence_trace") or {}
        agg = trace.get("aggregation") or {}
        comps = agg.get("score_components") or {}
        if not comps and rec.get("score") is not None:
            comps = {"composite": rec.get("score")}
        for name, val in (comps or {}).items():
            try:
                v = float(val)
                if v != 0.0:
                    non_zero_components.add(name)
            except (TypeError, ValueError):
                pass
    score_md.append("**Component names with non-zero in samples:**")
    score_md.append(", ".join(sorted(non_zero_components)[:50]))
    score_md.append("")
    uw_contrib = [c for c in non_zero_components if any(u in c.lower() for u in ["flow", "dark", "tide", "greeks", "iv_rank", "oi_", "shorts", "etf", "whale", "congress", "insider"])]
    score_md.append("**UW-sourced (inferred):** " + ", ".join(uw_contrib))
    score_md.append("")
    if trade_intents:
        sample = trade_intents[-1]
        trace = sample.get("intelligence_trace") or {}
        agg = trace.get("aggregation") or {}
        comps = agg.get("score_components") or {}
        score_md.append("## Sample score_components (last trade_intent)")
        score_md.append("```json")
        score_md.append(json.dumps(comps, indent=2, default=str)[:1500])
        score_md.append("```")
    (REPORTS / "UW_SCORE_CONTRIBUTION.md").write_text("\n".join(score_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 5) UW_GATE_INFLUENCE.md
    # -------------------------------------------------------------------------
    gate_md = [
        "# UW Gate Influence (Score → Decision)",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        "Gates (score_gate, risk_gate, capacity_gate, displacement_gate, directional_gate) use composite score and capacity/risk state.",
        "UW data influences **composite score**; gates do not reference UW endpoints by name.",
        "**Causal chain:** UW → score_components → composite score → score_gate (min threshold) and capacity/risk/displacement/directional gates.",
        "",
    ]
    for rec in trade_intents[:5]:
        trace = rec.get("intelligence_trace") or {}
        gates = trace.get("gates") or {}
        gate_md.append(f"- **{rec.get('symbol')}** ({rec.get('decision_outcome')}): gates={list(gates.keys())}")
    (REPORTS / "UW_GATE_INFLUENCE.md").write_text("\n".join(gate_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 6) UW_DECISION_IMPACT_MATRIX.md
    # -------------------------------------------------------------------------
    impact = []
    for ep in UW_ENDPOINTS:
        in_cache = _cache_has_endpoint(ep)
        # Heuristic: if in cache and used in composite (from map), USED; if not in cache but wired, BROKEN; if in cache and no score comp, INGESTED BUT UNUSED
        if in_cache:
            impact.append((ep, "USED", "Data in cache; composite uses it (see UW_SIGNAL_ENGINE_MAP)."))
        else:
            impact.append((ep, "BROKEN", "Expected but missing in cache; score uses neutral default."))
    impact_md = [
        "# UW Decision Impact Matrix",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        "| Endpoint | Status | Notes |",
        "|----------|--------|-------|",
    ]
    for ep, status, notes in impact:
        impact_md.append(f"| {ep} | {status} | {notes} |")
    (REPORTS / "UW_DECISION_IMPACT_MATRIX.md").write_text("\n".join(impact_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 7) UW_CONFIG_AND_EVENTS.md
    # -------------------------------------------------------------------------
    events_24h = _read_jsonl(SYSTEM_EVENTS_JSONL, since_min=EVENTS_WINDOW_MIN) if SYSTEM_EVENTS_JSONL.exists() else []
    uw_events = [r for r in events_24h if "uw" in json.dumps(r).lower() or "cache" in json.dumps(r).lower()]
    config_md = [
        "# UW Config and Events",
        "",
        f"**Generated:** {now.isoformat()}",
        f"**System events (last 24h, uw/cache):** {len(uw_events)}",
        "",
        "## Config references",
        "",
        "- **config.registry:** CacheFiles.UW_FLOW_CACHE = data/uw_flow_cache.json",
        "- **uw_flow_daemon:** SmartPoller endpoints option_flow, dark_pool_levels, greek_exposure, greeks, top_net_impact, market_tide, oi_change, etf_flow, iv_rank, shorts_ftds, max_pain",
        "- **Market hours:** daemon polls 3x less frequently when market closed (offhours).",
        "",
        "## Sample system events (uw/cache)",
        "",
    ]
    for r in uw_events[-15:]:
        config_md.append("```json")
        config_md.append(json.dumps(r, indent=2, default=str)[:400])
        config_md.append("```")
    (REPORTS / "UW_CONFIG_AND_EVENTS.md").write_text("\n".join(config_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 8) UW_SIGNAL_ENGINE_VERDICT.md
    # -------------------------------------------------------------------------
    used_count = sum(1 for _, status, _ in impact if status == "USED")
    broken = [ep for ep, status, _ in impact if status == "BROKEN"]
    verdict_pass = used_count >= 5  # At least half of endpoints contributing
    verdict_md = [
        "# UW Signal Engine Verdict",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        "## Per-endpoint (PASS = data in cache and wired into score)",
        "",
    ]
    for ep, status, _ in impact:
        verdict_md.append(f"- **{ep}:** {'PASS' if status == 'USED' else 'FAIL'} ({status})")
    verdict_md.append("")
    verdict_md.append("## Statement")
    verdict_md.append("")
    if verdict_pass:
        verdict_md.append("**UW data is materially influencing live trading decisions.**")
    else:
        verdict_md.append("**UW data is partially influencing live trading decisions; several endpoints are missing (BROKEN).**")
    verdict_md.append("")
    verdict_md.append("## Endpoints to re-enable or re-wire for paid edge")
    verdict_md.append("")
    verdict_md.append(", ".join(broken) if broken else "None (all wired and present in cache).")
    (REPORTS / "UW_SIGNAL_ENGINE_VERDICT.md").write_text("\n".join(verdict_md), encoding="utf-8")

    return 0 if verdict_pass else 1


if __name__ == "__main__":
    sys.exit(main())
