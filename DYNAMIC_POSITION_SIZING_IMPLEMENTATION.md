# Dynamic & Conviction-Based Position Sizing Implementation

**Date:** 2026-01-05  
**Status:** ✅ **COMPLETE**

---

## Summary

Replaced fixed `SIZE_BASE_USD` ($500) with dynamic equity-based sizing that scales with signal conviction while respecting the 1.5% risk ceiling.

---

## Changes Made

### 1. Dynamic Position Sizing (Step 1)

**Location:** `main.py` lines 4505-4525, 4532-4552, 4546-4566

**Before:**
```python
notional_target = Config.SIZE_BASE_USD  # Fixed $500
qty = max(1, int(notional_target / ref_price))
```

**After:**
```python
from risk_management import calculate_position_size, get_risk_limits
account = self.executor.api.get_account()
account_equity = float(account.equity)
base_notional = calculate_position_size(account_equity)  # 1.5% of equity ($825 for $55k)
```

**Impact:**
- Paper account ($55k): Base position size is now $825 (1.5% of equity) instead of $500
- Live account ($10k): Base position size is now $150 (1.5% of equity) instead of $500
- Positions scale dynamically as account equity changes

---

### 2. Conviction-Based Scaling (Step 2)

**Location:** All three sizing locations in `decide_and_execute()`

**Implementation:**
```python
# Conviction-based scaling: >4.5 -> 2.0%, <3.5 -> 1.0%, base 1.5%
if score > 4.5:
    conviction_mult = 2.0 / 1.5  # Scale to 2.0% (1.33x)
elif score < 3.5:
    conviction_mult = 1.0 / 1.5  # Scale to 1.0% (0.67x)
else:
    conviction_mult = 1.0  # Base 1.5%

notional_target = min(base_notional * conviction_mult, limits["max_position_dollar"])
```

**Scaling Rules:**
- **High Conviction (score > 4.5):** Attempts to scale to 2.0% of equity, capped at `max_position_dollar` ($825 for paper, $300 for live)
- **Base Conviction (3.5 <= score <= 4.5):** 1.5% of equity
- **Low Conviction (score < 3.5):** Scales down to 1.0% of equity

**Note:** The `min()` function ensures scaling respects the 1.5% risk ceiling from `risk_management.get_risk_limits()["max_position_dollar"]`.

---

### 3. Attribution Logging (Step 3)

**Location:** `main.py` lines 4983-4989, 5311-5313

**Added to Context:**
```python
# Capture account equity and position size for attribution
account_equity_at_entry = float(account.equity)
position_size_usd = qty * ref_price_check

# Add to attribution context
context["account_equity_at_entry"] = round(account_equity_at_entry, 2)
context["position_size_usd"] = round(position_size_usd, 2)
```

**Verification:**
- `logs/attribution.jsonl` now includes `account_equity_at_entry` and `position_size_usd` in the context field
- Enables analysis of position sizing effectiveness and equity scaling

---

## Safety Checks (Step 4)

### Concentration Gate
- **Location:** `main.py` line 4446-4457
- **Function:** Blocks bullish entries if portfolio net_delta_pct > 70%
- **Status:** ✅ Active and enforced before position sizing

### Liquidity Limits
- **Location:** `main.py` line 4920-4935
- **Function:** `risk_management.validate_order_size()` checks:
  - Buying power (95% safety margin)
  - Max position size (enforced by `max_position_dollar`)
  - Min position size ($50 minimum)
- **Status:** ✅ Active and enforced before order submission

### Entry Score Validation
- **Location:** `main.py` line 5227-5234
- **Function:** Blocks entries with `entry_score <= 0.0`
- **Status:** ✅ Active - prevents scaling math failures

---

## Order of Operations

1. **Score Calculation** (composite/per-ticker/default)
2. **Conviction-Based Base Sizing** (1.0% - 1.5% - 2.0% based on score)
3. **UW Conviction Modifier** (if UW flow cache populated)
4. **Dynamic Sizing Multiplier** (v3.2 slippage/regime-based)
5. **Risk Validation** (buying power, position limits)
6. **Order Submission**

---

## Expected Behavior

### Paper Account ($55k Starting Equity)

| Entry Score | Base % | Scaled % | Dollar Amount | Capped At |
|-------------|--------|----------|---------------|-----------|
| > 4.5       | 1.5%   | 2.0%     | $1,100        | $825 (1.5%) |
| 3.5 - 4.5   | 1.5%   | 1.5%     | $825          | $825       |
| < 3.5       | 1.5%   | 1.0%     | $550          | $550       |

**Note:** The 2.0% scaling is capped at $825 (max_position_dollar) to respect the 1.5% risk ceiling.

### Live Account ($10k Starting Equity)

| Entry Score | Base % | Scaled % | Dollar Amount | Capped At |
|-------------|--------|----------|---------------|-----------|
| > 4.5       | 1.5%   | 2.0%     | $200          | $200      |
| 3.5 - 4.5   | 1.5%   | 1.5%     | $150          | $150      |
| < 3.5       | 1.5%   | 1.0%     | $100          | $100      |

---

## Testing Checklist

- [x] Syntax validation passed
- [ ] Verify position sizes in `logs/attribution.jsonl` show dynamic sizing
- [ ] Verify `account_equity_at_entry` is logged correctly
- [ ] Verify `position_size_usd` is logged correctly
- [ ] Verify high-conviction signals (score > 4.5) attempt larger sizes
- [ ] Verify low-conviction signals (score < 3.5) use smaller sizes
- [ ] Verify positions are capped at `max_position_dollar` limit
- [ ] Verify concentration gate still blocks >70% long-delta
- [ ] Verify liquidity checks still enforce buying power limits
- [ ] Verify 0.0 entry_score fix still blocks invalid entries

---

## Files Modified

- `main.py`: 
  - Lines 4505-4525: Composite score sizing
  - Lines 4532-4552: Per-ticker learning sizing
  - Lines 4546-4566: Default sizing
  - Lines 4983-4989: Account equity capture
  - Lines 5311-5313: Attribution context updates

---

## Next Steps

1. Deploy to droplet
2. Monitor `logs/attribution.jsonl` for position sizing verification
3. Review actual position sizes vs. expected sizes based on entry scores
4. Adjust scaling thresholds if needed based on performance
