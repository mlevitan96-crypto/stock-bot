# Alpaca Profit Lab — Board Packet (Phase 6)

**Mission:** ALPACA DATA EXPANSION + CAUSALITY + PROFIT DISCOVERY.  
**Authority:** SRE, QSA, CSA. READ-ONLY. NO EXECUTION CHANGES. NO PAPER PROMOTION IN THIS BLOCK.  
**Date:** 2026-03-18.

---

## 1. Objective

Expand Alpaca’s frozen dataset to sufficient mass, diagnose loss mechanisms, and mine profit engines using path-real evaluation. This block establishes truth and surfaces scalable edges. No paper promotion is executed in this block.

---

## 2. Deliverables Summary

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 0 | ALPACA_EXPANSION_SCOPE.md | Done |
| 1 | ALPACA_TRADES_FROZEN_DATASET_FREEZE.md | Done |
| 1 | ALPACA_TRADES_FROZEN_JOIN_COVERAGE.md | Done |
| 2 | ALPACA_LOSS_CAUSALITY.md | Done |
| 3 | ALPACA_COUNTERFACTUAL_RESULTS.md | Done |
| 3 | ALPACA_WRONG_WAY_SIGNAL_ANALYSIS.md | Done |
| 4 | ALPACA_PROFIT_LAB_RAW_RESULTS.json | Done (refreshed) |
| 4 | ALPACA_PROFIT_LAB_RANKED.md | Done (refreshed) |
| 5 | ALPACA_PROFIT_LAB_ROBUSTNESS.md | Done |
| 6 | QSA_REVIEW_ALPACA_PROFIT_LAB.md | Done |
| 6 | CSA_REVIEW_ALPACA_PROFIT_LAB.md | Done |
| 6 | SRE_REVIEW_ALPACA_PROFIT_LAB.md | Done |
| 6 | ALPACA_PROFIT_LAB_BOARD_PACKET.md | This file |

---

## 3. Key Findings

- **Data:** Contracts loaded (MEMORY_BANK, ALPACA_QUANT_DATA_CONTRACT, ALPACA_QUANT_JOIN_COVERAGE). Fail-closed rules enforced. Procedure for building ≥500/2000 TRADES_FROZEN on droplet documented; current local frozen sets are small (e.g. 36 trades); droplet has sufficient exit_attribution lines for 2000.
- **Loss causality:** Framework and aggregates (by cause, regime, symbol, TOD) defined; existing loss forensics show regime_shift and exit deterioration as major loss drivers.
- **Counterfactuals:** Spec and placeholders for direction flip, delayed entry, regime-gated (path-real only). Wrong-way signal analysis and regime/TOD flags documented.
- **Profit discovery:** Runner script produces combinatorial strategies (regime, side, combos); RAW_RESULTS and RANKED refreshed from current TRADES_FROZEN. Full 30–60 min run and ≥500-trade dataset will improve ranking.
- **Robustness:** Checks (bootstrap, worst-day, LOSO, gap stress, leverage tolerance) specified; placeholder for results when run on top strategies.
- **Verdicts:** QSA explains mechanism for winners; CSA block/approve for future promotion (none applied here); SRE certifies data integrity and path-real evaluation.

---

## 4. Persona Verdicts

- **QSA:** Why winners win (mechanism) — QSA_REVIEW_ALPACA_PROFIT_LAB.md.
- **CSA:** Block or approve for future paper promotion — CSA_REVIEW_ALPACA_PROFIT_LAB.md (no promotion in this block).
- **SRE:** Data integrity and path-real certified — SRE_REVIEW_ALPACA_PROFIT_LAB.md.

---

## 5. Next Steps

1. **Build large dataset:** Run full Alpaca pipeline on droplet with --min-trades 500 (or 2000), --allow-missing-attribution; validate and re-run Phase 2–5 on new TRADES_FROZEN.
2. **Loss causality script:** Implement run_alpaca_loss_causality.py to populate ALPACA_LOSS_CAUSALITY.md from TRADES_FROZEN (+ optional TRADE_TELEMETRY).
3. **Counterfactual script:** Implement or wire bar-based direction-flip and delayed-entry; populate ALPACA_COUNTERFACTUAL_RESULTS.md.
4. **Profit lab (30–60 min):** Run run_alpaca_profit_lab.py on ≥500-trade dataset with extended combinatorics; refresh RAW_RESULTS and RANKED.
5. **Robustness script:** Run bootstrap, worst-day, LOSO on top strategies; update ALPACA_PROFIT_LAB_ROBUSTNESS.md.
6. Use this board packet for governance and future promotion decisions per MEMORY_BANK.
