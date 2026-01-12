# Comprehensive Trading Investigation Report
**Date:** 2026-01-10  
**Issue:** GOOG concentration and losses  
**Status:** 🔴 CRITICAL INVESTIGATION

---

## Executive Summary

Based on comprehensive codebase analysis and system architecture review, I've identified several potential root causes for the GOOG concentration and losses:

### Key Findings

1. **Concentration Gate Logic** - The portfolio concentration gate (line 5292 in main.py) blocks bullish entries when net_delta_pct > 70%, but this should PREVENT concentration, not cause it
2. **GOOG vs GOOGL Symbol Handling** - The system tracks both GOOG and GOOGL separately, which could lead to over-concentration if both are being traded
3. **Signal Generation** - Need to verify if UW API is generating excessive GOOG signals
4. **Position Reconciliation** - Potential state desync between bot's internal state and Alpaca API

---

## Detailed Analysis

### 1. Portfolio Concentration Gate (V4.0)

**Location:** `main.py` lines 5143-5315

**Current Logic:**
```python
# Calculate net long-delta exposure
if len(open_positions) > 0 and net_delta_pct > 70.0 and c.get("direction") == "bullish":
    # BLOCKS bullish entries when portfolio is >70% long-delta
    log_event("gate", "concentration_blocked_bullish", ...)
    continue
```

**Issue:** This gate should PREVENT concentration, but if:
- GOOG signals are consistently the strongest (highest composite scores)
- Other symbols are being blocked by this gate
- GOOG signals pass all other gates
- Then GOOG would accumulate while other symbols are blocked

**Root Cause Hypothesis:**
- If portfolio becomes >70% long-delta from GOOG positions
- All OTHER bullish signals get blocked
- But GOOG signals might still pass if they're bearish, or if the gate logic has a bug
- OR: GOOG signals are so strong they pass before concentration reaches 70%

### 2. Symbol Duplication (GOOG vs GOOGL)

**Finding:** The system tracks both GOOG and GOOGL as separate symbols:
- Both appear in `TICKERS` list (line 268)
- Both have separate profiles in `profiles.json`
- Theme mapping treats them as separate (Technology sector)

**Risk:** If both GOOG and GOOGL are generating signals:
- They're counted as separate positions
- Theme risk gate might not catch the combined exposure
- Could lead to 2x concentration in the same underlying

### 3. Signal Scoring and Ranking

**Location:** `main.py` line 5201
```python
# CRITICAL: Sort clusters by composite_score DESC to trade strongest signals first
clusters_sorted = sorted(clusters, key=lambda x: x.get("composite_score", 0.0), reverse=True)
```

**Issue:** If GOOG consistently has the highest composite scores:
- It gets prioritized in every cycle
- Other symbols with lower scores get passed over
- Over time, this leads to GOOG accumulation

**Need to Verify:**
- What are the actual composite scores for GOOG vs other symbols?
- Is GOOG scoring artificially high due to:
  - Strong UW flow signals
  - High conviction scores
  - Whale activity
  - Dark pool prints

### 4. Position Limits and Capacity

**Location:** `main.py` line 5198
```python
MAX_NEW_POSITIONS_PER_CYCLE = 6
```

**Issue:** If GOOG signals are consistently in the top 6:
- Every cycle, GOOG gets a new position
- Other symbols never get a chance
- Over multiple cycles, GOOG accumulates

### 5. Theme Risk Gate

**Location:** `main.py` lines 5317-5322
```python
if Config.ENABLE_THEME_RISK:
    violations = correlated_exposure_guard(open_positions, self.theme_map, Config.MAX_THEME_NOTIONAL_USD)
    sym_theme = self.theme_map.get(symbol, "general")
    if sym_theme in violations:
        log_event("gate", "theme_exposure_blocked", ...)
        continue
```

**Issue:** Need to verify:
- Is `MAX_THEME_NOTIONAL_USD` being enforced?
- Is GOOG/GOOGL properly mapped to Technology theme?
- Is the theme gate working correctly?

### 6. Cooldown Period

**Location:** Multiple gates check cooldown (COOLDOWN_MINUTES_PER_TICKER, default: 15 minutes)

**Issue:** If GOOG signals are coming in every cycle:
- Cooldown might not be preventing re-entry
- Or cooldown is being bypassed for high-conviction signals (score >= 4.0)

---

## Immediate Actions Required

### 1. Check Current Positions (DROPLET)

