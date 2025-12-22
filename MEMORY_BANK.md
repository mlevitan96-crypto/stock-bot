# Trading Bot Memory Bank
## Comprehensive Knowledge Base for Future Conversations

**Last Updated:** 2025-12-21 (Full Learning Cycle Script Added - Process All Historical Data Now)  
**Purpose:** Centralized knowledge base for all project details, common issues, solutions, and best practices.

---

## Project Overview

**Project Name:** Stock Trading Bot  
**Repository:** https://github.com/mlevitan96-crypto/stock-bot  
**Environment:** Ubuntu droplet (DigitalOcean), Python 3.12, externally-managed Python environment  
**Deployment:** `deploy_supervisor.py` manages all services (dashboard, trading-bot, uw-daemon)

### Core Components

1. **Trading Bot** (`main.py`): Main trading logic, position management, entry/exit decisions
2. **Dashboard** (`dashboard.py`): Web UI on port 5000, shows positions, SRE monitoring, executive summary
3. **UW Daemon** (`uw_flow_daemon.py`): Fetches and caches UnusualWhales API data
4. **Deploy Supervisor** (`deploy_supervisor.py`): Process manager for all services
5. **SRE Monitoring** (`sre_monitoring.py`): Health monitoring for signals, APIs, execution
6. **Learning Engine** (`comprehensive_learning_orchestrator_v2.py`): Comprehensive multi-timeframe learning system
   - **IMPORTANT**: This is the ONLY learning orchestrator. The old `comprehensive_learning_orchestrator.py` (without _v2) is DEPRECATED and REMOVED - should NOT be used or referenced.
   - All learning goes through `comprehensive_learning_orchestrator_v2.py`
   - **Architecture Mapping**: 
     - Run `architecture_mapping_audit.py` regularly to catch mapping issues
     - Run `architecture_self_healing.py` (with --apply) to automatically fix common issues
     - All paths must use `config/registry.py` (StateFiles, CacheFiles, LogFiles, ConfigFiles) - NO hardcoded paths
7. **Learning Enhancements** (`learning_enhancements_v1.py`): Pattern learning (gate, UW blocked, signal patterns)
8. **Learning Scheduler** (`comprehensive_learning_scheduler.py`): Multi-timeframe learning automation (daily/weekly/bi-weekly/monthly)
9. **Profitability Tracker** (`profitability_tracker.py`): Daily/weekly/monthly performance tracking
10. **Adaptive Signal Optimizer** (`adaptive_signal_optimizer.py`): Bayesian weight optimization with anti-overfitting guards

---

## Environment Setup

### Critical Environment Variables

**Location:** `~/stock-bot/.env` (loaded by Python via `load_dotenv()`, NOT visible in shell)

**Required Variables:**
- `UW_API_KEY`: UnusualWhales API key
- `ALPACA_KEY`: Alpaca trading API key
- `ALPACA_SECRET`: Alpaca trading API secret
- `ALPACA_BASE_URL`: Usually `https://paper-api.alpaca.markets` for paper trading
- `TRADING_MODE`: `PAPER` or `LIVE`

**Important Note:** Environment variables loaded by Python (`load_dotenv()`) are NOT visible in shell. This is EXPECTED behavior. To verify secrets are loaded, check if bot is making API calls or responding to health endpoints.

### Python Environment

**Ubuntu Externally-Managed Environment:**
- Use virtual environment: `python3 -m venv venv`
- Activate: `source venv/bin/activate`
- Or use `--break-system-packages` flag (not recommended)

**Dependencies:**
- `requirements.txt` contains all Python packages
- Key packages: `alpaca-trade-api`, `flask`, `python-dotenv`

---

## Deployment Procedures

### Standard Deployment

```bash
cd ~/stock-bot
git pull origin main
chmod +x FIX_AND_DEPLOY.sh
./FIX_AND_DEPLOY.sh
```

### Quick Restart (After Code Changes)

```bash
cd ~/stock-bot
git pull origin main
pkill -f "deploy_supervisor"
sleep 3
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"
sleep 5
```

### Manual Service Management

**Check running processes:**
```bash
ps aux | grep -E "deploy_supervisor|main.py|dashboard.py" | grep -v grep
```

