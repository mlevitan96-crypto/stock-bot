# Droplet Final Verification Instructions

## Complete End-to-End Verification

**Status:** All local audits passed. Ready for droplet verification.

---

## Run on Droplet Console

**Copy and paste this command in your DigitalOcean console:**

```bash
cd ~/stock-bot && git fetch origin main && git reset --hard origin/main && bash FINAL_DROPLET_VERIFICATION.sh
```

---

## What This Does

The `FINAL_DROPLET_VERIFICATION.sh` script will:

1. **Pull Latest Code** - Gets all audit scripts and fixes
2. **Install Dependencies** - Ensures all packages are installed
3. **Run Final Verification** - Tests dashboard, self-healing, monitoring, trading
4. **Run Complete Audit** - Checks hardcoded values, logging, bugs, labels
5. **Test Imports** - Verifies all critical modules can be imported
6. **Test Endpoints** - Verifies all dashboard and main.py endpoints exist
7. **Check Self-Healing** - Verifies self-healing modules present
8. **Check Monitoring** - Verifies monitoring functions present
9. **Check Trading** - Verifies all trading functions present
10. **Save Results** - Commits and pushes results back to Git

---

## Expected Output

You should see:
- ✓ Final verification passed
- ✓ Complete audit passed (or warnings only)
- ✓ All critical imports successful
- ✓ All dashboard endpoints present
- ✓ All main.py endpoints present
- ✓ Trading ability confirmed
- ✓✓✓ ALL CRITICAL VERIFICATIONS PASSED - BOT READY FOR TRADING ✓✓✓

---

## After Running

The script will automatically:
- Save results to `droplet_final_verification_results.json`
- Commit and push results to Git
- I will then pull the results and confirm everything works

---

## Alternative: Automatic via Git Pull

If you just run `git pull origin main`, the post-merge hook will automatically:
1. Run `FINAL_DROPLET_VERIFICATION.sh`
2. Run `FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh`
3. Run complete verification
4. Push results back to Git

So you can also just run:
```bash
cd ~/stock-bot && git pull origin main
```

---

**Status:** Ready for droplet verification. All local tests passed.

