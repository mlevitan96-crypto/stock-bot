#!/usr/bin/env python3
"""
Signal + weight + exit "lay of the land" inventory.

Memory Bank: §3.2 Data Source Rule; §4 Signal Integrity; §7 COMPOSITE_WEIGHTS_V2, adaptive state/signal_weights.json.
Static inventory: config/registry COMPOSITE_WEIGHTS_V2, uw_composite_v2 weight application, adaptive sources.
Exit usage: whether exit logic references composite_score, weights, UW intel, regime.
Runtime evidence: state/signal_weights.json, state/score_telemetry.json, system_events composite_version_used.
Output: reports/STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY_<DATE>.md (no account/order IDs; observability only).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo root on path
REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _tail_jsonl(path: Path, n: int = 500) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines.append(line)
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def run(base_dir: Path, target_date: str) -> str:
    base_dir = base_dir.resolve()
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    state_dir = base_dir / "state"
    logs_dir = base_dir / "logs"

    # --- Static: COMPOSITE_WEIGHTS_V2 ---
    cw_v2: dict = {}
    version = ""
    try:
        from config.registry import COMPOSITE_WEIGHTS_V2
        cw_v2 = dict(COMPOSITE_WEIGHTS_V2)
        version = str(cw_v2.get("version", ""))
    except Exception as e:
        cw_v2 = {"_error": str(e)}
        version = "N/A"

    # Base weights / components from Memory Bank §7.2 (formula) + registry
    entry_components = [
        "flow_component", "dp_component", "insider_component", "iv_component", "smile_component",
        "whale_score", "event_component", "motif_bonus", "toxicity_component", "regime_component",
        "congress_component", "shorts_component", "inst_component", "tide_component", "calendar_component",
        "greeks_gamma_component", "ftd_pressure_component", "iv_rank_component", "oi_change_component",
        "etf_flow_component", "squeeze_score_component",
    ]
    # Registry keys that are numeric weights/params (not nested "uw")
    weight_like_keys = [k for k in cw_v2.keys() if k not in ("version", "uw") and isinstance(cw_v2.get(k), (int, float))]

    # --- Where weights applied (code references) ---
    weight_application = [
        "uw_composite_v2.py: get_weight(component, regime), get_multiplier(component)",
        "uw_composite_v2.py: _compute_composite_score_core() uses COMPOSITE_WEIGHTS_V2 and adaptive multipliers",
        "config/registry.py: COMPOSITE_WEIGHTS_V2 (single source of truth per Memory Bank §7.7)",
    ]
    adaptive_sources = [
        "state/signal_weights.json (runtime adaptive multipliers 0.25x–2.5x)",
        "adaptive_signal_optimizer.py: get_optimizer(), get_weights_for_composite(regime), get_multipliers_only(); persists to state/signal_weights.json",
    ]

    # --- Exit usage (code audit) ---
    # main.py: exit path uses current_composite_score (recomputed via compute_composite_score_v2), score_deterioration, now_v2_score; log_exit_attribution(..., v2_exit_score, v2_exit_components)
    # src/exit/exit_attribution.py: build_exit_attribution_record(..., v2_exit_score, v2_exit_components) — records score and components at exit
    exits_use_composite_score = "YES"
    exits_use_component_breakdown = "YES"
    exits_use_uw_intel = "YES"
    exits_use_regime = "YES"
    exits_use_weights = "YES"
    exit_refs = [
        "main.py: current_composite_score from compute_composite_score_v2(); score_deterioration, now_v2_score, decay_ratio; log_exit_attribution(..., v2_exit_score, v2_exit_components)",
        "src/exit/exit_attribution.py: build_exit_attribution_record(..., score_deterioration, relative_strength_deterioration, v2_exit_score, v2_exit_components)",
    ]

    # --- Runtime evidence ---
    signal_weights_snapshot: dict | None = None
    if (state_dir / "signal_weights.json").exists():
        data = _load_json(state_dir / "signal_weights.json")
        if isinstance(data, dict):
            # Redact any PII; keep structure for observability
            signal_weights_snapshot = {
                "weight_bands": list(data.get("weight_bands", {}).keys()) if isinstance(data.get("weight_bands"), dict) else None,
                "version": data.get("version"),
                "keys_present": list(data.keys()),
            }

    score_telemetry_snapshot: dict | None = None
    if (state_dir / "score_telemetry.json").exists():
        data = _load_json(state_dir / "score_telemetry.json")
        if isinstance(data, dict):
            score_telemetry_snapshot = {
                "component_zero_pct": data.get("component_zero_pct"),
                "missing_intel_counts": data.get("missing_intel_counts"),
                "keys_present": list(data.keys()),
            }

    composite_version_used: str | None = None
    events = _tail_jsonl(logs_dir / "system_events.jsonl", 200)
    for ev in reversed(events):
        if isinstance(ev, dict) and ev.get("subsystem") == "scoring" and ev.get("event_type") == "composite_version_used":
            composite_version_used = ev.get("v2_weights_version") or ev.get("composite_version") or json.dumps(ev)[:80]
            break

    # --- Weights table (component -> base weight; adaptive multiplier if available; effective) ---
    # Base weights from Memory Bank §7.2 (approximate; exact in uw_composite_v2)
    base_weights_approx = {
        "options_flow": 2.4, "dp_strength": 1.3, "insider": 0.5, "iv_skew": 0.6, "smile_slope": 0.35,
        "whale": 0.7, "event_align": 0.4, "motif": 0.6, "toxicity": -0.9, "regime": 0.3,
        "congress": 0.9, "shorts_squeeze": 0.7, "institutional": 0.5, "market_tide": 0.4, "calendar": 0.45,
        "greeks_gamma": 0.4, "ftd_pressure": 0.3, "iv_rank": 0.2, "oi_change": 0.35, "etf_flow": 0.3, "squeeze_score": 0.2,
    }
    adaptive_multipliers: dict = {}
    if isinstance(signal_weights_snapshot, dict) and signal_weights_snapshot.get("weight_bands"):
        # weight_bands is component -> multiplier or similar; use keys only for table if we don't have full structure
        adaptive_multipliers = {"(see state/signal_weights.json)": 1.0}

    # --- Build markdown ---
    now_iso = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Stock Signal / Weight / Exit Inventory",
        "",
        f"**Date:** {target_date}",
        f"**Generated:** {now_iso}",
        "",
        "## Memory Bank (cited)",
        "",
        "- **Golden Workflow:** User→Cursor→GitHub→Droplet→GitHub→Cursor→User (MEMORY_BANK §0.1)",
        "- **Data Source Rule:** Reports use droplet production data; ReportDataFetcher / droplet as source of truth (§3.2)",
        "- **Signal Integrity:** No \"unknown\" unless truly unknown; preserve signal_type, metadata (§4)",
        "- **Composite v2 + weight tuning:** config/registry.py COMPOSITE_WEIGHTS_V2; adaptive state/signal_weights.json (§7.5, §7.7)",
        "- **Attribution invariants:** Append-only logs (attribution, exit_attribution, master_trade_log) (§5.5, §7.9)",
        "",
        "---",
        "",
        "## 1. Static inventory (code + config)",
        "",
        "### COMPOSITE_WEIGHTS_V2 (config/registry.py)",
        f"- **Version:** {version}",
        f"- **Numeric/param keys:** {weight_like_keys[:20]}{'...' if len(weight_like_keys) > 20 else ''}",
        "",
        "### Where weights are applied",
        "",
    ]
    for w in weight_application:
        lines.append(f"- {w}")
    lines.extend([
        "",
        "### Adaptive multiplier sources",
        "",
    ])
    for a in adaptive_sources:
        lines.append(f"- {a}")
    lines.extend([
        "",
        "### Signals feeding entry (composite formula §7.2)",
        "",
        "| Component | Base weight (approx) |",
        "|-----------|----------------------|",
    ])
    for c, w in list(base_weights_approx.items())[:15]:
        lines.append(f"| {c} | {w} |")
    if len(base_weights_approx) > 15:
        lines.append(f"| ... (+{len(base_weights_approx) - 15} more) | — |")
    lines.extend([
        "",
        "---",
        "",
        "## 2. Exit usage inventory",
        "",
        "| Question | Determination |",
        "|----------|---------------|",
        f"| Exits use composite_score? | **{exits_use_composite_score}** |",
        f"| Exits use component breakdown? | **{exits_use_component_breakdown}** |",
        f"| Exits use UW intel features? | **{exits_use_uw_intel}** |",
        f"| Exits use regime/posture? | **{exits_use_regime}** |",
        f"| **Exits use weights / adaptive multipliers?** | **{exits_use_weights}** |",
        "",
        "**File/symbol references:**",
        "",
    ])
    for ref in exit_refs:
        lines.append(f"- {ref}")
    lines.extend([
        "",
        "---",
        "",
        "## 3. Runtime evidence (droplet-state if present)",
        "",
    ])
    if signal_weights_snapshot:
        lines.append("- **state/signal_weights.json:** active multipliers snapshot (keys_present, weight_bands components, version).")
        lines.append(f"  - keys: {signal_weights_snapshot.get('keys_present')}")
    else:
        lines.append("- **state/signal_weights.json:** not present or unreadable.")
    if score_telemetry_snapshot:
        lines.append("- **state/score_telemetry.json:** component zero% and missing intel counts present.")
        lines.append(f"  - keys: {score_telemetry_snapshot.get('keys_present')}")
    else:
        lines.append("- **state/score_telemetry.json:** not present or unreadable.")
    if composite_version_used:
        lines.append(f"- **logs/system_events.jsonl (composite_version_used):** {composite_version_used}")
    else:
        lines.append("- **logs/system_events.jsonl (composite_version_used):** no recent event found.")
    lines.extend([
        "",
        "---",
        "",
        "## 4. Gaps and next safe actions",
        "",
        "- **Gaps:** Unknown exit paths (if any) should be audited; signal_decay variants documented in §7.1; veto traceability via gate_event rules (§4.3).",
        "- **Next safe actions (observability only):** Run this inventory on droplet after EOD; include manifest pass/fail in daily review; no strategy or safety logic changes.",
        "",
        "---",
        "",
    ])

    out_md = reports_dir / f"STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY_{target_date}.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return str(out_md)


def main() -> int:
    parser = argparse.ArgumentParser(description="Signal/weight/exit inventory report")
    parser.add_argument("--date", default=None, help="Target date YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--base-dir", default=None, help="Repo root (default: parent of scripts/)")
    args = parser.parse_args()

    base_dir = Path(args.base_dir) if args.base_dir else REPO
    target_date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    out_path = run(base_dir, target_date)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
