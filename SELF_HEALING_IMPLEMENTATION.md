# Self-Healing Trading System Implementation Summary

## Overview
This document summarizes the implementation of a self-healing, risk-aware trading service with state persistence, health aggregation, API contract protection, chaos testing, and trade sanity checks.

## Implementation Date
2026-01-10

## Components Implemented

### 1. State Persistence (Risk #6)
**File:** `state_manager.py`

**Purpose:** Persist trading state across restarts to prevent unsafe re-entry.

**Features:**
- Versioned state schema with open positions, PnL, trade timestamps
- Atomic writes to `state/trading_state.json`
- Reconciliation with Alpaca (ground truth)
- Self-healing: detects corruption, moves corrupt file to backup, reconciles with Alpaca
- Refuses to start trading if reconciliation fails

**Integration:**
- Initialized in `StrategyEngine.__init__()` in `main.py`
- State updated after every position open/close
- State loaded and reconciled on startup

### 2. Trade Guard (Risk #15)
**File:** `trade_guard.py`

**Purpose:** Mandatory sanity checks before any order is sent to Alpaca.

**Checks:**
- Max position size per symbol
- Max portfolio exposure / concentration
- Max notional per order
- Direction flip protection
- Price sanity (within configurable % band)
- Cooldown (minimum time between trades)
- Buying power validation

**Integration:**
- Called early in `AlpacaExecutor.submit_entry()` in `main.py`
- All orders must pass `evaluate_order()` before submission
- Rejections logged to `logs/orders.jsonl`

### 3. API Contract Protection (Risk #11)
**Files:** `alpaca_client.py`, `uw_client.py`

**Purpose:** Detect API schema changes early and fail loudly.

**Features:**
- Explicit response contracts for critical endpoints
- Startup compatibility checks
- Error classification: AUTH_ERROR, RATE_LIMIT, NETWORK, SCHEMA_ERROR, UNKNOWN
- Retry logic for transient errors (RATE_LIMIT, NETWORK)
- Fail-fast for non-transient errors (AUTH_ERROR, SCHEMA_ERROR)

**Integration:**
- Compatibility checks run in `deploy_supervisor.py` on startup
- API clients can be used as drop-in replacements for direct API calls

### 4. Aggregated Health (Risk #9)
**File:** `deploy_supervisor.py` (enhanced)

**Purpose:** Prevent "fake green" states where dashboard is up but trading is dead.

**Features:**
- Health registry tracks all services (trading-bot, uw-daemon, dashboard, heartbeat-keeper)
- Per-service status: OK, DEGRADED, FAILED
- Overall system health computation:
  - FAILED if any critical service is FAILED
  - DEGRADED if any critical is DEGRADED or supportive is FAILED
  - OK only if all critical == OK
- Persisted to `state/health.json`
- Self-healing: stops restarting services after N failures in M minutes

**Integration:**
- Dashboard reads `state/health.json` via `/api/system/health` endpoint
- Health displayed in dashboard with overall status badge

### 5. Chaos Testing Hooks (Risk #12)
**File:** `deploy_supervisor.py` (enhanced)

**Purpose:** Deliberately break parts of the system in controlled way for testing.

**Modes:**
- `alpaca_down`: Simulate Alpaca API failures
- `invalid_creds`: Simulate invalid credentials
- `supervisor_crash`: Controlled supervisor crash
- `state_corrupt`: Corrupt state file to test self-heal

**Usage:**
Set `CHAOS_MODE` environment variable (e.g., `CHAOS_MODE=alpaca_down`)

**Safety:**
- Cannot be accidentally enabled in production
- Explicit environment variable required

## Self-Healing Behavior Pattern

### DETECT → CLASSIFY → RESPOND → RECOVER OR HALT SAFELY

1. **Detection:**
   - Supervisor monitors child processes
   - State manager detects corrupt state
   - API adapters detect schema/auth/network issues
   - Trade guard detects order-level insanity

2. **Classification:**
   - **TRANSIENT**: Network, rate-limit, temporary Alpaca outage
   - **PERSISTENT CONFIG**: Missing/invalid creds, bad .env
   - **CODE/SCHEMA**: API drift, state schema incompatibility
   - **LOGIC/RISK**: Trade guard rejections

3. **Response:**
   - **TRANSIENT**: Backoff + retry, within limits. If recovered, log recovery.
   - **PERSISTENT CONFIG or CODE/SCHEMA**: Stop trading. Mark system health as FAILED_CONFIG or FAILED_API_SCHEMA. Do NOT auto-restart into a loop.
   - **LOGIC/RISK**: Reject individual trades, log and continue.

4. **Recovery:**
   - For transient issues: System returns to healthy state without manual intervention.
   - For hard failures: System remains in SAFE HALT mode until human intervention. All failures visible via health.json and dashboard.