**View supervisor logs:**
```bash
screen -r supervisor
# Press Ctrl+A then D to detach
```

**Stop all services:**
```bash
pkill -f "deploy_supervisor"
pkill -f "python.*main.py"
pkill -f "python.*dashboard.py"
```

---

## Common Issues & Solutions

### Issue 1: Environment Variables Show "NOT SET" in Shell

**Symptom:** Diagnostic scripts show `UW_API_KEY: NOT SET` even though bot is running

**Root Cause:** Environment variables from `.env` are loaded by Python process, not shell

**Solution:** This is EXPECTED. Verify bot is working by:
- Check if bot responds to health endpoint: `curl http://localhost:8081/health`
- Check supervisor logs: `screen -r supervisor`
- Bot making API calls = secrets are loaded

**Verification Script:** `VERIFY_BOT_IS_RUNNING.sh`

### Issue 2: Git Merge Conflicts

**Symptom:** `error: Your local changes to the following files would be overwritten by merge`

**Solution:**
```bash
git stash
git fetch origin main
git reset --hard origin/main
git pull origin main
```

**Automated:** `FIX_AND_DEPLOY.sh` handles this automatically

### Issue 3: Dashboard Shows "0s" for Freshness/Update Times

**Symptom:** SRE Monitoring tab shows "Last Update: 0s" and "Freshness: 0s"

**Root Cause:** `data_freshness_sec` was `null` in API response

**Solution:** Fixed in `sre_monitoring.py` - now always sets `data_freshness_sec` to `cache_age` (cache file modification time)

**Fix Applied:** 2025-12-19 - `data_freshness_sec` now always has a value

### Issue 4: Bot Not Placing Trades

**Possible Causes:**
1. Max positions reached (16) - check `state/position_metadata.json`
2. All signals blocked - check `state/blocked_trades.jsonl`
3. Market closed - check market status
4. Worker thread not running - check `logs/run.jsonl`

**Diagnosis Scripts:**
- `FULL_SYSTEM_AUDIT.py`: Comprehensive health check
- `DIAGNOSE_WHY_NO_ORDERS.py`: Focus on order execution
- `CHECK_DISPLACEMENT_AND_EXITS.py`: Check displacement/exit logic

### Issue 5: Module Not Found Errors

**Symptom:** `ModuleNotFoundError: No module named 'alpaca_trade_api'`

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

Or if using system Python:
```bash
pip3 install --break-system-packages alpaca-trade-api
```

### Issue 6: Dashboard Not Updating After Code Changes

**Symptom:** Code changes pushed but dashboard still shows old data

**Solution:** Dashboard must be restarted to load new Python code:
```bash
pkill -f "python.*dashboard.py"
# Restart via deploy_supervisor or manually
```

**Script:** `RESTART_DASHBOARD_AND_BOT.sh`

---

## Key File Locations

### Configuration Files
- `config/registry.py`: Centralized configuration
- `config/uw_signal_contracts.py`: UW API endpoint definitions
- `.env`: Environment variables (secrets)

### Log Files (in `logs/` directory)
- `run.jsonl`: Execution cycles
- `signals.jsonl`: Signal generation
- `orders.jsonl`: Order execution
- `exit.jsonl`: Position exits
- `attribution.jsonl`: Trade attribution (P&L, components, exit reasons)
- `displacement.jsonl`: Displacement events
- `gate.jsonl`: Gate blocks
- `worker.jsonl`: Worker thread events
- `supervisor.jsonl`: Supervisor logs
- `comprehensive_learning.jsonl`: Learning engine cycles
- `weight_learning.jsonl`: Weight learning updates

### State Files (in `state/` directory)
- `position_metadata.json`: Current positions
- `blocked_trades.jsonl`: Blocked trade reasons
- `displacement_cooldowns.json`: Displacement cooldowns
- `learning_processing_state.json`: Learning system state (last processed IDs, totals)
- `profitability_tracking.json`: Daily/weekly/monthly performance metrics
- `signal_weights.json`: Adaptive signal weights (from `adaptive_signal_optimizer.py`)
- `gate_pattern_learning.json`: Gate pattern learning state (V1 enhancements)
- `uw_blocked_learning.json`: UW blocked entry learning state (V1 enhancements)
- `signal_pattern_learning.json`: Signal pattern learning state (V1 enhancements)

