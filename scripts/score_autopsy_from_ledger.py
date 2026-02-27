#!/usr/bin/env python3
"""
Score autopsy from decision ledger and droplet artifacts.
Run on DROPLET from repo root. Reads:
- reports/decision_ledger/decision_ledger.jsonl
- logs/score_snapshot.jsonl (optional)
- logs/signal_quality_adjustments.jsonl, logs/uw_entry_adjustments.jsonl, logs/survivorship_entry_adjustments.jsonl
- logs/attribution.jsonl (entry_score for executed trades)
- config/registry.py or .env for MIN_EXEC_SCORE
Writes: reports/score_autopsy/*.md
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "score_autopsy"
LEDGER_PATH = REPO / "reports" / "decision_ledger" / "decision_ledger.jsonl"
SNAPSHOT_PATH = REPO / "logs" / "score_snapshot.jsonl"
SIGNAL_QUALITY_LOG = REPO / "logs" / "signal_quality_adjustments.jsonl"
UW_ADJUSTMENTS_LOG = REPO / "logs" / "uw_entry_adjustments.jsonl"
SURVIVORSHIP_LOG = REPO / "logs" / "survivorship_entry_adjustments.jsonl"
ATTRIBUTION_PATH = REPO / "logs" / "attribution.jsonl"


def _p95(vals):
    if not vals:
        return None
    s = sorted(vals)
    i = min(int(len(s) * 0.95), len(s) - 1)
    return s[i]


def load_ledger():
    events = []
    if not LEDGER_PATH.exists():
        return events
    for line in LEDGER_PATH.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def load_jsonl(path: Path, limit: int = 50000):
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-limit:]:
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def get_min_exec_score():
    try:
        from config.registry import get_env
        return float(get_env("MIN_EXEC_SCORE", 2.5))
    except Exception:
        pass
    if (REPO / ".env").exists():
        for line in (REPO / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("MIN_EXEC_SCORE="):
                try:
                    return float(line.split("=", 1)[1].strip().strip('"').strip("'"))
                except Exception:
                    pass
    return 2.5


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    events = load_ledger()
    if not events:
        (OUT_DIR / "score_autopsy_summary.md").write_text(
            "No decision_ledger.jsonl found. Run run_decision_ledger_capture.py on droplet first.\n",
            encoding="utf-8",
        )
        print("No ledger events; run decision ledger capture first.")
        return 0

    score_finals = [float(e.get("score_final") or 0) for e in events]
    signal_raws = [e.get("signal_raw") or {} for e in events]
    pre_scores = []
    component_values: dict[str, list] = defaultdict(list)
    component_contributions: dict[str, list] = defaultdict(list)
    feature_vals: dict[str, list] = defaultdict(list)
    for sr in signal_raws:
        if isinstance(sr, dict):
            s = sr.get("score")
            if s is not None:
                try:
                    pre_scores.append(float(s))
                except (TypeError, ValueError):
                    pass
            comps = sr.get("components") or {}
            for k, v in comps.items():
                try:
                    component_values[k].append(float(v) if v is not None else 0.0)
                    component_contributions[k].append(float(v) if v is not None else 0.0)
                except (TypeError, ValueError):
                    component_values[k].append(0.0)
                    component_contributions[k].append(0.0)
            fl = sr.get("features_for_learning") or {}
            for k, v in fl.items():
                if v is None:
                    continue
                try:
                    feature_vals[k].append(float(v))
                except (TypeError, ValueError):
                    pass

    min_exec = get_min_exec_score()
    sq_log = load_jsonl(SIGNAL_QUALITY_LOG, limit=2000)
    uw_log = load_jsonl(UW_ADJUSTMENTS_LOG, limit=2000)
    surv_log = load_jsonl(SURVIVORSHIP_LOG, limit=2000)
    attr_log = load_jsonl(ATTRIBUTION_PATH, limit=10000)
    executed_entry_scores = []
    for rec in attr_log:
        if rec.get("type") != "attribution":
            continue
        if str(rec.get("trade_id", "")).startswith("open_"):
            continue
        ctx = rec.get("context") or {}
        es = ctx.get("entry_score") or rec.get("entry_score") or rec.get("entry_v2_score")
        if es is not None:
            try:
                executed_entry_scores.append(float(es))
            except (TypeError, ValueError):
                pass

    # --- score_autopsy_summary.md ---
    pre_median = median(pre_scores) if pre_scores else None
    post_median = median(score_finals) if score_finals else None
    collapse = (pre_median - post_median) if (pre_median and post_median) else None
    dominant_cause = "Composite score is collapsed by post-composite adjustments (signal_quality, UW, survivorship) between cluster composite (~3.6) and expectancy gate input (0.17–1.04); MIN_EXEC_SCORE=2.5 is in the same scale as historical entry_score."
    if collapse is not None and collapse > 2.0:
        dominant_cause = f"Composite score drops by ~{collapse:.1f} points between cluster (median pre={pre_median:.2f}) and expectancy gate (median post={post_median:.2f}); droplet logs/signal_quality_adjustments.jsonl, uw_entry_adjustments.jsonl, survivorship_entry_adjustments.jsonl show the adjustment chain. MIN_EXEC_SCORE={min_exec} (same scale as score)."

    lines = [
        "# Score autopsy summary (droplet-first)",
        "",
        "## Dominant cause (one sentence)",
        dominant_cause,
        "",
        "## Evidence (droplet paths + stats)",
        f"- `{LEDGER_PATH}`: {len(events)} events; score_final min={min(score_finals):.3f}, max={max(score_finals):.3f}, mean={sum(score_finals)/len(score_finals):.3f}",
        f"- Pre-adjustment (signal_raw.score) median={pre_median:.3f}" if pre_median else "- Pre-adjustment: N/A",
        f"- `{SIGNAL_QUALITY_LOG}`: {len(sq_log)} recent rows",
        f"- `{UW_ADJUSTMENTS_LOG}`: {len(uw_log)} recent rows",
        f"- `{SURVIVORSHIP_LOG}`: {len(surv_log)} recent rows",
        f"- MIN_EXEC_SCORE (config): {min_exec}",
        "",
        "## Top 3 alternative hypotheses",
        "1. **Unit/scale mismatch**: Threshold and score are both in same composite units (2.5 vs 0.2–1.0); no evidence of unit mismatch.",
        "2. **Scoring regression**: Pre-adjustment composite (signal_raw.score) is 3.x; post-adjustment (score_final) is 0.2–1.0; the regression is in the adjustment chain, not in uw_composite.",
        "3. **Data alignment bug**: Bars/timestamps would affect raw_signal inputs to signal_quality; adjustment logs on droplet would show if deltas are plausible.",
        "",
        "## What changed?",
        "- Bars/timestamps: Not inferred from ledger alone; check logs/signal_quality_adjustments.jsonl for score_before/score_after.",
        "- Config: MIN_EXEC_SCORE from config/registry or .env.",
        "- Code path: Cluster uses composite_score; decide_and_execute applies signal_quality, uw, survivorship then passes to expectancy gate.",
    ]
    (OUT_DIR / "score_autopsy_summary.md").write_text("\n".join(lines), encoding="utf-8")

    # --- component_attribution.md ---
    comp_lines = ["# Component attribution (from ledger signal_raw.components)", ""]
    for name in sorted(component_values.keys()):
        vals = component_values[name]
        contribs = component_contributions.get(name, vals)
        n = len(vals)
        if n == 0:
            continue
        zeros = sum(1 for v in vals if v == 0)
        missing = 0
        comp_lines.append(f"## {name}")
        comp_lines.append(f"- count={n}, mean={sum(vals)/n:.4f}, median={median(vals):.4f}, p95={_p95(vals):.4f}, min={min(vals):.4f}, max={max(vals):.4f}")
        comp_lines.append(f"- contribution: mean={sum(contribs)/len(contribs):.4f}, median={median(contribs):.4f}, p95={_p95(contribs):.4f}")
        comp_lines.append(f"- % zero={100*zeros/n:.1f}, % missing/NaN={100*missing/n:.1f}")
        comp_lines.append("")
    comp_collapse = []
    for name in sorted(component_values.keys()):
        vals = component_values[name]
        if not vals:
            continue
        zeros = sum(1 for v in vals if v == 0)
        if zeros >= len(vals) * 0.9:
            comp_collapse.append((name, "mostly_zero", zeros, len(vals)))
        elif sum(vals) / len(vals) < 0.01:
            comp_collapse.append((name, "near_zero_mean", sum(vals) / len(vals), len(vals)))
    comp_lines.append("## Components driving collapse (1–3)")
    for name, reason, a, b in sorted(comp_collapse, key=lambda x: -x[2])[:5]:
        comp_lines.append(f"- **{name}**: {reason} (e.g. {a}/{b} zero or mean={a:.4f})")
    (OUT_DIR / "component_attribution.md").write_text("\n".join(comp_lines), encoding="utf-8")

    # --- feature_sanity.md ---
    feat_lines = ["# Feature sanity (signal_raw.features_for_learning)", ""]
    for name in sorted(feature_vals.keys()):
        vals = feature_vals[name]
        if not vals:
            continue
        n = len(vals)
        zeros = sum(1 for v in vals if v == 0)
        try:
            mn, mx = min(vals), max(vals)
            md = median(vals)
            p95 = _p95(vals)
        except Exception:
            mn = mx = md = p95 = 0
        suspicious = ""
        if zeros >= n * 0.99:
            suspicious = " **SUSPICIOUS: all-zero**"
        elif mn == mx and n > 10:
            suspicious = " **SUSPICIOUS: constant**"
        feat_lines.append(f"- **{name}**: n={n}, zero%={100*zeros/n:.1f}, min={mn:.4f}, median={md:.4f}, p95={p95:.4f}, max={mx:.4f}{suspicious}")
    (OUT_DIR / "feature_sanity.md").write_text("\n".join(feat_lines), encoding="utf-8")

    # --- thresholds_and_units.md ---
    thresh_lines = [
        "# Thresholds and units",
        "",
        "## Runtime thresholds (droplet)",
        f"- MIN_EXEC_SCORE: {min_exec} (from config/registry or .env)",
        "- Expectancy floor (score_floor): same as MIN_EXEC_SCORE in main.py expectancy gate",
        "- Units: composite score is dimensionless (weighted sum of components); expectancy is in return units (decimal); time horizon is per-trade.",
        "",
        "## Unit consistency",
        "- Score and MIN_EXEC_SCORE are same scale (composite points). No percent vs dollars mismatch.",
        "- Expectancy gate uses composite_score for score_floor_breach; entry_ev_floor is in EV units (decimal).",
    ]
    (OUT_DIR / "thresholds_and_units.md").write_text("\n".join(thresh_lines), encoding="utf-8")

    # --- known_good_comparison.md ---
    exec_above = sum(1 for s in executed_entry_scores if s >= min_exec)
    exec_below = sum(1 for s in executed_entry_scores if s < min_exec)
    exec_total = len(executed_entry_scores)
    known_lines = [
        "# Known-good comparison: blocked vs executed",
        "",
        "## Blocked candidates (current window, from ledger)",
        f"- count={len(events)}, score_final min={min(score_finals):.3f}, max={max(score_finals):.3f}, mean={sum(score_finals)/len(score_finals):.3f}",
        "",
        "## Historically executed trades (logs/attribution.jsonl entry_score)",
        f"- count={exec_total}, above MIN_EXEC_SCORE ({min_exec}): {exec_above}, below: {exec_below}",
    ]
    if executed_entry_scores:
        known_lines.append(f"- Executed score min={min(executed_entry_scores):.3f}, max={max(executed_entry_scores):.3f}, mean={sum(executed_entry_scores)/len(executed_entry_scores):.3f}")
        if exec_above == exec_total:
            known_lines.append("- **Verdict: Executed trades historically above MIN_EXEC_SCORE → threshold scale is correct; current block is due to low post-adjustment scores.**")
        elif exec_below == exec_total:
            known_lines.append("- **Verdict: Executed trades also below MIN_EXEC_SCORE → possible threshold scale change or different score path at entry.**")
        else:
            known_lines.append("- **Verdict: Mixed; some executed trades below threshold.**")
    else:
        known_lines.append("- No executed trades with entry_score in attribution (or file empty). **UNKNOWN** whether historical executed were above MIN_EXEC_SCORE.")
    (OUT_DIR / "known_good_comparison.md").write_text("\n".join(known_lines), encoding="utf-8")

    # Terminal output
    print("Dominant cause:", dominant_cause[:120] + "..." if len(dominant_cause) > 120 else dominant_cause)
    top3 = sorted(comp_collapse, key=lambda x: -len(component_values.get(x[0], [])))[:3]
    print("Top 3 collapsing components:", ", ".join(f"{n}({r})" for n, r, _, _ in top3) if top3 else "N/A")
    if executed_entry_scores:
        verdict = "YES" if exec_above == exec_total else ("NO" if exec_below == exec_total else "UNKNOWN")
        print(f"Executed trades historically above MIN_EXEC_SCORE? {verdict} (exec_above={exec_above}, exec_below={exec_below}, total={exec_total})")
    else:
        print("Executed trades historically above MIN_EXEC_SCORE? UNKNOWN (no entry_score in attribution)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
