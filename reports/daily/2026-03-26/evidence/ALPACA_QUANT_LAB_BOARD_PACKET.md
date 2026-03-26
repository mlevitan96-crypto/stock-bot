# Alpaca Quant Lab — Board Packet (Phase 6)

**Mission:** Consolidated verdicts and evidence for board review.  
**Authority:** QSA, CSA, SRE.  
**Date:** 2026-03-18.

---

## 1. Objective

Establish data truth, diagnose loss mechanisms, and discover scalable profit engines for the Alpaca stock bot using multi-model, evidence-driven analysis. **READ-ONLY:** no live or paper execution changes.

---

## 2. Deliverables Summary

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 0 | ALPACA_QUANT_DATA_CONTRACT.md | Done |
| 0 | ALPACA_QUANT_JOIN_COVERAGE.md | Done |
| 1 | ALPACA_QUANT_FEATURE_INVENTORY.md | Done |
| 1 | ALPACA_QUANT_SIGNAL_REDUNDANCY.md | Done |
| 2 | ALPACA_QUANT_LOSS_DECOMP.md | Done |
| 3 | ALPACA_QUANT_COUNTERFACTUALS.md | Done |
| 3 | ALPACA_QUANT_WRONG_WAY_SIGNALS.md | Done |
| 4 | ALPACA_PROFIT_LAB_RAW_RESULTS.json | Schema + runner |
| 4 | ALPACA_PROFIT_LAB_RANKED.md | Template |
| 5 | ALPACA_PROFIT_LAB_ROBUSTNESS.md | Template |
| 6 | QSA_REVIEW_ALPACA_QUANT_LAB.md | Template |
| 6 | CSA_REVIEW_ALPACA_QUANT_LAB.md | Template |
| 6 | SRE_REVIEW_ALPACA_QUANT_LAB.md | Done (certification) |
| 6 | ALPACA_QUANT_LAB_BOARD_PACKET.md | This file |

---

## 3. Key Findings (Summary)

- **Data:** Canonical grains (trade_id, trade_key) defined; join to alpaca_*_attribution is 0% on droplet; TRADES_FROZEN is the authoritative closed-trade list for PnL/regime/exit analysis.
- **Loss:** Regime shift, sentiment/score deterioration, and vol expansion are dominant exit drivers on losers; many losers have high exit_score_deterioration or signal_decay/stale_alpha_cutoff.
- **Counterfactuals:** Direction flip, delayed entry, and regime-gated analysis are defined path-real; implement with bars per ALPACA_QUANT_COUNTERFACTUALS.md.
- **Profit discovery:** Runner script `scripts/audit/run_alpaca_profit_lab.py` evaluates combinatorial strategies (regime, side, combos) on TRADES_FROZEN; run 30–60 min for full combinatorial expansion; rank by PnL and expectancy.

---

## 4. Persona Verdicts

- **QSA:** Explains why winners win; review in QSA_REVIEW_ALPACA_QUANT_LAB.md (populate after Phase 4/5).
- **CSA:** Block or approve paper promotion per CSA_REVIEW_ALPACA_QUANT_LAB.md (populate after Phase 4/5 and SRE).
- **SRE:** Data integrity certified per SRE_REVIEW_ALPACA_QUANT_LAB.md.

---

## 5. Next Steps

1. Run `scripts/alpaca_edge_2000_pipeline.py` (or equivalent) to produce a frozen dataset with TRADES_FROZEN.csv (and TRADE_TELEMETRY if bars available).
2. Run `scripts/audit/run_alpaca_profit_lab.py` to populate ALPACA_PROFIT_LAB_RAW_RESULTS.json and ALPACA_PROFIT_LAB_RANKED.md.
3. Run robustness checks on top strategies (Phase 5); update ALPACA_PROFIT_LAB_ROBUSTNESS.md.
4. Populate QSA and CSA verdicts in Phase 6 reviews.
5. Use this board packet for governance and promotion decisions per MEMORY_BANK.
