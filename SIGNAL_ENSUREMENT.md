# Signal Ensurement System

## Overview

All signals (insider, iv_term_skew, smile_slope) are now automatically computed, persisted, and used in trade decisions.

## How It Works

### 1. Automatic Cache Enrichment
- **Service**: `cache_enrichment_service.py` runs every 60 seconds
- **Function**: Computes `iv_term_skew` and `smile_slope` for all symbols
- **Persistence**: Writes computed values back to `data/uw_flow_cache.json`
- **Insider**: Ensures `insider` structure exists (defaults to NEUTRAL if no data)

### 2. On-Demand Computation
- **Location**: `main.py` during signal processing
- **Function**: If signals are missing, computes them on-the-fly
- **Persistence**: Immediately writes back to cache using `atomic_write_json`
- **Fallback**: Always ensures signals exist before scoring

### 3. Self-Healing System
- **Service**: `self_healing_monitor.py` runs every 5 minutes
- **Function**: Detects missing signals and triggers enrichment
- **Action**: Computes missing signals and updates cache
- **Logging**: All healing attempts logged to `logs/self_healing.log`

### 4. Signal Usage in Trade Decisions

All signals are used in composite scoring (`uw_composite_v2.py`):

- **insider**: Weight 0.5, contributes to composite score
  - BULLISH: `0.5 * (0.50 + modifier)`
  - BEARISH: `0.5 * (0.50 - abs(modifier))`
  - NEUTRAL: `0.5 * 0.25`

- **iv_term_skew**: Weight 0.6, contributes to composite score
  - Aligned with flow: `0.6 * abs(skew) * 1.3` (boost)
  - Not aligned: `0.6 * abs(skew) * 0.7` (penalty)

- **smile_slope**: Weight 0.35, contributes to composite score
  - `0.35 * abs(smile_slope)`

## Verification

### Check if signals are computed:
```bash
cd /root/stock-bot
python3 -c "
import json
from pathlib import Path
cache = json.loads(Path('data/uw_flow_cache.json').read_text())
for sym in ['AAPL', 'MSFT', 'NVDA', 'QQQ', 'SPY']:
    if sym in cache:
        data = cache[sym]
        print(f'{sym}: iv_term_skew={data.get(\"iv_term_skew\")}, smile_slope={data.get(\"smile_slope\")}, insider={bool(data.get(\"insider\"))}')
"
```

### Check if signals are used:
```bash
# Check composite scoring includes these signals
grep -n "insider_component\|iv_component\|smile_component" uw_composite_v2.py
```

### Force enrichment now:
```bash
cd /root/stock-bot && source venv/bin/activate && python3 cache_enrichment_service.py
```

## Services Running

1. **Cache Enrichment Service**: Runs every 60 seconds (background thread in main.py)
2. **Self-Healing Monitor**: Runs every 5 minutes (background thread in main.py)
3. **On-Demand Computation**: Happens during each signal evaluation in main.py

## Expected Behavior

After deployment:
- All signals will be computed within 60 seconds
- Cache will be updated with computed values
- SRE monitoring will show signals as "healthy"
- Trade decisions will use all signals in composite scoring

## Complete Ecosystem: The Feedback Loop

The system operates as a continuous learning cycle:

```
┌─────────────────┐
│ 1. SIGNALS      │ → Computed (iv_term_skew, smile_slope, insider)
│   Computed      │   Stored in cache
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. TRADING      │ → Signals used in composite scoring
│   Decisions     │   Adaptive weights applied
│   Execution     │   Trades executed
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. LEARNING     │ → Trade outcomes logged
│   Outcomes      │   P&L attribution tracked
│   Analysis      │   Component performance measured
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. WEIGHTS      │ → Adaptive weights updated
│   Updated       │   Bayesian learning applied
│   Applied       │   Multipliers adjusted (0.25x-2.5x)
└────────┬────────┘
         │
         └──────────┐
                    │
         ┌──────────▼──────────┐
         │ Back to Step 1      │
         │ (Improved Signals)  │
         └─────────────────────┘
```

### Ecosystem Health Check

Run the comprehensive health check to verify all stages:

```bash
cd /root/stock-bot && source venv/bin/activate && python3 ecosystem_health_check.py
```

This checks:
1. ✅ Signals are computed and stored
2. ✅ Signals are used in trade decisions
3. ✅ Trades are logged for learning
4. ✅ Learning system processes outcomes
5. ✅ Adaptive weights are updated
6. ✅ Updated weights affect future scoring

### Key Files in the Ecosystem

- **Signals**: `data/uw_flow_cache.json` (computed signals)
- **Trading**: `data/live_orders.jsonl` (executed trades)
- **Learning**: `data/attribution.jsonl`, `data/feature_store.jsonl` (trade outcomes)
- **Weights**: `state/signal_weights.json` (adaptive weights)
- **Profiles**: `profiles.json` (per-ticker learning)

## Troubleshooting

If signals still show "no_data":
1. Check cache enrichment service is running: `ps aux | grep cache_enrichment`
2. Check logs: `tail -f logs/cache_enrichment.log`
3. Manually run enrichment: `python3 cache_enrichment_service.py`
4. Check cache file: `cat data/uw_flow_cache.json | python3 -m json.tool | head -50`

If ecosystem health check shows issues:
1. Run full health check: `python3 ecosystem_health_check.py`
2. Check each stage individually
3. Verify learning is active: Check `state/signal_weights.json` exists
4. Verify trades are being logged: Check `data/attribution.jsonl` has recent entries
5. Verify adaptive weights are loaded: Check logs for "adaptive_weights_active"