### Data Files (in `data/` directory)
- `uw_flow_cache.json`: UW API cache
- `live_orders.jsonl`: Order events
- `uw_attribution.jsonl`: UW signal attribution (including blocked entries with decision="rejected")

---

## Architecture Patterns

### Signal Flow
1. **UW Daemon** → Fetches data → Updates `data/uw_flow_cache.json`
2. **Cache Enrichment** → Computes signals → Updates cache
3. **Main Bot** → Reads cache → Generates clusters → Scores → Executes

### Trade Execution Flow
1. `run_once()` → Generates clusters
2. `decide_and_execute()` → Scores clusters → Checks gates → Calls `submit_entry()`
3. `evaluate_exits()` → Checks exit criteria → Calls `close_position()`

### Exit Criteria
- Time-based: `TIME_EXIT_DAYS_STALE` (default 14 days)
- Trailing stop: `TRAILING_STOP_PCT` (default 2%)
- Signal decay: Current score < entry score threshold
- Flow reversal: Signal direction changed
- Regime protection: High volatility negative gamma protection
- Profit targets: Scale-out at 2%, 5%, 10%
- Stale positions: Low movement for extended time

### Displacement Logic
When `MAX_CONCURRENT_POSITIONS` (16) reached:
1. Find candidate positions (age > 4h, P&L < ±1%, score advantage > 2.0)
2. Check cooldown (6 hours after displacement)
3. Close weakest position
4. Open new position

---

## SRE Monitoring

### Health Endpoints

**Dashboard:** `http://localhost:5000/api/sre/health`  
**Bot:** `http://localhost:8081/api/sre/health`

### Signal Categories

1. **CORE Signals** (Required):
   - `options_flow`: Options flow sentiment
   - `dark_pool`: Dark pool activity
   - `insider`: Insider trading

2. **COMPUTED Signals** (Should exist):
   - `iv_term_skew`: IV term structure skew
   - `smile_slope`: Volatility smile slope

3. **ENRICHED Signals** (Optional):
   - `whale_persistence`, `event_alignment`, `temporal_motif`, `congress`, `institutional`, `market_tide`, `calendar_catalyst`, `etf_flow`, `greeks_gamma`, `ftd_pressure`, `iv_rank`, `oi_change`, `squeeze_score`, `shorts_squeeze`

### Health Status Levels

- **healthy**: All critical components working
- **degraded**: Some warnings but functional
- **critical**: Critical issues preventing operation

---

## Learning Engine

### Integration Points

- `main.py` line 1952: `run_daily_learning()` called in `learn_from_outcomes()`
- `main.py` line 1056: `learn_from_trade_close()` called after each trade
- `main.py` line 5400: Daily learning triggered after market close
- `main.py` line 5404: Profitability tracking updated daily/weekly/monthly
- `comprehensive_learning_orchestrator_v2.py`: Central orchestrator for all learning
  - **DEPRECATED/REMOVED**: `comprehensive_learning_orchestrator.py` (old version without _v2) - DO NOT USE OR REFERENCE
  - **DEPRECATED/REMOVED**: `_learn_from_outcomes_legacy()` in main.py - DO NOT USE OR REFERENCE
  - Only `comprehensive_learning_orchestrator_v2.py` should be used for all learning operations

### Learning Schedule (Industry Best Practices)

**SHORT-TERM (Continuous):**
- Records trade immediately after close
- NO weight updates (prevents overfitting)
- EWMA updated in daily batch only

**MEDIUM-TERM (Daily):**
- Processes all new trades from the day
- Updates EWMA for all components
- Updates weights ONLY if:
  - MIN_SAMPLES (50) met
  - MIN_DAYS_BETWEEN_UPDATES (3) passed
  - Statistical significance confirmed (Wilson intervals)

**WEEKLY:**
- Weekly weight adjustments
- Profile retraining
- Weekly profitability metrics

**MONTHLY:**
- Monthly profitability metrics
- Long-term trend analysis

### Overfitting Safeguards (2025-12-21 Implementation)

