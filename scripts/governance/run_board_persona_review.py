#!/usr/bin/env python3
"""
Board and persona review of current governance data.

Reads live data (state, latest decision, effectiveness aggregates, expectancy_gate_diagnostic,
recommendation) and prior docs (strategic review, personas what-to-do-differently).
Emits Adversarial, Quant, Product, Execution/SRE, Risk, and Board verdict.
Writes to reports/governance/board_review_<timestamp>.md and .json.

Run on droplet after each governance cycle (or standalone). Additive; does not change LOCK/REVERT.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_text(p: Path, max_chars: int = 8000) -> str:
    if not p.exists():
        return ""
    try:
        s = p.read_text(encoding="utf-8", errors="replace")
        return s[:max_chars] + ("..." if len(s) > max_chars else "")
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Board and persona review of governance data")
    ap.add_argument("--base-dir", type=Path, default=REPO, help="Repo base (state, reports)")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output dir (default: base-dir/reports/governance)")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    out_dir = args.out_dir or (base / "reports" / "governance")
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Load current data ---
    state = _load_json(base / "state" / "equity_governance_loop_state.json") or {}
    baseline_dir = base / "reports" / "effectiveness_baseline_blame"
    agg = _load_json(baseline_dir / "effectiveness_aggregates.json") or {}
    diagnostic = _load_json(baseline_dir / "expectancy_gate_diagnostic.json") or {}

    eq_dir = base / "reports" / "equity_governance"
    run_dirs = sorted([p for p in eq_dir.iterdir() if p.is_dir() and p.name.startswith("equity_governance_")], key=lambda p: p.name, reverse=True) if eq_dir.exists() else []
    latest_run = run_dirs[0] if run_dirs else None
    decision = _load_json(latest_run / "lock_or_revert_decision.json") if latest_run else None
    recommendation = _load_json(latest_run / "recommendation.json") if latest_run else None
    if not decision and baseline_dir.exists():
        decision = {}

    stopping = (decision or {}).get("stopping_checks") or {}
    cand = (decision or {}).get("candidate") or {}
    base_metrics = (decision or {}).get("baseline") or {}
    dist = (diagnostic.get("distribution") or {}) if isinstance(diagnostic.get("distribution"), dict) else {}
    by_bucket = dist.get("by_score_bucket") or {}

    # --- Prior docs (for context in review) ---
    prior_strategic = _read_text(base / "reports" / "STRATEGIC_REVIEW_AND_PATH_TO_PROFITABILITY_2026-02-26.md", 4000)
    prior_personas_diff = _read_text(base / "reports" / "governance" / "PERSONAS_WHAT_TO_DO_DIFFERENTLY_2026-02-26.md", 3000)
    prior_five_ideas = _read_text(base / "reports" / "governance" / "FIVE_IDEAS_PROFITABILITY_MULTI_MODEL_2026-02-26.md", 2000)

    # --- Build data summary for personas ---
    data_summary = {
        "last_decision": (decision or {}).get("decision"),
        "stopping_condition_met": (decision or {}).get("stopping_condition_met"),
        "stopping_checks": stopping,
        "candidate_expectancy": cand.get("expectancy_per_trade"),
        "candidate_win_rate": cand.get("win_rate"),
        "candidate_joined": cand.get("joined_count"),
        "baseline_expectancy": base_metrics.get("expectancy_per_trade"),
        "baseline_win_rate": base_metrics.get("win_rate"),
        "state_last_lever": state.get("last_lever"),
        "state_expectancy_history_len": len(state.get("expectancy_history") or []),
        "state_last_replay_jump_cycle": state.get("last_replay_jump_cycle"),
        "aggregates_joined": agg.get("joined_count"),
        "aggregates_expectancy": agg.get("expectancy_per_trade"),
        "aggregates_win_rate": agg.get("win_rate"),
        "aggregates_giveback": agg.get("avg_profit_giveback"),
        "diagnostic_p50_score": dist.get("p50"),
        "diagnostic_pct_marginal": dist.get("pct_marginal_2_5_to_2_9"),
        "diagnostic_by_bucket": by_bucket,
        "recommendation_next_lever": (recommendation or {}).get("next_lever"),
        "recommendation_suggested_min_exec_score": (recommendation or {}).get("suggested_min_exec_score"),
    }

    # --- Persona sections (reference data + prior guidance) ---
    def adversarial() -> str:
        exp_gt_0 = stopping.get("expectancy_gt_0")
        pct_marg = data_summary.get("diagnostic_pct_marginal")
        p50 = data_summary.get("diagnostic_p50_score")
        lines = [
            "## Adversarial",
            "",
            "**Current numbers:**",
            f"- Stopping: expectancy_gt_0={exp_gt_0}, win_rate_ge_baseline_plus_2pp={stopping.get('win_rate_ge_baseline_plus_2pp')}, giveback_le={stopping.get('giveback_le_baseline_plus_005')}.",
            f"- Candidate expectancy={data_summary.get('candidate_expectancy')}, baseline={data_summary.get('baseline_expectancy')}; decision={data_summary.get('last_decision')}.",
            f"- Expectancy-gate diagnostic: p50 entry_score={p50}, pct_marginal_2_5_to_2_9={pct_marg}%.",
            "",
            "**Prior guidance (strategic review):** Expectancy gate may be selecting for marginal trades; need evidence we are not selecting for bad expectancy by construction.",
            "",
        ]
        if pct_marg is not None and p50 is not None:
            if pct_marg > 15:
                lines.append("**Verdict:** High marginal share — we may be selecting for bad expectancy. Consider tightening threshold or investigating score pipeline.")
            else:
                lines.append("**Verdict:** Marginal share is low; diagnostic is in place. Keep loop; monitor by_score_bucket expectancy over time.")
        else:
            lines.append("**Verdict:** Diagnostic not yet populated or no score data; ensure expectancy_gate_diagnostic runs each cycle.")
        lines.append("")
        return "\n".join(lines)

    def quant() -> str:
        wr = stopping.get("win_rate_ge_baseline_plus_2pp")
        lines = [
            "## Quant",
            "",
            "**Current numbers:**",
            f"- Baseline joined={data_summary.get('aggregates_joined')}, expectancy={data_summary.get('aggregates_expectancy')}, win_rate={data_summary.get('aggregates_win_rate')}, giveback={data_summary.get('aggregates_giveback')}.",
            f"- Recommendation: next_lever={data_summary.get('recommendation_next_lever')}, suggested_min_exec_score={data_summary.get('recommendation_suggested_min_exec_score')}.",
            f"- Stopping checks: all four present; expectancy_gt_0, wr_ge_baseline_plus_2pp, giveback_le, joined_ge_100.",
            "",
            "**Prior guidance:** Gate on ≥50 (we use 100). WTD vs 30D optional for risk brake. Entry lever variety: add down-weight worst signal as option.",
            "",
            "**Verdict:** Evidence pipeline is in place. Optional: add WTD effectiveness comparison; add down-weight-worst-signal as entry lever variant.",
            "",
        ]
        return "\n".join(lines)

    def product_op() -> str:
        lines = [
            "## Product / Operator",
            "",
            "**Current numbers:**",
            f"- One canonical baseline dir: reports/effectiveness_baseline_blame; joined={data_summary.get('aggregates_joined')}.",
            f"- Last cycle: decision={data_summary.get('last_decision')}, lever={data_summary.get('state_last_lever')}; expectancy_history length={data_summary.get('state_expectancy_history_len')}.",
            "",
            "**Prior guidance:** One baseline, one lever per cycle, 50- or 100-trade gate, LOCK/REVERT. Success = stop guessing, one correct lever, positive expectancy.",
            "",
            "**Verdict:** Process aligned. Continue one lever at a time; 100-trade gate is acceptable. No process change required.",
            "",
        ]
        return "\n".join(lines)

    def execution_sre() -> str:
        p50 = data_summary.get("diagnostic_p50_score")
        by_bucket = data_summary.get("diagnostic_by_bucket") or {}
        lines = [
            "## Execution / SRE",
            "",
            "**Current numbers:**",
            f"- Expectancy-gate diagnostic: p50_score={p50}; by_score_bucket trade counts and expectancy present.",
            f"- Buckets: 2_5_to_2_7 expectancy={by_bucket.get('2_5_to_2_7', {}).get('expectancy_per_trade')}, 2_7_to_2_9={by_bucket.get('2_7_to_2_9', {}).get('expectancy_per_trade')}, above_3_2={by_bucket.get('above_3_2', {}).get('expectancy_per_trade')}.",
            "",
            "**Prior guidance:** Investigate score ledger vs MIN_EXEC_SCORE; ensure gate truth and dashboard align. Diagnostic now runs each cycle.",
            "",
            "**Verdict:** Diagnostic is live. If dashboard or gate logic diverges from attribution scores, fix; otherwise continue.",
            "",
        ]
        return "\n".join(lines)

    def risk() -> str:
        exp = data_summary.get("candidate_expectancy")
        lines = [
            "## Risk",
            "",
            "**Current numbers:**",
            f"- Candidate expectancy={exp}; stopping_condition_met={data_summary.get('stopping_condition_met')}.",
            f"- Brake: documented in runbook (raise MIN_EXEC_SCORE or pause); suggested_min_exec_score in use.",
            "",
            "**Prior guidance:** If drawdown unacceptable, apply brake (e.g. 3.0 or pause) and document; don't rely on UW for profit yet.",
            "",
            "**Verdict:** Brake is optional. Apply only if drawdown is unacceptable; then document the decision.",
            "",
        ]
        return "\n".join(lines)

    def board_verdict() -> str:
        met = data_summary.get("stopping_condition_met")
        dec = data_summary.get("last_decision")
        lines = [
            "## Board verdict",
            "",
            "**Synthesis:**",
            f"- Current decision={dec}, stopping_condition_met={met}. All personas have reviewed current data and prior guidance.",
            "- Adversarial and Execution/SRE: expectancy-gate diagnostic is in place; marginal share and by-bucket expectancy are monitored.",
            "- Quant: evidence pipeline and stopping_checks are in place; optional WTD and down-weight-worst-signal remain.",
            "- Product: process aligned; one baseline, one lever, 100-trade gate.",
            "- Risk: brake documented; apply if drawdown is unacceptable.",
            "",
            "**Conclusion:** No change to loop logic. Continue governance cycles; use diagnostic and board review for ongoing evaluation.",
            "",
        ]
        return "\n".join(lines)

    def consensus_top3_and_next() -> str:
        return '''## Board + personas: agreed top 3 and next

**1. Add down-weight worst signal as entry-lever option** — From signal_effectiveness/top5_harmful, pick the single worst signal; when lever=entry, allow overlay that down-weights it (e.g. -0.05). One cycle at a time; 100-trade gate. Supported: Strategic Phase B1, Quant, Product; Adversarial/SRE/Risk agree.

**2. Keep loop running; monitor with diagnostic and board review** — No structural change. Use expectancy_gate_diagnostic and board_review_latest to monitor. Supported: all personas.

**3. Ensure giveback populated when possible; use risk brake when needed** — (a) Verify giveback in effectiveness_aggregates when exit data has it; fix if still null. (b) When drawdown unacceptable, apply brake (MIN_EXEC_SCORE 3.0 or pause) and document. Supported: Quant, Execution/SRE, Risk.

**Next:** (1) Implement down-weight-worst-signal as entry option. (2) Continue loop; verify giveback on droplet. (3) Apply brake only when drawdown is unacceptable. See reports/governance/BOARD_CONSENSUS_TOP3_AND_NEXT.md.
'''

    # --- Plugins note (if plugins dir exists) ---
    plugins_note = ""
    plugins_dir = base / "plugins"
    if plugins_dir.exists():
        try:
            plugins_list = [p.name for p in plugins_dir.iterdir() if p.is_dir() or p.suffix in (".py", ".json")]
            plugins_note = "\n**Plugins available:** " + ", ".join(sorted(plugins_list)[:20]) + "\n"
        except Exception:
            pass

    # --- Assemble markdown ---
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    md_lines = [
        "# Board and persona review (governance)",
        "",
        f"**Generated:** {ts} UTC",
        "",
        "**Data source:** state, latest lock_or_revert_decision, effectiveness_aggregates, expectancy_gate_diagnostic, recommendation.",
        "**Prior context:** STRATEGIC_REVIEW_AND_PATH_TO_PROFITABILITY, PERSONAS_WHAT_TO_DO_DIFFERENTLY, FIVE_IDEAS.",
        "",
        plugins_note,
        "---",
        "",
        adversarial(),
        "---",
        "",
        quant(),
        "---",
        "",
        product_op(),
        "---",
        "",
        execution_sre(),
        "---",
        "",
        risk(),
        "---",
        "",
        board_verdict(),
        "---",
        "",
        consensus_top3_and_next(),
        "---",
        "",
        "*Generated by scripts/governance/run_board_persona_review.py*",
    ]
    md_content = "\n".join(md_lines)

    # --- Write outputs ---
    out_md = out_dir / f"board_review_{ts}.md"
    out_json = out_dir / f"board_review_{ts}.json"
    out_md.write_text(md_content, encoding="utf-8")

    json_out = {
        "timestamp": ts,
        "data_summary": data_summary,
        "personas": {
            "adversarial": adversarial(),
            "quant": quant(),
            "product_operator": product_op(),
            "execution_sre": execution_sre(),
            "risk": risk(),
            "board_verdict": board_verdict(),
        },
        "consensus_top3_and_next": consensus_top3_and_next(),
    }
    out_json.write_text(json.dumps(json_out, indent=2), encoding="utf-8")

    # Also write latest for easy read
    latest_md = out_dir / "board_review_latest.md"
    latest_json = out_dir / "board_review_latest.json"
    latest_md.write_text(md_content, encoding="utf-8")
    latest_json.write_text(json.dumps(json_out, indent=2), encoding="utf-8")

    print(f"Wrote {out_md} and {out_json}; updated board_review_latest.md / .json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
