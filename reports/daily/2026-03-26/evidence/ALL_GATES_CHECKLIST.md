# All Gates That Can Prevent Trades (Signal → Execution)

Use this checklist to verify every point that can result in zero orders. When using **INJECT_SIGNAL_TEST=1**, a synthetic cluster (SPY, score 4.0) is injected when normal clusters are 0; the first blocker after injection is the gate preventing trades.

---

## A. run_once() — before decide_and_execute

| # | Gate | Location | Condition to block | How to check on droplet |
|---|------|----------|--------------------|--------------------------|
| A1 | **Freeze** | monitoring_guards.check_freeze_state() | Returns False: governor_freezes.json has active freezes, or performance freeze, or state/health_safe_mode.flag | `cat state/governor_freezes.json`; `test -f state/health_safe_mode.flag` |
| A2 | **Risk limits** | run_risk_checks() | safe_to_trade False (daily loss, drawdown) | logs/run.jsonl risk_freeze; risk_management logs |
| A3 | **Heartbeat staleness** | check_heartbeat_staleness() | Required heartbeats > 30min old (PAPER) | state/heartbeats/*.json last modified |
| A4 | **UW cache empty** | cache_symbol_count == 0 | No symbol keys in data/uw_flow_cache.json | Cache has keys not starting with _ |
| A5 | **Composite score floor** | check_composite_score_floor(clusters) | All clusters below floor | Monitoring alert composite_score_floor_breach |
| A6 | **Broker degraded** | degraded_mode | Reconciliation reported degraded (broker unreachable) | run_once sets degraded_mode from reconciliation |
| A7 | **Not armed** | trading_is_armed() | ALPACA_BASE_URL not paper-api.alpaca.markets | Env ALPACA_BASE_URL; log run_once not_armed_skip_entries |
| A8 | **Not reconciled** | ensure_reconciled() | Executor positions not in sync with broker | log run_once not_reconciled_skip_entries |

---

## B. decide_and_execute() — cycle-level (return [])

| # | Gate | Location | Condition to block |
|---|------|----------|--------------------|
| B1 | **Kill switch** | kill_switch_active() | state/kill_switch.json enabled | `cat state/kill_switch.json` |
| B2 | **Live safety caps** | check_live_safety_caps() | LIVE mode and caps hit (positions, notional) | policy_variants; log gate live_safety_cap |
| B3 | **No clusters** | len(clusters_sorted)==0 | Called with 0 clusters | N/A when using inject test |

---

## C. decide_and_execute() — per-candidate (continue = skip this symbol)

| # | Gate | Log event / _inc_gate | Condition to block |
|---|------|------------------------|--------------------|
| C1 | UW deferred | gate uw_deferred | apply_uw_to_score returned uw_deferred |
| C2 | Regime gate | gate regime_blocked | ENABLE_REGIME_GATING and regime_gate_ticker False |
| C3 | Concentration | gate concentration_blocked_bullish | net_delta_pct > 70% and direction bullish |
| C4 | Theme risk | gate theme_exposure_blocked | ENABLE_THEME_RISK and correlated_exposure_guard |
| C5 | Bad ref price | sizing bad_ref_price | get_last_trade(symbol) <= 0 |
| C6 | Min notional floor | sizing min_notional_floor_reject | actual_notional < MIN_NOTIONAL_USD |
| C7 | Position flip close failed | position_flip close_failed / close_position_not_verified | Opposite position close failed |
| C8 | Max one position per symbol | gate max_one_position_per_symbol | Already have position in symbol (or normalized) |
| C9 | Expectancy gate | gate expectancy_blocked | Score below expectancy floor (V3.2) |
| C10 | Max new positions per cycle | gate max_new_positions_per_cycle_reached | new_positions_this_cycle >= MAX_NEW_POSITIONS_PER_CYCLE |
| C11 | Score below min | gate score_below_min | score < min_score (MIN_EXEC_SCORE or self-healing adjusted) |
| C12 | Displacement blocked/failed | gate displacement_* | Displacement logic blocks or fails |
| C13 | Max positions reached | gate max_positions_reached | len(opens) >= max_positions |
| C14 | Cooldown | gate symbol_on_cooldown | Symbol in executor.cooldowns |
| C15 | Momentum ignition | gate momentum_ignition_blocked | momentum_ignition_filter blocks |
| C16 | Market closed | gate market_closed_block_entry | Market hours check fails |
| C17 | Price sanity | gate price_sanity_blocked_invalid_price | ref_price invalid |
| C18 | Long-only (short blocked) | gate long_only_blocked_short_entry | BLOCK_SHORT_ENTRIES and side sell |
| C19 | High vol no alignment | gate blocked_high_vol_no_alignment | policy_variants directional gate |
| C20 | Invalid entry score | gate invalid_entry_score_blocked | entry_score <= 0 or invalid |

---

## D. submit_entry() — order submission

| # | Gate | Log / return | Condition to block |
|---|------|--------------|--------------------|
| D1 | Asset not shortable | submit_entry asset_not_shortable_blocked | Short entry and symbol not shortable |
| D2 | Trade guard | submit_entry trade_guard_blocked | Trade guard rejected |
| D3 | Spread watchdog | submit_entry spread_watchdog_blocked | Spread > MAX_SPREAD_BPS |
| D4 | Min notional | submit_entry min_notional_blocked | notional < MIN_NOTIONAL_USD |
| D5 | Fractional / price | submit_entry status blocked | Fractional not supported or price too high |
| D6 | Risk validation | submit_entry risk_validation_blocked | Position size / risk check failed |

---

## Injection test result (2026-03-02)

With **INJECT_SIGNAL_TEST=1** and **\_injected_test** bypass (skip UW/survivorship/signal_quality for synthetic cluster):
- **Outcome:** clusters=1, **orders=1** — execution path works; order placed and filled (SPY).
- Blockers identified for **natural** signals: (1) **UW defer** (repair_failed_defer) when UW quality missing; (2) **Expectancy gate** (score_floor_breach) when apply_uw_to_score returns a penalized score so composite_exec_score < MIN_EXEC_SCORE. Fix: ensure real composite scores are above threshold (freshness 180min + conviction 0.5 default) and/or relax UW defer for paper when data is missing.

---

## Injection test (find the blocker)

1. On droplet: set `INJECT_SIGNAL_TEST=1` and optionally `INJECT_SIGNAL_SYMBOL=SPY` in env (e.g. in .env or systemd Environment).
2. Restart the bot so one run_once runs with 0 natural clusters and injects 1 synthetic (SPY, 4.0).
3. After one cycle, check:
   - `logs/run.jsonl` last line: clusters=1, orders=0 or orders=1
   - `logs/gate.jsonl` last entries for symbol SPY: which gate fired
   - `logs/submit_entry.jsonl`: any entry attempt or block reason
   - `logs/worker_debug.log`: "INJECT_SIGNAL_TEST: Injected 1 synthetic cluster"
4. If orders=0, the first gate that logged for that cycle is the blocker.

---

## Droplet one-liner checks

```bash
# Freeze
cat state/governor_freezes.json 2>/dev/null || echo "no freeze file"
test -f state/health_safe_mode.flag && echo "HEALTH_SAFE_MODE ON" || echo "no health_safe_mode"

# Kill switch
cat state/kill_switch.json 2>/dev/null || echo "no kill_switch"

# Armed (paper URL) – check in .env
grep -E "ALPACA_BASE_URL|TRADING_MODE" .env 2>/dev/null

# Recent gate blocks
tail -20 logs/gate.jsonl

# Recent submit_entry
tail -10 logs/submit_entry.jsonl

# Last run
tail -1 logs/run.jsonl
```
