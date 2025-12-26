# Comprehensive Trading Failure Points Analysis

**Date:** 2025-12-26  
**Purpose:** Document ALL possible failure points that prevent trading  
**Status:** Living Document - Must be updated when new failure points are discovered

## Executive Summary

This document catalogs **every single point** in the trading flow where trading can be blocked or prevented. Each failure point must have:
1. Detection mechanism
2. Self-healing capability
3. Dashboard visibility
4. Test harness verification

---

## Failure Point Categories

### Category 1: Data & Signal Generation
### Category 2: Scoring & Evaluation
### Category 3: Gates & Filters
### Category 4: Execution & Broker
### Category 5: State & Configuration
### Category 6: System & Infrastructure

---

## CATEGORY 1: DATA & SIGNAL GENERATION

### FP-1.1: UW Daemon Not Running
**Location:** `uw_flow_daemon.py`  
**Impact:** No data → No signals → No trades  
**Detection:**
- Process check: `pgrep -f uw_flow_daemon`
- Cache file age: `data/uw_flow_cache.json` last modified
- Heartbeat check: `heartbeat_keeper.py`

**Self-Healing:**
- `heartbeat_keeper.py` should restart daemon
- Systemd auto-restart on failure

**Dashboard:** ✅ Health status shows daemon status

**Test:** Inject daemon stop, verify restart

---

### FP-1.2: UW Cache File Missing or Empty
**Location:** `data/uw_flow_cache.json`  
**Impact:** `read_uw_cache()` returns empty → No clusters → No trades  
**Detection:**
- File existence check
- File size check (should be > 0)
- Symbol count check (should have symbols)

**Self-Healing:**
- Verify daemon is running
- Restart daemon if cache empty

**Dashboard:** ✅ Cache status, symbol count

**Test:** Delete cache file, verify recreation

---

### FP-1.3: UW Cache Stale (> 10 minutes old)
**Location:** `data/uw_flow_cache.json` metadata  
**Impact:** Stale data → Poor signals → No trades  
**Detection:**
- Check `_metadata.last_update` timestamp
- Alert if > 10 minutes old

**Self-Healing:**
- Restart daemon if stale
- Check daemon logs for errors

**Dashboard:** ✅ Cache freshness indicator

**Test:** Modify cache timestamp, verify detection

---

### FP-1.4: No Symbols in Cache
**Location:** `read_uw_cache()` in `main.py`  
**Impact:** Empty cache → No symbols to process → No trades  
**Detection:**
- Count symbols in cache (exclude `_metadata`)
- Alert if count == 0

**Self-Healing:**
- Check daemon polling logs
- Verify API connectivity
- Restart daemon

**Dashboard:** ✅ Symbol count display

**Test:** Clear all symbols from cache, verify detection

---

### FP-1.5: UW API Authentication Failure
**Location:** `uw_flow_daemon.py` API calls  
**Impact:** API returns 401/403 → No data → No trades  
**Detection:**
- Check API response status codes in logs
- Monitor for 401/403 errors

**Self-Healing:**
- Alert (cannot auto-fix auth issues)
- Log error for manual intervention

**Dashboard:** ✅ API status, error count

**Test:** Invalid API key, verify detection

---

### FP-1.6: UW API Rate Limit Exceeded
**Location:** `uw_flow_daemon.py` API calls  
**Impact:** API returns 429 → Polling stops → Stale data → No trades  
**Detection:**
- Check for 429 status codes
- Monitor request rate

**Self-Healing:**
- Implement backoff
- Reduce polling frequency
- Use token bucket algorithm

**Dashboard:** ✅ API rate limit status

**Test:** Simulate rate limit, verify backoff

---

### FP-1.7: No Clusters Generated
**Location:** `cluster_signals()` in `main.py`  
**Impact:** No clusters → `decide_and_execute()` receives empty list → No trades  
**Detection:**
- Check cluster count before `decide_and_execute()`
- Log if 0 clusters

**Self-Healing:**
- Check cache data quality
- Verify signal generation logic
- Check for data normalization issues

**Dashboard:** ✅ Cluster count per cycle

**Test:** Inject empty cache, verify 0 clusters

---

