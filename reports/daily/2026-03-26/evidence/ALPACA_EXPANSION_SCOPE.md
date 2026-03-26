# Alpaca Data Expansion + Causality + Profit Discovery — Scope (Phase 0)

**Mission:** ALPACA DATA EXPANSION + CAUSALITY + PROFIT DISCOVERY  
**Authority:** SRE (data truth), QSA (quant causality), CSA (governance). READ-ONLY. NO EXECUTION CHANGES. NO PAPER PROMOTION IN THIS BLOCK.  
**Date:** 2026-03-18.

---

## 1. Contracts Loaded

### 1.1 MEMORY_BANK.md

- **Version:** 2026-01-12 (SSH Deployment Verified); Alpaca governance current 2026-03-17.
- **Verification:** Loaded; no content hash stored in MEMORY_BANK itself. Scope assumes MEMORY_BANK is the authoritative rule set for behavior, data sourcing, and Truth Gate.
- **Relevant sections:** §3.4 Truth Gate (droplet execution and canonical data; HARD FAILURE for missing data, join coverage below threshold, schema mismatch); §5.5 log paths; §7.12 Exit Intelligence; §8.5 Telemetry.

### 1.2 ALPACA_QUANT_DATA_CONTRACT.md

- **Loaded.** Defines: inventory of Alpaca data sources (orders/fills/positions, bars, indicators, regime, market hours); canonical grains (trade_id, trade_key = symbol|side|entry_time_iso, position_id optional); validation (join coverage, missing fields, timestamp alignment, corporate actions, gap behavior).
- **Path:** reports/audit/ALPACA_QUANT_DATA_CONTRACT.md.

### 1.3 ALPACA_QUANT_JOIN_COVERAGE.md

- **Loaded.** Defines: primary join (TRADES_FROZEN by trade_key vs ENTRY/EXIT_ATTRIBUTION_FROZEN); operational reality (TRADES_FROZEN built from exit_attribution.jsonl; alpaca_* empty on droplet → 0% join to canonical); MEMORY_BANK bar (min join 98%, min_trades 200, min_final_exits 200); fail-closed and override (--allow-missing-attribution).
- **Path:** reports/audit/ALPACA_QUANT_JOIN_COVERAGE.md.

---

## 2. Fail-Closed Rules (Enforced)

| Rule | Source | Action |
|------|--------|--------|
| **Coverage < MEMORY_BANK bar** | JOIN_COVERAGE, pipeline | If join coverage &lt; 98% or trades &lt; min_trades/min_final_exits (200 default), pipeline raises and writes ALPACA_JOIN_INTEGRITY_BLOCKER_*.md. Do not treat run as valid for lever attribution when below threshold unless override explicitly accepted. |
| **Missing required data** | MEMORY_BANK §3.4 | Missing exit_attribution or master_trade_log = HARD FAILURE; do not proceed to conclusions. |
| **Path-real only** | Data contract, Phase 3/4 | No guessed prices. Counterfactuals and profit discovery use bars/trade outcomes only. |
| **No execution / paper promotion** | Mission | This block is READ-ONLY; no live or paper execution changes; no paper promotion decisions executed in this block. |

---

## 3. Expansion Objectives (This Block)

1. **Phase 1:** Build or document large TRADES_FROZEN dataset (target ≥500 closed trades, prefer ≥2000); validate trade_key uniqueness, timestamp alignment, gap detection, market-hours correctness; write dataset freeze and join coverage reports.
2. **Phase 2:** Loss causality decomposition (direction correctness, MAE/MFE, entry vs exit attribution, gap impact, regime mismatch); aggregate by cause, regime, symbol, time-of-day.
3. **Phase 3:** Counterfactual analysis (direction flip, delayed entry, regime-gated) path-real; wrong-way signal analysis.
4. **Phase 4:** Massive profit discovery (combinatorial strategies, path-real PnL, rank by total PnL and expectancy, deduplicate); run 30–60 min.
5. **Phase 5:** Robustness (bootstrap, worst-day removal, leave-one-symbol-out, gap stress, leverage tolerance).
6. **Phase 6:** QSA/CSA/SRE verdicts and board packet (why winners win; block/approve for future paper promotion; certify data integrity).

---

## 4. Out of Scope (This Block)

- Pushing code to GitHub or triggering droplet deployment (per mission: Cursor executes; droplet pipeline run may be documented for operator).
- Making or applying paper promotion changes.
- Modifying live or paper trading configuration.