**Key Parameters** (`adaptive_signal_optimizer.py`):
- `MIN_SAMPLES = 50` (increased from 30, industry standard: 50-100)
- `MIN_DAYS_BETWEEN_UPDATES = 3` (prevents over-adjustment)
- `LOOKBACK_DAYS = 60` (increased from 30, more stable learning)
- `UPDATE_STEP = 0.05` (5% max change per update)
- `EWMA_ALPHA = 0.15` (85% weight on history, 15% on new)

**Safeguards:**
1. ✅ Batch processing (no per-trade weight updates)
2. ✅ Minimum 50 samples before adjustment
3. ✅ Minimum 3 days between updates
4. ✅ Wilson confidence intervals (95% statistical significance)
5. ✅ EWMA smoothing (prevents overreacting to noise)
6. ✅ Small update steps (5% max)
7. ✅ Multiple conditions required (Wilson AND EWMA must agree)

**Industry Alignment:**
- Matches practices used by Two Sigma, Citadel, prop trading firms
- Conservative approach prevents overfitting while maintaining responsiveness

### Learning Components

1. **Actual Trades** (`logs/attribution.jsonl`): All historical trades processed
2. **Exit Events** (`logs/exit.jsonl`): Exit signal learning
3. **Blocked Trades** (`state/blocked_trades.jsonl`): Counterfactual learning
4. **Gate Events** (`logs/gate.jsonl`): Gate pattern learning ✅ **IMPLEMENTED**
5. **UW Blocked Entries** (`data/uw_attribution.jsonl`): Missed opportunities ✅ **IMPLEMENTED**
6. **Signal Patterns** (`logs/signals.jsonl`): Signal generation patterns ✅ **IMPLEMENTED**
7. **Execution Quality** (`logs/orders.jsonl`): Order execution analysis (tracking only, learning pending)

### Health Check

**On Server**:
```bash
curl http://localhost:8081/health | python3 -m json.tool | grep -A 10 comprehensive_learning
```

**Comprehensive Learning Status**:
```bash
cd ~/stock-bot
python3 check_comprehensive_learning_status.py
```

**Profitability Tracking**:
```bash
cd ~/stock-bot
python3 profitability_tracker.py
```

**Local (Windows)**:
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python VERIFY_LEARNING_PIPELINE.py
```

### Learning Pipeline Verification

**Quick Status Check** (copy/paste ready):
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python check_learning_status.py
```

**Check if Trades Closing**:
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python check_trades_closing.py
```

**Full Learning Report**:
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python manual_learning_check.py
```

**Note**: All scripts must be run from project root directory.

---

## Best Practices

### Code Changes

1. **Always test locally** before pushing
2. **Document changes** in commit messages
3. **Follow SDLC process** (see `DEPLOYMENT_BEST_PRACTICES.md`)
4. **Run regression tests** after deployment (`VERIFY_DEPLOYMENT.sh`)

### Deployment

1. **Use `FIX_AND_DEPLOY.sh`** for standard deployments
2. **Verify after deployment** using verification scripts
3. **Monitor first hour** after deployment
4. **Check supervisor logs** if issues occur

### Troubleshooting

1. **Check logs first**: `logs/supervisor.jsonl`, `logs/worker.jsonl`
2. **Verify processes**: `ps aux | grep python`
3. **Test endpoints**: `curl http://localhost:5000/api/sre/health`
4. **Check environment**: Verify `.env` file exists and has required vars
5. **Use diagnostic scripts**: `FULL_SYSTEM_AUDIT.py`, `DIAGNOSE_WHY_NO_ORDERS.py`

### Git Workflow

1. **Pull before making changes**: `git pull origin main`
2. **Handle conflicts**: Use `git stash` and `git reset --hard origin/main`
3. **Commit with clear messages**: Describe what and why
4. **Push immediately**: Don't let changes sit locally

---

## Diagnostic Scripts Reference

