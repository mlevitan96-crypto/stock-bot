# B2 Rollback Drill Proof

**Generated (UTC):** 2026-03-05T15:48:01.782922+00:00

## Drill steps

1. **B2 OFF:** Set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false, restart stock-bot.
   - Env: `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false`
   - Health 200: True

2. **B2 ON:** Set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true, restart stock-bot.
   - Env: `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true`
   - Health 200: True

## Result

Rollback drill passed. One-config flip + restart is verified; B2 is re-enabled for continued live paper test.
