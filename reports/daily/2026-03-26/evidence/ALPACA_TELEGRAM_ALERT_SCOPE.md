# Alpaca Trade-Count Telegram Governance Alerts — Scope (Phase 0)

**Mission:** ALPACA TRADE-COUNT TELEGRAM GOVERNANCE ALERTS  
**Authority:** CSA (governance), SRE (integrity). READ-ONLY. NO EXECUTION OR PAPER PROMOTION.  
**Date:** 2026-03-18.

---

## 1. Context Loaded

### 1.1 ALPACA_EXPANSION_SCOPE.md

- **Loaded.** Expansion objectives: build TRADES_FROZEN ≥500 (prefer 2000); loss causality; counterfactuals; profit discovery; robustness; verdicts. Fail-closed rules: coverage &lt; MEMORY_BANK bar, missing data, path-real only, no execution/promotion in block.

### 1.2 ALPACA_TRADES_FROZEN_DATASET_FREEZE.md

- **Loaded.** Target ≥500 closed trades, prefer 2000. Source: `logs/exit_attribution.jsonl`; pipeline step1 builds TRADES_FROZEN. Build procedure on droplet documented; validation: trade_key uniqueness, timestamps, gap detection.

### 1.3 ALPACA_QUANT_DATA_CONTRACT.md

- **Loaded.** Data sources, canonical grains (trade_id, trade_key), bars and indicators; TRADES_FROZEN is canonical closed-trade list from exit_attribution.

---

## 2. Telegram Credentials (No Secrets in Code)

- **Contract:** Telegram credentials MUST be provided via **environment** (e.g. systemd `Environment=` or `.env` loaded by process), not hardcoded in repository.
- **Variables:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (same as existing pipeline: `scripts/alpaca_edge_2000_pipeline.py` `send_telegram()`, `scripts/verify_telegram_env.py`).
- **Verification:** Run `python scripts/verify_telegram_env.py` to confirm token and chat_id are set at runtime. If missing, alerts are skipped and logged (fail-closed: log only, no crash).
- **Systemd:** On droplet, ensure the service or wrapper that runs the pipeline (or the milestone-check job) has access to these env vars, e.g. from a systemd override or environment file that is not committed.

---

## 3. Objective

Add **deterministic** Telegram alerts when:

1. **Trade-count milestones:** TRADES_FROZEN reaches T1 (100), T2 (500), T3 (2000); each fires **once**; state persisted to prevent duplicates.
2. **Analysis completion:** Loss causality, counterfactual, profit discovery lab, robustness, board packet finalized — each alert includes phase name, artifact paths, readiness status.

Enables confirm → update → finish governance without impacting execution or paper promotion.

---

## 4. Out of Scope (This Block)

- No execution or paper promotion.
- No code changes that affect trading or order flow.
- No secrets stored in code; credentials from environment only.
