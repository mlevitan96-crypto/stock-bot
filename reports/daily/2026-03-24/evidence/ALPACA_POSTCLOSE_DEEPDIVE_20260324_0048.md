# ALPACA Post-Close Deep Dive — `20260324` `0048` UTC tag

- **TRADING_ROOT:** `/root/stock-bot`
- **Telegram env source:** `systemd:/etc/systemd/system/stock-bot.service+/root/stock-bot/.env`
- **Session window (ET calendar day):** 2026-03-24 → UTC [2026-03-24T04:00:00+00:00, 2026-03-25T04:00:00+00:00)
- **Dry-run:** True

## 1) Data integrity & coverage (SRE + Eng Lead)

### Global row counts (loaded, cap per file 300000)
| Sink | Total | In session window |
|------|------:|------------------:|
| run.jsonl | 2046 | 2046 |
| orders.jsonl | 16442 | 1480 |
| signal_context.jsonl | 1 | 1 |
| blocked_trades.jsonl | 19206 | 5040 |
| exit_attribution.jsonl | 2860 | 209 |

### Session event mix
- trade_intent: **1169** (entered/blocked per decision_outcome field when present)
- exit_intent: **56**
- orders (typed `order`): **1446**
- fills / closed (heuristic type): **0** / **0**

### Deterministic join coverage (session window)
| Cohort | n | canonical_trade_id | decision_event_id | symbol_normalized |
|--------|---|--------------------|--------------------|-----------------|
| orders | 1446 | 0 | 0 | 0 |
| trade_intent | 1169 | 0 | 0 | 0 |
| exit_attribution | 209 | 0 | 0 | time_bucket_id=0 |

**Eng Lead:** schemas are read as-is; missing keys are reported, not imputed.

## 2) PnL deep dive (Quant)

- Exit rows in session with pnl_pct: **209**
- Win / loss count: **101** / **104**
- Mean / median pnl_pct: **0.047530270373674084** / **0.0**

## 3) Correlation & contribution (Quant)

Pearson(v2_exit_component, pnl_pct) — associative only; exit-time leakage risk (CSA).

| feature | n | r |
|---------|---:|---:|
| `v2_exit.regime_shift` | 209 | -0.1704 |
| `v2_exit.sector_shift` | 209 | 0.1591 |
| `v2_exit.sentiment_deterioration` | 209 | 0.1067 |
| `v2_exit.vol_expansion` | 209 | 0.0992 |
| `v2_exit.score_deterioration` | 209 | 0.0122 |

## 4) Blocked trades & opportunity cost (Quant + CSA)

- Blocked rows in session: **5040**
- Top reasons:
  - `displacement_blocked`: 3489
  - `max_positions_reached`: 1336
  - `expectancy_blocked:score_floor_breach`: 153
  - `max_new_positions_per_cycle`: 43
  - `order_validation_failed`: 19
- **Opportunity cost / counterfactual PnL:** not computed (no deterministic post-hoc execution path).

## 5) What-if analysis (Quant + CSA)

- **Status:** not executed — would require replay with frozen bars and promotion-safe simulator.
- **NOT PROMOTED** for live behavior changes from this section.

## 6) CI / infra incidents (SRE)

- Local `.github/`: **not present on droplet (expected)**
- Review `journalctl -u stock-bot.service` / disk manually if incidents suspected (not scraped here).

## 7) Board recommendations (Board)

1. Unblock CSA: backfill or enable join keys for the post-close session window before promotion use.
2. Treat offline attribution as narrative-only until join coverage meets MEMORY_BANK contract.
3. Re-run this job after next session once emitters populate keys.

## 8) CSA approval gate (CSA)

- **APPROVED_PLAN:** **NO**

### CSA join blockers (FAIL CLOSED)

- Session orders present but zero canonical_trade_id and zero decision_event_id
- Session trade_intent rows present but zero join keys
- Session exit_attribution rows present with activity but zero canonical_trade_id/decision_event_id

Deterministic joins on canonical keys are required for attribution-grade post-close sign-off.
---
- Reports: `ALPACA_POSTCLOSE_DEEPDIVE_20260324_0048.md`, `ALPACA_POSTCLOSE_SUMMARY_20260324_0048.md`
- **No live trading changes made.**

