# Comprehensive Trade Workflow Review - Why Trades Aren't Happening

## Date: 2026-01-05

## Executive Summary

This document provides a complete review of the trade workflow from signal generation to order execution, identifying all potential blocking points and diagnostic steps.

## Complete Trade Workflow

### Phase 1: Bot Loop (`run_once()` function)

**Location:** `main.py` line ~5666

**Steps:**
1. **Freeze State Check** (line ~5679)
   - Checks `state/freeze_active.json`
   - **BLOCKER:** If frozen, returns early with 0 orders
   - **Diagnostic:** Check if freeze file exists

2. **Risk Management Checks** (line ~5776)
   - Calls `risk_management.run_risk_checks()`
   - **BLOCKER:** If `safe_to_trade = False`, returns early
   - **Diagnostic:** Check risk management logs

3. **Heartbeat Staleness Check** (line ~5805)
   - Checks if modules are responsive
   - **BLOCKER:** May trigger auto-heal, but doesn't block trading directly

4. **UW Data Collection** (line ~5819-5978)
   - Reads from UW cache (or polls API if cache empty)
   - Builds maps: `gex_map`, `dp_map`, `net_map`, `vol_map`, `ovl_map`
   - **BLOCKER:** If no cache and no API access, clusters = []
   - **Diagnostic:** Check cache size, signal generation

5. **Signal Clustering** (line ~5993)
   - Calls `cluster_signals(all_trades)`
   - **BLOCKER:** If no trades, clusters = []
   - **Diagnostic:** Check `logs/signals.jsonl`

6. **Composite Scoring** (line ~6002-6192)
   - For each symbol in cache, runs composite scoring
   - Creates synthetic clusters from composite scores
   - **BLOCKER:** If composite scores don't pass gate, no clusters
   - **Diagnostic:** Check composite scoring logs, gate rejections

7. **Trading Armed Check** (line ~6229)
   - Calls `trading_is_armed()`
   - **BLOCKER:** If False, orders = [] (skips execution)
   - **Diagnostic:** Check TRADING_MODE, ALPACA_BASE_URL mismatch

8. **Reconciliation Check** (line ~6231)
   - Calls `ensure_reconciled()`
   - **BLOCKER:** If False, orders = [] (skips execution)
   - **Diagnostic:** Check reconciliation logs

9. **Decision & Execution** (line ~6250-6254)
   - Calls `engine.decide_and_execute(clusters, ...)`
   - **Diagnostic:** Check how many clusters passed, what orders were returned

### Phase 2: Decision & Execution (`decide_and_execute()` function)

**Location:** `main.py` line ~4585

**For each cluster, checks multiple gates:**

1. **Regime Gate** (line ~4645)
   - `regime_gate_ticker(prof, market_regime)`
   - **BLOCKER:** If False, `continue` (skip cluster)

2. **Concentration Gate** (line ~4649)
   - Checks `net_delta_pct > 70%` for bullish entries
   - **BLOCKER:** If portfolio > 70% long-delta, blocks bullish
   - **Diagnostic:** Check concentration gate logs

3. **Theme Risk Gate** (line ~4662)
   - `correlated_exposure_guard()`
   - **BLOCKER:** If theme exposure > MAX_THEME_NOTIONAL_USD, `continue`

4. **Composite Score Calculation** (line ~4670-4730)
   - Calculates final score
   - Applies regime/macro multipliers
   - **Diagnostic:** Check score calculation logs

5. **Position Flip/Exists Check** (line ~4868-4903)
   - Checks if position already exists
   - **BLOCKER:** If exists in same direction, `continue`
   - **Action:** If exists in opposite direction and score >= 4.0, flips position

6. **Expectancy Gate (V3.2)** (line ~4905-4973)
   - `ExpectancyGate.should_enter()`
   - **BLOCKER:** If `should_trade = False`, `continue`
   - **Diagnostic:** Check expectancy gate logs, gate_reason

7. **Cycle Position Limit** (line ~4977)
   - `MAX_NEW_POSITIONS_PER_CYCLE = 6`
   - **BLOCKER:** If limit reached, `continue`

8. **Score Threshold Gate** (line ~4988-5027)
   - `MIN_EXEC_SCORE = 2.0` (default, can be adjusted by stage)
   - Bootstrap stage: `min_score = 1.5`
   - Self-healing threshold adjustments
   - **BLOCKER:** If `score < min_score`, `continue`
   - **Diagnostic:** Check score vs threshold logs

