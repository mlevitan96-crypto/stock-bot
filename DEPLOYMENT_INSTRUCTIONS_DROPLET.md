# Deployment Instructions for Droplet

## ⚠️ CRITICAL: Run This on the Droplet

**You must SSH into the droplet and run these commands to complete deployment.**

---

## Quick Deployment (Copy/Paste This Entire Block)

```bash
cd ~/stock-bot
git pull origin main
bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
```

This single command will:
1. Pull latest code
2. Install all dependencies
3. Verify all modules
4. Run all tests
5. Run complete verification
6. Push results back to Git

---

## Step-by-Step Deployment

### Step 1: SSH into Droplet

```bash
ssh root@your_droplet_ip
# or
ssh your_user@your_droplet_ip
```

### Step 2: Navigate to Project

```bash
cd ~/stock-bot
```

### Step 3: Pull Latest Code

```bash
git pull origin main
```

### Step 4: Run Deployment Script

```bash
chmod +x FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
```

### Step 5: Verify Results

The script will automatically:
- Install dependencies
- Run all tests
- Verify all modules
- Push results to Git

Check the output for:
- ✓ All modules import successfully
- ✓ Integration tests passed
- ✓ Regression tests passed
- ✓ Complete verification passed

---

## What Gets Verified

1. **Module Imports**
   - structural_intelligence modules
   - learning modules
   - self_healing modules
   - api_management modules
   - main.py

2. **Integration Tests**
   - Regime Detector
   - Macro Gate
   - Structural Exit
   - Thompson Sampling
   - Shadow Logger
   - Token Bucket
   - Full Integration

3. **Regression Tests**
   - Main imports
   - Module imports
   - Config registry
   - Signal modules

4. **Complete Verification**
   - File integrity
   - Import validation
   - Backtest execution

---

## Expected Output

```
==========================================
FORCE DROPLET DEPLOYMENT - STRUCTURAL INTELLIGENCE
==========================================
Started: [timestamp]

Step 1: Pulling latest code from Git...
✓ Code updated

Step 2: Installing dependencies...
✓ Dependencies installed

Step 3: Verifying module imports...
  ✓ structural_intelligence modules
  ✓ learning modules
  ✓ self_healing modules
  ✓ api_management modules
  ✓ main.py imports

✓ All modules import successfully

Step 4: Running integration tests...
✓ Integration tests passed

Step 5: Running regression tests...
✓ Regression tests passed

Step 6: Running complete droplet verification...
✓ Complete verification passed

Step 7: Testing main.py startup (dry run)...
  ✓ main.py imported successfully
  ✓ All main.py components available

Step 8: Committing and pushing results...
✓ Results pushed to Git

==========================================
DEPLOYMENT VERIFICATION SUMMARY
==========================================
Integration Tests: PASS
Regression Tests: PASS
Complete Verification: PASS

✓✓✓ ALL VERIFICATIONS PASSED - DEPLOYMENT SUCCESSFUL ✓✓✓
```

---

## Troubleshooting

### If Dependencies Fail to Install

```bash
# Try with pip instead of pip3
pip install hmmlearn numpy scipy tzdata

# Or install in virtual environment
source venv/bin/activate
pip install hmmlearn numpy scipy tzdata
```

### If Module Imports Fail

Check that all files are present:
```bash
ls -la structural_intelligence/
ls -la learning/
ls -la self_healing/
ls -la api_management/
```

### If Tests Fail

Check the output files:
```bash
cat integration_test_output.txt
cat regression_test_output.txt
cat verification_output.txt
```

### If Git Push Fails

Check Git configuration:
```bash
git config --list
git remote -v
```

---

## After Deployment

Once deployment is successful:

1. **Monitor Dashboard**: Check for structural intelligence indicators
2. **Check Logs**: Look for regime detection and macro adjustments
3. **Review Shadow Logger**: Check threshold adjustments
4. **Monitor Token Bucket**: Check API quota management

---

## Verification Files

After successful deployment, these files will be created:
- `structural_intelligence_test_results.json`
- `regression_test_results.json`
- `droplet_verification_results.json`
- `integration_test_output.txt`
- `regression_test_output.txt`
- `verification_output.txt`

All results are automatically pushed to Git.

---

**Run the deployment script now to complete the deployment!**

