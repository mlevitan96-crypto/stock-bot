# Quant appendix — table specifications (strict cohort)

Populate from **trade_facts** (Workstream A). All tables are **strict-scope** unless labeled exploratory.

**Global keys:** `trade_id` (`open_SYM_ISO`), `canonical_trade_id` / `trade_key`, `symbol`, `session_anchor_et` (optional).

---

## A1. trade_facts (master)

Names below match the **framework** spec; aliases in parentheses are equivalent for tooling.

| Column | Type | Source |
|--------|------|--------|
| canonical_trade_id | string | Alias resolution / unified |
| symbol | string | exit_attribution |
| side | long/short | Normalized from exit |
| quantity | float | orders / position |
| intent_timestamp (intent_ts) | datetime | run.jsonl trade_intent / entry_decision_made |
| fill_timestamp (fill_ts) | datetime | orders.jsonl |
| close_timestamp (close_ts) | datetime | exit_attribution.timestamp |
| fill_price (fill_px) | float | orders |
| close_price (close_px) | float | exit |
| fees | float | orders / activities (log proxy if warehouse off) |
| realized_pnl (realized_pnl_usd) | float | exit_attribution / broker-consistent field |
| holding_time (hold_seconds) | float | close − fill |
| maximum_favorable_excursion (mfe_pct or mfe_usd) | float | Bar path or internal high_water — **gap if missing** |
| maximum_adverse_excursion (mae_pct or mae_usd) | float | Same |
| exit_type_or_reason (exit_reason_normalized) | enum | Workstream E mapping |
| signals_present | json / flags | Normalized from exit row + snapshots |
| signal_strengths | json | Per-signal strength where logged |
| signals_json | json | Optional raw bundle for CSA / G |
| entry_score | float | entry_decision_made / metadata |
| intent_to_fill_latency (intent_to_fill_sec) | float | fill − intent |
| slippage_estimate (slippage_est) | float | Define formula (mid vs fill) — **telemetry gap if no mid** |
| blocked | bool | blocked_trades / intent CI |
| blocked_reason | string | |

---

## B1. PnL decomposition (per trade)

| Column | Notes |
|--------|--------|
| pnl_signal_component | Model: entry edge vs exit — **define** |
| pnl_execution_component | Slippage + fees |
| pnl_giveback | MFE − realized (if MFE available) |
| opportunity_cost_flag | Blocked near-miss (provisional) |

---

## C1. Directional summary

| side | n | win_rate | expectancy_usd | p5_pnl | p95_pnl |

---

## D1. Entry quality quadrants

| quadrant | n | sum_pnl | avg_ttfp_sec | avg_mfe | avg_mae | mfe_capture_ratio |

---

## E1. Exit attribution rollup

| exit_bucket | n | sum_pnl | avg_giveback | max_drawdown_contrib |

---

## F1. Blocked / missed (log-native)

| symbol | blocked_at | reason | shadow_signal_strength | notes |

---

## G1. Signal edge map

| signal_key | participation_rate | expectancy_when_present | expectancy_when_absent | long_short_split |

---

## H1. Regime slices

| vol_bucket | trend_bucket | tod_bucket | dow | n | expectancy |

---

## I1. Ten axes (one sheet per axis)

Required views (framework Workstream I):

1. Signal agreement count vs PnL  
2. Signal disagreement penalty  
3. Latency sensitivity  
4. Exit optionality loss  
5. False positive cost per signal  
6. Asymmetry ratio of wins to losses  
7. Loss clustering in time  
8. Regime transition trades  
9. Signal persistence during holding  
10. Anti-signal performance when signal is absent  

Each sheet: definition (SQL/pseudocode), filter, cohort n, primary metric, **HOW** if actionable.

---

## J1. Decision matrix (see separate template)

Row grain: `signal | exit_type | direction | regime_bucket` → KEEP/KILL/GATE/SIZE + rationale + confidence.