### FP-1.8: Cluster Generation Errors
**Location:** `cluster_signals()` in `main.py`  
**Impact:** Exception in clustering → No clusters → No trades  
**Detection:**
- Try/except around cluster generation
- Log exceptions

**Self-Healing:**
- Log error details
- Continue with empty clusters (graceful degradation)

**Dashboard:** ✅ Error count, last error message

**Test:** Inject malformed data, verify error handling

---

## CATEGORY 2: SCORING & EVALUATION

### FP-2.1: Adaptive Weights Not Initialized
**Location:** `state/signal_weights.json`  
**Impact:** `get_weight()` fails or returns 0 → Scores incorrect → No trades  
**Detection:**
- Check `weight_bands` count (should be 21)
- Verify all components have weight bands

**Self-Healing:**
- Auto-initialize if missing
- Run `fix_adaptive_weights_init.py` if needed

**Dashboard:** ✅ Weight initialization status, component count

**Test:** Delete weight_bands, verify auto-init

---

### FP-2.2: Composite Score Calculation Failure
**Location:** `compute_composite_score_v3()` in `uw_composite_v2.py`  
**Impact:** Exception in scoring → Score = 0 or None → No trades  
**Detection:**
- Try/except around score calculation
- Log exceptions
- Check for None/NaN scores

**Self-Healing:**
- Log error details
- Use fallback scoring if available
- Skip symbol if scoring fails

**Dashboard:** ✅ Scoring error count, last error

**Test:** Inject invalid data, verify error handling

---

### FP-2.3: Score Below Threshold
**Location:** `decide_and_execute()` in `main.py`  
**Impact:** All scores < threshold → No trades  
**Detection:**
- Log all scores vs threshold
- Track score distribution
- Alert if all scores consistently low

**Self-Healing:**
- Self-healing threshold adjusts if 3 losses
- Adaptive weights learn to improve scores
- Review threshold if consistently blocking

**Dashboard:** ✅ Score distribution, threshold status

**Test:** Inject low scores, verify blocking

---

### FP-2.4: Enrichment Failure
**Location:** `enrich_signal()` in `uw_enrichment_v2.py`  
**Impact:** Enrichment fails → Missing data → Incorrect scores → No trades  
**Detection:**
- Try/except around enrichment
- Check for missing required fields
- Log enrichment errors

**Self-Healing:**
- Use fallback enrichment
- Skip enrichment if non-critical
- Log for investigation

**Dashboard:** ✅ Enrichment error count

**Test:** Inject invalid cache data, verify handling

---

### FP-2.5: Regime Detection Failure
**Location:** `regime_detector.py`  
**Impact:** Regime detection fails → Wrong multipliers → Incorrect scores → No trades  
**Detection:**
- Try/except around regime detection
- Check for None/unknown regime
- Log regime detection errors

**Self-Healing:**
- Use default regime if detection fails
- Fallback to "NEUTRAL" regime

**Dashboard:** ✅ Regime status, detection errors

**Test:** Inject regime detection failure, verify fallback

---

## CATEGORY 3: GATES & FILTERS

### FP-3.1: Freeze State Active
**Location:** `check_freeze_state()` in `monitoring_guards.py`  
**Impact:** Freeze active → All trades blocked  
**Detection:**
- Check `state/governor_freezes.json`
- Check `state/pre_market_freeze.flag`
- Check performance freeze logic

**Self-Healing:**
- Auto-clear freezes after conditions met
- Performance freeze disabled in PAPER mode
- Manual override available

**Dashboard:** ✅ Freeze status, freeze reason

**Test:** Create freeze file, verify blocking

---

### FP-3.2: Max Positions Reached
**Location:** `can_open_new_position()` in `main.py`  
**Impact:** At max positions → New trades blocked  
**Detection:**
- Check `api.list_positions()` count
- Compare to `MAX_CONCURRENT_POSITIONS` (16)

**Self-Healing:**
- Opportunity displacement if enabled
- Wait for exits
- Normal operation (not a failure)

**Dashboard:** ✅ Position count, max positions

**Test:** Fill to max positions, verify blocking

---

