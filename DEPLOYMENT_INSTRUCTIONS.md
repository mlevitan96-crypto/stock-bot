# Deploy Adaptive Weights Fix - Instructions

**Target:** 104.236.102.57 (stock-bot)  
**Service:** stockbot.service  
**Fix Script:** FIX_ADAPTIVE_WEIGHTS_REDUCTION.py

## Quick Deploy (Recommended)

Run on droplet:

```bash
cd /root/stock-bot
git pull origin main
python3 FIX_ADAPTIVE_WEIGHTS_REDUCTION.py
sudo systemctl restart stockbot
```

## One-Liner from Local Machine

```bash
ssh alpaca "cd /root/stock-bot && git pull origin main && python3 FIX_ADAPTIVE_WEIGHTS_REDUCTION.py && sudo systemctl restart stockbot"
```

## What the Fix Does

1. **Creates Backup** - Backs up `state/signal_weights.json` before changes
2. **Resets Multipliers** - Resets all component multipliers from 0.25x → 1.0x
3. **Resets Beta Distributions** - Resets regime beta distributions to defaults
4. **Preserves Structure** - Maintains weight file structure for compatibility

## Expected Results

**Before Fix:**
- 19 components at 0.25x multiplier (74.4% reduction)
- Average score: 1.232 (below 2.7 threshold)
- 0 orders (all signals below threshold)

**After Fix:**
- All components at 1.0x multiplier (default)
- Average score: ~4-5 (above 2.7 threshold)
- Trades should start executing
- Stagnation alerts should decrease

## Verification

Check weights after fix:

```bash
ssh alpaca "cd /root/stock-bot && python3 -c \"
from uw_composite_v2 import get_weight, WEIGHTS_V3
print('options_flow:', get_weight('options_flow', 'mixed'), '(expected: 2.4)')
print('dark_pool:', get_weight('dark_pool', 'mixed'), '(expected: 1.3)')
print('iv_term_skew:', get_weight('iv_term_skew', 'mixed'), '(expected: 0.6)')
\""
```

Expected output:
- options_flow: 2.4 ✅
- dark_pool: 1.3 ✅ (was 0.333)
- iv_term_skew: 0.6 ✅ (was 0.154)

## Service Status

Check service status:
```bash
ssh alpaca "sudo systemctl status stockbot"
```

Check service logs:
```bash
ssh alpaca "journalctl -u stockbot -n 50 --no-pager"
```
