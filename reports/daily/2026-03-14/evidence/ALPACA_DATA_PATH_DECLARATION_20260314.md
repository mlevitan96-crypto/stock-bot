# ALPACA — Canonical Data Path Declaration

**Mission:** DATA PATH INTEGRITY & SIGNAL GRANULARITY CONFIRMATION  
**Phase:** 0 — Canonical path declaration (freeze assumptions)  
**Timestamp:** 20260314  
**Repo commit:** `2e4f5d4d42545b34e59993477fb650b252c7638a`

---

## Primary source (profitability & tuning)

| Logical name | Repo-relative path | Droplet absolute path |
|--------------|--------------------|-------------------------|
| Exit attribution (closed trades) | `logs/exit_attribution.jsonl` | `/root/stock-bot/logs/exit_attribution.jsonl` |

---

## Secondary sources

| Logical name | Repo-relative path | Droplet absolute path |
|--------------|--------------------|-------------------------|
| Master trade log | `logs/master_trade_log.jsonl` | `/root/stock-bot/logs/master_trade_log.jsonl` |
| Attribution (closed PnL rollups) | `logs/attribution.jsonl` | `/root/stock-bot/logs/attribution.jsonl` |

---

## Pipeline consumer

| Component | Path | Role |
|-----------|------|------|
| Pipeline script | `scripts/alpaca_edge_2000_pipeline.py` | Step 1 reads primary source, builds frozen dataset |
| Step 1 default exit input | `--exit-log` default: `REPO/logs/exit_attribution.jsonl` | Source for TRADES_FROZEN.csv |
| Step 1 output | `reports/dataset_<TS>/TRADES_FROZEN.csv` | Frozen trade rows (trade_key, PnL, regime, etc.) |
| Entry attribution (optional join) | `logs/alpaca_entry_attribution.jsonl` | Optional; used for join coverage when present |
| Exit attribution canonical (optional) | `logs/alpaca_exit_attribution.jsonl` | Optional; frozen copy used for join when present |

---

## Assumptions (frozen)

1. **Primary** for profitability and tuning is `logs/exit_attribution.jsonl`. All pipeline Step 1 CSV output is derived from this file.
2. **Secondary** sources are used for reconciliation, day-PnL, and EOD views; they are not the default Step 1 input.
3. Pipeline does **not** overwrite or modify the primary/secondary logs; it only reads them and writes to `reports/dataset_<TS>/`.
4. Join key is **trade_key** = `symbol|side|entry_time_iso` (UTC, second precision). See `src/telemetry/alpaca_trade_key.py` and `docs/ALPACA_TRADE_KEY_CONTRACT.md`.
