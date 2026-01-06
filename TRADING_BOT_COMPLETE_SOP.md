# Trading Bot Complete SOP (Standard Operating Procedure)

**Version:** 1.0  
**Last Updated:** 2026-01-06  
**Purpose:** Complete reference for trading bot operation, troubleshooting, and failure diagnosis

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Startup Sequence](#startup-sequence)
3. [Trading Cycle Workflow](#trading-cycle-workflow)
4. [Signal Processing Pipeline](#signal-processing-pipeline)
5. [Execution Pipeline](#execution-pipeline)
6. [Failure Points & Diagnostics](#failure-points--diagnostics)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Recovery Procedures](#recovery-procedures)

---

## System Architecture

### Components

1. **deploy_supervisor.py** - Main orchestrator
   - Starts all services
   - Monitors process health
   - Auto-restarts failed services
   - Location: `/root/stock-bot/deploy_supervisor.py`

2. **main.py** - Trading engine
   - Runs trading cycles
   - Processes signals
   - Executes trades
   - Evaluates exits
   - Location: `/root/stock-bot/main.py`

3. **uw_flow_daemon.py** - Data fetcher
   - Polls UW API
   - Caches signals
   - Updates cache every 60s
   - Location: `/root/stock-bot/uw_flow_daemon.py`

4. **dashboard.py** - Web interface
   - Health dashboard
   - Metrics display
   - Port 5000
   - Location: `/root/stock-bot/dashboard.py`

### Service Management

**Service:** `trading-bot.service` (systemd)
- **Start:** `systemctl start trading-bot.service`
- **Stop:** `systemctl stop trading-bot.service`
- **Restart:** `systemctl restart trading-bot.service`
- **Status:** `systemctl status trading-bot.service`
- **Logs:** `journalctl -u trading-bot.service -f`

---

## Startup Sequence

### Phase 1: Service Start (systemd)

1. systemd starts `trading-bot.service`
2. Service executes: `/root/stock-bot/systemd_start.sh`
3. Script activates venv and runs: `python deploy_supervisor.py`

**Check:** `systemctl status trading-bot.service`

### Phase 2: Supervisor Initialization

1. `deploy_supervisor.py` starts
2. Creates required directories
3. Checks for secrets (.env file)
4. Starts services in order:
   - Dashboard (port 5000) - **FIRST**
   - UW Flow Daemon
   - Trading Bot (main.py)

**Check:** `ps aux | grep deploy_supervisor`

### Phase 3: Trading Bot Initialization

1. `main.py` loads
2. Initializes:
   - Alpaca API client
   - Strategy engine
   - Position executor
   - Watchdog (worker thread)
3. Starts worker thread (runs cycles)
4. Starts health supervisor

**Check:** `ps aux | grep "python.*main.py"`

### Phase 4: Worker Loop Start

1. Worker thread starts (`_worker_loop`)
2. Checks market status
3. If market open: runs first cycle
4. If market closed: logs cycle but skips trading
5. Sleeps for `RUN_INTERVAL_SEC` (default: 60s)
6. Repeats

**Check:** `tail -f logs/run.jsonl`

---

## Trading Cycle Workflow

### Cycle Frequency
- **Interval:** 60 seconds (`Config.RUN_INTERVAL_SEC`)
- **During Market Hours:** Full trading enabled
- **After Market Close:** Signal processing only, no new entries

### Cycle Steps (in order)

#### Step 1: Freeze Check (0s)
- **File:** `state/governor_freezes.json`
- **Check:** `check_freeze_state()`
- **Action if frozen:** Skip cycle, log freeze status
- **Diagnostic:** 
  ```bash
  cat state/governor_freezes.json | jq '.[] | select(.active == true)'
  ```

#### Step 2: UW Cache Read (1s)
- **File:** `data/uw_flow_cache.json`
- **Check:** Cache exists and has data
- **Action:** Load cache, enrich signals
- **Diagnostic:**
  ```bash
  cat data/uw_flow_cache.json | jq 'keys | length'  # Should be > 0
  ```

#### Step 3: Signal Generation (2-5s)
- **Process:** 
  1. Iterate through cache symbols
  2. Enrich each signal (`enrich_signal`)
  3. Compute composite score (`compute_composite_score_v3`)
  4. Apply freshness fix (minimum 0.9)
- **Output:** List of signals with scores
- **Diagnostic:**
  ```bash
  tail -50 data/uw_attribution.jsonl | jq -r '.symbol + ": " + (.score | tostring)'
  ```

#### Step 4: Signal Review / Gate Check (5-8s)
- **Gates Applied (in order):**
  1. **Composite Score Threshold** (`should_enter_v2`)
     - Score >= threshold (base: 2.7)
     - Toxicity < 0.90
     - Freshness >= 0.30
  2. **Expectancy Gate** (v3.2 features)
     - Expectancy >= entry_floor
  3. **Risk Management**
     - Max positions check
     - Symbol exposure limits
     - Sector exposure limits
- **Output:** Filtered clusters ready for execution
- **Diagnostic:**
  ```bash
  tail -50 logs/composite_gate.jsonl | jq -r '.symbol + ": " + .msg + " (score=" + (.score | tostring) + ")"'
  ```

#### Step 5: Execution (8-15s)
- **Process:**
  1. Sort clusters by score (highest first)
  2. For each cluster:
     - Check momentum filter (optional)
     - Calculate position size
     - Submit order to Alpaca
     - Mark position open
     - Log attribution
- **Output:** Orders placed, positions tracked
- **Diagnostic:**
  ```bash
  tail -50 logs/orders.jsonl | jq -r '.symbol + ": " + .action'
  ```

#### Step 6: Exit Evaluation (15-20s)
- **Process:**
  1. Iterate open positions
  2. Check exit conditions:
     - Trailing stop
     - Time-based exit
     - Structural exit signals
     - Profit target
  3. Submit exit orders if triggered
- **Output:** Exit orders, position closures
- **Diagnostic:**
  ```bash
  tail -50 logs/exit.jsonl | jq -r '.symbol + ": " + .reason'
  ```

#### Step 7: Metrics & Logging (20-25s)
- **Process:**
  1. Compute daily P&L
  2. Calculate win rate
  3. Update risk metrics
  4. Log cycle completion
- **Output:** `logs/run.jsonl` entry
- **Diagnostic:**
  ```bash
  tail -1 logs/run.jsonl | jq '{ts, clusters, orders, metrics}'
  ```

#### Step 8: Sleep (until next cycle)
- **Duration:** `RUN_INTERVAL_SEC - (cycle_duration)`
- **Minimum:** 0 seconds

---

## Signal Processing Pipeline

### Data Flow

```
UW API → uw_flow_daemon.py → uw_flow_cache.json → main.py → Composite Scoring → Gate Check → Execution
```

### Key Files

1. **`data/uw_flow_cache.json`** - Raw signal cache
   - Updated by `uw_flow_daemon.py` every 60s
   - Contains: sentiment, conviction, dark_pool, insider data

2. **`data/uw_attribution.jsonl`** - All scoring attempts
   - Every symbol evaluated
   - Includes: score, components, decision (signal/rejected)

3. **`logs/composite_gate.jsonl`** - Gate decisions
   - Accepted/rejected signals
   - Includes: score, threshold, rejection reason

### Composite Score Calculation

**Components:**
1. **Flow Component** (weight: 2.4)
   - `flow_weight * conviction`
   - **Critical Fix:** Force 2.4 (adaptive weights disabled)

2. **Dark Pool** (weight: 1.3)
   - Total premium, print count

3. **Insider** (weight: 0.5)
   - Net buys/sells

4. **IV Skew** (weight: 0.6)
   - Term structure skew

5. **Smile Slope** (weight: 0.35)
   - Volatility smile

6. **Whale Persistence** (weight: 0.7)
   - Large order patterns

7. **Toxicity Penalty** (weight: -0.9)
   - Negative component (reduces score)

**Final Score:**
```
composite_raw = sum(all_components)
composite_score = composite_raw * freshness
```

**Critical Fix:** Freshness minimum 0.9 (in `main.py` lines 6127-6142)

---

## Execution Pipeline

### Order Submission Flow

1. **Position Size Calculation**
   - Base notional: `BASE_NOTIONAL_USD`
   - ATR multiplier: From volatility
   - Sizing overlay: From composite score

2. **Order Types**
   - **Market Order:** Primary (immediate execution)
   - **Limit Order:** Fallback if market fails
   - **Stop Loss:** Trailing stop attached

3. **Position Tracking**
   - **File:** `state/position_metadata.json`
   - Tracks: entry price, quantity, entry time, components

4. **Exit Conditions**
   - Trailing stop hit
   - Time limit (intraday)
   - Profit target
   - Structural exit signal

---

## Failure Points & Diagnostics

### Category 1: Service/Process Failures

#### 1.1 Bot Process Not Running
**Symptoms:**
- No cycles in `logs/run.jsonl`
- `pgrep -f "python.*main.py"` returns nothing

**Diagnostic:**
```bash
systemctl status trading-bot.service
ps aux | grep deploy_supervisor
ps aux | grep "python.*main.py"
```

**Fix:**
```bash
systemctl restart trading-bot.service
# Wait 30 seconds
tail -f logs/run.jsonl  # Should see new cycles
```

#### 1.2 Supervisor Not Running
**Symptoms:**
- No processes visible
- Service shows "active" but no Python processes

**Diagnostic:**
```bash
systemctl status trading-bot.service
journalctl -u trading-bot.service -n 50
```

**Fix:**
```bash
systemctl restart trading-bot.service
```

#### 1.3 Worker Thread Not Starting
**Symptoms:**
- Process running but no cycles
- No `logs/run.jsonl` entries

**Diagnostic:**
```bash
grep -i "worker.*start" logs/system.jsonl | tail -5
grep -i "thread.*started" logs/system.jsonl | tail -5
```

**Fix:**
- Check for errors in logs
- Restart service
- Check freeze state

### Category 2: Data/Configuration Failures

#### 2.1 UW Cache Empty
**Symptoms:**
- `data/uw_flow_cache.json` has no symbols (only `_metadata`)
- All scores are 0

**Diagnostic:**
```bash
cat data/uw_flow_cache.json | jq 'keys | length'
cat data/uw_flow_cache.json | jq 'keys | map(select(startswith("_") == false)) | length'
```

**Fix:**
```bash
# Check daemon
ps aux | grep uw_flow_daemon
# Check daemon logs
tail -50 logs/uw_flow_daemon.jsonl
# Restart if needed
systemctl restart trading-bot.service
```

#### 2.2 Missing Configuration Files
**Symptoms:**
- Import errors
- Missing weights/thresholds

**Diagnostic:**
```bash
ls -la data/uw_weights.json
ls -la state/uw_thresholds_hierarchical.json
python3 -c "import uw_composite_v2; print(uw_composite_v2.WEIGHTS_V3)"
```

**Fix:**
```bash
python3 create_weights.py  # Creates uw_weights.json if missing
```

#### 2.3 Threshold File Override
**Symptoms:**
- Thresholds in logs show 3.50 (should be 2.7)
- Signals blocked despite good scores

**Diagnostic:**
```bash
cat state/uw_thresholds_hierarchical.json | jq '.'
python3 -c "import uw_composite_v2; print(uw_composite_v2.get_threshold('AAPL', 'base'))"
```

**Fix:**
```bash
# Delete override file
rm state/uw_thresholds_hierarchical.json
# Verify default
python3 -c "import uw_composite_v2; print(uw_composite_v2.ENTRY_THRESHOLDS)"
```

### Category 3: Scoring Failures

#### 3.1 Flow Component Too Low
**Symptoms:**
- Scores 0.025-0.612 (should be 2.5-4.0)
- Flow component = 0.612 (should be ~2.4)

**Diagnostic:**
```bash
python3 -c "import uw_composite_v2; print(uw_composite_v2.get_weight('options_flow', 'mixed'))"
# Should print: 2.4
```

**Fix:**
- Already fixed in code (force 2.4)
- Restart bot to load fix

#### 3.2 enrich_signal Missing Fields
**Symptoms:**
- Flow component = 0.0
- Sentiment/conviction missing

**Diagnostic:**
```bash
python3 -c "
import json
from pathlib import Path
import sys
sys.path.insert(0, '/root/stock-bot')
import uw_enrichment_v2

cache = json.load(open('data/uw_flow_cache.json'))
symbol = list(cache.keys())[0]
if not symbol.startswith('_'):
    enriched = uw_enrichment_v2.enrich_signal(symbol, cache, 'NEUTRAL')
    print(f'sentiment: {enriched.get(\"sentiment\")}')
    print(f'conviction: {enriched.get(\"conviction\")}')
"
```

**Fix:**
- Already fixed in `uw_enrichment_v2.py`
- Restart bot to load fix

#### 3.3 Freshness Killing Scores
**Symptoms:**
- Good raw scores but final score very low
- Freshness < 0.5 in logs

**Diagnostic:**
```bash
tail -50 data/uw_attribution.jsonl | jq -r 'select(.components.freshness_factor < 0.5) | .symbol + ": " + (.components.freshness_factor | tostring)'
```

**Fix:**
- Already fixed in `main.py` (minimum 0.9 freshness)
- Restart bot to load fix

### Category 4: Gate Blocking Failures

#### 4.1 All Signals Blocked
**Symptoms:**
- 0 clusters, 0 orders
- All signals rejected in `logs/composite_gate.jsonl`

**Diagnostic:**
```bash
tail -100 logs/composite_gate.jsonl | jq -r 'group_by(.msg) | map({msg: .[0].msg, count: length})'
tail -100 logs/composite_gate.jsonl | jq -r 'select(.msg == "rejected") | .rejection_reason' | sort | uniq -c
```

**Common Reasons:**
- Score below threshold (check threshold value)
- Toxicity too high (check toxicity in scores)
- Freshness too low (should be fixed)

#### 4.2 Threshold Too High
**Symptoms:**
- Scores 2.5-3.0 but all rejected
- Threshold in logs = 3.50

**Diagnostic:**
```bash
tail -20 logs/composite_gate.jsonl | jq -r '.threshold' | sort -u
python3 -c "import uw_composite_v2; print(uw_composite_v2.ENTRY_THRESHOLDS)"
```

**Fix:**
- Check for override file (delete if exists)
- Verify code has correct thresholds (2.7/2.9/3.2)
- Restart bot

### Category 5: Execution Failures

#### 5.1 Orders Not Submitting
**Symptoms:**
- Clusters created but no orders
- No entries in `logs/orders.jsonl`

**Diagnostic:**
```bash
tail -50 logs/system.jsonl | grep -i "order\|alpaca\|submit" | tail -10
tail -50 logs/system.jsonl | grep -i error | tail -10
```

**Common Causes:**
- Alpaca API errors
- Max positions reached
- Risk management blocks

#### 5.2 Alpaca API Errors
**Symptoms:**
- Errors in logs about API calls
- Orders fail with API errors

**Diagnostic:**
```bash
tail -100 logs/system.jsonl | grep -i "alpaca\|api" | grep -i error | tail -10
```

**Fix:**
- Check API keys in `.env`
- Check Alpaca account status
- Check rate limits

### Category 6: Freeze/Blocking States

#### 6.1 Active Freeze
**Symptoms:**
- No cycles executing
- Freeze message in logs

**Diagnostic:**
```bash
cat state/governor_freezes.json | jq '.[] | select(.active == true)'
```

**Fix:**
```bash
python3 << 'EOF'
import json
from pathlib import Path
from datetime import datetime, timezone

freeze_file = Path('state/governor_freezes.json')
if freeze_file.exists():
    data = json.load(open(freeze_file))
    for key in list(data.keys()):
        if data[key].get('active', False):
            data[key]['active'] = False
            data[key]['cleared_at'] = datetime.now(timezone.utc).isoformat()
            print(f"Cleared: {key}")
    json.dump(data, open(freeze_file, 'w'), indent=2)
EOF
```

#### 6.2 Market Closed
**Symptoms:**
- Cycles running but no trading
- Market open check returns False

**Diagnostic:**
```bash
python3 -c "
import sys
sys.path.insert(0, '/root/stock-bot')
from main import is_market_open_now
print(f'Market open: {is_market_open_now()}')
"
```

**Fix:**
- Normal during closed hours
- Check market hours (9:30 AM - 4:00 PM ET)

---

## Monitoring & Health Checks

### Real-Time Monitoring

#### Dashboard
- **URL:** `http://your-server:5000`
- **Health:** `http://your-server:5000/health`
- **SRE Status:** `http://your-server:5000/api/sre/health`

#### Log Monitoring
```bash
# Watch cycles
tail -f logs/run.jsonl

# Watch signals
tail -f data/uw_attribution.jsonl | jq -r '.symbol + ": " + (.score | tostring) + " -> " + .decision'

# Watch gate events
tail -f logs/composite_gate.jsonl | jq -r '.symbol + ": " + .msg + " (score=" + (.score | tostring) + ")"

# Watch orders
tail -f logs/orders.jsonl | jq -r '.symbol + ": " + .action'
```

### Health Check Script

**File:** `check_current_trading_status.py`

**Run:**
```bash
python3 check_current_trading_status.py
```

**Checks:**
1. Recent composite scores
2. Recent run cycles
3. Recent gate events
4. Current thresholds
5. Freshness fix verification
6. Cache data sample

### Automated Diagnostics

**File:** `diagnose_complete.py`

**Run:**
```bash
python3 diagnose_complete.py
```

**Checks:**
1. Bot process status
2. Latest cycle age
3. Freeze state
4. Code fixes verification
5. Market status

---

## Troubleshooting Guide

### Problem: No Trades (0 positions, 0 orders)

**Step 1: Check if cycles are running**
```bash
tail -5 logs/run.jsonl
# Should show recent entries (within last 60 seconds)
```

**If NO cycles:**
- Check service status: `systemctl status trading-bot.service`
- Check process: `ps aux | grep "python.*main.py"`
- Check freezes: `cat state/governor_freezes.json | jq '.[] | select(.active == true)'`
- Restart: `systemctl restart trading-bot.service`

**If cycles ARE running but 0 clusters/orders:**

**Step 2: Check scores**
```bash
tail -50 data/uw_attribution.jsonl | jq -r 'select(.decision == "signal") | .symbol + ": " + (.score | tostring)'
# Should see signals with scores >= 2.7
```

**If NO signals:**
- Check flow component: `python3 verify_weight_fix.py`
- Check threshold: `python3 -c "import uw_composite_v2; print(uw_composite_v2.get_threshold('AAPL', 'base'))"`
- Check cache: `cat data/uw_flow_cache.json | jq 'keys | length'`

**If signals exist but blocked:**

**Step 3: Check gate events**
```bash
tail -50 logs/composite_gate.jsonl | jq -r 'select(.msg == "rejected") | .rejection_reason' | sort | uniq -c
```

**Common issues:**
- Score < threshold → Check threshold value
- Toxicity > 0.90 → Normal, high toxicity blocks
- Freshness < 0.30 → Should be fixed (minimum 0.9)

**Step 4: Check execution**
```bash
tail -50 logs/orders.jsonl
# Should see order submissions
```

**If no orders:**
- Check Alpaca API errors: `tail -100 logs/system.jsonl | grep -i alpaca`
- Check max positions: `python3 -c "from main import Config; print(Config.MAX_CONCURRENT_POSITIONS)"`

### Problem: Scores Too Low

**Check flow weight:**
```bash
python3 verify_weight_fix.py
# Should print: 2.4
```

**Check enrich_signal:**
```bash
python3 debug_score_calculation.py
# Check flow component value
```

**Check freshness:**
```bash
tail -50 data/uw_attribution.jsonl | jq -r '.components.freshness_factor' | sort -n | head -1
# Should be >= 0.9 (if fix is active)
```

### Problem: Cycles Stopped

1. **Check process:**
   ```bash
   ps aux | grep "python.*main.py"
   ```

2. **Check logs for errors:**
   ```bash
   tail -100 logs/system.jsonl | grep -i error
   ```

3. **Check freeze:**
   ```bash
   cat state/governor_freezes.json | jq '.[] | select(.active == true)'
   ```

4. **Restart:**
   ```bash
   systemctl restart trading-bot.service
   ```

---

## Recovery Procedures

### Complete Reset (if everything is broken)

1. **Stop service:**
   ```bash
   systemctl stop trading-bot.service
   ```

2. **Clear freezes:**
   ```bash
   python3 << 'EOF'
   import json
   from pathlib import Path
   freeze_file = Path('state/governor_freezes.json')
   if freeze_file.exists():
       data = json.load(open(freeze_file))
       for key in data:
           data[key]['active'] = False
       json.dump(data, open(freeze_file, 'w'), indent=2)
   EOF
   ```

3. **Verify fixes:**
   ```bash
   python3 verify_weight_fix.py
   python3 check_current_trading_status.py
   ```

4. **Restart:**
   ```bash
   systemctl start trading-bot.service
   ```

5. **Monitor:**
   ```bash
   tail -f logs/run.jsonl
   # Should see cycles every 60 seconds
   ```

### Partial Reset (if only scoring is broken)

1. **Reset adaptive weights:**
   ```bash
   python3 fix_adaptive_weights_killing_scores.py
   ```

2. **Delete threshold overrides:**
   ```bash
   rm state/uw_thresholds_hierarchical.json
   ```

3. **Restart:**
   ```bash
   systemctl restart trading-bot.service
   ```

---

## Quick Reference

### Critical Files

- **Cache:** `data/uw_flow_cache.json`
- **Weights:** `data/uw_weights.json`
- **Thresholds:** `uw_composite_v2.py` (ENTRY_THRESHOLDS)
- **Freezes:** `state/governor_freezes.json`
- **Positions:** `state/position_metadata.json`

### Critical Values

- **Threshold (base):** 2.7
- **Flow Weight:** 2.4
- **Freshness Minimum:** 0.9
- **Cycle Interval:** 60 seconds

### Diagnostic Commands

```bash
# Process status
ps aux | grep python

# Service status
systemctl status trading-bot.service

# Latest cycle
tail -1 logs/run.jsonl | jq '{ts, clusters, orders}'

# Recent scores
tail -20 data/uw_attribution.jsonl | jq -r '.symbol + ": " + (.score | tostring) + " -> " + .decision'

# Gate events
tail -20 logs/composite_gate.jsonl | jq -r '.symbol + ": " + .msg + " (score=" + (.score | tostring) + ")"

# Freezes
cat state/governor_freezes.json | jq '.[] | select(.active == true)'
```

---

**END OF SOP**
