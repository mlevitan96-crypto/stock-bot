# Exit Redesign Contract — Multi-Factor Pressure + Learning Loop

**Version:** 1.0.0  
**Status:** Contract (acceptance criteria and promotion gates).  
**Non-negotiables:** No loosening of risk controls; no silent inference; promotion requires evidence; everything reversible.

---

## 1. Acceptance criteria (definition of "fixed")

| # | Criterion | Verification |
|---|-----------|---------------|
| AC1 | Exit decision is driven by **multi-factor pressure** (continuous score 0..1), not first-trigger cascade, except hard overrides. | Exit loop uses `exit_pressure >= threshold` as primary trigger; overrides (stop loss, liquidation, compliance, stale pricing) always win. |
| AC2 | Every exit evaluation and every executed close emits **truth logs** with inputs, score, thresholds, decision, components. | `logs/exit_truth.jsonl` present; schema: ts, symbol, position_id, exit_pressure, thresholds, decision, components, close_reason, exit_reason_code. |
| AC3 | Effectiveness v2 shows **measurable reduction in giveback** and/or **increase in saved_loss** without unacceptable tail-risk increase. | `reports/exit_review/exit_effectiveness_v2.json`; objective function doc; comparison vs baseline. |
| AC4 | Dashboard truth audit **PASS** for exit panels and exit truth coverage. | Dashboard contract includes Exit Pressure, Exit Truth Coverage, Giveback/SavedLoss/LeftMoney; audit script checks freshness and coverage. |
| AC5 | EOD enforces exit truth coverage and effectiveness run daily; EOD fails if exit_truth missing/stale or coverage below threshold. | EOD wiring runs exit effectiveness v2 and dashboard truth audit; fail conditions documented. |

---

## 2. Hard overrides (always win; never relaxed)

- **Stop loss** (P&L ≤ configured floor)
- **Catastrophic risk** (liquidation, margin, compliance)
- **Stale pricing / integrity** (no valid quote or risk data)
- **Regime safety override** (e.g. high_vol_neg_gamma + loss threshold)

Pressure-based exit is **only** used when none of the above fire first.

---

## 3. Exit pressure model (primary decision engine)

- **ExitPressureScore:** continuous scalar in [0, 1] (or unbounded then squashed).
- **Two-tier thresholds:**
  - `EXIT_PRESSURE_NORMAL`: close when pressure ≥ this (normal exit).
  - `EXIT_PRESSURE_URGENT`: close with higher urgency (faster/aggressive).
- **Components** (each logged with name, value, weight, contribution):
  - Signal deterioration (conviction decay, composite slope, missing intel)
  - Flow reversal (flow delta, dark pool, options flow, sentiment flip)
  - Regime risk (vol regime shift, correlation, breadth, macro proximity)
  - Price action (trend break, momentum stall, mean reversion, gap risk)
  - Position risk (drawdown, MAE, gamma/vega if options, liquidity)
  - Time decay / opportunity cost (time-in-trade vs horizon, stagnation)
  - Profit protection (giveback from MFE, trailing as pressure contributor)
  - Crowding / squeeze (shorts/FTD, borrow stress if available)

Existing cascade rules become **pressure contributors** or **hard overrides**; no silent removal.

---

## 4. Truth logging contract

- **File:** `logs/exit_truth.jsonl`
- **Per evaluation tick:** ts, symbol, position_id, exit_pressure, thresholds (normal, urgent), decision (HOLD | CLOSE_NORMAL | CLOSE_URGENT | OVERRIDE_*), components (list of {name, value, weight, contribution}), close_reason (composite string), exit_reason_code, regime_snapshot, entry_snapshot, pnl_snapshot, mfe/mae, giveback, spread/liquidity (if available).
- **Per executed close:** same plus execution outcome (fill price, qty, order_id).

No exit decision without a corresponding truth record.

---

## 5. Counterfactual and effectiveness

- **Counterfactuals:** For every closed trade, compute and store hold+N-bars and exit-earlier outcomes; label saved_loss, left_money, good_exit, bad_exit, entry_blame, exit_blame. Store in `reports/exit_review/exit_counterfactuals.json` (or equivalent).
- **Effectiveness v2:** By exit_reason_code, regime, symbol bucket: avg/median pnl, tail loss, giveback distribution, saved_loss rate, left_money rate, time-in-trade, pressure-at-exit. Output: `exit_effectiveness_v2.json`, `exit_effectiveness_v2.md`.
- **Objective function:** Documented in `docs/EXIT_OBJECTIVE_FUNCTION.md`. Minimize giveback, left_money, tail loss; maximize realized pnl, saved_loss; constrain turnover, slippage proxy, risk.

---

## 6. Tuning loop (recommendations only)

- **Script:** `scripts/exit_tuning/suggest_exit_tuning.py`
- **Outputs:** `reports/exit_review/exit_tuning_recommendations.md`, `reports/exit_review/exit_tuning_patch.json` (config-only).
- **No automatic application;** Board review required before applying any patch.

---

## 7. Promotion gates (must all pass)

| Gate | Check |
|------|--------|
| G1 | Backtest improvement on objective function (giveback down or saved_loss up, within tail constraint). |
| G2 | No increase in tail loss beyond configured tolerance. |
| G3 | Truth logs present and fresh; dashboard truth audit PASS. |
| G4 | No integrity regressions (attribution schema, exit_reason_code taxonomy). |
| G5 | Rollback plan validated (feature flag off, config revert, redeploy). |
| G6 | Shadow run shows expected direction (would-have-exited earlier/later, giveback/saved_loss delta). |

Promotion checklist: `reports/exit_review/EXIT_PROMOTION_CHECKLIST.md`.

---

## 8. Feature flag and config

- **EXIT_PRESSURE_ENABLED:** default OFF until evidence passes.
- **EXIT_PRESSURE_NORMAL**, **EXIT_PRESSURE_URGENT:** thresholds.
- Component weights and regime modifiers in config; all reversible via config patch.

---

## 9. Personas (adversarial review)

- **Prosecutor:** Exits are the main profit leak; break design with edge cases (gap, halt, missing data).
- **Defender:** Safety overrides and simplicity where needed; no silent failures.
- **SRE:** Logs, freshness, EOD wiring, dashboard truth.
- **Quant:** Objective function, giveback, saved_loss, MFE/MAE, regime conditioning.
- **Board:** Promotion gates, rollback, copy/paste summaries.

---

## 10. Deliverables (code, analysis, ops, governance)

- **Code:** `src/exit/exit_pressure_v3.py`; exit loop refactor (pressure as primary + overrides); `logs/exit_truth.jsonl` emission; counterfactual computation + artifacts.
- **Analysis:** This contract; `exit_effectiveness_v2.{json,md}`; `exit_tuning_recommendations.md`; `EXIT_PROMOTION_CHECKLIST.md`.
- **Ops:** EOD wiring updated; dashboard truth contract updated; audit PASS.
- **Governance:** `reports/exit_review/CURSOR_FINAL_SUMMARY.txt`; SAFE_TO_APPLY checklist + rollback steps.
