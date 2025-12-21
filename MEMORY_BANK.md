# Trading Bot Memory Bank
## Comprehensive Knowledge Base for Future Conversations

**Last Updated:** 2025-12-19 (Learning Pipeline Verification Added)  
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
6. **Learning Engine** (`comprehensive_learning_orchestrator.py`): ML-based parameter optimization

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
- `displacement.jsonl`: Displacement events
- `gate.jsonl`: Gate blocks
- `worker.jsonl`: Worker thread events
- `supervisor.jsonl`: Supervisor logs
- `comprehensive_learning.jsonl`: Learning engine cycles

### State Files (in `state/` directory)
- `position_metadata.json`: Current positions
- `blocked_trades.jsonl`: Blocked trade reasons
- `displacement_cooldowns.json`: Displacement cooldowns

### Data Files (in `data/` directory)
- `uw_flow_cache.json`: UW API cache
- `live_orders.jsonl`: Order events
- `attribution.jsonl`: Trade attribution (P&L, close reasons)

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

- `main.py` line 5620: Learning orchestrator imported
- `main.py` line 5645: Learning thread started
- `main.py` line 5687: Health endpoint includes learning status
- `sre_monitoring.py` line 541: SRE health includes learning status

### Learning Components

1. **Counterfactual Analysis**: What-if scenarios
2. **Weight Variations**: Test different signal weights
3. **Timing Optimization**: Entry/exit timing
4. **Sizing Optimization**: Position sizing
5. **Exit Threshold Learning**: Optimize exit parameters
6. **Profit Target Learning**: Optimize scale-out targets
7. **Risk Limit Learning**: Optimize risk parameters

### Health Check

**On Server**:
```bash
curl http://localhost:8081/health | python3 -m json.tool | grep -A 10 comprehensive_learning
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

## Recent Fixes (2025-12-19)

1. **SRE Monitoring Freshness**: Fixed `data_freshness_sec` always being null
2. **Dashboard Display**: Added learning engine status, improved signal metadata
3. **Trade Execution**: Verified entry/exit logic working correctly
4. **Learning Engine**: Verified integration and health reporting
5. **Deployment Scripts**: Added comprehensive deployment and verification scripts

**Documentation:** See `SRE_MONITORING_AND_TRADE_EXECUTION_FIXES.md`

---

## Future Improvements

1. **Phase 3 Learning**: Full implementation of parameter optimization
2. **Regime-Specific Learning**: Market regime-aware parameter tuning
3. **Symbol-Specific Optimization**: Per-symbol parameter learning
4. **Multi-Parameter Optimization**: Simultaneous optimization of multiple parameters
5. **Execution Quality Learning**: Full integration of execution analysis

---

## Contact & Support

**Repository:** https://github.com/mlevitan96-crypto/stock-bot  
**Deployment Location:** `~/stock-bot` on Ubuntu droplet  
**Dashboard URL:** `http://<droplet-ip>:5000`

---

**Note:** This memory bank should be updated after each significant change or fix to maintain accuracy.
