# Alpaca Trades Frozen — Dataset Freeze (Phase 1, SRE)

**Mission:** Build large TRADES_FROZEN dataset (≥500 closed trades, prefer ≥2000).  
**Authority:** SRE. READ-ONLY. No execution changes.  
**Date:** 2026-03-18.

---

## 1. Target

- **Minimum:** ≥500 closed trades.
- **Prefer:** ≥2000 (pipeline default max_trades=2000).
- **Source:** `logs/exit_attribution.jsonl` on droplet (or local when synced). Pipeline step1 builds TRADES_FROZEN from this log.

---

## 2. Build Procedure (On Droplet)

1. **Ensure canonical logs exist on droplet:**  
   - `logs/exit_attribution.jsonl` (primary; per TRADE_DATA_COLLECTION_SUMMARY, droplet had 2,001 lines).  
   - Optional: `logs/master_trade_log.jsonl`, `logs/attribution.jsonl`.

2. **Run full Alpaca pipeline (read-only):**  
   ```bash
   cd /root/stock-bot  # or project_dir
   python scripts/alpaca_edge_2000_pipeline.py \
     --max-trades 2000 \
     --min-trades 500 \
     --min-final-exits 500 \
     --allow-missing-attribution \
     --skip-bars \
     --no-telegram
   ```  
   - Use `--allow-missing-attribution` when alpaca_entry_attribution / alpaca_exit_attribution are empty (join coverage 0%); otherwise pipeline fails at step1 (join &lt; 98%).  
   - Omit `--skip-bars` to fetch bars for step2 (TRADE_TELEMETRY, MFE/MAE); use `--bars-rate-limit-safe` (default) to avoid rate limits.

3. **Output directory:** `reports/alpaca_edge_2000_<TS>/`  
   - `TRADES_FROZEN.csv` — canonical closed-trade list.  
   - `INPUT_FREEZE.md` — trade count, hashes, join coverage.  
   - Optional: `TRADE_TELEMETRY.csv` (if step2 ran with bars).

---

## 3. Current State (Local / Last Known)

- **Existing frozen runs (local):** e.g. `reports/alpaca_edge_2000_20260317_1721/` — **36 trades** (below 500). Built with `--allow-missing-attribution`; join coverage 0% (alpaca_* empty).  
- **Droplet (per TRADE_DATA_COLLECTION_SUMMARY):** exit_attribution.jsonl had **2,001 lines**; sufficient to build up to 2000 trades once pipeline is run on droplet with above args.

---

## 4. Validation (Post-Freeze)

| Check | Method |
|-------|--------|
| **trade_key uniqueness** | Count distinct trade_key in TRADES_FROZEN.csv; must equal row count. |
| **Timestamp alignment** | entry_time, exit_time UTC, second precision; entry_time &lt; exit_time. |
| **Gap detection** | For bar-based work: identify trades with overnight/weekend span; tag in TRADE_TELEMETRY or separate pass. |
| **Market-hours correctness** | Entry/exit times fall within expected session (RTH/ETH per config); no hard requirement to drop if outside, but document. |

---

## 5. Fail-Closed

- **Coverage < MEMORY_BANK bar:** If pipeline is run without `--allow-missing-attribution` and join coverage &lt; 98% or trades &lt; min_trades/min_final_exits, pipeline raises and writes ALPACA_JOIN_INTEGRITY_BLOCKER_*.md. For expansion with 0% alpaca_* join, use override and document in ALPACA_TRADES_FROZEN_JOIN_COVERAGE.md.
- **Sample size:** For this expansion block, target ≥500 trades; if droplet run yields &lt;500, document and either re-run when more exits exist or proceed with explicit “below target” caveat.

---

## 6. Artifacts Produced by Pipeline

- `reports/alpaca_edge_2000_<TS>/TRADES_FROZEN.csv`  
- `reports/alpaca_edge_2000_<TS>/INPUT_FREEZE.md`  
- `reports/alpaca_edge_2000_<TS>/TRADE_TELEMETRY.csv` (if step2 run)  
- Optional: ENTRY_ATTRIBUTION_FROZEN.jsonl, EXIT_ATTRIBUTION_FROZEN.jsonl (when alpaca_* populated)
