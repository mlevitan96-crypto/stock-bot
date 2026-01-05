# Scoring Engine Fix - Deployed

## Date: 2026-01-05

## Fix Applied

**Problem:** Signals with score=0.00 and source=unknown were being logged because `flow_clusters` (unscored) were being used when composite scoring didn't run.

**Root Cause:** 
- When composite scoring doesn't run (cache empty or use_composite=False), `clusters` stayed as `flow_clusters`
- `flow_clusters` from `cluster_signals()` don't have `composite_score` or `source` fields
- These unscored clusters got logged to `signals.jsonl` with score=0.00

**Fix:**
Added `else` clause after composite scoring block to clear `clusters` when composite scoring should run but doesn't:
- If cache exists but composite didn't run → clear clusters (prevent unscored signals)
- If cache is empty → clear clusters (prevent unscored signals)

This ensures unscored `flow_clusters` are NEVER logged.

## Deployment Status

✅ Code fixed
✅ Committed and pushed to Git
✅ Pulled to droplet
✅ Service restarted

## Expected Results

After this fix:
- No signals with score=0.00 should be logged
- No signals with source=unknown should be logged
- If composite scoring runs → only scored clusters logged
- If composite scoring doesn't run → no clusters logged (empty list)

## Next Steps

Wait 2-5 minutes for new signals and verify:
- Signals have scores > 0.0
- Signals have source="composite_v3"
- No signals with score=0.00

---

**Status:** ✅ FIX DEPLOYED - Awaiting verification
