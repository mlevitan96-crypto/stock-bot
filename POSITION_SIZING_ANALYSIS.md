# Position Sizing Analysis

**Date:** 2026-01-05  
**Issue:** Position sizes are around 1% instead of expected 1.5%

---

## Current Implementation

### Position Sizing Logic in `decide_and_execute()`

**Location:** `main.py` lines 4505-4506, 4532-4533, 4546-4547

```python
notional_target = Config.SIZE_BASE_USD
qty = max(1, int(notional_target / ref_price))
```

**Problem:** Uses **fixed dollar amount** (`Config.SIZE_BASE_USD`) instead of percentage of account equity.

### Configuration

**From `config/registry.py` line 170:**
```python
POSITION_SIZE_USD = get_env("POSITION_SIZE_USD", 500, float)
```

**Note:** `SIZE_BASE_USD` is not found in config - it may be using a default or hardcoded value.

### Risk Management Module

**From `risk_management.py` line 296-306:**
```python
def calculate_position_size(account_equity: float) -> float:
    """Calculate position size based on account equity"""
    limits = get_risk_limits()
    
    dynamic_size = account_equity * limits["risk_per_trade_pct"]  # 1.5% for paper
    
    # Clamp between min and max
    return max(
        limits["min_position_dollar"],
        min(dynamic_size, limits["max_position_dollar"])
    )
```

**Expected:** 1.5% of account equity = $825 for $55k paper account

---

## The Issue

1. **Current:** Position sizing uses fixed `Config.SIZE_BASE_USD` (likely $500-550)
2. **Expected:** Should use `risk_management.calculate_position_size(account_equity)` = 1.5% of equity

**Result:** If account is $55k and SIZE_BASE_USD is $550, that's 1% instead of 1.5% ($825).

---

## Solution

Update `decide_and_execute()` to use dynamic position sizing from risk management module:

```python
# Instead of:
notional_target = Config.SIZE_BASE_USD
qty = max(1, int(notional_target / ref_price))

# Should be:
from risk_management import calculate_position_size
account = self.executor.api.get_account()
account_equity = float(account.equity)
notional_target = calculate_position_size(account_equity)  # 1.5% of equity
qty = max(1, int(notional_target / ref_price))
```

This would ensure:
- Paper account ($55k): $825 per position (1.5%)
- Live account ($10k): $150 per position (1.5%)
- Scales dynamically as equity changes

---

## Additional Checks Needed

1. **Verify signals are firing:**
   - Check `logs/attribution.jsonl` for recent trades
   - Check `state/blocked_trades.jsonl` for blocked signals
   - Check `logs/gate.jsonl` for gate blocks

2. **Verify signal scoring:**
   - Check if composite scores are being calculated
   - Verify UW flow cache is populated
   - Check if signals are passing gates

3. **Verify position sizing:**
   - Check actual notional values in recent trades
   - Compare to account equity percentage
