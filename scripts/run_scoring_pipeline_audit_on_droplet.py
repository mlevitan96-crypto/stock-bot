#!/usr/bin/env python3
"""
Scoring pipeline trade-blocker audit. RUN ON THE DROPLET.
Uses real droplet data: decision_ledger, expectancy_gate_truth, uw_flow_cache, logs.
Produces: SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md (and runs full_signal_review + signal_audit_diagnostic).
Assumption: something is broken; find all signals per trade, which fire, which are tied to engine, and whether we can trade.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "reports" / "signal_review"
AUDIT_MD = OUT_DIR / "SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md"
FUNNEL_JSON = OUT_DIR / "signal_funnel.json"
DIAGNOSTIC_JSON = OUT_DIR / "signal_audit_diagnostic_droplet.json"
BREAKDOWN_JSONL = REPO / "logs" / "signal_score_breakdown.jsonl"
DEFAULT_DAYS = 7


def get_min_exec_score() -> float:
    try:
        from config.registry import Thresholds
        return float(getattr(Thresholds, "MIN_EXEC_SCORE", 2.5))
    except Exception:
        return 2.5


def run_full_signal_review(days: int) -> bool:
    rc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "full_signal_review_on_droplet.py"), "--days", str(days)],
        cwd=str(REPO), capture_output=True, text=True, timeout=300,
    )
    if rc.returncode != 0 and rc.stderr:
        print(rc.stderr[:2000], file=sys.stderr)
    return rc.returncode == 0


def run_signal_audit_diagnostic() -> dict | None:
    rc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "signal_audit_diagnostic.py")],
        cwd=str(REPO), capture_output=True, text=True, timeout=120,
    )
    raw = (rc.stdout or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "diagnostic output was not valid JSON", "raw_preview": raw[:500]}


def run_breakdown_summary() -> bool:
    if not BREAKDOWN_JSONL.exists():
        return False
    n_lines = sum(1 for _ in BREAKDOWN_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines() if _.strip())
    if n_lines < 10:
        return False
    rc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "signal_score_breakdown_summary_on_droplet.py")],
        cwd=str(REPO), capture_output=True, timeout=90,
    )
    return rc.returncode == 0


def build_audit_md(
    min_exec_score: float,
    funnel: dict | None,
    diagnostic: dict | None,
    breakdown_available: bool,
    days: int,
) -> str:
    lines = [
        "# Scoring pipeline trade-blocker audit",
        "",
        f"**Generated (droplet):** {datetime.now(timezone.utc).isoformat()}",
        f"**Window:** last {days} days. **MIN_EXEC_SCORE (config):** {min_exec_score}",
        "",
        "---",
        "",
        "## 1. Executive summary",
        "",
    ]

    # Dominant choke and verdict
    if funnel:
        dom = funnel.get("dominant_choke_point") or {}
        stage = dom.get("stage", "unknown")
        reason = dom.get("reason", "unknown")
        pct = dom.get("pct", 0)
        total = funnel.get("total_candidates", 0)
        exp = funnel.get("expectancy_distributions") or {}
        post_median = (exp.get("post_adjust") or {}).get("p50")
        pct_above = exp.get("pct_above_min_exec_post")
        lines.extend([
            f"- **Dominant choke point:** {stage} — {reason} ({dom.get('count', 0)} / {total} = {pct}%).",
            f"- **Score distribution (post-adjust):** median = {post_median}; % above MIN_EXEC_SCORE = {pct_above}%.",
            "",
        ])
        if stage == "5_expectancy_gate" and (pct_above or 0) == 0:
            lines.append("**Verdict:** Trades are **not** occurring because **every candidate fails the expectancy gate** (composite score below MIN_EXEC_SCORE). The pipeline is blocking correctly; the issue is **scores are too low**, not a gate bug.")
        elif total == 0:
            lines.append("**Verdict:** No candidates in window. Check: decision_ledger capture, UW cache, universe.")
        else:
            lines.append("**Verdict:** See dominant choke and score distribution above; check whether score level or later gates (capacity, theme, etc.) are blocking.")
        lines.append("")
    else:
        lines.append("No funnel data (full_signal_review did not produce signal_funnel.json or no ledger events).")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 2. All signals in the pipeline (tied to trade engine)",
        "",
        "Every signal below is **wired** into the trade engine:",
        "- **Path:** `main.py` → load `data/uw_flow_cache.json` → `uw_enrichment_v2.enrich_signal()` → `uw_composite_v2.compute_composite_score_v2()` → clusters with `source=composite_v3` → `decide_and_execute()` → expectancy gate (composite_exec_score vs MIN_EXEC_SCORE) → `submit_entry()`.",
        "- **Composite formula:** sum of component contributions × freshness; clamp 0–8. Entry requires score ≥ MIN_EXEC_SCORE and passing `should_enter_v2` (threshold, freshness ≥ 0.30, toxicity < 0.90).",
        "",
    ])

    if diagnostic:
        inv = diagnostic.get("signal_inventory") or []
        dead = diagnostic.get("dead_or_muted") or []
        value_audit = diagnostic.get("value_audit") or {}
        comp_dist = diagnostic.get("composite_distribution") or {}
        lines.append("### 2.1 Signal inventory (from uw_composite_v2)")
        lines.append("")
        lines.append("| signal_name | weight | status | pct_zero | mean_contribution |")
        lines.append("|-------------|--------|--------|----------|-------------------|")
        for s in inv:
            name = s.get("name", "")
            w = s.get("weight", "")
            va = value_audit.get(name, {})
            pct_zero = va.get("pct_zero")
            mean_c = va.get("mean")
            status = "DEAD/MUTED" if any(d.get("signal_name") == name for d in dead) else "OK"
            lines.append(f"| {name} | {w} | {status} | {pct_zero}% | {mean_c} |")
        lines.append("")
        lines.append("### 2.2 Dead or muted signals (not contributing)")
        if dead:
            for d in dead:
                lines.append(f"- **{d.get('signal_name')}**: {d.get('failure_mode')} — {d.get('suspected_root_cause')} (confidence: {d.get('confidence')})")
        else:
            lines.append("(None identified by diagnostic.)")
        lines.append("")
        lines.append("### 2.3 Composite score distribution (diagnostic sample)")
        if comp_dist:
            lines.append(f"- min={comp_dist.get('min')}, max={comp_dist.get('max')}, mean={comp_dist.get('mean')}, count={comp_dist.get('count')}")
            lines.append(f"- pct_below_2={comp_dist.get('pct_below_2')}%, pct_below_3={comp_dist.get('pct_below_3')}%")
        if diagnostic.get("error"):
            lines.append(f"- **Error:** {diagnostic['error']}")
        lines.append("")
    else:
        lines.append("(Signal audit diagnostic did not run or produced no JSON. Check `data/uw_flow_cache.json` and script.)")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Per-trade flow: signals firing and reaching execution",
        "",
        "For each candidate that reaches `decide_and_execute`:",
        "1. **Cluster** has `composite_score` and `source=composite_v3`.",
        "2. **Adjustments** (signal_quality, UW, survivorship) may reduce score → `composite_exec_score`.",
        "3. **Expectancy gate** compares `composite_exec_score` to MIN_EXEC_SCORE; if below → block (score_floor_breach).",
        "4. **Later gates:** regime, concentration, theme, momentum, cooldown, position exists, trade_guard.",
        "5. **submit_entry** → Alpaca only if all pass.",
        "",
        "If **no trades**: the dominant blocker in section 1 is where the pipeline stops (almost always expectancy_gate:score_floor_breach when scores are low).",
        "",
        "---",
        "",
        "## 4. Can we make trades?",
        "",
    ])

    if funnel:
        s7 = funnel.get("stages", {}).get("7_order_placement_outcomes", {})
        reasons = s7.get("top_reasons") or []
        fills = 0
        for r in reasons:
            if isinstance(r, (list, tuple)) and len(r) >= 2 and r[0] == "filled":
                fills = int(r[1])
                break
        pct_above = (funnel.get("expectancy_distributions") or {}).get("pct_above_min_exec_post")
        dom = funnel.get("dominant_choke_point") or {}
        stage = dom.get("stage", "")
        # Current pipeline is blocked if expectancy is dominant choke and no candidates above MIN_EXEC_SCORE
        currently_blocked = (stage == "5_expectancy_gate" and (pct_above or 0) == 0)
        if currently_blocked:
            lines.append("**No (current run).** In this window, composite scores are below MIN_EXEC_SCORE for **all** candidates, so the expectancy gate blocks every one. No new orders would reach Alpaca from the current scoring pipeline.")
            lines.append("")
            lines.append("(Any fills in the window are from earlier runs; the current signal/score state does not allow new trades.)")
            lines.append("")
            lines.append("**Root cause (score level):** Likely combination of: (1) missing or zero flow/conviction/dark_pool/insider in UW cache, (2) many components defaulting to 0 or neutral when data missing, (3) freshness decay, (4) adjustment chain reducing score. Fix: ensure UW cache is populated and fresh; verify conviction/sentiment present; consider neutral defaults for missing components (see MEMORY_BANK §7).")
        elif fills > 0 and (pct_above or 0) > 0:
            lines.append(f"**Yes.** Some candidates are above MIN_EXEC_SCORE and some orders reached Alpaca ({fills} fills in window). Pipeline is not fully blocked.")
        else:
            lines.append("Scores may be above MIN_EXEC_SCORE for some candidates but a later gate (capacity, theme, trade_guard, etc.) is blocking. See dominant choke point and stage 6 reasons in signal_funnel.json.")
    else:
        lines.append("Cannot conclude without funnel data. Run full_signal_review_on_droplet.py and ensure decision_ledger has events.")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Droplet commands (re-run audit)",
        "",
        "```bash",
        "cd /root/stock-bot",
        "python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days 7",
        "```",
        "",
        "To enable per-candidate signal breakdown (optional):",
        "```bash",
        "export SIGNAL_SCORE_BREAKDOWN_LOG=1",
        "# run main.py / paper until logs/signal_score_breakdown.jsonl has 100+ lines",
        "python3 scripts/signal_score_breakdown_summary_on_droplet.py",
        "python3 scripts/signal_pipeline_deep_dive_on_droplet.py",
        "```",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Scoring pipeline trade-blocker audit (run on droplet)")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Window days for funnel")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    min_exec = get_min_exec_score()
    print(f"MIN_EXEC_SCORE (config): {min_exec}")

    # Full signal review (funnel, traces, adversarial)
    print("Running full_signal_review_on_droplet.py ...")
    run_full_signal_review(args.days)
    funnel = None
    if FUNNEL_JSON.exists():
        try:
            funnel = json.loads(FUNNEL_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Signal audit diagnostic (droplet cache → component values)
    print("Running signal_audit_diagnostic.py ...")
    diagnostic = run_signal_audit_diagnostic()
    if diagnostic:
        DIAGNOSTIC_JSON.write_text(json.dumps(diagnostic, indent=2, default=str), encoding="utf-8")
        print(f"Wrote {DIAGNOSTIC_JSON}")

    # Optional: breakdown summary if log exists
    breakdown_ok = run_breakdown_summary()

    audit_md = build_audit_md(min_exec, funnel, diagnostic, breakdown_ok, args.days)
    AUDIT_MD.write_text(audit_md, encoding="utf-8")
    print(f"Wrote {AUDIT_MD}")

    # Terminal summary
    if funnel:
        dom = funnel.get("dominant_choke_point") or {}
        print(f"Dominant choke: {dom.get('stage')} — {dom.get('reason')} ({dom.get('pct')}%)")
    if diagnostic and diagnostic.get("composite_distribution"):
        print(f"Diagnostic composite mean: {diagnostic['composite_distribution'].get('mean')}")
    print("--- SCORING_PIPELINE_AUDIT DONE ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