### FP-3.3: Max New Positions Per Cycle
**Location:** `decide_and_execute()` in `main.py`  
**Impact:** `new_positions_this_cycle >= 6` → Further trades blocked this cycle  
**Detection:**
- Track `new_positions_this_cycle` counter
- Log when limit reached

**Self-Healing:**
- Normal operation (safety limit)
- Resets next cycle

**Dashboard:** ✅ New positions this cycle

**Test:** Execute 6 trades, verify 7th blocked

---

### FP-3.4: Expectancy Gate Blocking
**Location:** `ExpectancyGate.should_enter()` in `v3_2_features.py`  
**Impact:** Expectancy < threshold → Trade blocked  
**Detection:**
- Log expectancy vs threshold
- Track blocked trades by expectancy

**Self-Healing:**
- Adaptive learning improves expectancy
- Threshold adjusts by stage

**Dashboard:** ✅ Expectancy distribution, blocked count

**Test:** Inject low expectancy, verify blocking

---

### FP-3.5: Regime Gate Blocking
**Location:** `regime_gate_ticker()` in `main.py`  
**Impact:** Symbol profile indicates poor performance in current regime → Blocked  
**Detection:**
- Log regime gate decisions
- Track blocked symbols by regime

**Self-Healing:**
- Learning updates regime performance
- Gate thresholds adjust

**Dashboard:** ✅ Regime gate status, blocked symbols

**Test:** Configure poor regime performance, verify blocking

---

### FP-3.6: Theme Risk Limit
**Location:** `correlated_exposure_guard()` in `main.py`  
**Impact:** Theme exposure would exceed limit → Blocked  
**Detection:**
- Check theme exposure before trade
- Log violations

**Self-Healing:**
- Normal operation (risk management)
- Wait for positions to close

**Dashboard:** ✅ Theme exposure, limits

**Test:** Exceed theme limit, verify blocking

---

### FP-3.7: Cooldown Period Active
**Location:** `can_open_symbol()` in `main.py`  
**Impact:** Symbol traded recently (< 15 min) → Blocked  
**Detection:**
- Check cooldown timestamps
- Log cooldown blocks

**Self-Healing:**
- Normal operation (prevents overtrading)
- Cooldown expires automatically

**Dashboard:** ✅ Cooldown status per symbol

**Test:** Trade symbol, verify cooldown blocks

---

### FP-3.8: Self-Healing Threshold Raised
**Location:** `SelfHealingThreshold.check_recent_trades()` in `main.py`  
**Impact:** Threshold raised by 0.5 → More trades blocked  
**Detection:**
- Check `state/self_healing_threshold.json`
- Monitor threshold adjustments

**Self-Healing:**
- Resets after 24 hours or winning trade
- Normal operation (risk management)

**Dashboard:** ✅ Threshold status, adjustment history

**Test:** Trigger 3 losses, verify threshold raise

---

## CATEGORY 4: EXECUTION & BROKER

### FP-4.1: Alpaca API Connection Failure
**Location:** `AlpacaExecutor` in `main.py`  
**Impact:** Cannot connect to Alpaca → No trades possible  
**Detection:**
- Try/except around API calls
- Check connection status
- Monitor API response times

**Self-Healing:**
- Retry with backoff
- Alert if persistent failure
- Enter reduce-only mode

**Dashboard:** ✅ Alpaca connection status

**Test:** Disconnect network, verify detection

---

### FP-4.2: Alpaca API Authentication Failure
**Location:** `AlpacaExecutor` initialization  
**Impact:** Invalid credentials → No trades possible  
**Detection:**
- Check API response for 401/403
- Validate credentials on startup

**Self-Healing:**
- Alert (cannot auto-fix credentials)
- Log error for manual intervention

**Dashboard:** ✅ Alpaca auth status

**Test:** Invalid credentials, verify detection

---

### FP-4.3: Insufficient Buying Power
**Location:** `AlpacaExecutor.submit_entry()`  
**Impact:** Not enough cash → Order rejected → No trade  
**Detection:**
- Check account buying power
- Validate order size vs buying power

**Self-Healing:**
- Reduce position size
- Skip trade if insufficient funds
- Alert if consistently insufficient

**Dashboard:** ✅ Buying power, position size

