# Alpaca Quant Lab — Join Coverage (SRE-LED)

**Mission:** Phase 0 — Validate join coverage, missing fields, timestamp alignment.  
**Authority:** SRE. Fail-closed if coverage < MEMORY_BANK bar.  
**Date:** 2026-03-18.

---

## 1. Join Model

### 1.1 Primary Join (Pipeline)

- **Left:** TRADES_FROZEN.csv rows (one per closed trade), key = **trade_key** = `{symbol}|{side}|{entry_time_iso}` (UTC, second precision).
- **Right (entry):** ENTRY_ATTRIBUTION_FROZEN.jsonl (from `logs/alpaca_entry_attribution.jsonl` when present); key = **trade_key** (or derived via `_derive_trade_key_from_entry_rec`).
- **Right (exit):** EXIT_ATTRIBUTION_FROZEN.jsonl (from `logs/alpaca_exit_attribution.jsonl` when present); key = **trade_key** (or derived via `_derive_trade_key_from_exit_rec`).

**Reality on droplet:** `alpaca_entry_attribution.jsonl` and `alpaca_exit_attribution.jsonl` are **empty**. So:

- **Entry join coverage** = 0% (no rows in frozen entry attribution to match).
- **Exit join coverage** = 0% when using canonical Alpaca exit path only.

Pipeline step1 builds TRADES_FROZEN from **`logs/exit_attribution.jsonl`** (the non-canonical, populated log). Join coverage is then computed against:

- ENTRY_ATTRIBUTION_FROZEN from `logs/alpaca_entry_attribution.jsonl` → typically 0% entry match.
- EXIT_ATTRIBUTION_FROZEN from `logs/alpaca_exit_attribution.jsonl` → typically 0% exit match.

So with default paths, **join coverage will be below 98%** unless `--allow-missing-attribution` is used. For **quant lab**, the authoritative trade list is still the same source as TRADES_FROZEN (exit_attribution.jsonl); the “join” to “canonical” Alpaca attribution is what fails.

### 1.2 Operational Join (What Actually Links Data)

- **TRADES_FROZEN** is built directly from `logs/exit_attribution.jsonl`. Each row already contains the fields from that log (symbol, side, entry/exit time, PnL, regime, v2_exit_score, etc.). So there is no separate “join” needed for basic PnL/regime/exit-reason analysis — the CSV is a direct extract.
- **Entry attribution (entry score, components):** When `alpaca_entry_attribution.jsonl` is empty, entry-side attribution (e.g. composite score at entry) is missing for join-based workflows; it may appear in master_trade_log or exit_attribution context when those records carry it.
- **Exit attribution:** Exit details (v2_exit_components, exit_quality_metrics, etc.) are already on each exit_attribution record that was used to build TRADES_FROZEN. So for “exit attribution” we have full coverage for the frozen rows by construction.

**Conclusion:** Join coverage as computed by the pipeline (against alpaca_*_attribution) is 0% on the current droplet. For **quant lab**, the meaningful “coverage” is:

1. **Trade-level coverage:** 100% of TRADES_FROZEN rows come from exit_attribution.jsonl and have PnL, times, regime, exit reason, v2_exit_score.
2. **Entry-score coverage:** Partial — only where master_trade_log or exit_attribution carry entry_score/entry components (e.g. from joined entry snapshot or backfill).
3. **Bar coverage:** Per step2; missing bars for a trade → that trade omitted from bar-based studies (path-real only).

---

## 2. MEMORY_BANK Bar (Fail-Closed)

- **Threshold:** min join coverage 98% (entry and exit), min_trades 200, min_final_exits 200 (scripts/alpaca_edge_2000_pipeline.py).
- **If coverage < bar:** Pipeline raises, writes `reports/audit/ALPACA_JOIN_INTEGRITY_BLOCKER_<ts>.md`, classification JOIN_INTEGRITY or SAMPLE_SIZE. Quant lab MUST NOT treat the run as valid for lever attribution conclusions when join coverage is below threshold.
- **Override:** `--allow-missing-attribution` allows run to proceed; use only when explicitly accepting lower join quality (e.g. for bar-only or PnL-only studies that do not rely on entry/exit attribution join).

For **this lab**, we proceed with the understanding that:

- **Data truth:** TRADES_FROZEN is the canonical closed-trade list from exit_attribution.jsonl; no second join is required for PnL/regime/exit_reason/v2_exit_score.
- **Attribution depth:** Entry/exit join to alpaca_*_attribution is 0% on droplet; loss decomposition and counterfactuals use whatever entry/exit fields are present on exit_attribution and master_trade_log (and optional bar data when available).

---

## 3. Missing Fields (Summary)

| Field / need | Source | Status |
|--------------|--------|--------|
| trade_id, trade_key | exit_attribution, pipeline | Present; trade_key derived in step1. |
| symbol, side, entry/exit time, entry/exit price, PnL | exit_attribution → TRADES_FROZEN | Present. |
| exit_reason, entry_regime, exit_regime, time_in_trade | exit_attribution | Present. |
| v2_exit_score, v2_exit_components | exit_attribution | Present when emitted. |
| MFE/MAE | exit_quality_metrics (exit_attribution) | Best-effort; may be null. |
| Entry composite score / components | master_trade_log or entry attribution | Partial; entry attribution empty on droplet. |
| Bars (OHLCV) | data/bars_cache, Alpaca | Per symbol/date; gaps possible. |

---

## 4. Timestamp Alignment

- **trade_key:** Entry time normalized to UTC, second precision (`alpaca_trade_key.normalize_time`). No subsecond in key.
- **Logs:** entry_timestamp, exit_timestamp, ts may have subsecond; join uses second-precision key.
- **Bars:** Exchange-aligned; cache keyed by symbol/date/resolution.

---

## 5. Corporate Actions & Gaps

- **Corporate actions:** Not explicitly adjusted in pipeline; data used as-is.
- **Gap behavior:** Missing bars → omit trade from bar-based path-real analysis. Missing attribution (alpaca_*) → entry/exit join 0%; lab uses TRADES_FROZEN + exit_attribution fields + master_trade_log where available.

---

## 6. Recommendation for Quant Lab

- **Phase 0 pass:** Data contract and grains are defined (ALPACA_QUANT_DATA_CONTRACT.md). Join coverage against alpaca_*_attribution is 0% on droplet; lab does not depend on that join for core PnL/regime/exit analysis because TRADES_FROZEN is built from the same log that has full exit detail.
- **Fail-closed:** For any analysis that *requires* entry attribution join (e.g. entry-score-only studies), either (a) populate alpaca_entry_attribution and re-run step1, or (b) use master_trade_log/exit_attribution context and document partial coverage. Do not assert “full join coverage” when alpaca_* files are empty.
- **Bar-based work:** Use step2 and bars cache; document trades skipped due to missing bars.
