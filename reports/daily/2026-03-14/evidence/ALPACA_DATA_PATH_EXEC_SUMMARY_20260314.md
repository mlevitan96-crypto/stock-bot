# ALPACA — Data path integrity & signal granularity: Executive summary

**Mission:** DATA PATH INTEGRITY & SIGNAL GRANULARITY CONFIRMATION  
**Timestamp:** 20260314  
**Authority:** Cursor executor; CSA and SRE embedded reviewers with veto authority.  
**Scope:** READ-ONLY diagnostic. No strategy or execution logic changes.

---

## Summary answers

| Question | Answer |
|----------|--------|
| **Are we collecting the right data?** | **YES** |
| **Are we reading it correctly?** | **YES** |
| **Can we adjust fine-grained signal controls?** | **YES** (via code/config; no runtime API) |

---

## 1. Are we collecting the right data?

**YES.** Primary source for profitability and tuning is `logs/exit_attribution.jsonl`. Per trade we collect:

- PnL (realized), symbol, side, entry/exit timestamps and prices, qty, exit_reason, entry/exit regime, time_in_trade_minutes.
- **Signal granularity:** v2_exit_score, v2_exit_components (per-lever values), attribution_components (signal_id + contribution), exit_reason_code, regime/strategy/mode, and optional exit_quality_metrics (MFE/MAE).

Secondary sources: `logs/master_trade_log.jsonl`, `logs/attribution.jsonl` — used for reconciliation and EOD views. All are append-only on the droplet.

**Evidence:** `reports/audit/TRADE_DATA_COLLECTION_SUMMARY.md`, `ALPACA_DATA_PATH_DECLARATION_20260314.md`, `ALPACA_SIGNAL_GRANULARITY_20260314.md`.

---

## 2. Are we reading it correctly?

**YES.** The pipeline (Step 1) reads `logs/exit_attribution.jsonl` and builds TRADES_FROZEN.csv. Confirmed on the droplet:

- File paths opened and row counts (source vs pipeline) reconciled (Phase 1).
- TRADES_FROZEN.csv row count matches expectations from exit_attribution (last N trades; minor drops only for blank/json_error/not_dict/no_exit_ts).
- trade_key derivation is consistent across exit_attribution and TRADES_FROZEN (Phase 2). No silent filtering from schema drift.

**Evidence:** `ALPACA_PIPELINE_READ_RECON_20260314.md`, `ALPACA_TRADE_KEY_INTEGRITY_20260314.md`, `ALPACA_BOARD_CONSISTENCY_20260314.md`.

---

## 3. Can we adjust fine-grained signal controls?

**YES.** Exit levers (flow_deterioration, score_deterioration, regime_shift, vol_expansion, thesis_invalidated, etc.) are logged per trade and are separable. Weights and thresholds are in code (`exit_score_v2.py`, exit pressure config); adjustment is via code/config deployment. There is no runtime API for tuning without deploy. For governed, audit-trail tuning this is sufficient.

**Evidence:** `ALPACA_SIGNAL_GRANULARITY_20260314.md` (signal × available_fields × adjustable matrix).

---

## Evidence pointers (paths)

| Artifact | Path |
|----------|------|
| Canonical path declaration | `reports/audit/ALPACA_DATA_PATH_DECLARATION_20260314.md` |
| Pipeline read reconciliation | `reports/audit/ALPACA_PIPELINE_READ_RECON_20260314.md` |
| Trade key & join integrity | `reports/audit/ALPACA_TRADE_KEY_INTEGRITY_20260314.md` |
| Signal granularity | `reports/audit/ALPACA_SIGNAL_GRANULARITY_20260314.md` |
| Board consistency | `reports/audit/ALPACA_BOARD_CONSISTENCY_20260314.md` |
| Retention & overwrite safety | `reports/audit/ALPACA_RETENTION_SAFETY_20260314.md` |
| CSA verdict | `reports/audit/CSA_REVIEW_ALPACA_DATA_PATH_20260314.md` |
| SRE verdict | `reports/audit/SRE_REVIEW_ALPACA_DATA_PATH_20260314.md` |

**Droplet paths (absolute):** Primary: `/root/stock-bot/logs/exit_attribution.jsonl`. Secondary: `/root/stock-bot/logs/master_trade_log.jsonl`, `/root/stock-bot/logs/attribution.jsonl`. Pipeline consumer: `scripts/alpaca_edge_2000_pipeline.py` (Step 1).

---

## CSA verdict (summary)

- **Data paths:** Correct and consistent.  
- **Signal telemetry:** Sufficient for fine-grained tuning.  
- **Blockers to governed adjustment:** None identified.  
Full text: `reports/audit/CSA_REVIEW_ALPACA_DATA_PATH_20260314.md`.

---

## SRE verdict (summary)

- **Pipeline reads real droplet data:** Confirmed.  
- **Artifacts stable and non-destructive:** Confirmed (APPEND_ONLY_OK).  
- **Operational risk:** Low for data path integrity and retention.  
Full text: `reports/audit/SRE_REVIEW_ALPACA_DATA_PATH_20260314.md`.

---

**END MISSION**
