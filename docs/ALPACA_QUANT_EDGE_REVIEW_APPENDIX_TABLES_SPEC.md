# Quant appendix — table specifications (strict cohort)

Populate from **trade_facts** (Workstream A). All tables are **strict-scope** unless labeled exploratory.

**Global keys:** `trade_id` (`open_SYM_ISO`), `canonical_trade_id` / `trade_key`, `symbol`, `session_anchor_et` (optional).

---

## A1. trade_facts (master)

| Column | Type | Source |
|--------|------|--------|
| canonical_trade_id | string | Alias resolution / unified |
| symbol | string | exit_attribution |
| side | long/short | Normalized from exit |
| quantity | float | orders / position |
| intent_ts | datetime | run.jsonl trade_intent / entry_decision |
| fill_ts | datetime | orders.jsonl |
| close_ts | datetime | exit_attribution.timestamp |
| fill_px | float | orders |
| close_px | float | exit |
| fees | float | orders / activities (log proxy if warehouse off) |
| realized_pnl_usd | float | exit_attribution / broker-consistent field |
| hold_seconds | float | close_ts − fill_ts |
| mfe_pct | float | Requires bar path or internal high_water — **gap if missing** |
| mae_pct | float | Same |
| exit_reason_normalized | enum | Workstream E mapping |
| signals_json | json | exit row + snapshots |
| entry_score | float | entry_decision_made / metadata |
| intent_to_fill_sec | float | fill_ts − intent_ts |
| slippage_est | float | Define formula (mid vs fill) — **telemetry gap if no mid** |
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

Each sheet: definition SQL/pseudocode, filter, cohort n, primary metric, **HOW** if actionable.

---

## J1. Decision matrix (see separate template)

Row grain: `signal | exit_type | direction | regime_bucket` → KEEP/KILL/GATE/SIZE + rationale + confidence.
