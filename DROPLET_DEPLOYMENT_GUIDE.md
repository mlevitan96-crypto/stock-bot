# Droplet Deployment Guide - Learning Powerhouse

## Deployment Strategy

**RECOMMENDATION: Incremental Deployment**

Deploy in phases to minimize risk and allow monitoring:

1. **Phase 1 (SAFE - Deploy Now):** Exit learning + Profit target learning
2. **Phase 2 (After Phase 1 Stable):** Risk limit learning + Execution quality learning
3. **Phase 3 (Future):** Additional optimizations

---

## Phase 1: Exit & Profit Target Learning (SAFE TO DEPLOY NOW)

### What's Included:
- ✅ Exit threshold optimization
- ✅ Close reason performance analysis
- ✅ Exit signal weight updates
- ✅ Profit target & scale-out optimization

### Deployment Steps:

```bash
# 1. SSH into droplet
ssh your_user@your_droplet_ip

# 2. Navigate to project directory
cd ~/stock-bot  # or wherever your project is

# 3. Pull latest changes
git pull origin main

# 4. Activate virtual environment (if using one)
source venv/bin/activate  # or: python3 -m venv venv && source venv/bin/activate

# 5. Install any new dependencies (if needed)
pip install -r requirements.txt

# 6. Run tests to verify
python test_learning_system.py

# Expected output: "TEST SUMMARY: 6 passed, 0 failed"

# 7. Restart services
# If using process-compose:
process-compose down
process-compose up -d

# OR if using systemd:
sudo systemctl restart stock-bot

# OR if running manually:
# Stop current process (Ctrl+C or kill)
# Start: python main.py
```

### Verification:

```bash
# 1. Check logs for learning cycle
tail -f logs/comprehensive_learning.log

# 2. Check that learning orchestrator is running
# Look for: "Starting comprehensive learning cycle"

# 3. After market close, verify learning results
# Check: data/comprehensive_learning.jsonl
# Should see exit_thresholds and profit_targets analysis

# 4. Verify no errors
grep -i error logs/comprehensive_learning.log | tail -20
```

### Monitoring (First 24-48 Hours):

1. **Check Learning Cycle Runs:**
   ```bash
   # Should run after market close
   grep "Learning cycle complete" logs/comprehensive_learning.log | tail -5
   ```

2. **Verify No Regressions:**
   - Trading continues normally
   - Exits still work
   - Profit targets still trigger
   - No new errors in logs

3. **Check Learning Output:**
   ```bash
   # View latest learning results
   tail -50 data/comprehensive_learning.jsonl | jq .
   ```

---

## Phase 2: Risk Limits & Execution Quality (Deploy After Phase 1 Stable)

### What's Included:
- ✅ Risk limit optimization (CONSERVATIVE - only tightens)
- ✅ Execution quality learning

### Deployment Steps:

**Same as Phase 1, but wait until:**
- Phase 1 has run for at least 3-5 trading days
- No errors observed
- Learning cycle completing successfully

### Additional Verification:

```bash
# Check risk limit recommendations
grep "Risk limit recommendation" logs/comprehensive_learning.log

# Check execution quality analysis
grep "execution_quality" data/comprehensive_learning.jsonl | tail -1 | jq .
```

---

## Full Deployment (All at Once - If You Prefer)

If you want to deploy everything at once:

```bash
# Follow Phase 1 steps above
# All features are backward compatible and safe
```

---

## Rollback Plan (If Needed)

If something goes wrong:

```bash
# 1. Stop services
process-compose down
# OR: sudo systemctl stop stock-bot

# 2. Revert to previous commit
git log --oneline -10  # Find previous good commit
git checkout <previous_commit_hash>

# 3. Restart services
process-compose up -d
# OR: sudo systemctl start stock-bot
```

---

## Files Changed (For Reference)

### Modified:
- `comprehensive_learning_orchestrator.py` - Added all learning methods
- `main.py` - Enhanced exit attribution logging
- `test_learning_system.py` - Test suite

### New:
- `LEARNING_POWERHOUSE_IMPLEMENTATION.md` - Documentation
- `COMPREHENSIVE_HARDCODED_AUDIT.md` - Full audit
- `BEST_IN_BREED_ROADMAP.md` - Roadmap
- `EXIT_LEARNING_IMPLEMENTATION.md` - Exit learning docs

---

## Environment Variables (If Needed)

No new environment variables required. All learning uses existing configuration.

---

## Troubleshooting

### Learning Cycle Not Running:

```bash
# Check if orchestrator is initialized
grep "ComprehensiveLearningOrchestrator" logs/*.log

# Check for import errors
python -c "from comprehensive_learning_orchestrator import ComprehensiveLearningOrchestrator; print('OK')"
```

### Learning Results Empty:

```bash
# Check if attribution.jsonl exists and has data
wc -l logs/attribution.jsonl
tail -5 logs/attribution.jsonl | jq .
```

### Errors in Learning:

```bash
# Check for specific errors
grep -i error logs/comprehensive_learning.log | tail -20

# Learning errors don't crash the system - they're logged and ignored
```

---

## Success Criteria

After deployment, you should see:

1. ✅ Learning cycle runs after market close
2. ✅ Exit threshold recommendations appear in logs
3. ✅ Profit target recommendations appear in logs
4. ✅ No trading regressions
5. ✅ All existing functionality works

---

## Next Steps After Deployment

1. **Monitor for 3-5 trading days**
2. **Review learning recommendations** in logs
3. **Verify gradual adjustments** are being applied
4. **Check that P&L improves** over time
5. **Proceed to Phase 2** when ready

---

## Questions?

If you encounter issues:
1. Check logs first: `logs/comprehensive_learning.log`
2. Verify tests pass: `python test_learning_system.py`
3. Check that attribution data exists: `logs/attribution.jsonl`

All learning is **non-blocking** - errors don't crash the trading system.
