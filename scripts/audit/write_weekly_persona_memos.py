#!/usr/bin/env python3
"""
Write weekly persona memos (CSA, SRE, Risk, Execution, Research, Innovation, Owner).
Reads from weekly ledger summary, CSA verdict/findings, board/shadow. Outputs to
reports/board/WEEKLY_REVIEW_<date>_<PERSONA>.md.

Usage:
  python scripts/audit/write_weekly_persona_memos.py [--date YYYY-MM-DD] [--base-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _load_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_text(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(description="Write weekly persona memos")
    ap.add_argument("--date", default=None, help="Date YYYY-MM-DD")
    ap.add_argument("--base-dir", default=None, help="Repo root")
    args = ap.parse_args()
    base = Path(args.base_dir).resolve() if args.base_dir else REPO
    from datetime import datetime, timezone
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit_dir = base / "reports" / "audit"
    board_dir = base / "reports" / "board"
    board_dir.mkdir(parents=True, exist_ok=True)

    mission_id = f"CSA_WEEKLY_REVIEW_{date_str}"
    ledger = _load_json(audit_dir / f"WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_{date_str}.json") or {}
    verdict = _load_json(audit_dir / f"CSA_VERDICT_{mission_id}.json") or {}
    findings_md = _load_text(audit_dir / f"CSA_FINDINGS_{mission_id}.md")
    board_review = _load_json(base / "reports" / "board" / "last387_comprehensive_review.json") or {}
    shadow = _load_json(base / "reports" / "board" / "SHADOW_COMPARISON_LAST387.json") or {}
    sre = _load_json(audit_dir / "SRE_STATUS.json") or {}
    gov = _load_json(audit_dir / "GOVERNANCE_AUTOMATION_STATUS.json") or {}

    def w(path: Path, lines: list[str]) -> None:
        path.write_text("\n".join(lines), encoding="utf-8")

    # --- CSA ---
    w(board_dir / f"WEEKLY_REVIEW_{date_str}_CSA.md", [
        "# Weekly Review — CSA (Chief Strategy Auditor)",
        f"**Date:** {date_str}",
        "",
        "## 3 strongest findings",
        "1. Ledger evidence: executed " + str(ledger.get("executed_count", "—")) + ", blocked " + str(ledger.get("blocked_count", "—")) + ", CI blocked " + str(ledger.get("counter_intel_blocked_count", "—")) + " (7d window).",
        "2. CSA verdict: " + str(verdict.get("verdict", "—")) + " (" + str(verdict.get("confidence", "—")) + "). Recommendation: " + str(verdict.get("recommendation", "—"))[:80] + ".",
        "3. Missing data and counterfactuals drive HOLD until closed; shadow/board alignment required for any promotion.",
        "",
        "## 3 biggest risks",
        "1. Promoting without shadow comparison or cohort stability (7d vs 14d/30d).",
        "2. Blocked/CI counts not tied to opportunity-cost measurement (shadow would have profited).",
        "3. Validation failure rate (" + str(ledger.get("validation_failure_rate_pct", "—")) + "%) may indicate overly strict gates or missing instrumentation.",
        "",
        "## 3 recommended actions (ranked)",
        "1. Do not promote in this mission; use weekly packet to prioritize next experiments.",
        "2. Instrument blocked opportunity cost (blocked-when-shadow-profitable) in next ledger build.",
        "3. Re-run CSA after required_next_experiments are completed and ledger includes 14d/30d sanity checks.",
        "",
        "## What evidence would change my mind?",
        "Shadow comparison showing clear advance candidate with stable 7d/14d/30d metrics; closed missing_data items; and governance/SRE green.",
        "",
    ])

    # --- SRE / Operations ---
    w(board_dir / f"WEEKLY_REVIEW_{date_str}_SRE_Operations.md", [
        "# Weekly Review — SRE / Operations",
        f"**Date:** {date_str}",
        "",
        "## 3 strongest findings",
        "1. SRE overall_status: " + str(sre.get("overall_status", "—")) + "; event_count: " + str(sre.get("event_count", "—")) + ".",
        "2. Governance status: " + str(gov.get("status", "—")) + "; timestamp: " + str(gov.get("timestamp", "—"))[:30] + ".",
        "3. Weekly evidence manifest confirms which artifacts were pulled from droplet; any critical_missing would have blocked the audit.",
        "",
        "## 3 biggest risks",
        "1. Stale board/shadow artifacts (older than 7d) leading to wrong conclusions.",
        "2. Cron or governance loop failures not detected in time.",
        "3. Dashboard or profitability cockpit not showing weekly section after deploy.",
        "",
        "## 3 recommended actions (ranked)",
        "1. Verify dashboard shows Weekly Review section post-deploy; fix route if missing.",
        "2. Ensure SRE_EVENTS.jsonl and GOVERNANCE_AUTOMATION_STATUS.json are fresh; investigate anomalies.",
        "3. Document runbook for weekly evidence collection (collect_weekly_droplet_evidence.py) and ledger build.",
        "",
        "## What evidence would change my mind?",
        "Fresh SRE_STATUS with no anomalies; governance green; and successful deploy verification showing weekly section on cockpit.",
        "",
    ])

    # --- Risk Officer ---
    w(board_dir / f"WEEKLY_REVIEW_{date_str}_Risk_Officer.md", [
        "# Weekly Review — Risk Officer",
        f"**Date:** {date_str}",
        "",
        "## 3 strongest findings",
        "1. Executed count " + str(ledger.get("executed_count", "—")) + " in 7d; blocked " + str(ledger.get("blocked_count", "—")) + " — concentration and max_positions pressure inferred from board review.",
        "2. Board review blocked_trade_distribution and counter_intelligence (if present) inform downside of current gating.",
        "3. No real-money exposure; paper/live paper only — tail risk is operational and reputational.",
        "",
        "## 3 biggest risks",
        "1. Regime shift (vol spike, drawdown) without regime-specific sizing or pause.",
        "2. Concentration in single name or sector if universe narrows.",
        "3. Displacement blocks masking opportunity cost; unknown correlation of blocked vs. would-be losers.",
        "",
        "## 3 recommended actions (ranked)",
        "1. Add regime tag to ledger events where available; report concentration by symbol/sector in summary.",
        "2. Require risk sign-off before B2 live paper or real money; document max drawdown and position limits.",
        "3. Track tail scenarios (e.g. 2σ move) in backtest or shadow before enabling larger size.",
        "",
        "## What evidence would change my mind?",
        "Concentration and regime metrics in the ledger; explicit max_positions and displacement block counts; and a risk checklist for real-money readiness.",
        "",
    ])

    # --- Execution Microstructure ---
    w(board_dir / f"WEEKLY_REVIEW_{date_str}_Execution_Microstructure.md", [
        "# Weekly Review — Execution Microstructure",
        f"**Date:** {date_str}",
        "",
        "## 3 strongest findings",
        "1. Validation failed count: " + str(ledger.get("validation_failed_count", "—")) + "; rate " + str(ledger.get("validation_failure_rate_pct", "—")) + "%.",
        "2. Top blocked reasons (if any) may include order_validation_failed or size constraints — see ledger summary.",
        "3. No fill/slippage proxy in ledger yet; execution quality inferred from exit_attribution hold_time and PnL.",
        "",
        "## 3 biggest risks",
        "1. Overly strict order validation causing unnecessary blocks.",
        "2. Timing/latency not instrumented; possible late entries or early exits.",
        "3. No explicit fill quality or spread proxy in decision ledger.",
        "",
        "## 3 recommended actions (ranked)",
        "1. Log validation failure reason codes (size, margin, symbol, etc.) as structured fields for aggregation.",
        "2. Add optional fill_timestamp and order_submit_timestamp to exit_attribution for latency proxy.",
        "3. Review top validation_failed reasons; relax only where evidence supports (e.g. size cap too low).",
        "",
        "## What evidence would change my mind?",
        "Structured validation_failed reasons; fill vs. submit timestamps; and a spread or slippage proxy in the ledger.",
        "",
    ])

    # --- Research Lead ---
    w(board_dir / f"WEEKLY_REVIEW_{date_str}_Research_Lead.md", [
        "# Weekly Review — Research Lead",
        f"**Date:** {date_str}",
        "",
        "## 3 strongest findings",
        "1. 7d primary window; 14d/30d sanity checks noted in mission but require ledger extension (multiple --days or cohorts).",
        "2. Board review (last387) and shadow comparison define cohort; stability across 7d vs 30d is not yet computed in this pipeline.",
        "3. Counterfactuals not tested (from CSA) and missing_data list define next experiments.",
        "",
        "## 3 biggest risks",
        "1. Cohort instability (different symbol mix or regime across 7d vs 30d) invalidating comparisons.",
        "2. Missing baselines (do-nothing, buy-and-hold, time-window counterfactuals).",
        "3. Experiment design not answerable (e.g. no clear success criteria or sample size).",
        "",
        "## 3 recommended actions (ranked)",
        "1. Add 14d and 30d ledger summaries to weekly run; report nomination stability (e.g. same top shadow across windows).",
        "2. Define one do-nothing or buy-hold baseline and add to board comparison.",
        "3. For each required_next_experiment, add success criteria and minimum N.",
        "",
        "## What evidence would change my mind?",
        "Stable nomination across 7d/14d/30d; a documented baseline; and success criteria for each experiment.",
        "",
    ])

    # --- Innovation (5 crazy angles) ---
    w(board_dir / f"WEEKLY_REVIEW_{date_str}_Innovation.md", [
        "# Weekly Review — Innovation (Crazy Angles)",
        f"**Date:** {date_str}",
        "",
        "## 3 strongest findings",
        "1. Current pipeline is stock-only; listed options could capture theta or hedge delta.",
        "2. Universe and regime are levers; time-of-day and volatility regime switching under-explored.",
        "3. Radical simplification (kill weak signals, single exit rule) could improve clarity and reduce leakage.",
        "",
        "## 3 biggest risks",
        "1. Pivoting to options before stock edge is proven adds complexity and cost.",
        "2. Structural changes (universe, time gating) may invalidate existing backtests.",
        "3. Over-simplification could remove the only edge we have.",
        "",
        "## 3 recommended actions (ranked)",
        "1. Complete pivot analysis (stocks vs listed options) with evidence; stay course unless bottleneck is structural.",
        "2. Run one minimum viable experiment per crazy angle (see below) only if capacity allows.",
        "3. Do not change trading logic in this mission; document angles for future board.",
        "",
        "## 5 crazy angles",
        "",
        "| Angle | Expected upside | Key risk | Minimum viable experiment | Data needed |",
        "|-------|-----------------|----------|----------------------------|-------------|",
        "| **1. Options-income pivot** | Theta capture; defined risk | Assignment, liquidity, monitoring | Paper trade one underlying 30d; compare PnL vs stock-only | Options chain, assignment log, margin |",
        "| **2. Universe change** | Better edge concentration | Regime shift in new names | Backtest last387 with narrowed universe (e.g. top 20 by volume) | Universe history, volume |",
        "| **3. Time-of-day gating** | Avoid low-liquidity or mean-reversion hours | Miss morning momentum | Log entry time; compare win rate 10–11 vs 14–15 | entry_timestamp in ledger |",
        "| **4. Volatility regime switching** | Size down or pause in high vol | Lag in regime detection | Tag regime (e.g. VIX bucket) per exit; compare PnL by regime | VIX or proxy in attribution |",
        "| **5. Kill/keep radical simplification** | Single exit rule, single signal group; easier to tune | Lose edge from variety | Shadow: only decay exit + one signal group vs current | Shadow comparison with reduced config |",
        "",
        "## What evidence would change my mind?",
        "Quantified bottleneck (signal vs execution vs exits vs sizing); proof that options improve edge capture without unacceptable complexity; and one positive MVP result per angle.",
        "",
    ])

    # --- Owner / CEO (synthesis) ---
    w(board_dir / f"WEEKLY_REVIEW_{date_str}_Owner_CEO.md", [
        "# Weekly Review — Owner / CEO (Synthesis)",
        f"**Date:** {date_str}",
        "",
        "## 3 strongest findings",
        "1. Week in numbers: executed " + str(ledger.get("executed_count", "—")) + ", blocked " + str(ledger.get("blocked_count", "—")) + ", CI " + str(ledger.get("counter_intel_blocked_count", "—")) + "; CSA verdict " + str(verdict.get("verdict", "—")) + ".",
        "2. Promotable next: see shadow nomination and CSA findings; no promotion in this mission.",
        "3. Profit leaks and unturned rocks: see CSA value_leaks, missing_data, and WEEKLY_UNTURNED_ROCKS.",
        "",
        "## 3 biggest risks",
        "1. Real-money readiness unclear without closed experiments and risk checklist.",
        "2. Pivot to options-income could distract if stock edge is not yet proven.",
        "3. Missing instrumentation (opportunity cost, CI false positive rate) limits confidence.",
        "",
        "## 3 recommended actions (ranked)",
        "1. Use WEEKLY_DECISION_PACKET for prioritization; run top 5 experiments with success criteria.",
        "2. Keep course on stocks until pivot analysis recommends otherwise; then staged 30/60/90 plan.",
        "3. Deploy cockpit weekly section and verify on droplet; keep trades until next CSA visible.",
        "",
        "## What evidence would change my mind?",
        "Clear 'can we win?' answer with timeline; real-money readiness checklist satisfied; and pivot analysis with a stay/hybrid/pivot recommendation tied to evidence.",
        "",
    ])

    print("Wrote 7 persona memos to", board_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
