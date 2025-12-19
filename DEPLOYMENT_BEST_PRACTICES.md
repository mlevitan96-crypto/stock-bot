# Deployment Best Practices & SDLC Process

## Overview

This document defines the proper Software Development Lifecycle (SDLC) process for deploying changes to the trading bot, including regression testing, verification, and documentation requirements.

## Pre-Deployment Checklist

Before deploying ANY changes:

- [ ] **Code Review**: Changes reviewed and tested locally
- [ ] **Documentation**: Changes documented in commit message
- [ ] **No Breaking Changes**: Verify backward compatibility
- [ ] **Dependencies**: Check if new dependencies required
- [ ] **Configuration**: Verify no new env vars needed (or document if needed)
- [ ] **Git Status**: Clean working directory, no uncommitted changes

## Deployment Process (SDLC)

### Phase 1: Preparation

1. **Verify Current State**
   ```bash
   cd ~/stock-bot
   git status  # Should be clean
   ps aux | grep "python.*main.py\|deploy_supervisor" | grep -v grep  # Check what's running
   ```

2. **Backup Current State**
   ```bash
   git log --oneline -1  # Note current commit
   cp -r state state.backup.$(date +%Y%m%d_%H%M%S)  # Backup state if needed
   ```

### Phase 2: Code Update

3. **Pull Latest Code**
   ```bash
   git stash  # Save any local changes
   git fetch origin main
   git reset --hard origin/main  # Accept incoming changes
   ```

4. **Verify Code Integrity**
   ```bash
   python3 -c "import main; print('✅ main.py imports successfully')"
   python3 -c "from dashboard import app; print('✅ dashboard.py imports successfully')"
   ```

### Phase 3: Environment Setup

5. **Verify Virtual Environment**
   ```bash
   if [ ! -d "venv" ]; then
       python3 -m venv venv
   fi
   source venv/bin/activate
   pip install -r requirements.txt -q
   ```

6. **Verify Environment Variables**
   ```bash
   # .env file should exist
   if [ -f ".env" ]; then
       echo "✅ .env file exists"
       # Verify format (should have KEY=value, no spaces)
       grep -E "^(UW_API_KEY|ALPACA_KEY|ALPACA_SECRET)=" .env | wc -l
       # Should show 3 (all required vars present)
   else
       echo "❌ .env file missing - create it with required secrets"
       exit 1
   fi
   ```

**NOTE**: Environment variables in `.env` are loaded by Python's `load_dotenv()` in the Python process. They are NOT visible in shell. This is EXPECTED behavior.

### Phase 4: Deployment

7. **Stop Existing Services**
   ```bash
   pkill -f "deploy_supervisor"
   pkill -f "python.*main.py"
   pkill -f "python.*dashboard.py"
   sleep 3
   ```

8. **Start Services with Supervisor**
   ```bash
   screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"
   sleep 5
   ```

### Phase 5: Verification & Regression Testing

9. **Verify Services Started**
   ```bash
   # Check supervisor
   ps aux | grep "deploy_supervisor" | grep -v grep
   
   # Check bot
   ps aux | grep "python.*main.py" | grep -v grep
   
   # Check dashboard
   ps aux | grep "python.*dashboard.py" | grep -v grep
   ```

10. **Verify Bot Health (Functional Test)**
    ```bash
    # Bot health endpoint (proves secrets loaded)
    curl -s http://localhost:8081/health | python3 -m json.tool | head -10
    
    # Dashboard health
    curl -s http://localhost:5000/api/health_status | python3 -m json.tool | head -5
    ```

11. **Verify Secrets Are Loaded (Indirect Test)**
    ```bash
    # If bot responds to health endpoint, secrets are loaded
    # If bot can access Alpaca API, secrets work
    curl -s http://localhost:8081/health | grep -i "error\|missing\|secret" && echo "❌ Secrets issue" || echo "✅ Secrets loaded"
    ```

12. **Regression Testing Checklist**
    - [ ] Bot process running
    - [ ] Dashboard accessible
    - [ ] Health endpoints responding
    - [ ] No errors in supervisor logs: `tail -50 logs/supervisor.jsonl | grep -i error`
    - [ ] Recent activity in logs: `tail -5 logs/run.jsonl`
    - [ ] SRE dashboard loads: `curl -s http://localhost:5000/api/sre/health | python3 -m json.tool | head -5`

### Phase 6: Monitoring

