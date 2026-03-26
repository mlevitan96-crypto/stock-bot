# Alpaca Quant Lab — Data Contract & Truth Freeze (SRE-LED)

**Mission:** Phase 0 — Data Truth & Contract Freeze  
**Authority:** SRE (integrity). READ-ONLY: no live or paper execution changes.  
**Date:** 2026-03-18.

---

## 1. Inventory of Alpaca Data Sources

### 1.1 Orders, Fills, Positions

| Source | Location | Grain | Notes |
|--------|----------|--------|--------|
| **Alpaca API (runtime)** | `alpaca_client.py`, `main.py` | order `id`, position `symbol`/`qty`/`side` | REST: `get_orders()`, `get_position(symbol)`, `get_all_positions()`. Not persisted as canonical time-series; used for live state only. |
| **Fills** | Via order status / position close | Per fill event | Inferred from order status updates and close flow; no dedicated fills log. |
| **Positions (open)** | State + Alpaca API | Per symbol | `state/` position metadata; `entry_ts` in metadata is join key for exit. |

**Contract:** Orders/fills are not a primary quant source; closed-trade attribution is.

---

### 1.2 Closed-Trade Attribution (Primary Quant Sources)

| Source | Path | Grain | Schema / Key fields |
|--------|------|--------|----------------------|
| **Exit attribution (primary)** | `logs/exit_attribution.jsonl` | One record per closed trade | `trade_id`, `symbol`, `side`, `entry_timestamp`, `exit_timestamp`/`timestamp`, `entry_price`, `exit_price`, `realized_pnl_usd`/`pnl`, `exit_reason`, `entry_regime`, `exit_regime`, `v2_exit_score`, `v2_exit_components`, `time_in_trade_minutes`, `exit_quality_metrics` (MFE/MAE when present), `attribution_components`, `mode`, `strategy`. |
| **Attribution (PnL rollups)** | `logs/attribution.jsonl` | One record per closed-trade PnL event | `ts`, `type`, `trade_id`, `symbol`, `pnl_usd`, `context`, `strategy_id`. |
| **Master trade log** | `logs/master_trade_log.jsonl` | One record per trade (append at exit) | `trade_id`, `symbol`, `side`, `entry_ts`, `exit_ts`, `entry_price`, `exit_price`, `size`, `realized_pnl_usd`, `v2_score`, `entry_v2_score`, `exit_reason`, `source`, `timestamp`, `intel_snapshot`, `signals`, `feature_snapshot`, `regime_snapshot`. |
| **Alpaca entry attribution (canonical)** | `logs/alpaca_entry_attribution.jsonl` | Per entry | Schema present; **empty on droplet** (see TRADE_DATA_COLLECTION_SUMMARY). |
| **Alpaca exit attribution (canonical)** | `logs/alpaca_exit_attribution.jsonl` | Per exit | Schema present; **empty on droplet**. |

**Verdict:** Profitability and quant analysis use `exit_attribution.jsonl` and/or `master_trade_log.jsonl` as authoritative. Alpaca canonical entry/exit files are optional for current lab.

---

### 1.3 Bars (OHLCV)

| Source | Location | Grain | Resolution |
|--------|----------|--------|------------|
| **Bars cache (pipeline)** | `data/bars_cache/<SYMBOL>/<DATE>_<resolution>.json` | Per symbol, per date, per resolution | 1Min (primary), 5Min, 15Min available |
| **Alpaca API** | `fetch_bars_safe(api, symbol, timeframe, limit)` | Per symbol, time range | 1Min default; used at runtime and by pipeline step2 |
| **Parquet (replay)** | `data/bars/alpaca_daily.parquet`, `data/bars/<YYYY-MM-DD>/<SYMBOL>_1Min.json` | Symbol, date | Used by replay and bar-by-bar studies |

**Contract:** Bar-by-bar and path-real counterfactuals use cached bars; no guessed prices. Pipeline step2 fetches via `src.data.alpaca_bars_fetcher.fetch_bars_cached` with rate-limit safety.

---

### 1.4 Indicators / Signals

| Source | Location | Grain | Notes |
|--------|----------|--------|--------|
| **Composite score (v2)** | Computed at decision time; stored in attribution / master_trade_log | Per trade (entry/exit) | `uw_composite_v2.py`; components in `attribution_components`, `v2_exit_components`. |
| **Feature snapshot** | `master_trade_log.feature_snapshot`, exit_attribution context | Per trade | `telemetry/feature_snapshot.py` — price/volume/regime-derived features. |
| **Regime snapshot** | `state/regime_posture_state.json`, `state/regime_state.json` | Time snapshot | bull/bear/chop/crash; RISK_ON/RISK_OFF/NEUTRAL. Written by `regime_posture_v2`, `regime_detector`. |
| **Market context** | `state/market_context_v2.json` | Time snapshot | premarket/overnight, vol term proxy, market_trend, volatility_regime, risk_on_off. |
| **Symbol risk features** | `state/symbol_risk_features.json` | Per symbol | realized_vol_5d/20d, beta_vs_spy. |
| **UW flow / intel** | `state/uw_cache/`, `state/premarket_intel.json`, `state/postmarket_intel.json` | Symbol / time | Flow conviction, dark pool, etc.; fed into composite. |

**Contract:** Indicators are either stored on the trade record (exit_attribution, master_trade_log) or in state files keyed by time; join to trade via entry_ts/exit_ts and trade_id.

