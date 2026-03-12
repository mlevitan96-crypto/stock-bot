# Quantified Governance Experiment Framework — Alpaca

**Scope:** Alpaca stock bot. Analysis-only; no execution impact, no risk scaling, no deploy authorization use.

---

## 1. Purpose

This document defines the governance, experimentability, and monitoring pipeline for the Alpaca stock bot:

- **Quantified governance:** Hypothesis-led experiments with a clear lifecycle and validation windows.
- **CSA + SRE review hooks:** Reports and decision spines support dedicated review sections; both roles are review-only.
- **Hypothesis ledger + health checks:** Append-only ledger and validation scripts; safe when missing or empty.

---

## 2. CSA + SRE Review Hooks for Alpaca Decision Spines

Alpaca decision spines and governance reports **should support** the following sections. These are **review-only**; they do not gate execution or deployment.

### 2.1 CSA_REVIEW

- **Profit logic:** Assumptions behind PnL and expectancy; consistency with strategy and regime.
- **Assumptions:** Stated hypotheses, data windows, and constraints.
- **Opportunity cost:** Foregone alternatives (e.g., different exit timing, sizing, or filters) and their implied impact.

**Output:** Narrative or structured block in reports (e.g. `CSA_REVIEW` in verdict JSON or markdown). No code or config changes from CSA.

### 2.2 SRE_REVIEW

- **Observability:** Logging, metrics, and dashboards sufficient to detect failures and regressions.
- **Failure modes:** Identified failure modes and mitigations (e.g., API downtime, stale data, restart behavior).
- **Rollback:** How to revert or pause safely; no automatic rollback from this pipeline.

**Output:** Narrative or structured block in reports (e.g. `SRE_REVIEW` in verdict JSON or markdown). No execution impact.

---

## 3. Report Support

Reports that participate in the Alpaca governance pipeline should:

- Include a **CSA_REVIEW** section (or equivalent) when reporting on profitability, promotions, or experiment outcomes.
- Include an **SRE_REVIEW** section (or equivalent) when reporting on health, automation, or operational readiness.

Existing artifacts (e.g. `reports/audit/CSA_VERDICT_*.json`, `reports/audit/CSA_SUMMARY_*.md`, SRE status files) can be extended with these sections as needed. This document does not require immediate code changes; it establishes the contract for future report generators and decision spines.

---

## 4. ANALYSIS WORKERS — SAFE TO SCALE

The following analysis-only batch jobs are safe to run in parallel (e.g. multiprocessing or batch) to utilize idle CPU. They use read-only access to logs/artifacts; no order placement, no API writes.

| Workload | Description | Notes |
|----------|-------------|--------|
| Historical expectancy recomputation | Recompute expectancy from closed trades / score snapshots over configurable windows | Read-only: logs, state, telemetry |
| Slippage distribution analysis | Analyze fill vs signal price and time-to-fill distributions | Read-only: execution logs, order history |
| Session-based PnL attribution | Attribute PnL by session, symbol, strategy, exit reason | Read-only: closed trades, position metadata |
| Counterfactual "would-have-traded" analysis | Replay entry/exit rules on historical data to estimate impact of parameter changes | Read-only: bars, scores, blocked_trades |

**Constraints:** Read-only access to logs/artifacts; no order placement; no API writes; safe to scale via multiprocessing or batch scheduling.

---

## 5. References

- **Ledger:** `state/governance_experiment_1_hypothesis_ledger_alpaca.json`
- **Tag script:** `scripts/tag_profit_hypothesis_alpaca.py`
- **Validate script:** `scripts/validate_hypothesis_ledger_alpaca.py`
- **Break alert:** `scripts/notify_governance_experiment_alpaca_break.py` (invalid or stale ledger → one Telegram message)
- **Completion alert:** `scripts/notify_governance_experiment_alpaca_complete.py` (validation window satisfied + ledger healthy → one Telegram message; at most once per phase)
- **MEMORY_BANK:** Section "Alpaca quantified governance (experiment pipeline)"
