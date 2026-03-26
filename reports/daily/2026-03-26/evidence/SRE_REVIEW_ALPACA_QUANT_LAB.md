# SRE Review — Alpaca Quant Lab (Phase 6)

**Mission:** Certify data integrity for the quant lab.  
**Authority:** SRE (integrity).  
**Date:** 2026-03-18.

---

## 1. Data Integrity Certification

### 1.1 Sources

- **Canonical trade list:** TRADES_FROZEN.csv built from `logs/exit_attribution.jsonl` (see ALPACA_QUANT_DATA_CONTRACT.md).
- **Join coverage:** Documented in ALPACA_QUANT_JOIN_COVERAGE.md. Entry/exit join to alpaca_*_attribution is 0% on droplet; lab uses TRADES_FROZEN as direct extract for PnL/regime/exit_reason.

### 1.2 Grains

- **trade_id**, **trade_key** (symbol|side|entry_time_iso) defined and used consistently.
- **position_id** optional; **position_close_id** not a separate grain (close = same trade_id).

### 1.3 Timestamp & Gaps

- Timestamps UTC, second precision in trade_key; bars aligned to exchange.
- Missing bars → trade omitted from bar-based path-real studies; documented.

### 1.4 Fail-Closed

- If join coverage or sample size below MEMORY_BANK bar (98% / 200 trades), pipeline fails and writes blocker; lab must not assert valid attribution when run with override.

---

## 2. Certification Statement

- **Data contract:** Frozen and documented (Phase 0).
- **Join coverage:** As documented; lab does not rely on alpaca_*_attribution join for core PnL/regime analysis.
- **Path-real:** Counterfactuals and profit discovery use only actual trade outcomes and, when available, cached bars; no guessed prices.

**Certification:** Data integrity for the Alpaca Quant Lab is **certified** subject to: (1) TRADES_FROZEN and inputs sourced from droplet/canonical logs; (2) no use of local-only or non-frozen data for conclusions; (3) bar-based work clearly marking trades omitted for missing bars.

*(SRE may add run-specific checks and date after running pipeline and lab scripts.)*
