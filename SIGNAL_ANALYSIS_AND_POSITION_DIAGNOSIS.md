# Signal Generation & Position Analysis

**Date:** 2026-01-06  
**Analysis of:** Why bot has 0 positions and what signals are generating

## Diagnostic Results

### Signal Generation Status

**Recent Signals:**
- Total signals in log: 2,000
- Recent signals: 20
- **ALL recent signals show:** `score=0.00, source=unknown`
- This indicates signals are being generated from flow_trades, NOT composite scoring

### Composite Scoring Status

**Recent Attribution Records (last 30):**
- Total attribution records: 2,560
- **Recent decisions: 0 signals, 30 rejected**
- **Score range: 0.03 - 0.58, avg=0.24**
- **All 30 recent records: decision=rejected**
- **Threshold being used: 3.50** (NOT 2.7 - fix not deployed!)

**Recent Scores:**
- C: score=0.56, rejected (threshold=2.70)
- TSLA: score=0.56, rejected (threshold=2.70)
- JNJ: score=0.08, rejected (threshold=2.70)
- COST: score=0.27, rejected (threshold=2.70)
- SPY: score=0.25, rejected (threshold=2.70)

**Composite Gate Events (last 20):**
- Total: 20,570 events
- **Recent: 0 accepted, 20 rejected**
- All showing: `score=X.XX < threshold=3.50`

### Run Cycles

**Recent Cycles (last 10):**
- All cycles: `clusters=0, orders=0`
- Composite enabled: `true`
- Current P&L: -$12.15 (2 trades, 0% win rate)
- Total trades: 2

### Gate Events

**Recent Gate Events:**
- Total: 33,134 events
- Recent types:
  - `momentum_ignition_passed`: 7
  - `already_positioned`: 6
  - `expectancy_blocked`: 5
  - `momentum_ignition_blocked`: 4
  - `max_new_positions_per_cycle_reached`: 3

**Recent Rejections:**
- META: expectancy_blocked, score=0.00
- TSLA: expectancy_blocked, score=0.00
- QQQ: momentum_ignition_blocked, score=0.00
- SPY: momentum_ignition_blocked, score=0.00

## Root Causes Identified

### 1. ❌ Fixes NOT Deployed on Droplet
- **Threshold:** Still 3.50 (should be 2.7)
- **enrich_signal fix:** Unknown if deployed
- **Action Required:** Deploy fixes and restart bot

### 2. ❌ Scores Still Very Low (0.03-0.58)
Even after fixes, scores would be low. Possible reasons:
- Cache data has low `conviction` values (< 0.1)
- Cache data missing `sentiment` or has "NEUTRAL"
- Freshness is very low (< 0.3), killing scores
- Dark pool data missing or weak

### 3. ❌ No Clusters Created
- Composite scoring creates clusters when `gate_result = True`
- But scores are 0.03-0.58, threshold is 3.50 → all rejected
- Result: 0 clusters → 0 orders

## Immediate Actions Required

### 1. Deploy Fixes to Droplet
```bash
cd /root/stock-bot
git pull origin main
# Restart bot to load new code
systemctl restart trading-bot.service
```

### 2. Verify Cache Data Quality
Check if cache has good conviction values:
```bash
python3 -c "import json; cache = json.load(open('data/uw_flow_cache.json')); \
symbols = [k for k in cache.keys() if not k.startswith('_')]; \
print(f'Symbols: {len(symbols)}'); \
for s in symbols[:5]: \
    data = cache[s]; \
    print(f'{s}: conviction={data.get(\"conviction\")}, sentiment={data.get(\"sentiment\")}')"
```

### 3. Check Freshness Values
Low freshness (0.1) suggests cache is stale (> 2 hours old). Check:
```bash
python3 -c "import json, time; cache = json.load(open('data/uw_flow_cache.json')); \
symbols = [k for k in cache.keys() if not k.startswith('_')]; \
for s in symbols[:3]: \
    data = cache[s]; \
    last_update = data.get('_last_update', 0); \
    age_hours = (time.time() - last_update) / 3600 if last_update else 999; \
    print(f'{s}: last_update={age_hours:.1f}h ago')"
```

## Expected After Fixes Deploy

1. **Threshold:** Will be 2.7 (allows signals >= 2.7 to pass)
2. **enrich_signal:** Will include sentiment & conviction
3. **Scores:** Should increase if cache has good conviction values
   - If conviction = 0.5-0.9: flow_component = 2.4 * 0.5-0.9 = 1.2-2.16
   - Composite raw should be 2.5-4.0 (with other components)
4. **Clusters:** Should be created when scores >= 2.7
5. **Orders:** Should be placed when clusters pass all gates

## If Scores Still Low After Fixes

If scores remain < 2.7 after fixes deploy, the issue is **cache data quality**:
- Cache may have low conviction values (< 0.2)
- Cache may be stale (> 2 hours old, freshness kills scores)
- Dark pool data may be missing or weak
- Need to investigate why UW daemon isn't populating good data

## Next Steps

1. ✅ Deploy fixes to droplet
2. ✅ Restart bot service
3. ⏳ Wait 1-2 cycles
4. ⏳ Check scores again (should see 2.5-4.0 range)
5. ⏳ Check clusters (should be > 0)
6. ⏳ Check orders (should be > 0)

---

**Status:** Fixes ready, need deployment and restart