| Script | Purpose | Run From |
|--------|---------|----------|
| `FULL_SYSTEM_AUDIT.py` | Comprehensive system health check | Project root |
| `DIAGNOSE_WHY_NO_ORDERS.py` | Diagnose why orders aren't being placed | Project root |
| `CHECK_DISPLACEMENT_AND_EXITS.py` | Check displacement and exit logic | Project root |
| `VERIFY_LEARNING_PIPELINE.py` | Verify learning system is processing trades | Project root |
| `check_learning_status.py` | Quick learning status check | Project root |
| `check_trades_closing.py` | Check if trades are closing and logged | Project root |
| `manual_learning_check.py` | Detailed learning system report | Project root |
| `check_comprehensive_learning_status.py` | Comprehensive learning system status | Project root |
| `profitability_tracker.py` | Daily/weekly/monthly profitability report | Project root |
| `check_uw_blocked_entries.py` | Check UW attribution for blocked entries | Project root |
| `reset_learning_state.py` | Reset learning processing state | Project root |
| `backfill_historical_learning.py` | Process all historical data for learning | Project root |
| `check_learning_enhancements.py` | Check status of learning enhancements (gate, UW, signal) | Project root |
| `test_learning_enhancements.py` | Regression tests for learning enhancements | Project root |
| `test_learning_integration.py` | Integration tests for learning enhancements | Project root |
| `VERIFY_BOT_IS_RUNNING.sh` | Verify bot is running (handles env var confusion) | Project root |
| `VERIFY_DEPLOYMENT.sh` | Regression testing after deployment | Project root |
| `VERIFY_TRADE_EXECUTION_AND_LEARNING.sh` | Verify trade execution and learning engine | Project root |
| `RESTART_DASHBOARD_AND_BOT.sh` | Restart services after code changes | Project root |
| `FIX_AND_DEPLOY.sh` | Complete deployment with conflict resolution | Project root |

**Important**: All Python scripts must be run from the **project root directory** (where `main.py` is located).

---

## Known Limitations

1. **Market Closed**: Some checks show 0 activity when market is closed (normal)
2. **Enriched Signals**: May show "optional" if enrichment service not running (expected)
3. **Cache Freshness**: Shows cache file age, not individual signal age (approximation)
4. **Shell Env Vars**: Environment variables not visible in shell (loaded by Python only)

---

## Quick Reference Commands

### Check Bot Status
```bash
curl http://localhost:8081/health | python3 -m json.tool | head -20
```

### Check Dashboard
```bash
curl http://localhost:5000/api/sre/health | python3 -m json.tool | head -20
```

### View Recent Orders
```bash
tail -20 data/live_orders.jsonl | python3 -m json.tool
```

### View Recent Exits
```bash
tail -20 logs/exit.jsonl | python3 -m json.tool
```

### Check Blocked Trades
```bash
tail -20 state/blocked_trades.jsonl | python3 -m json.tool
```

### View Supervisor Logs
```bash
tail -50 logs/supervisor.jsonl | grep -i error
```

---

## Recent Fixes & Improvements

### 2025-12-21: Multi-Timeframe Learning Automation

1. **Weekly Learning Cycle**:
   - Runs every Friday after market close
   - Focus: Weekly pattern analysis, trend detection, weight optimization
   - Updates weekly profitability tracking

2. **Bi-Weekly Learning Cycle**:
   - Runs every other Friday (odd weeks) after market close
   - Focus: Deeper pattern analysis, regime detection, structural changes
   - Detects performance shifts and regime changes

3. **Monthly Learning Cycle**:
   - Runs first trading day of month after market close
   - Focus: Long-term profitability, structural optimization, major adjustments
   - Evaluates profitability status and goal tracking (60% win rate)

**Automation**: All cycles fully automated in background thread  
**Profitability Focus**: All cycles track and optimize for long-term profitability  
**Status**: ✅ Production ready

### 2025-12-21: Learning Enhancements V1 Implementation

1. **Gate Pattern Learning**:
   - Tracks which gates block which trades
   - Analyzes gate effectiveness
   - Learns optimal gate thresholds
   - State: `state/gate_pattern_learning.json`

2. **UW Blocked Entry Learning**:
   - Tracks blocked UW entries (decision="rejected")
   - Analyzes signal combinations
   - Tracks sentiment patterns
   - State: `state/uw_blocked_learning.json`