**Test:** Set low buying power, verify handling

---

### FP-4.4: Order Rejection by Broker
**Location:** `AlpacaExecutor.submit_entry()`  
**Impact:** Order rejected → No trade  
**Detection:**
- Check order status
- Log rejection reasons

**Self-Healing:**
- Retry with adjusted parameters
- Log rejection for learning
- Skip if persistent rejection

**Dashboard:** ✅ Order rejection count, reasons

**Test:** Submit invalid order, verify handling

---

### FP-4.5: Position Reconciliation Failure
**Location:** `position_reconciliation_loop.py`  
**Impact:** Positions out of sync → Double-entry risk → Trading halted  
**Detection:**
- Compare local vs broker positions
- Log discrepancies

**Self-Healing:**
- Auto-reconcile positions
- Alert if reconciliation fails
- Halt trading if critical mismatch

**Dashboard:** ✅ Position reconciliation status

**Test:** Create position mismatch, verify reconciliation

---

## CATEGORY 5: STATE & CONFIGURATION

### FP-5.1: Missing Environment Variables
**Location:** `get_env()` calls throughout  
**Impact:** Missing required vars → Bot fails to start or misconfigures  
**Detection:**
- Validate all required env vars on startup
- Check for None/missing values

**Self-Healing:**
- Use defaults where possible
- Alert for required vars
- Fail fast on critical missing vars

**Dashboard:** ✅ Config validation status

**Test:** Remove env var, verify detection

---

### FP-5.2: Invalid Configuration Values
**Location:** Config class initialization  
**Impact:** Invalid config → Bot misbehaves → No trades  
**Detection:**
- Validate config ranges
- Check for negative/invalid values
- Type checking

**Self-Healing:**
- Use safe defaults
- Alert on invalid config
- Log config issues

**Dashboard:** ✅ Config validation errors

**Test:** Set invalid config, verify validation

---

### FP-5.3: State File Corruption
**Location:** All `state/*.json` files  
**Impact:** Corrupted state → Bot fails to load → No trades  
**Detection:**
- Try/except around JSON loads
- Validate JSON structure
- Check file integrity

**Self-Healing:**
- Backup corrupted files
- Reinitialize with defaults
- Alert on corruption

**Dashboard:** ✅ State file health

**Test:** Corrupt state file, verify recovery

---

### FP-5.4: Missing Required Files
**Location:** Various file reads  
**Impact:** Missing file → Bot fails → No trades  
**Detection:**
- Check file existence before read
- Validate required files on startup

**Self-Healing:**
- Create missing files with defaults
- Alert if cannot create
- Fail fast on critical missing files

**Dashboard:** ✅ Required files status

**Test:** Delete required file, verify handling

---

## CATEGORY 6: SYSTEM & INFRASTRUCTURE

### FP-6.1: Bot Process Not Running
**Location:** Systemd service  
**Impact:** Bot not running → No trades  
**Detection:**
- Systemd status check
- Process check: `pgrep -f main.py`

**Self-Healing:**
- Systemd auto-restart
- `heartbeat_keeper.py` restart if needed

**Dashboard:** ✅ Bot process status

**Test:** Stop bot, verify restart

---

### FP-6.2: Bot Process Crashed
**Location:** Main loop in `main.py`  
**Impact:** Unhandled exception → Bot crashes → No trades  
**Detection:**
- Systemd status (failed)
- Check crash logs
- Monitor for exceptions

**Self-Healing:**
- Systemd auto-restart
- Log crash details
- Alert on persistent crashes

**Dashboard:** ✅ Crash count, last crash

**Test:** Inject unhandled exception, verify restart

---

### FP-6.3: Bot Stuck/Unresponsive
**Location:** Main loop in `main.py`  
**Impact:** Bot running but not processing → No trades  
**Detection:**
- Check last activity timestamp
- Monitor cycle completion
- Heartbeat check

**Self-Healing:**
- Restart if unresponsive > 5 minutes
- Alert on stuck state

**Dashboard:** ✅ Last activity time, cycle status

**Test:** Inject infinite loop, verify detection

---