**Command to run on droplet:**
```bash
cd /root/stock-bot
source venv/bin/activate  # If venv exists
python3 -c "
from main import Config
import alpaca_trade_api as api
a = api.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
pos = a.list_positions()
print(f'Total positions: {len(pos)}')
goog = [p for p in pos if 'GOOG' in p.symbol]
print(f'GOOG positions: {len(goog)}')
for p in pos:
    print(f'{p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f} | P/L: ${float(p.unrealized_pl):.2f}')
"
```

### 2. Check Recent Signals

**Check UW cache:**
```bash
cd /root/stock-bot
python3 -c "
import json
cache = json.load(open('data/uw_flow_cache.json'))
for sym in ['GOOG', 'GOOGL']:
    if sym in cache:
        d = cache[sym]
        print(f'{sym}: conviction={d.get(\"conviction\", 0):.3f}, sentiment={d.get(\"sentiment\", \"MISS\")}')
"
```

### 3. Check Recent Logs

**Check for GOOG activity:**
```bash
cd /root/stock-bot
tail -500 logs/trading.log | grep -E 'GOOG|composite_score|concentration_gate' | tail -50
```

### 4. Check Blocked Trades

**See what's being blocked:**
```bash
cd /root/stock-bot
tail -500 logs/trading.log | grep -E 'blocked|gate.*blocked' | tail -30
```

---

## Root Cause Hypotheses

### Hypothesis 1: GOOG Signals Are Artificially Strong
- UW API is generating strong GOOG signals consistently
- Composite scoring favors GOOG
- GOOG passes all gates while other symbols fail

### Hypothesis 2: Concentration Gate Bug
- Gate logic has a bug that allows GOOG through
- Or gate is failing open (error handling allows trading)
- GOOG accumulates while others are blocked

### Hypothesis 3: Symbol Duplication
- Both GOOG and GOOGL are being traded
- Theme risk gate doesn't catch combined exposure
- Leads to 2x concentration

### Hypothesis 4: Position Reconciliation Issue
- Bot's internal state shows different positions than Alpaca
- Reconciliation is failing or throttled
- Bot thinks it has fewer GOOG positions than it actually does

### Hypothesis 5: Score Ranking Bias
- GOOG consistently ranks #1 in composite scores
- Gets priority in every cycle
- Other symbols never get a chance

---

## Recommended Fixes

### Fix 1: Add Symbol-Level Position Limit
```python
MAX_POSITIONS_PER_SYMBOL = 1  # Prevent multiple positions in same symbol
```

### Fix 2: Normalize GOOG/GOOGL
- Treat GOOG and GOOGL as the same symbol for position limits
- Combine their theme exposure calculations

### Fix 3: Add Diversification Gate
- Require minimum number of different symbols before allowing more of same symbol
- Example: Must have 3+ different symbols before allowing 2nd position in any symbol

### Fix 4: Review Composite Scoring
- Check if GOOG is getting artificial boosts
- Verify component weights are balanced
- Check for data quality issues in UW signals

### Fix 5: Enhanced Logging
- Log why each symbol passes/fails gates
- Log composite scores for all symbols in each cycle
- Log concentration calculations

---

## Next Steps

1. **IMMEDIATE:** Get current positions from droplet (see commands above)
2. **IMMEDIATE:** Check recent logs for GOOG activity
3. **URGENT:** Verify concentration gate is working correctly
4. **URGENT:** Check if both GOOG and GOOGL are being traded
5. **HIGH:** Review composite scores for GOOG vs other symbols
6. **HIGH:** Check theme risk gate enforcement
7. **MEDIUM:** Implement symbol-level position limits
8. **MEDIUM:** Normalize GOOG/GOOGL handling

---

## Files to Review

1. `main.py` lines 5143-5315 (concentration gate)
2. `main.py` line 5201 (score sorting)
3. `main.py` line 5198 (position limits)
4. `config/theme_risk.json` (theme mappings)
5. `profiles.json` (GOOG vs GOOGL profiles)
6. Recent logs: `logs/trading.log`
7. UW cache: `data/uw_flow_cache.json`
8. Orders: `data/order.jsonl`

---

## Investigation Status

- ✅ Codebase analysis complete
- ✅ Concentration gate logic reviewed
- ✅ Signal scoring logic reviewed
- ⏳ **PENDING:** Current positions check (needs droplet access with proper Python environment)
- ⏳ **PENDING:** Recent logs analysis
- ⏳ **PENDING:** Signal score comparison
- ⏳ **PENDING:** Root cause confirmation

---

**CRITICAL:** Need to access droplet with proper Python environment to get actual position data and confirm root cause.
