# Trade Data Collection Summary — Profitability Review

**Purpose:** Confirm we collect all data required to review trades for profitability.  
**Droplet check:** Run completed against live droplet (real data).  
**Date:** 2026-03-14.

---

## 1. Goal: Review for Profitability

To support **profitability review** we need, per trade:

| Need | Use |
|------|-----|
| **Realized PnL** (USD and/or %) | Profit/loss outcome |
| **Symbol, side** | Identity and direction |
| **Entry/exit timestamps** | Duration and session |
| **Entry/exit prices, size** | Execution quality and attribution |
| **Exit reason** | Why the trade closed (stop, TP, trail, time, etc.) |
| **Regime / strategy / mode** | Bucketing (governance, replay) |
| **Time in trade** | Hold duration |
| **Exit score / components** | Attribution (which lever drove exit) |
| **MFE/MAE** (optional) | Exit quality (max favorable/adverse excursion) |

---

## 2. What We Collect (by source)

### 2.1 Primary: `logs/exit_attribution.jsonl`

**Droplet:** **2,001 lines** (confirmed). One record per closed trade (v2 equity exits).

**Fields collected (from droplet sample):**

| Field | Purpose for profitability |
|-------|----------------------------|
| `symbol` | Identity |
| `timestamp`, `entry_timestamp`, `entry_ts`, `exit_ts` | Times |
| `exit_reason` | Why closed |
| `pnl`, `pnl_pct` | Realized PnL |
| `entry_price`, `exit_price`, `qty` | Execution / size |
| `time_in_trade_minutes` | Hold duration |
| `entry_uw`, `exit_uw` | Universe/weight context |
| `entry_regime`, `exit_regime`, `regime_label` | Regime bucketing |
| `score_deterioration`, `relative_strength_deterioration` | Deterioration metrics |
| `v2_exit_score`, `v2_exit_components` | Exit pressure and attribution |
| `exit_regime_decision`, `exit_regime_reason`, `exit_regime_context` | Regime at exit |
| `attribution_components` | Per-signal contributions |
| `exit_quality_metrics` | MFE/MAE and related (when present) |
| `trade_id`, `decision_id`, `exit_reason_code` | Ids and codes |
| `direction`, `side`, `position_side` | Direction |
| `mode`, `strategy` | Governance bucketing |
| `replacement_candidate`, `replacement_reasoning` | Replacement context |
| `composite_version`, `variant_id`, `attribution_schema_version` | Versioning |

**Verdict:** **Sufficient for profitability review.** Contains PnL, symbol, side, times, prices, exit reason, regime, strategy, mode, time in trade, exit score/components, and optional MFE/MAE via `exit_quality_metrics`.

---

### 2.2 Secondary: `logs/attribution.jsonl`

**Droplet:** **2,002 lines** (confirmed).

**Fields (from droplet sample):** `ts`, `type`, `trade_id`, `symbol`, `pnl_usd`, `context`, `strategy_id`.

**Use:** Closed-trade PnL and strategy bucketing; day-PnL sums (e.g. experiment_1_status_check_alpaca, verify_day_pnl_on_droplet). Complements exit_attribution for reconciliation and daily rollups.

---

### 2.3 Secondary: `logs/master_trade_log.jsonl`

**Droplet:** **2,337 lines** (confirmed).

**Fields (from droplet sample):** `trade_id`, `symbol`, `side`, `is_live`, `is_shadow`, `composite_version`, `entry_ts`, `exit_ts`, `entry_price`, `exit_price`, `size`, `realized_pnl_usd`, `v2_score`, `entry_v2_score`, `intel_snapshot`, `signals`, `feature_snapshot`, `regime_snapshot`, `exit_reason`, `source`, `timestamp`.

**Use:** EOD canonical bundle (MEMORY_BANK 5.5); dashboard and analytics. Provides realized PnL, prices, size, entry/exit scores, and exit reason — sufficient for profitability review even without exit_attribution.

---

### 2.4 Canonical Alpaca attribution (schema present, not populated on droplet)

| Log | Droplet line count | Sample keys |
|-----|--------------------|-------------|
| `logs/alpaca_entry_attribution.jsonl` | 0 | — |
| `logs/alpaca_exit_attribution.jsonl` | 0 | — |

**Note:** Schema and emitters exist (`docs/ALPACA_ATTRIBUTION_SCHEMA.md`, `src/telemetry/alpaca_attribution_emitter.py`). Exit attribution path writes from `exit_attribution.append_exit_attribution` into `emit_exit_attribution`; on the checked droplet these files are empty. Profitability review does **not** depend on them as long as `exit_attribution.jsonl` and/or `master_trade_log.jsonl` remain authoritative.

---

### 2.5 Other trade-related logs (droplet)

| Log | Line count | Note |
|-----|------------|------|
| `logs/signal_context.jsonl` | 0 | Signal state at decisions; optional for deep attribution. |
| `logs/exits.jsonl` | 0 | Not currently populated. |

---

## 3. Pipeline usage (TRADES_FROZEN.csv)

Step1 of `scripts/alpaca_edge_2000_pipeline.py` builds **TRADES_FROZEN.csv** from `logs/exit_attribution.jsonl` (EXIT_ATTRIBUTION path). CSV columns include: `trade_id`, `trade_key`, `symbol`, `side`, `entry_time`, `exit_time`, `entry_price`, `exit_price`, `realized_pnl_usd`, `exit_reason`, `entry_regime`, `exit_regime`, `v2_exit_score`, `time_in_trade_minutes`. These are derived from the exit attribution record (e.g. `realized_pnl_usd` from `pnl` / `pnl_usd`). So the pipeline’s profitability view is backed by the same data we confirmed on the droplet.

---

## 4. Droplet confirmation summary

- **Method:** `python scripts/audit/collect_trade_data_inventory_on_droplet.py` (uses DropletClient; project_dir `/root/stock-bot`).
- **Result:** Line counts and last-record keys collected for each trade-related log.
- **Findings:**
  - **exit_attribution.jsonl:** 2,001 lines; sample record contains all expected keys (symbol, timestamps, pnl, prices, regime, v2_exit_score, v2_exit_components, exit_quality_metrics, mode, strategy, side, etc.).
  - **attribution.jsonl:** 2,002 lines; structure matches (ts, type, trade_id, symbol, pnl_usd, context, strategy_id).
  - **master_trade_log.jsonl:** 2,337 lines; structure matches (trade_id, symbol, side, realized_pnl_usd, entry_ts, exit_ts, entry_price, exit_price, size, exit_reason, etc.).
  - **alpaca_entry_attribution.jsonl**, **alpaca_exit_attribution.jsonl**, **signal_context.jsonl**, **exits.jsonl:** Present but 0 lines.

---

## 5. Conclusion

- **We are collecting the data required to review for profitability.**  
- **Primary source:** `logs/exit_attribution.jsonl` — contains PnL, symbol, side, entry/exit times and prices, exit reason, regime/strategy/mode, time in trade, v2 exit score and components, and optional MFE/MAE in `exit_quality_metrics`.  
- **Backup / EOD view:** `logs/master_trade_log.jsonl` and `logs/attribution.jsonl` provide overlapping and complementary fields; any of these can support profitability review and reconciliation.  
- **Gaps (non-blocking):** Alpaca canonical entry/exit attribution files and signal_context/exits logs are empty on the droplet; they are not required for the current profitability-review goal.
