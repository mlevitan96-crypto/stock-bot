# Droplet Investigation Summary
**Date:** 2026-01-10  
**Status:** Investigation Complete - Code Analysis Done, Direct Access Blocked

---

## Investigation Results

### ✅ Completed Analysis

1. **Codebase Review** - Comprehensive analysis of trading logic
2. **Concentration Gate Logic** - Reviewed V4.0 portfolio concentration gate (main.py lines 5143-5315)
3. **Signal Scoring** - Reviewed composite score ranking system (line 5201)
4. **Position Limits** - Reviewed MAX_NEW_POSITIONS_PER_CYCLE (line 5198)
5. **Theme Risk Gate** - Reviewed correlated_exposure_guard logic (lines 5317-5322)
6. **GOOG/GOOGL Handling** - Identified potential symbol duplication issue

### ⚠️ Blocked Access

**Issue:** Cannot directly access Alpaca API from droplet due to:
- `alpaca_trade_api` module not installed in system Python
- No virtual environment found at `/root/stock-bot/venv/`
- Bot process not currently running (no systemd service found)
- Data directories (`data/`, `logs/`, `state/`) don't exist yet

**This suggests:**
- Bot may not have been started yet today
- Or bot is running in a different environment/location
- Or dependencies need to be installed

---

## Root Cause Analysis (Based on Code Review)

### Primary Hypothesis: Score Ranking Bias

**Location:** `main.py` line 5201
```python
clusters_sorted = sorted(clusters, key=lambda x: x.get("composite_score", 0.0), reverse=True)
```

**Problem:**
- Bot sorts signals by composite score and trades strongest first
- If GOOG consistently scores highest, it gets priority every cycle
- With `MAX_NEW_POSITIONS_PER_CYCLE = 6`, GOOG can accumulate if it's always in top 6
- Other symbols get blocked by concentration gate once portfolio >70% long-delta

### Secondary Issues

1. **No Symbol-Level Position Limit**
   - Missing check to prevent multiple positions in same symbol
   - GOOG can accumulate across multiple cycles

2. **GOOG vs GOOGL Duplication**
   - System treats them as separate symbols
   - Could lead to 2x concentration in same underlying
   - Theme risk gate might not catch combined exposure

3. **Concentration Gate Limitation**
   - Only blocks NEW bullish entries when >70% long-delta
   - Doesn't prevent GOOG from accumulating if signals are bearish
   - Or if GOOG signals pass before reaching 70% threshold

---

## Immediate Actions Required

### 1. Start Bot and Check Positions

**On droplet, run:**
```bash
cd /root/stock-bot

# Check if bot is supposed to run via systemd
systemctl status stock-bot
# OR
systemctl status trading-bot

# If not running, check how to start it
# Look for: deploy_supervisor.py, main.py, or startup scripts

# Once bot is running, positions should appear
# Check via API endpoint if available:
curl http://localhost:8080/api/cockpit
```

### 2. Install Dependencies (if needed)

```bash
cd /root/stock-bot

# Check for requirements.txt
cat requirements.txt

# Install dependencies
pip3 install -r requirements.txt
# OR if using venv:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Get Current Positions

**Once dependencies are installed:**
```bash
cd /root/stock-bot
python3 get_positions_direct.py
```

**Or via main.py:**
```bash
cd /root/stock-bot
python3 -c "
import sys
sys.path.insert(0, '.')
from main import Config, StrategyEngine
engine = StrategyEngine()
positions = engine.executor.api.list_positions()
print(f'Positions: {len(positions)}')
for p in positions:
    print(f'{p.symbol}: {p.qty} @ \${float(p.avg_entry_price):.2f} | P/L: \${float(p.unrealized_pl):.2f}')
"
```

---

## Recommended Fixes

### Fix 1: Add Symbol-Level Position Limit

**Location:** `main.py` in `decide_and_execute()` function

**Add before line 5209 (for loop):**
```python
# Count existing positions per symbol
symbol_position_count = {}
for pos in open_positions:
    sym = pos.symbol
    symbol_position_count[sym] = symbol_position_count.get(sym, 0) + 1

# Inside the for loop (around line 5211), add:
symbol = c["ticker"]
if symbol_position_count.get(symbol, 0) >= 1:  # MAX 1 position per symbol
    log_event("gate", "symbol_position_limit", symbol=symbol, 
             existing_count=symbol_position_count.get(symbol, 0))
    continue
```

### Fix 2: Normalize GOOG/GOOGL

**Location:** `main.py` in `decide_and_execute()` function

**Add normalization function:**
```python
def normalize_symbol(symbol: str) -> str:
    """Normalize GOOG/GOOGL to single symbol for position limits"""
    if symbol in ("GOOG", "GOOGL"):
        return "GOOG"  # Use GOOG as canonical
    return symbol
```

**Use in position counting:**
```python
normalized_symbol = normalize_symbol(symbol)
if symbol_position_count.get(normalized_symbol, 0) >= 1:
    continue
```

### Fix 3: Enhanced Diversification Gate

**Add before concentration gate:**
```python
# Require minimum diversification before allowing more of same symbol
unique_symbols = len(set(p.symbol for p in open_positions))
if unique_symbols < 3 and symbol_position_count.get(symbol, 0) >= 1:
    log_event("gate", "diversification_required", 
             unique_symbols=unique_symbols, symbol=symbol)
    continue
```

---

## Files Modified/Created

1. ✅ `TRADING_INVESTIGATION_REPORT.md` - Comprehensive analysis
2. ✅ `get_positions_direct.py` - Script to get positions (needs deps)
3. ✅ `check_goog_droplet.py` - GOOG investigation script
4. ✅ `investigate_trading_droplet.py` - Full investigation script
5. ✅ `DROPLET_INVESTIGATION_SUMMARY.md` - This file

---

## Next Steps

1. **URGENT:** Start the bot on droplet (if not running)
2. **URGENT:** Install dependencies if missing
3. **URGENT:** Get actual current positions to confirm GOOG concentration
4. **HIGH:** Implement symbol-level position limit (Fix 1)
5. **HIGH:** Normalize GOOG/GOOGL handling (Fix 2)
6. **MEDIUM:** Add diversification gate (Fix 3)
7. **MEDIUM:** Review composite scoring for GOOG bias

---

## Investigation Status

- ✅ Codebase analysis complete
- ✅ Root cause hypotheses identified
- ✅ Recommended fixes documented
- ⏳ **PENDING:** Actual position data from droplet (blocked by missing dependencies)
- ⏳ **PENDING:** Bot startup/status check
- ⏳ **PENDING:** Implementation of fixes

---

**CRITICAL:** The bot needs to be running with proper dependencies to get actual position data. Once positions are confirmed, implement the recommended fixes immediately to prevent further GOOG concentration.
