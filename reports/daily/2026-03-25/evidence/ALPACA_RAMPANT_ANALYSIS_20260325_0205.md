# ALPACA Rampant Analysis — `20260325_0205`

- **TRADING_ROOT:** `/root/stock-bot`
- **Generated (UTC):** 2026-03-25T00:15:49.816067+00:00

## Phase 0 — Baseline & safety (SRE + CSA)

- **git HEAD:** `28abc2a33e365caa58736b99a175ae360f9d1447` (rc=0)
- **stock-bot.service:** `active`
- **uw-flow-daemon.service:** `active`
- **Writes:** only this file and `ALPACA_RAMPANT_SUMMARY_<tag>.md` under `reports/` (plus this script if uploaded separately).
- **Memory Bank canonical section:** **PASS** — ok
- **Governance artifacts present:** offline audit + closure proof (20260325_0112): **YES**

## Phase 1 — Maximal attribution dataset

### Source row counts (cap per file: 200000)

| Sink | Rows |
|------|------|
| `logs/run.jsonl` | 2052 |
| `logs/orders.jsonl` | 16442 |
| `logs/signal_context.jsonl` | 1 |
| `state/blocked_trades.jsonl` | 19206 |
| `logs/exit_attribution.jsonl` | 2860 |

### Deterministic join coverage (canonical keys only)

| Metric | Count |
|--------|------:|
| orders_with_canonical_trade_id | 0 |
| orders_with_decision_event_id | 0 |
| trade_intent_with_canonical_trade_id | 0 |
| trade_intent_with_decision_event_id | 0 |
| exit_attribution_indexed_by_trade_key | 2855 |
| **entry_snapshot × exit pnl (canonical_trade_id)** | 0 |

### Economics field presence (orders.jsonl)
- Rows with explicit fee/slippage schema fields: **0** / 14551 typed `order`
- **Excluded:** silent fees; use `fee_excluded_reason` on paper per attribution contract.

## Phase 2 — Rampant edge search (parallel lanes)

### A) Feature-level attribution (exit_attribution components + quality)

| rank | feature | n | delta_mean_pnl_pct | lane |
|------|---------|---|---------------------|------|
| 1 | `v2_exit.vol_expansion` | 2857 | -0.0941612 | exit_attribution |
| 2 | `v2_exit.score_deterioration` | 2857 | -0.0182795 | exit_attribution |
| 3 | `v2_exit.regime_shift` | 2857 | -0.010156 | exit_attribution |
| 4 | `v2_exit.sentiment_deterioration` | 2857 | -0.00886449 | exit_attribution |
| 5 | `v2_exit.sector_shift` | 2857 | -0.0069974 | exit_attribution |
| 6 | `v2_exit.darkpool_deterioration` | 2857 | 0 | exit_attribution |
| 7 | `v2_exit.earnings_risk` | 2857 | 0 | exit_attribution |
| 8 | `v2_exit.flow_deterioration` | 2857 | 0 | exit_attribution |
| 9 | `v2_exit.overnight_flow_risk` | 2857 | 0 | exit_attribution |
| 10 | `v2_exit.thesis_invalidated` | 2857 | 0 | exit_attribution |

### B) Exit-first failure analysis

- Trades with pnl_pct < 0: **1624**; pnl_pct > 0: **1197**
- **losers** — mean MAE%: None, mean MFE%: None (coverage n_mae=0, n_mfe=0)
- **winners** — mean MAE%: None, mean MFE%: None (coverage n_mae=0, n_mfe=0)

### C) Regime segmentation (hour-of-exit vs mean pnl)

| hour_utc | n | mean_pnl_pct |
|----------|---|--------------|
| 13 | 47 | -0.0135782 |
| 14 | 502 | -0.164174 |
| 15 | 397 | 0.0134164 |
| 16 | 566 | -0.0857136 |
| 17 | 363 | -0.0746939 |
| 18 | 408 | -0.000647881 |
| 19 | 458 | -0.21706 |
| 20 | 117 | -0.142472 |

**Vol expansion vs pnl (quartile lift):**
- lift=-0.0941612 n=2857

### D) Opportunity cost — blocked ledger

- **Blocked rows analyzed:** 19206
- **Top block reasons:**
  - `displacement_blocked`: 14400
  - `max_positions_reached`: 3933
  - `expectancy_blocked:score_floor_breach`: 421
  - `max_new_positions_per_cycle`: 250
  - `order_validation_failed`: 201
  - `symbol_on_cooldown`: 1
- **Score distribution (blocked):** mean=4.722995043215661 n=19206
- **Counterfactual PnL:** not joined (would require deterministic post-hoc price path); **pending** per MEMORY_BANK frozen-artifact rules.

### E) Robustness & mirage detection

- **Walk-forward split:** n1=1429 n2=1429 (by row order in exit_attribution file = time proxy; **not** guaranteed pure time sort — CSA flag).
- **Top |lift| feature (first_half):** `score_deterioration` delta=0.159658
- **Top |lift| feature (second_half):** `vol_expansion` delta=-0.122628
- **Stability:** top feature **differs** across halves → high mirage risk.
- **Leakage:** exit-time components vs realized pnl — causal direction ambiguous; **NOT PROMOTED**.


## Phase 3 — Board review

### Quant verdict
- **Top offline candidates:** see Lane A table (exit components + entry snapshot joins where `canonical_trade_id` matched).
- **Effect sizes:** quartile mean pnl delta; interpret as associative only.
- **Entry vs exit:** `entry_fs.*` rows come from joined `trade_intent` × `exit_attribution` only.

### SRE verdict
- **Join integrity:** indexes built only on `canonical_trade_id`, `decision_event_id`, and `build_trade_key(symbol, side, entry_timestamp)` for exit rows — **no** same-bar heuristic symbol joins.
- **Reproducibility:** command in Phase 4.
- **Sink corruption:** not scanned byte-by-byte; JSONL parse errors skipped (count implicit in row totals).

### CSA verdict
- **Mirages rejected:** constant components, leakage-prone exit→pnl correlations, unstable walk-forward names.
- **SHORTLIST for future live confirmation:** top 5 rows in Lane A with |lift|>0 and n≥500 (if any); else **none** until more keyed data.
- **NOT PROMOTED:** all findings **OFFLINE ONLY**.

## Phase 4 — Live-ready prep (no changes executed)

- **Emitters:** aligned with MEMORY_BANK `Alpaca attribution truth contract (canonical)`; restart `stock-bot.service` after code changes (documented; **not** restarted in this mission).
- **Tomorrow:** market-open cycles append new keyed rows; joins improve as `canonical_trade_id` / `decision_event_id` populate.

```bash
cd /root/stock-bot && TRADING_BOT_ROOT=/root/stock-bot ./venv/bin/python3 scripts/alpaca_rampant_analysis_mission.py
```

