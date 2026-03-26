# Alpaca Trades Frozen — Join Coverage (Phase 1, SRE)

**Mission:** Validate join coverage for expanded TRADES_FROZEN dataset.  
**Authority:** SRE.  
**Date:** 2026-03-18.

---

## 1. Join Model (Recap)

- **TRADES_FROZEN.csv** is built directly from `logs/exit_attribution.jsonl`. Each row = one closed trade; key = **trade_key** = `{symbol}|{side}|{entry_time_iso}` (UTC, second precision).
- **Entry attribution join:** Match to ENTRY_ATTRIBUTION_FROZEN.jsonl (from `logs/alpaca_entry_attribution.jsonl`). On droplet that file is **empty** → **entry join coverage = 0%**.
- **Exit attribution join:** Match to EXIT_ATTRIBUTION_FROZEN.jsonl (from `logs/alpaca_exit_attribution.jsonl`). On droplet that file is **empty** → **exit join coverage = 0%**.

---

## 2. Expansion Run (With Override)

- To build TRADES_FROZEN with ≥500 (or 2000) trades when alpaca_* files are empty, pipeline must be run with **--allow-missing-attribution** so that step1 does not raise on join coverage &lt; 98%.
- **Trade-level coverage:** 100% of TRADES_FROZEN rows have PnL, times, regime, exit_reason, v2_exit_score from the source log (exit_attribution.jsonl). No second join is required for these fields.
- **Entry-score/component coverage:** Partial; only where master_trade_log or exit_attribution context carries entry score/components. Bar coverage: per step2; missing bars → omit trade from bar-based path-real studies.

---

## 3. Validation Checklist (Post-Freeze)

| Metric | Expected (expansion run) | Action if below |
|--------|---------------------------|------------------|
| trades_total | ≥500 (target ≥2000) | Document; proceed with caveat or re-run when more data. |
| join_coverage_entry_pct | 0% (droplet alpaca_* empty) | Document; use --allow-missing-attribution; do not assert entry-attribution join. |
| join_coverage_exit_pct | 0% (same) | Document; exit detail is on each exit_attribution row used to build CSV. |
| trade_key uniqueness | 100% unique | Fail if duplicates. |
| timestamp alignment | entry &lt; exit, UTC | Flag anomalies. |

---

## 4. MEMORY_BANK Bar

- **Bar (default):** min_join_coverage 98%, min_trades 200, min_final_exits 200.
- **This expansion:** We accept 0% join to alpaca_* for building the frozen list; we do **not** assert lever attribution conclusions that require entry/exit join to canonical Alpaca attribution. PnL/regime/exit_reason/v2_exit_score are fully covered by construction from exit_attribution.jsonl.
