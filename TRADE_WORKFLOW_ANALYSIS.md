# Comprehensive Trade Workflow Analysis

## Complete Workflow: Signal → Trade Execution

### Workflow Steps:

1. **Bot Loop (`run_once()` function)**
   - Checks freeze state → Returns early if frozen
   - Checks risk limits → Returns early if breached
   - Reads UW cache (or polls API)
   - Clusters signals
   - Runs composite scoring
   - Calls `decide_and_execute()`

2. **Decision & Execution (`decide_and_execute()` function)**
   - Checks `trading_is_armed()` → Skips if not armed
   - Checks reconciliation → Skips if not reconciled
   - For each cluster:
     - Regime gate check
     - Concentration gate (>70% long-delta blocks bullish)
     - Theme risk gate
     - Composite score calculation
     - Expectancy gate (V3.2)
     - Score threshold gate
     - Cooldown gate
     - Position exists gate (already positioned)
     - Momentum ignition filter
     - Spread watchdog
     - Size validation
     - Calls `submit_entry()`

3. **Order Submission (`submit_entry()` function)**
   - Spread watchdog check
   - Size validation (MIN_NOTIONAL_USD)
   - Limit order attempts (with backoff)
   - Market order fallback
   - Logs to `order.jsonl`

4. **Order Execution (Alpaca API)**
   - API call to `submit_order()`
   - Errors logged to `critical_api_failure.log`
   - Successful orders appear as positions

## Key Gates That Can Block Trades:

1. **Freeze State** (`state/freeze_active.json`)
2. **Risk Limits** (Daily loss, drawdown)
3. **Trading Armed** (`trading_is_armed()` - checks TRADING_MODE vs endpoint)
4. **Reconciliation** (`ensure_reconciled()`)
5. **Regime Gate** (`regime_gate_ticker()`)
6. **Concentration Gate** (net_delta_pct > 70% blocks bullish)
7. **Theme Risk** (MAX_THEME_NOTIONAL_USD)
8. **Expectancy Gate** (V3.2 - minimum expected value)
9. **Score Threshold** (`MIN_EXEC_SCORE` or stage-based)
10. **Cooldown** (COOLDOWN_MINUTES_PER_TICKER)
11. **Position Exists** (already have position)
12. **Momentum Ignition** (momentum_ignition_filter)
13. **Spread Watchdog** (MAX_SPREAD_BPS > 50)
14. **Min Notional** (MIN_NOTIONAL_USD)
15. **API Errors** (client_order_id uniqueness, etc.)

## Diagnostic Checklist:

- [ ] Is `run_once()` being called?
- [ ] Is freeze state blocking?
- [ ] Are risk limits blocking?
- [ ] Is `trading_is_armed()` returning False?
- [ ] Is reconciliation failing?
- [ ] Are signals being generated?
- [ ] Are clusters being created?
- [ ] Is composite scoring generating signals?
- [ ] Which gates are blocking?
- [ ] Are orders being submitted?
- [ ] Are API calls succeeding?