## Failure Playbook

### TRANSIENT Errors (Network, Rate Limit)
**What happens:**
- API calls retry with exponential backoff (up to 3 attempts)
- If recovery succeeds: Log recovery event, continue trading
- If all retries fail: Mark service as DEGRADED, log error

**Recovery:**
- Automatic recovery when network/rate limit issues resolve
- No manual intervention required

### PERSISTENT CONFIG Errors (Invalid Credentials, Bad .env)
**What happens:**
- API compatibility check fails on startup
- System marked as FAILED_CONFIG
- Trading halted
- Error logged to health.json and logs

**Recovery:**
- Manual intervention required: Fix credentials in `.env`
- Restart service after fix

### CODE/SCHEMA Errors (API Drift, State Schema Incompatibility)
**What happens:**
- API compatibility check detects schema mismatch
- System marked as FAILED_API_SCHEMA
- Trading halted
- Error logged with full context

**Recovery:**
- Manual intervention required: Update code to match new API schema
- Restart service after fix

### LOGIC/RISK Errors (Trade Guard Rejections)
**What happens:**
- Individual trades rejected by trade guard
- Rejection logged with reason
- Trading continues for other symbols
- No system health impact

**Recovery:**
- Automatic: System continues trading normally
- Review rejection logs to understand why trades were blocked

### State Corruption
**What happens:**
- State manager detects corrupt state file
- Moves corrupt file to backup (`trading_state.json.corrupt.TIMESTAMP`)
- Starts with empty state
- Attempts reconciliation with Alpaca
- If reconciliation fails: System refuses to start trading

**Recovery:**
- If reconciliation succeeds: Automatic recovery, trading resumes
- If reconciliation fails: Manual intervention required to investigate

### Service Repeated Failures
**What happens:**
- Supervisor tracks failure count per service
- After N failures in M minutes: Service marked as FAILED
- Supervisor stops restarting that service
- Overall system health marked as DEGRADED or FAILED

**Recovery:**
- Manual intervention required: Investigate service logs, fix root cause
- Restart service after fix

## Files Modified/Created

### New Files
- `state_manager.py` - State persistence
- `trade_guard.py` - Trade sanity checks
- `alpaca_client.py` - Hardened Alpaca API client
- `uw_client.py` - Hardened UW API client
- `SELF_HEALING_IMPLEMENTATION.md` - This document

### Modified Files
- `deploy_supervisor.py` - Added health registry, aggregated health, chaos hooks, API compatibility checks
- `main.py` - Integrated state_manager and trade_guard
- `dashboard.py` - Added aggregated health display

### State Files Created
- `state/trading_state.json` - Persistent trading state
- `state/health.json` - Aggregated system health

## Configuration

### Environment Variables
- `CHAOS_MODE` - Enable chaos testing (off|alpaca_down|invalid_creds|supervisor_crash|state_corrupt)
- `MAX_POSITION_SIZE_USD` - Max position size per symbol (default: 500)
- `MAX_NOTIONAL_PER_ORDER` - Max notional per order (default: 2000)
- `MAX_PORTFOLIO_EXPOSURE_PCT` - Max portfolio exposure (default: 0.30 = 30%)
- `MAX_CONCENTRATION_PER_SYMBOL_PCT` - Max concentration per symbol (default: 0.15 = 15%)
- `MAX_PRICE_DEVIATION_PCT` - Max price deviation (default: 0.05 = 5%)
- `MIN_COOLDOWN_MINUTES` - Minimum cooldown between trades (default: 5)

## Testing

### Manual Testing
1. **State Corruption Test:**
   ```bash
   echo "{ invalid json }" > state/trading_state.json
   # Restart bot - should self-heal
   ```

2. **Chaos Testing:**
   ```bash
   export CHAOS_MODE=alpaca_down
   # Restart bot - observe behavior
   ```

3. **Trade Guard Test:**
   - Attempt to place order exceeding limits
   - Verify rejection in logs

### Health Monitoring
- Check `state/health.json` for aggregated health
- Check dashboard at `/api/system/health` endpoint
- Monitor logs for self-healing events

## Notes

- All changes are **additive** - no existing logic removed
- Core strategy logic unchanged
- Wallet/P&L/risk math unchanged (except for state persistence)
- Process structure unchanged (deploy_supervisor.py + children)
- Existing logging preserved and extended
- `.env` secrets loading path unchanged

## Future Enhancements

1. **State Migration:** Implement version migration logic for state schema changes
2. **Chaos Test Runner:** Automated script to run chaos tests and validate behavior
3. **Health Metrics:** Add more detailed health metrics (latency, error rates, etc.)
4. **Trade Guard Tuning:** Learn optimal limits from historical data
5. **API Contract Versioning:** Track API versions and warn on mismatches
