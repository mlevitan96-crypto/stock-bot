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

Full persona: **`docs/ALPACA_TIERED_BOARD_REVIEW_DESIGN.md` §8.1** (Chief Strategy Auditor — Economic Truth Guardian, Alpaca). In report sections, emphasize:

- **Economic truth:** Learning readiness from **live entry/exit intent + realized outcome**; durable edge vs sparse/lucky outcomes; signal decay by time-of-day or regime.
- **Discipline:** False confidence from sparse data; missed-opportunity zones from conservative gating (describe only — no lever changes).
- **Explicit non-scope in this role:** No portfolio construction, capital allocation, or execution timing.

**Narrative verdict labels (learning layer):** `CSA_LEARNING_UNBLOCKED_LIVE_TRUTH_CONFIRMED`, `CSA_LEARNING_BLOCKED`, `CSA_PASS_WEAK` — see §8.1 and §8.3 of the tiered design doc for coexistence with legacy **PROCEED | HOLD | ESCALATE | ROLLBACK** in `CSA_VERDICT_*.json`.

**Output:** Narrative or structured block in reports (e.g. `CSA_REVIEW` in verdict JSON or markdown). No code or config changes from CSA.

### 2.2 SRE_REVIEW

Full persona: **`docs/ALPACA_TIERED_BOARD_REVIEW_DESIGN.md` §8.2** (Site Reliability Engineer — Operational Integrity Sentinel, Alpaca). In report sections, emphasize:

- **Session integrity:** Session-aware joins; partial-day silence; telemetry completeness across market hours; overnight stale state.
- **Explicit non-scope in this role:** No strategy review; no learning decisions.

**Narrative verdict labels (pipeline layer):** `SRE_LEARNING_PIPELINE_HEALTHY`, `SRE_PIPELINE_DEGRADED` (non-blocking), `SRE_PIPELINE_UNHEALTHY` (blocking) — see §8.2 and §8.3 for coexistence with existing `SRE_STATUS.json` / events tooling.

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