---

### 1.5 Regime Labels

| Source | Path | Values |
|--------|------|--------|
| **Regime posture (v2)** | `state/regime_posture_state.json` | `regime_label`: bull, bear, chop, crash |
| **Regime state (intel)** | `state/regime_state.json` | RISK_ON, RISK_OFF, NEUTRAL, BEAR, MIXED |
| **Structural detector** | `state/regime_detector_state.json` | RISK_ON, NEUTRAL, RISK_OFF, PANIC |
| **Per-trade** | `entry_regime`, `exit_regime` in exit_attribution / TRADES_FROZEN | From snapshot at entry/exit time |

**Contract:** Regime at entry/exit is the regime snapshot at that time; no retroactive relabeling unless replay explicitly overwrites.

---

### 1.6 Market Hours Metadata

| Source | Location | Notes |
|--------|----------|--------|
| **Market open/close** | `main.py`, config, Alpaca | Used for bar staleness, session filters; not a separate log. |
| **Session state** | Implicit in timestamps | UTC; regular/ETH; premarket/postmarket from market_context. |

**Contract:** Time-of-day and session state are derived from timestamps + market hours logic; no separate canonical “market hours” table.

---

## 2. Canonical Grains (Freeze)

### 2.1 Trade Grain

| Grain | Definition | Join usage |
|-------|-------------|------------|
| **trade_id** | Stable identifier for a trade. Format: `open_{symbol}_{entry_ts_iso}` at entry; at exit may be same or `live:{SYMBOL}:{entry_ts_iso}`. | Primary join key in attribution and master_trade_log. |
| **trade_key** | Canonical string: `{symbol}\|{side}\|{entry_time_iso}` (UTC, second precision). Built by `src.telemetry.alpaca_trade_key.build_trade_key`. | Pipeline join key for TRADES_FROZEN ↔ ENTRY/EXIT_ATTRIBUTION_FROZEN. Uniquely identifies a closed trade. |

**Definition:** One **trade** = one position open to close. One row in TRADES_FROZEN = one closed trade.

### 2.2 Position Grain

| Grain | Definition | Join usage |
|-------|-------------|------------|
| **position_id** | Optional; from Alpaca or internal. When present, preferred in `telemetry/snapshot_join_keys.py` for exit join. | Exit snapshot ↔ attribution; many records may not have position_id (trade_id used). |

**Definition:** Open position is identified by symbol + entry_ts (and optionally position_id). No separate “position_close_id” in schema; the close is the same trade_id as the position.

### 2.3 Position Close

- **position_close_id** is not a separate canonical grain. The close event is tied to the same **trade_id** (or **trade_key**). One closed trade = one exit attribution record = one row in TRADES_FROZEN.

---

## 3. Validation Summary

### 3.1 Join Coverage

- **Primary join:** TRADES_FROZEN rows ↔ entry/exit attribution by **trade_key**.
- **Threshold (MEMORY_BANK / pipeline):** min join coverage 98% (entry and exit); min trades 200 (and min final_exits 200). Below = HARD FAILURE; see ALPACA_QUANT_JOIN_COVERAGE.md.

### 3.2 Missing Fields

- **exit_attribution:** All fields required for profitability review are documented in TRADE_DATA_COLLECTION_SUMMARY.md. Optional: MFE/MAE in `exit_quality_metrics` (best-effort).
- **master_trade_log:** Single-append contract; duplicate trade_id guarded in-process.
- **Bars:** Missing symbol/date → no path-real counterfactual for that trade; gap behavior is “omit or fail that trade” in studies.

### 3.3 Timestamp Alignment

- **Entry/exit:** UTC, second precision in trade_key; subsecond in logs allowed but normalized for join.
- **Bars:** Bar timestamps aligned to exchange; cache per symbol/date/resolution.

### 3.4 Corporate Action Handling

- No explicit corporate action adjustment in the documented pipeline. Splits/dividends may affect bar and position data from Alpaca; quant lab uses as-is unless a dedicated adjustment step is added.

### 3.5 Gap Behavior

- **Missing bars:** Pipeline step2 and bar-dependent studies skip or fail that trade for path-real work.
- **Missing attribution:** Join coverage below threshold fails pipeline (unless `--allow-missing-attribution`); lab should run without override for valid conclusions.

---

## 4. Fail-Closed Rule (MEMORY_BANK Bar)

- **Coverage < MEMORY_BANK bar:** If join coverage (entry or exit) is below configured threshold (default 98%) or sample size below min_trades/min_final_exits (default 200), the pipeline raises and writes a blocker; quant lab MUST NOT treat the run as valid for attribution or profit discovery.
- **Truth Gate:** All reports and conclusions require droplet execution and canonical data; only frozen artifacts (e.g. TRADES_FROZEN, frozen attribution) may be used for learning or tuning.

---

## 5. References

- MEMORY_BANK.md §3.4 Truth Gate, §5.5, §7.12 Exit Intelligence, §8.5 Telemetry.
- TRADE_DATA_COLLECTION_SUMMARY.md (reports/audit).
- scripts/alpaca_edge_2000_pipeline.py (step1_build_frozen_dataset, join by trade_key).
- src/telemetry/alpaca_trade_key.py (build_trade_key).
- telemetry/snapshot_join_keys.py (position_id, trade_id, surrogate).
- docs/DATA_CONTRACT_CHANGELOG.md.
