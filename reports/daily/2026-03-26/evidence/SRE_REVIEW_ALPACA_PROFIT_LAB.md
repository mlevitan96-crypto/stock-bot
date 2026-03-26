# SRE Review — Alpaca Profit Lab (Phase 6)

**Mission:** Certify data integrity and path-real evaluation.  
**Authority:** SRE (data truth). READ-ONLY.  
**Date:** 2026-03-18.

---

## 1. Data Integrity Certification

### 1.1 Sources

- **Canonical trade list:** TRADES_FROZEN.csv built from `logs/exit_attribution.jsonl` (ALPACA_QUANT_DATA_CONTRACT, ALPACA_TRADES_FROZEN_DATASET_FREEZE).
- **Join coverage:** Documented in ALPACA_QUANT_JOIN_COVERAGE.md and ALPACA_TRADES_FROZEN_JOIN_COVERAGE.md. Entry/exit join to alpaca_* is 0% on droplet; lab uses TRADES_FROZEN as direct extract for PnL/regime/exit_reason.

### 1.2 Grains

- **trade_id**, **trade_key** (symbol|side|entry_time_iso) defined and used consistently (alpaca_trade_key, pipeline step1).
- **position_id** optional; close event tied to same trade_id.

### 1.3 Timestamp & Gaps

- Timestamps UTC, second precision in trade_key; bars aligned to exchange.
- Missing bars → trade omitted from bar-based path-real studies; documented.

### 1.4 Fail-Closed

- If join coverage or sample size below MEMORY_BANK bar (98% / 200 trades), pipeline fails unless --allow-missing-attribution; lab does not assert valid lever attribution when run with override for join. Trade-level coverage from exit_attribution is 100% for frozen rows by construction.

---

## 2. Path-Real Evaluation

- **Counterfactuals (Phase 3):** Direction flip, delayed entry, regime-gated — use only actual bar (or fill) prices; no guessed prices.
- **Profit discovery (Phase 4):** Combinatorial strategies evaluated on realized_pnl_usd from TRADES_FROZEN (path-real outcomes).
- **Robustness (Phase 5):** Bootstrap, worst-day, LOSO, gap stress use same frozen dataset and optional TRADE_TELEMETRY.

---

## 3. Certification Statement

- **Data contract:** Frozen and documented (Phase 0, 1).
- **Join coverage:** As documented; lab does not rely on alpaca_*_attribution join for core PnL/regime analysis.
- **Path-real:** All counterfactual and profit discovery outputs use only actual trade outcomes and, when available, cached bars; no synthetic prices.

**Certification:** Data integrity for the Alpaca Profit Lab is **certified** subject to: (1) TRADES_FROZEN and inputs sourced from droplet/canonical logs; (2) no use of local-only or non-frozen data for conclusions; (3) bar-based work clearly marking trades omitted for missing bars.
