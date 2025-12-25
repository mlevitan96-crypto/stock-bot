# Droplet Console Workflow - Complete Guide

## Overview

**IMPORTANT: Cursor handles the complete workflow automatically. This guide is for reference only if SSH is unavailable.**

**Standard Workflow: User → Cursor → Git → Droplet (SSH) → Git → Cursor → User**

Cursor ALWAYS:
1. Pushes to Git
2. Triggers droplet via SSH (or instructs user only if SSH unavailable)
3. Pulls results from Git
4. Verifies everything
5. Reports completion

## Complete Workflow: User → Cursor → Git → Droplet → Git → Cursor → User

### Step 1: Cursor Pushes to Git ✅ (ALWAYS DONE BY CURSOR)
- Cursor commits and pushes all changes to GitHub
- Cursor verifies push succeeded
- **User never needs to do this - Cursor handles it**

### Step 2: Cursor Triggers Droplet (ALWAYS DONE BY CURSOR)

**PRIMARY: Cursor uses SSH** (automatic):
- Cursor uses `EXECUTE_DROPLET_DEPLOYMENT_NOW.py` or `droplet_client.py`
- Cursor executes deployment via SSH automatically
- User never needs to do anything

**FALLBACK ONLY: If SSH unavailable** (rare case):
- Cursor still pushes to Git (Step 1)
- User may need to trigger droplet manually via console (only if SSH not configured)

**NOTE: This is FALLBACK ONLY - Cursor normally handles this via SSH automatically**

If SSH is unavailable and Cursor instructs you to use console:

**Open DigitalOcean Console:**
1. Go to DigitalOcean dashboard
2. Click on your droplet
3. Click "Console" or "Access" → "Launch Droplet Console"
4. A browser-based terminal will open

**Run This Command (Only if Cursor instructs you - normally Cursor does this via SSH):**

```bash
cd ~/stock-bot && git fetch origin main && git reset --hard origin/main && bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
```

**What This Does:**
- Pulls latest code from Git (includes XAI implementation)
- Runs complete deployment verification:
  - Installs dependencies (hmmlearn, numpy, scipy, tzdata, paramiko if needed)
  - Verifies all module imports (including xai)
  - Runs integration tests
  - Runs regression tests
  - Runs XAI regression tests
  - Runs complete verification
  - Commits and pushes results back to Git

**Expected Output:**
- You'll see progress for each step
- Final summary showing which tests passed/failed
- Results automatically pushed to Git

### Step 3: Cursor Pulls Results from Git (ALWAYS DONE BY CURSOR)

After droplet deployment completes (via SSH or console), Cursor automatically:
- Pull results from Git: `git pull origin main`
- Check for result files:
  - `droplet_verification_results.json`
  - `xai_regression_test_output.txt`
  - `integration_test_output.txt`
  - `regression_test_output.txt`
  - `verification_output.txt`

### Step 4: Cursor Verifies & Reports

Cursor will:
- Read all result files
- Verify all tests passed
- Report completion status

## Quick Reference Commands for Console

### Deploy Latest Changes
```bash
cd ~/stock-bot && git pull origin main && bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
```

### Just Pull Code (No Deployment)
```bash
cd ~/stock-bot && git pull origin main
```

### Check Deployment Status
```bash
cd ~/stock-bot && tail -20 xai_regression_test_output.txt
```

### View All Test Results
```bash
cd ~/stock-bot && ls -la *test_output.txt *results.json
```

### Check if XAI is Working
```bash
cd ~/stock-bot && python3 test_xai_regression.py
```

## What Happens Automatically

When you run `git pull origin main` in the console, the **post-merge hook** (`run_investigation_on_pull.sh`) automatically:
1. Runs `FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh` (includes XAI tests)
2. Runs complete verification
3. Pushes results back to Git

So you can also just run:
```bash
cd ~/stock-bot && git pull origin main
```

And the deployment will happen automatically via the post-merge hook.

## Current Status

**Ready for Deployment:**
- ✅ All XAI code pushed to Git
- ✅ Deployment script updated with XAI tests
- ✅ Post-merge hook configured to run deployment automatically

**Next Step:**
Run in droplet console:
```bash
cd ~/stock-bot && git pull origin main
```

The post-merge hook will automatically run the full deployment and verification.

## Verification After Deployment

After running the command, check:
1. **Test Results**: Look for `xai_regression_test_output.txt` - should show "6/6 tests passed"
2. **Module Imports**: Should see "✓ xai modules" in output
3. **Git Status**: Results should be pushed back to Git automatically

## Troubleshooting

**If git pull fails:**
```bash
cd ~/stock-bot
git fetch origin main
git reset --hard origin/main
```

**If deployment script fails:**
```bash
cd ~/stock-bot
chmod +x FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
```

**If dependencies missing:**
```bash
cd ~/stock-bot
source venv/bin/activate  # if using venv
pip install -r requirements.txt
```

