#!/usr/bin/env python3
"""
Stock-Bot Signal Contribution & Intelligence Gap Auditor.

Memory Bank: §4 Signal Integrity; §7.2 Composite v2 scoring; §7.5–§7.7 Adaptive weights & telemetry;
§7.9 Attribution invariants. Observability-only (NO tuning, NO gating changes).

Loads droplet production data (logs/exit_attribution, master_trade_log, state/score_telemetry,
state/signal_weights, state/daily_universe_v2, reports/STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY).
Produces reports/STOCK_SIGNAL_CONTRIBUTION_AND_GAPS_<DATE>.md with:
- Signal coverage matrix, contribution & redundancy, regime blind spots
- Intelligence gap taxonomy, evidence-based roadmap (NO-APPLY)

Run from repo root: python scripts/signal_contribution_and_gaps_audit.py [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# §7.2 component list (uw_composite_v2.py components dict)
COMPONENTS = [
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
    "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow",
    "squeeze_score", "freshness_factor",
]


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _load_jsonl(path: Path, limit: int | None = None) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if limit and len(out) >= limit:
                break
    return out


def _outcome_bucket(pnl: float | None) -> str:
    if pnl is None:
        return "unknown"
    p = float(pnl)
    if p > 0:
        return "win"
    if p < 0:
        return "loss"
    return "flat"


def run(base_dir: Path, target_date: str) -> str:
    base_dir = base_dir.resolve()
    reports_dir = base_dir / "reports"
    logs_dir = base_dir / "logs"
    state_dir = base_dir / "state"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # --- Phase 1: Load data (graceful degrade) ---
    exit_attr = _load_jsonl(logs_dir / "exit_attribution.jsonl")
    master_log = _load_jsonl(logs_dir / "master_trade_log.jsonl")
    score_tel = _load_json(state_dir / "score_telemetry.json")
    signal_weights = _load_json(state_dir / "signal_weights.json")
    universe = _load_json(state_dir / "daily_universe_v2.json")
    inv_path = reports_dir / f"STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY_{target_date}.md"
    inventory_present = inv_path.exists()

    # Filter exit_attr by date (timestamp or entry_timestamp)
    def _in_date(r: dict) -> bool:
        ts = r.get("timestamp") or r.get("entry_timestamp") or ""
        return str(ts)[:10] == target_date if ts else True

    exit_filtered = [r for r in exit_attr if _in_date(r)] if exit_attr else []
    if not exit_filtered and exit_attr:
        exit_filtered = exit_attr[-500:]  # fallback: last 500

    # --- Phase 2: Signal contribution analysis ---
    comp_coverage: dict[str, int] = defaultdict(int)
    comp_defaulted: dict[str, int] = defaultdict(int)
    comp_present_contrib: dict[str, list[float]] = defaultdict(list)
    comp_outcome: dict[str, dict[str, int]] = defaultdict(lambda: {"win": 0, "loss": 0, "flat": 0, "unknown": 0})
    comp_present_in_loss: dict[str, int] = defaultdict(int)
    comp_absent_in_win: dict[str, int] = defaultdict(int)
    regime_coverage: dict[str, int] = defaultdict(int)

    for rec in exit_filtered:
        outcome = _outcome_bucket(rec.get("pnl"))
        regime = str(rec.get("entry_regime") or rec.get("exit_regime") or "").upper() or "UNKNOWN"
        regime_coverage[regime] += 1

        comps = rec.get("v2_exit_components") or {}
        if isinstance(comps, dict):
            for c in COMPONENTS:
                v = comps.get(c)
                if v is not None:
                    comp_coverage[c] += 1
                    try:
                        comp_present_contrib[c].append(float(v))
                    except (TypeError, ValueError):
                        comp_defaulted[c] += 1
                    comp_outcome[c][outcome] += 1
                    if outcome == "loss":
                        comp_present_in_loss[c] += 1
                else:
                    comp_defaulted[c] += 1
                    if outcome == "win":
                        comp_absent_in_win[c] += 1

    n_exits = len(exit_filtered)
    comp_pct: dict[str, float] = {}
    for c in COMPONENTS:
        comp_pct[c] = (comp_coverage[c] / n_exits * 100) if n_exits else 0.0

    # Score telemetry (component zero%, missing intel)
    comp_zero_pct: dict[str, float] = {}
    missing_intel: dict[str, int] = {}
    if isinstance(score_tel, dict):
        cz = score_tel.get("component_zero_pct") or score_tel.get("components") or {}
        if isinstance(cz, dict):
            comp_zero_pct = {k: float(v) for k, v in cz.items() if isinstance(v, (int, float))}
        mi = score_tel.get("missing_intel") or score_tel.get("missing_intel_counts") or {}
        if isinstance(mi, dict):
            missing_intel = {k: int(v) for k, v in mi.items() if isinstance(v, (int, float))}

    # Adaptive multipliers (base * multiplier = effective)
    base_weights: dict[str, float] = {
        "flow": 2.4, "dark_pool": 1.3, "insider": 0.5, "iv_skew": 0.6, "smile": 0.35,
        "whale": 0.7, "event": 0.4, "motif_bonus": 0.6, "toxicity_penalty": -0.9, "regime": 0.3,
        "congress": 0.9, "shorts_squeeze": 0.7, "institutional": 0.5, "market_tide": 0.4,
        "calendar": 0.45, "greeks_gamma": 0.4, "ftd_pressure": 0.3, "iv_rank": 0.2,
        "oi_change": 0.35, "etf_flow": 0.3, "squeeze_score": 0.2, "freshness_factor": 1.0,
    }
    adaptive_mult: dict[str, float] = {}
    if isinstance(signal_weights, dict):
        wb = signal_weights.get("weight_bands") or {}
        if isinstance(wb, dict):
            for k, v in wb.items():
                if isinstance(v, (int, float)):
                    adaptive_mult[k] = float(v)
                elif isinstance(v, dict) and "multiplier" in v:
                    adaptive_mult[k] = float(v.get("multiplier", 1.0))

    # --- Phase 3: Intelligence gap detection ---
    low_coverage_regimes = [r for r, c in regime_coverage.items() if c > 0 and c < max(regime_coverage.values(), default=1) // 3]
    over_rep_low_contrib: list[str] = []
    under_rep_high_contrib: list[str] = []
    for c in COMPONENTS:
        pct = comp_pct.get(c, 0)
        avg_contrib = sum(comp_present_contrib.get(c, [])) / max(len(comp_present_contrib.get(c, [])), 1)
        if pct > 80 and abs(avg_contrib) < 0.05:
            over_rep_low_contrib.append(c)
        if pct < 30 and abs(avg_contrib) > 0.1:
            under_rep_high_contrib.append(c)

    # Exit reason counts (bucketed)
    exit_reason_counts: dict[str, int] = defaultdict(int)
    for r in exit_filtered:
        reason = str(r.get("exit_reason") or "unknown")[:50]
        exit_reason_counts[reason] += 1

    # --- Phase 4: Recommendations (NO-APPLY) ---
    rec_review: list[dict] = []
    rec_deepen: list[dict] = []
    rec_add: list[dict] = []
    rec_protect: list[dict] = []

    for c in over_rep_low_contrib:
        rec_review.append({
            "signal": c, "evidence": f"coverage {comp_pct.get(c, 0):.0f}%, low avg contribution",
            "confidence": "medium", "risk": "Low; observability-only",
        })
    for c in under_rep_high_contrib:
        rec_protect.append({
            "signal": c, "evidence": f"coverage {comp_pct.get(c, 0):.0f}%, higher marginal contribution when present",
            "confidence": "medium", "risk": "Do not reduce weight without further analysis",
        })

    if low_coverage_regimes:
        rec_add.append({
            "gap": "REGIME_GAP",
            "evidence": f"Regimes {low_coverage_regimes} have low sample counts",
            "confidence": "low", "risk": "Regime-specific intel may be missing",
        })

    # --- Phase 5: Report generation ---
    now_iso = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Stock Signal Contribution & Intelligence Gap Audit",
        "",
        f"**Date:** {target_date}",
        f"**Generated:** {now_iso}",
        "",
        "## Intent & governance citations",
        "",
        "- **§4 Signal Integrity Contract:** preserve signal_type, metadata; no \"unknown\" unless truly unknown.",
        "- **§7.2 Composite v2 scoring:** formula components (flow, dp, insider, iv_skew, smile, whale, event, motif, toxicity, regime, congress, shorts, inst, tide, calendar, greeks, ftd, iv_rank, oi, etf, squeeze).",
        "- **§7.5–§7.7 Adaptive weights & telemetry:** state/signal_weights.json (0.25x–2.5x); state/score_telemetry.json (component zero%, missing intel).",
        "- **§7.9 Attribution invariants:** append-only logs; attribution MUST NEVER raise inside scoring.",
        "- **Observability-only:** NO tuning, NO gating changes. This report does not modify live behavior.",
        "",
        "---",
        "",
        "## Data sources (droplet)",
        "",
        f"- **exit_attribution.jsonl** (date-filtered): {len(exit_filtered)} records",
        f"- **master_trade_log.jsonl**: {len(master_log)} records",
        f"- **score_telemetry.json**: {'present' if score_tel else 'missing'}",
        f"- **signal_weights.json**: {'present' if signal_weights else 'missing'}",
        f"- **daily_universe_v2.json**: {'present' if universe else 'missing'}",
        f"- **STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY_{target_date}.md**: {'present' if inventory_present else 'missing'}",
        "",
        "---",
        "",
        "## Signal coverage matrix",
        "",
        "| Component | Coverage % | Defaulted % | Zero% (telemetry) | Avg contrib when present | Win | Loss | Flat |",
        "|-----------|------------|-------------|-------------------|--------------------------|-----|------|------|",
    ]

    for c in COMPONENTS:
        cov = comp_pct.get(c, 0)
        def_pct = (comp_defaulted.get(c, 0) / n_exits * 100) if n_exits else 0
        zr = comp_zero_pct.get(c, 0)
        avg = sum(comp_present_contrib.get(c, [])) / max(len(comp_present_contrib.get(c, [])), 1)
        o = comp_outcome.get(c, {})
        lines.append(f"| {c} | {cov:.0f}% | {def_pct:.0f}% | {zr:.0f}% | {avg:.3f} | {o.get('win', 0)} | {o.get('loss', 0)} | {o.get('flat', 0)} |")

    lines.extend([
        "",
        "---",
        "",
        "## Contribution & redundancy findings",
        "",
        "### Over-represented, low marginal contribution",
        "",
    ])
    if over_rep_low_contrib:
        for c in over_rep_low_contrib:
            lines.append(f"- **{c}**: High coverage, low avg contribution → candidate for REVIEW.")
    else:
        lines.append("- None identified.")
    lines.extend([
        "",
        "### Under-represented, high marginal contribution",
        "",
    ])
    if under_rep_high_contrib:
        for c in under_rep_high_contrib:
            lines.append(f"- **{c}**: Low coverage, higher contribution when present → PROTECT.")
    else:
        lines.append("- None identified.")
    lines.extend([
        "",
        "### Redundancy (correlation)",
        "",
        "- Full correlation matrix requires per-trade component vectors; deferred to offline analysis.",
        "- Signals that frequently co-occur with >80% overlap: check flow + dark_pool, iv_skew + smile.",
        "",
        "### Failure modes",
        "",
    ])
    fail_present_loss = [c for c in COMPONENTS if comp_present_in_loss.get(c, 0) > comp_outcome.get(c, {}).get("win", 0)]
    fail_absent_win = [c for c in COMPONENTS if comp_absent_in_win.get(c, 0) > 0]
    lines.append("- **Signals frequently present in losing trades:** " + (", ".join(fail_present_loss[:15]) if fail_present_loss else "None flagged."))
    lines.append("- **Signals absent in winning trades:** " + (", ".join(fail_absent_win[:15]) if fail_absent_win else "None flagged."))
    lines.extend([
        "",
        "---",
        "",
        "---",
        "",
        "## Regime blind spots",
        "",
        "| Regime | Exit count |",
        "|--------|------------|",
    ])
    for r, cnt in sorted(regime_coverage.items(), key=lambda x: -x[1]):
        lines.append(f"| {r} | {cnt} |")
    if low_coverage_regimes:
        lines.append("")
        lines.append(f"**Low-coverage regimes:** {low_coverage_regimes}")
    lines.extend([
        "",
        "---",
        "",
        "## Intelligence gap taxonomy",
        "",
        "| Gap type | Description | Count |",
        "|----------|-------------|-------|",
        f"| DATA_GAP | Intel not collected | {len([c for c in COMPONENTS if comp_pct.get(c, 0) < 20])} components <20% coverage |",
        f"| SIGNAL_GAP | Feature exists but unused | See over-represented low-contrib |",
        f"| TAXONOMY_GAP | Signal too coarse | Manual review |",
        f"| REGIME_GAP | No regime-specific intel | {len(low_coverage_regimes)} regimes |",
        "",
        "---",
        "",
        "## Exit reason summary (bucketed)",
        "",
    ])
    for reason, cnt in sorted(exit_reason_counts.items(), key=lambda x: -x[1])[:15]:
        lines.append(f"- **{reason}**: {cnt}")
    lines.extend([
        "",
        "---",
        "",
        "## Evidence-based roadmap (NO-APPLY)",
        "",
        "### 1. Signals to REVIEW (low contribution / high redundancy)",
        "",
    ])
    for r in rec_review[:10]:
        lines.append(f"- **{r['signal']}**: {r['evidence']} | Confidence: {r['confidence']} | **STATUS: SHADOW — NOT APPLIED**")
    if not rec_review:
        lines.append("- None.")
    lines.extend([
        "",
        "### 2. Signals to DEEPEN (taxonomy or metadata expansion)",
        "",
    ])
    for r in rec_deepen[:10]:
        lines.append(f"- {r.get('signal', r.get('gap', '?'))}: {r.get('evidence', '')} | **STATUS: SHADOW — NOT APPLIED**")
    if not rec_deepen:
        lines.append("- None.")
    lines.extend([
        "",
        "### 3. Intelligence to ADD (new data sources justified by gaps)",
        "",
    ])
    for r in rec_add[:10]:
        lines.append(f"- **{r.get('gap', '?')}**: {r.get('evidence', '')} | Confidence: {r.get('confidence', 'low')} | **STATUS: SHADOW — NOT APPLIED**")
    if not rec_add:
        lines.append("- None.")
    lines.extend([
        "",
        "### 4. Signals to PROTECT (high contribution, low coverage risk)",
        "",
    ])
    for r in rec_protect[:10]:
        lines.append(f"- **{r['signal']}**: {r['evidence']} | Confidence: {r['confidence']} | **STATUS: SHADOW — NOT APPLIED**")
    if not rec_protect:
        lines.append("- None.")
    lines.extend([
        "",
        "---",
        "",
        "*Generated by scripts/signal_contribution_and_gaps_audit.py. Observability-only; no live behavior changes.*",
        "",
    ])

    out_path = reports_dir / f"STOCK_SIGNAL_CONTRIBUTION_AND_GAPS_{target_date}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Signal contribution & intelligence gap audit")
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