9. **Cooldown Gate** (line ~5042)
   - `COOLDOWN_MINUTES_PER_TICKER = 15`
   - **BLOCKER:** If symbol traded recently, `continue`

10. **Momentum Ignition Filter** (line ~5141)
    - `check_momentum_before_entry()`
    - **BLOCKER:** If `passed = False`, `continue`

11. **Size Validation** (line ~5178)
    - Checks buying power, position size
    - **BLOCKER:** If insufficient buying power, `continue`

12. **Execution Router (V3.2)** (line ~5234)
    - Selects execution strategy
    - **Diagnostic:** Check execution router logs

13. **Order Submission** (line ~5313)
    - Calls `submit_entry()`
    - **Diagnostic:** Check order logs, API failures

### Phase 3: Order Submission (`submit_entry()` function)

**Location:** `main.py` line ~3085

**Steps:**
1. **Spread Watchdog** (line ~3099)
   - Checks if spread > MAX_SPREAD_BPS (50)
   - **BLOCKER:** If spread too wide, returns error

2. **Min Notional Check** (line ~3111)
   - `notional = qty * ref_price`
   - **BLOCKER:** If `notional < MIN_NOTIONAL_USD` (100), returns error

3. **Risk Validation** (line ~3118)
   - Checks order size against risk limits
   - **BLOCKER:** If validation fails, returns error

4. **Limit Order Submission** (line ~3177)
   - Attempts limit order with backoff retries
   - **BLOCKER:** API errors (logged to `critical_api_failure.log`)
   - **FIXED:** client_order_id uniqueness issue

5. **Market Order Fallback** (line ~3467)
   - Falls back to market order if limit fails
   - **BLOCKER:** API errors

## Key Configuration Values

- `MIN_EXEC_SCORE = 2.0` (default threshold)
- `MAX_SPREAD_BPS = 50` (spread watchdog)
- `MIN_NOTIONAL_USD = 100` (minimum order size)
- `COOLDOWN_MINUTES_PER_TICKER = 15` (cooldown period)
- `MAX_NEW_POSITIONS_PER_CYCLE = 6` (cycle limit)
- `MAX_THEME_NOTIONAL_USD` (theme exposure limit)

## Diagnostic Checklist

Run this comprehensive check:

1. **Freeze State**
   ```bash
   test -f state/freeze_active.json && echo "FROZEN" || echo "NOT FROZEN"
   ```

2. **Run Once Activity**
   ```bash
   grep -c "run_once" logs/system.jsonl
   tail -5 logs/system.jsonl | grep run_once
   ```

3. **Signal Generation**
   ```bash
   tail -5 logs/signals.jsonl
   ```

4. **Clusters Created**
   ```bash
   grep -c "cluster\|composite" logs/system.jsonl | tail -10
   ```

5. **Gate Blocks**
   ```bash
   grep "blocked\|BLOCKED" logs/trading.jsonl | tail -10
   ```

6. **Orders Submitted**
   ```bash
   tail -10 logs/order.jsonl
   ```

7. **API Failures**
   ```bash
   tail -10 logs/critical_api_failure.log
   ```

8. **Trading Armed**
   - Check: TRADING_MODE vs ALPACA_BASE_URL
   - Check: LIVE_TRADING_ACK if LIVE mode

9. **Alpaca Positions**
   - Check: Current positions via API

## Common Blocking Scenarios

1. **Freeze Active** → Check `state/freeze_active.json`
2. **Not Armed** → Check TRADING_MODE/URL mismatch
3. **No Signals** → Check UW cache, signal generation
4. **Gates Blocking** → Check gate logs in `logs/trading.jsonl`
5. **Score Too Low** → Check MIN_EXEC_SCORE, composite scores
6. **Cooldown Active** → Check cooldown timestamps
7. **API Errors** → Check `critical_api_failure.log`
8. **Concentration Limit** → Check net_delta_pct
9. **Theme Risk Limit** → Check theme exposure
10. **Expectancy Gate** → Check expectancy calculations

## Next Steps

1. Run comprehensive diagnostics on droplet
2. Check each gate systematically
3. Review logs for blocking reasons
4. Identify the specific gate/reason blocking trades
5. Fix or adjust the blocking condition