13. **Monitor First 10 Minutes**
    ```bash
    # Watch supervisor logs
    screen -r supervisor
    # Press Ctrl+A then D to detach
    ```

14. **Monitor First Hour**
    - Check for errors: `tail -100 logs/supervisor.jsonl | grep -i error`
    - Check bot activity: `tail -20 logs/run.jsonl`
    - Check trading: `tail -10 logs/orders.jsonl`

## Environment Variables Explained

### How .env Loading Works

1. **File Location**: `~/stock-bot/.env`
2. **Loader**: `deploy_supervisor.py` runs `load_dotenv()` which reads `.env`
3. **Process Scope**: Variables loaded into Python process environment
4. **Inheritance**: Child processes (main.py, dashboard.py) inherit these variables
5. **Shell Visibility**: Shell commands CANNOT see these variables (different process)

### Why Shell Shows "NOT SET"

When you run `echo $UW_API_KEY` in shell, it shows "NOT SET" because:
- Shell is a different process than Python
- Environment variables are process-local
- `.env` is loaded by Python, not shell
- This is **EXPECTED** and **NORMAL**

### How to Verify Secrets Are Actually Loaded

**Method 1: Test Bot Functionality (Recommended)**
```bash
# If bot responds to health endpoint, secrets are loaded
curl -s http://localhost:8081/health | python3 -m json.tool
```

**Method 2: Check Supervisor Logs**
```bash
# Supervisor logs will show if secrets are missing
tail -50 logs/supervisor.jsonl | grep -i "secret\|missing\|WARNING"
```

**Method 3: Check Bot Can Access APIs**
```bash
# If bot is making API calls, secrets work
tail -20 logs/run.jsonl | grep -i "alpaca\|api\|connected"
```

## Automated Deployment Script

Use `FIX_AND_DEPLOY.sh` which follows this SDLC process:

```bash
cd ~/stock-bot
git pull origin main
chmod +x FIX_AND_DEPLOY.sh
./FIX_AND_DEPLOY.sh
```

## Troubleshooting

### Bot Not Starting

1. Check supervisor logs: `screen -r supervisor`
2. Check for missing dependencies: `source venv/bin/activate && python3 main.py`
3. Verify .env file format: `cat .env | grep -E "^(UW_API_KEY|ALPACA_KEY|ALPACA_SECRET)="`

### Secrets Not Loading

1. Verify .env file exists: `ls -la .env`
2. Verify .env format (no spaces around =): `cat .env`
3. Check supervisor logs for warnings: `tail -50 logs/supervisor.jsonl | grep -i "secret\|missing"`

### Dashboard Not Loading

1. Check if running: `ps aux | grep "python.*dashboard.py"`
2. Check port: `netstat -tulpn | grep 5000`
3. Check logs: `screen -r supervisor` (look for dashboard messages)

## Regression Testing Standards

### Critical Tests (Must Pass)

1. ✅ Bot process starts
2. ✅ Dashboard accessible
3. ✅ Health endpoints respond
4. ✅ No critical errors in logs
5. ✅ Bot can access APIs (proves secrets work)

### Functional Tests (Should Pass)

1. ✅ Signals generating: `tail -10 logs/signals.jsonl`
2. ✅ Orders can be placed: `tail -10 logs/orders.jsonl`
3. ✅ Positions tracked: `tail -10 logs/run.jsonl | grep -i "position"`

### Performance Tests

1. ✅ No memory leaks (check over time)
2. ✅ Response times acceptable
3. ✅ No excessive CPU usage

## Documentation Requirements

Every deployment must include:

1. **Commit Message**: Clear description of changes
2. **Breaking Changes**: Documented if any
3. **New Dependencies**: Listed in requirements.txt
4. **Configuration Changes**: Documented in relevant .md files
5. **Testing**: Results of regression tests

## Rollback Procedure

If deployment fails:

1. **Stop Services**
   ```bash
   pkill -f "deploy_supervisor"
   ```

2. **Revert Code**
   ```bash
   git log --oneline -10  # Find previous good commit
   git checkout <previous_commit_hash>
   ```

3. **Restart**
   ```bash
   ./FIX_AND_DEPLOY.sh
   ```

## Summary

- ✅ Use `FIX_AND_DEPLOY.sh` for deployments
- ✅ Verify bot is running with functional tests (not shell env vars)
- ✅ Monitor first hour after deployment
- ✅ Document all changes
- ✅ Follow SDLC process for all deployments