### FP-6.4: Disk Space Full
**Location:** File writes  
**Impact:** Cannot write logs/state → Bot may fail → No trades  
**Detection:**
- Check disk space
- Monitor before writes

**Self-Healing:**
- Clean old logs
- Alert if space critical
- Halt if cannot write

**Dashboard:** ✅ Disk space, cleanup status

**Test:** Fill disk, verify handling

---

### FP-6.5: Memory Exhaustion
**Location:** All processes  
**Impact:** Out of memory → Bot crashes → No trades  
**Detection:**
- Monitor memory usage
- Check for memory leaks

**Self-Healing:**
- Restart if memory high
- Alert on memory issues
- Optimize memory usage

**Dashboard:** ✅ Memory usage

**Test:** Inject memory leak, verify detection

---

### FP-6.6: Network Connectivity Issues
**Location:** All API calls  
**Impact:** Cannot reach APIs → No data → No trades  
**Detection:**
- Ping/connectivity checks
- Monitor API response times
- Check for timeouts

**Self-Healing:**
- Retry with backoff
- Alert on persistent issues
- Use cached data if available

**Dashboard:** ✅ Network status, API connectivity

**Test:** Disconnect network, verify handling

---

## TEST HARNESS REQUIREMENTS

### Test-1: Signal Injection Test
**Purpose:** Inject fake signal and trace through entire flow  
**Steps:**
1. Create fake cluster with known score
2. Inject into `decide_and_execute()`
3. Trace through all gates
4. Verify execution path
5. Check for any blocking points

### Test-2: End-to-End Flow Test
**Purpose:** Test complete flow from cache to execution  
**Steps:**
1. Populate cache with test data
2. Generate clusters
3. Score signals
4. Check all gates
5. Attempt execution (paper mode)
6. Verify trade logged

### Test-3: Failure Point Simulation
**Purpose:** Test each failure point individually  
**Steps:**
1. For each FP, simulate failure condition
2. Verify detection
3. Verify self-healing (if applicable)
4. Verify dashboard update
5. Verify recovery

---

## MONITORING REQUIREMENTS

### M-1: Real-Time Health Dashboard
**Status:** Each failure point must have:
- Current status (OK/WARN/ERROR)
- Last check time
- Self-healing status
- Historical trends

### M-2: Alerting System
**Status:** Critical failures must:
- Alert immediately
- Escalate if not resolved
- Log all alerts

### M-3: Self-Healing Status
**Status:** Track:
- Self-healing attempts
- Success/failure rate
- Manual intervention required

---

## DASHBOARD REQUIREMENTS

### D-1: Failure Point Status Page
**Status:** Show all FPs with:
- Current status
- Last check
- Self-healing status
- Historical data

### D-2: Trading Readiness Indicator
**Status:** Overall status:
- GREEN: All critical FPs OK, trading ready
- YELLOW: Some FPs warning, trading may be limited
- RED: Critical FP failed, trading blocked

### D-3: Detailed FP Views
**Status:** Click on FP to see:
- Detection details
- Self-healing history
- Related logs
- Manual actions available

---

## SELF-HEALING REQUIREMENTS

### SH-1: Automatic Recovery
**Status:** Each FP must have:
- Detection mechanism
- Recovery procedure
- Success verification
- Fallback if recovery fails

### SH-2: Escalation
**Status:** If self-healing fails:
- Alert immediately
- Log for investigation
- Provide manual recovery steps

### SH-3: Learning from Failures
**Status:** Track:
- Failure frequency
- Recovery success rate
- Patterns in failures
- Improvements needed

---

## VERIFICATION CHECKLIST

Before declaring trading "ready", verify:

- [ ] All 50+ failure points documented
- [ ] Each FP has detection mechanism
- [ ] Each FP has self-healing (where possible)
- [ ] Each FP visible on dashboard
- [ ] Test harness covers all FPs
- [ ] End-to-end test passes
- [ ] Signal injection test passes
- [ ] Monitoring alerts configured
- [ ] Dashboard shows all FPs
- [ ] Self-healing verified for each FP
- [ ] Documentation complete

---

**This document must be updated whenever:**
- New failure point discovered
- New detection mechanism added
- New self-healing implemented
- New test case created
- Architecture changes

