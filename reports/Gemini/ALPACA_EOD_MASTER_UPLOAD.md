# Alpaca EOD Master Upload — Commander Brief

**Generated (local ingest):** 2026-05-01 (artifacts pulled from droplet `alpaca` after pipeline run).  
**Session anchor (droplet):** `PERF_TODAY_DATE=2026-05-01` (UTC calendar day used for perf / counterfactual / shadow deep dive).  
**Sources:** `reports/Gemini/alpaca_ml_cohort_flat.csv`, `reports/PERF_TODAY_*.json`, `reports/audit/counterfactual_blocked_intents_20260501.json`, `SHADOW_VS_LIVE_DEEP_DIVE.md` (2026-05-01), droplet `/tmp/eod_*.log`.

---

## 1. ML cohort flat (`alpaca_ml_cohort_flat.csv`)

| Metric | Value |
| --- | ---: |
| **Total rows** (closed cohort rows written by flattener) | **549** |
| **Win rate** (% of rows with `realized_pnl_usd` > 0) | **32.79%** (180 wins / 355 losses / 14 flat) |
| **Total realized PnL** (sum of `realized_pnl_usd`) | **-126.69 USD** |

**Flattener run (droplet):** `entry_snapshot_join_pct: 67.03 (368/549)`; `scoreflow_total_score_populated_pct: 100%`; `floor_epoch=1777075199.0`.

**Cross-check (same-day attribution slice, not identical to ML cohort):** `PERF_TODAY_RAW_STATS.json` reports **343** closed attributions, **net_pnl_usd -48.80**, **win_rate_pct 35.28** — different join window vs strict-epoch ML export; both retained for Commander context.

---

## 2. Veto counterfactuals & veto impact report

### 2a. Requested scripts (not in repo on droplet)

The following commands were executed on the droplet; **both files are absent** from `main`:

```
python3: can't open file '/root/stock-bot/scripts/resolve_veto_counterfactuals.py': [Errno 2] No such file or directory
python3: can't open file '/root/stock-bot/scripts/veto_impact_report.py': [Errno 2] No such file or directory
```

Raw logs: `reports/Gemini/droplet_eod_logs/eod_resolve_veto.log`, `eod_veto_impact.log`.

### 2b. Substitute — blocked-intent bar counterfactual (`counterfactual_blocked_intents_day.py`)

Full JSON written on droplet: `reports/audit/counterfactual_blocked_intents_20260501.json` (copy under `reports/Gemini/`).

**Cohort:** `all_blocked_today` — **779** blocked `trade_intent` rows for **2026-05-01**, **766** graded on forward **60m** signed return vs 1m bars.

| Field | Value |
| --- | ---: |
| Win rate (60m forward, signed) | 44.13% |
| Mean signed return 60m | -0.0139% |
| Median signed return 60m | -0.0377% |
| Wins / losses / flat | 338 / 418 / 10 |

### 2c. Substitute — “veto impact” style table from **gate = `blocked_reason`** (`PERF_TODAY_SIGNALS.json`)

*Not* dollar Missed Profit / Avoided Loss (those require the missing scripts + fill simulation). Below is **Count** by primary gate label for the session.

| Gate (`blocked_reason`) | Count |
| --- | ---: |
| offense_streak_two_losses_30m | 529 |
| max_one_position_per_symbol | 147 |
| offense_gate_blocked_rs_and_vwap | 59 |
| market_closed | 12 |
| displacement_failed | 11 |
| v2_agent_veto | 9 |
| portfolio_exposure_exceeds_limit_* (8 distinct threshold strings, 1 each) | 8 |
| cooldown_not_met_* | 4 |
| *(other single-count exposure lines)* | *(see JSON)* |

**Trade intent summary:** entered **157**, blocked **779**, total intents **936**.

---

## 3. Shadow vs live PnL (today’s session — `2026-05-01`)

Source: `SHADOW_VS_LIVE_DEEP_DIVE.md` (excerpt of top-line table).

| Metric | LIVE | SHADOW | DELTA (SHADOW − LIVE) |
| --- | ---: | ---: | ---: |
| Total trades (closed) | 366 | 0 | −366 |
| PnL realized (USD) | **-71.57** | **0.00** | +71.57 |
| Win rate (closed) | 35.25% | 0.00% | −35.25% |
| Expectancy (USD/trade, closed) | -0.1955 | 0.0000 | +0.1955 |

**Interpretation:** v2-only mode — **separate shadow trading tape is not present** (`logs/shadow_trades.jsonl` not applicable). Shadow **telemetry** (e.g. Challenger / ML flags on `trade_intent`) still exists in logs, but **shadow lane does not produce parallel fills or PnL** in this build. Commander should treat **SHADOW PnL = 0** as “not running a funded shadow book,” not as proof shadow would have been flat.

---

## 4. Pipeline log index (droplet → local)

| Artifact | Local path |
| --- | --- |
| ML flattener stdout | `reports/Gemini/droplet_eod_logs/eod_flattener.log` |
| Counterfactual stdout | `reports/Gemini/droplet_eod_logs/eod_counterfactual.log` |
| Perf today | `reports/Gemini/droplet_eod_logs/eod_perf_today.log` |
| Shadow deep dive | `reports/Gemini/droplet_eod_logs/eod_shadow_vs_live.log` |

---

## 5. Commander — three gate takeaways (from substitute veto table + counterfactual)

1. **`offense_streak_two_losses_30m` (529 blocks)** — Dominant friction: after two losses in 30 minutes the engine stood down aggressively; this is the single largest “why we did not trade” bucket for the session.  
2. **`max_one_position_per_symbol` (147 blocks)** — Second-largest: rotation / concentration policy capped repeated symbols despite flow; worth reviewing overlap with the lowered **0.30** entry threshold (many intents, few slots).  
3. **Bar counterfactual on **all** blocked intents (~44% forward “wins” at 60m, mean return slightly negative)** — Slightly **loss-avoiding** on average in a 60m bar proxy, but with **material opportunity cost** in the right tail; the missing `resolve_veto_counterfactuals` / `veto_impact_report` pair should be added to the repo if the Commander wants **Missed Profit / Avoided Loss in USD** per gate.