3. **Signal Pattern Learning**:
   - Records all signal generation events
   - Correlates signals with trade outcomes
   - Identifies best signal combinations
   - State: `state/signal_pattern_learning.json`

**Testing**: 24/24 unit tests passing, integration tests passing  
**Documentation**: `LEARNING_ENHANCEMENTS_IMPLEMENTATION.md`  
**Status**: ✅ Production ready

### 2025-12-21: Overfitting Safeguards & Profitability Tracking

1. **Overfitting Safeguards**:
   - Increased `MIN_SAMPLES` from 30 to 50 (industry standard)
   - Removed per-trade weight updates (now batched daily only)
   - Added `MIN_DAYS_BETWEEN_UPDATES = 3` (prevents over-adjustment)
   - Increased `LOOKBACK_DAYS` from 30 to 60 (more stable learning)
   - Aligned with industry best practices (Two Sigma, Citadel)

2. **Profitability Tracking System**:
   - Daily/weekly/monthly performance metrics
   - 30-day trend analysis (improving/declining)
   - Component performance tracking
   - Goal status (target: 60% win rate)

3. **Comprehensive Learning System**:
   - Processes ALL data sources (trades, exits, blocked trades, gates, UW entries)
   - Multi-timeframe learning (short/medium/long-term)
   - State tracking to avoid duplicate processing
   - 100% coverage of all log files

**Documentation:**
- `OVERFITTING_ANALYSIS_AND_RECOMMENDATIONS.md`: Industry best practices analysis
- `LEARNING_SCHEDULE_AND_PROFITABILITY.md`: Learning schedule and profitability tracking
- `DEPLOY_OVERFITTING_FIXES.md`: Deployment guide
- `LEARNING_SYSTEM_COMPLETE.md`: Complete learning system overview

### 2025-12-19: Learning Pipeline Verification

1. **SRE Monitoring Freshness**: Fixed `data_freshness_sec` always being null
2. **Dashboard Display**: Added learning engine status, improved signal metadata
3. **Trade Execution**: Verified entry/exit logic working correctly
4. **Learning Engine**: Verified integration and health reporting
5. **Deployment Scripts**: Added comprehensive deployment and verification scripts

**Documentation:** See `SRE_MONITORING_AND_TRADE_EXECUTION_FIXES.md`

---

## Key Interactions & Decisions (2025-12-21)

### Overfitting Concerns & Industry Best Practices

**User Concern**: "Before I deploy, I want to make sure we don't overfit and adjust too often. Is there a concern we do that with adjusting after every trade?"

**Analysis**: Valid concern. System was updating weights after every trade, which could lead to overfitting.

**Solution Implemented**:
1. Removed per-trade weight updates (now batched daily only)
2. Increased MIN_SAMPLES to 50 (industry standard)
3. Added MIN_DAYS_BETWEEN_UPDATES = 3
4. Increased LOOKBACK_DAYS to 60

**Result**: System now follows industry best practices (Two Sigma, Citadel) and is protected against overfitting while maintaining responsiveness.

### Profitability Goal

**User Goal**: "The overall goal is HOW DO WE MAKE MONEY? This must be profitable. The goal is to make every trade a winning one."

**Implementation**:
1. Comprehensive profitability tracking (daily/weekly/monthly)
2. 30-day trend analysis (improving/declining)
3. Goal status tracking (target: 60% win rate)
4. Component performance analysis
5. Full learning cycle: Signal → Trade → Learn → Review → Update → Trade

## Future Improvements

1. **Out-of-Sample Validation**: Validate weight updates on recent data before applying
2. **Regime-Specific Learning**: Market regime-aware parameter tuning
3. **Symbol-Specific Optimization**: Per-symbol parameter learning
4. **Multi-Parameter Optimization**: Simultaneous optimization of multiple parameters
5. **Execution Quality Learning**: Full integration of execution analysis
6. **Bootstrap Resampling**: Additional statistical validation

---

## Contact & Support

**Repository:** https://github.com/mlevitan96-crypto/stock-bot  
**Deployment Location:** `~/stock-bot` on Ubuntu droplet  
**Dashboard URL:** `http://<droplet-ip>:5000`

---

**Note:** This memory bank should be updated after each significant change or fix to maintain accuracy.
