# Risk Management Specification - Implementation Review

**Date**: 2025-12-17  
**Reviewer**: Code Review  
**Status**: ✅ **READY FOR IMPLEMENTATION** with minor clarifications

---

## Overall Assessment

**EXCELLENT SPECIFICATION** - This addresses all 5 critical gaps identified in the audit. The spec is well-structured and production-ready with minor suggestions below.

---

## ✅ **Strengths**

1. **Dual Mode Support** - PAPER vs LIVE with different risk profiles
2. **Multiple Safety Layers** - Daily loss, equity floor, drawdown, exposure limits
3. **Both Percentage & Dollar Caps** - Prevents edge cases
4. **Position Sizing** - Dynamic with hard caps
5. **Comprehensive Freeze Conditions** - Covers all risk scenarios

---

## ⚠️ **Clarifications & Recommendations**

### 1. **Mode Configuration** (MINOR)

**Current Spec:**
```python
PAPER_MODE = get_env_bool("PAPER_MODE", default=True)
```

**Codebase Reality:**
- Codebase uses `Config.TRADING_MODE = "PAPER" or "LIVE"`
- This is actually better because it's more explicit

**Recommendation:**
```python
# Use existing pattern, but add helper
def is_paper_mode():
    return Config.TRADING_MODE == "PAPER"

# Then use:
if is_paper_mode():
    STARTING_EQUITY = 55000
else:
    STARTING_EQUITY = 10000
```

**Status**: ✅ Minor change, easy to align

---

### 2. **Peak Equity Tracking** (IMPORTANT)

**Spec Says:**
> "Peak equity must be tracked persistently"

**Current State:**
- Codebase has `RAMP_DRAWDOWN_LIMIT` but no persistent peak equity tracking
- Need to implement peak equity file

**Implementation Required:**
```python
PEAK_EQUITY_FILE = Path("state/peak_equity.json")

def load_peak_equity():
    """Load peak equity from persistent storage"""
    if PEAK_EQUITY_FILE.exists():
        try:
            data = json.loads(PEAK_EQUITY_FILE.read_text())
            return float(data.get("peak_equity", STARTING_EQUITY))
        except:
            return STARTING_EQUITY
    return STARTING_EQUITY

def update_peak_equity(current_equity):
    """Update peak equity if current is higher"""
    peak = load_peak_equity()
    if current_equity > peak:
        atomic_write_json(PEAK_EQUITY_FILE, {
            "peak_equity": current_equity,
            "last_updated": datetime.now(timezone.utc).isoformat()
        })
        return current_equity
    return peak
```

**Status**: ✅ Needs implementation - straightforward

---

### 3. **Daily P&L Calculation** (IMPORTANT)

**Spec Requires:**
```python
def check_daily_loss_limit(daily_pnl, account_equity):
```

**Question**: How to calculate `daily_pnl`?

**Options:**
1. Sum all trades from `logs/attribution.jsonl` for today
2. Use account equity change: `current_equity - equity_at_market_open`
3. Track running daily P&L in state file

**Recommendation**: **Option 2** (account equity change) is most reliable:
- Doesn't depend on trade logs
- Accounts for unrealized P&L
- Real-time accurate

**Implementation:**
```python
# Store equity at market open
DAILY_START_EQUITY_FILE = Path("state/daily_start_equity.json")

def get_daily_start_equity():
    """Get equity at start of trading day"""
    if DAILY_START_EQUITY_FILE.exists():
        try:
            data = json.loads(DAILY_START_EQUITY_FILE.read_text())
            date = data.get("date")
            if date == datetime.now(timezone.utc).date().isoformat():
                return float(data.get("equity"))
        except:
            pass
    return None

def set_daily_start_equity(equity):
    """Set equity at start of trading day"""
    atomic_write_json(DAILY_START_EQUITY_FILE, {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "equity": equity
    })

def calculate_daily_pnl(current_equity):
    """Calculate today's P&L"""
    start_equity = get_daily_start_equity()
    if start_equity is None:
        # First check today - use current as baseline
        set_daily_start_equity(current_equity)
        return 0.0
    return current_equity - start_equity
```

**Status**: ✅ Needs implementation detail - provided above

---

### 4. **Exposure Limits Calculation** (MINOR CLARIFICATION)

**Spec Says:**
```python
MAX_SYMBOL_EXPOSURE = STARTING_EQUITY * 0.10   # 10%
MAX_SECTOR_EXPOSURE = STARTING_EQUITY * 0.30   # 30%
```

**Question**: Should limits be based on `STARTING_EQUITY` or `current_equity`?

**Spec Intent**: Based on `STARTING_EQUITY` (fixed limits)
- **Pros**: Prevents over-concentration even if account shrinks
- **Cons**: Limits become more restrictive as equity drops

**Recommendation**: **Use STARTING_EQUITY** (as spec'd) - this is correct for risk management. If you lose money, you should reduce exposure, not maintain it.

**Status**: ✅ Correct as specified

---

### 5. **Position Sizing Clarification** (MINOR)

**Spec Says:**
```python
def calculate_position_size(account_equity):
    dynamic_size = account_equity * RISK_PER_TRADE_PCT
    return clamp(dynamic_size, MIN_POSITION_DOLLAR, MAX_POSITION_DOLLAR)
```

**Question**: Should position size shrink as equity drops?

**Spec Intent**: Yes, dynamic sizing based on current equity
- **Pros**: Maintains risk percentage as account changes
- **Cons**: Smaller positions as losses occur (but this is risk management)

**Recommendation**: ✅ **Correct** - Dynamic sizing is the right approach

**Alternative Consideration**: You might want a floor:
```python
# Don't shrink below 50% of max if above equity floor
if account_equity >= MIN_ACCOUNT_EQUITY:
    min_allowed = MAX_POSITION_DOLLAR * 0.5
    return clamp(dynamic_size, min_allowed, MAX_POSITION_DOLLAR)
```

**Status**: ✅ Spec is correct, optional enhancement above

---

### 6. **Idempotency Key** (ENHANCEMENT)

**Spec Says:**
```python
def generate_idempotency_key(symbol, side, qty):
    return f"{symbol}_{side}_{qty}_{int(time.time()*1000)}_{uuid4().hex[:6]}"
```

**Current Codebase**: No idempotency keys used in order submission

**Enhancement Needed:**
- Use Alpaca's `client_order_id` parameter
- Store recent keys to prevent reuse within time window

**Implementation:**
```python
def generate_idempotency_key(symbol, side, qty):
    """Generate unique order ID for idempotency"""
    timestamp_ms = int(time.time() * 1000)
    unique_id = uuid4().hex[:8]
    return f"{symbol}_{side}_{qty}_{timestamp_ms}_{unique_id}"

# Use in order submission:
client_order_id = generate_idempotency_key(symbol, side, qty)
order = api.submit_order(
    symbol=symbol,
    qty=qty,
    side=side,
    type="limit",
    client_order_id=client_order_id,  # Prevents duplicates
    ...
)
```

**Status**: ✅ Needs implementation - straightforward

---

### 7. **Sector Lookup** (REQUIREMENT)

**Spec Requires:**
```python
sector = get_sector(p.symbol)
```

**Question**: Does this function exist?

**Answer**: Need to implement or use existing data source

**Options:**
1. Hard-code common symbols (AAPL = Technology, etc.)
2. Use Alpaca's asset details API
3. Use external API (e.g., Yahoo Finance)

**Recommendation**: Start with hard-coded mapping for common symbols, add API lookup as fallback:
```python
SECTOR_MAP = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "JPM": "Financial", "BAC": "Financial", "GS": "Financial",
    "XOM": "Energy", "CVX": "Energy",
    # ... expand as needed
}

def get_sector(symbol):
    """Get sector for symbol"""
    # Try hard-coded map first
    if symbol in SECTOR_MAP:
        return SECTOR_MAP[symbol]
    
    # Fallback: try to get from Alpaca asset details
    try:
        asset = api.get_asset(symbol)
        # Alpaca doesn't provide sector directly, would need another source
        return "Unknown"
    except:
        return "Unknown"
```

**Status**: ⚠️ **Needs implementation** - moderate complexity

---

### 8. **Circuit Breaker Implementation** (REFERENCE)

**Spec Says:**
> "Implement circuit breaker wrapper around all Alpaca API calls"

**Recommendation**: Use the circuit breaker class from the audit document, or create new one. The spec provides parameters but not implementation - that's fine, the audit has the code.

**Status**: ✅ Reference provided in audit

---

### 9. **Freeze Implementation** (VERIFICATION)

**Spec Lists Freeze Conditions** - Need to verify `freeze_trading()` function exists and works correctly.

**Current State:**
- Codebase has `state/governor_freezes.json` pattern
- Need to ensure all freeze conditions use this mechanism

**Implementation Pattern:**
```python
def freeze_trading(reason, **details):
    """Freeze trading immediately"""
    freeze_path = Path("state/governor_freezes.json")
    
    # Load existing freezes
    if freeze_path.exists():
        freezes = json.loads(freeze_path.read_text())
    else:
        freezes = {}
    
    # Add new freeze
    freeze_key = reason.replace(" ", "_").lower()
    freezes[freeze_key] = {
        "active": True,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details
    }
    
    # Write atomically
    atomic_write_json(freeze_path, freezes)
    
    # Log and alert
    log_event("freeze", "activated", reason=reason, **details)
    send_alert("FREEZE_ACTIVATED", reason=reason, **details)
```

**Status**: ✅ Pattern exists, needs verification it's used consistently

---

## 📋 **Implementation Checklist**

### Phase 1: Core Risk Limits (Critical)
- [ ] Implement mode detection (PAPER vs LIVE)
- [ ] Add daily loss limit check (both $ and %)
- [ ] Add account equity floor check
- [ ] Add maximum drawdown circuit breaker
- [ ] Implement peak equity tracking
- [ ] Implement daily start equity tracking

### Phase 2: Position & Exposure Limits
- [ ] Implement dynamic position sizing
- [ ] Add symbol exposure limit check
- [ ] Add sector exposure limit check
- [ ] Implement sector lookup function

### Phase 3: Order Safety
- [ ] Add order size validation against buying power
- [ ] Add idempotency key generation
- [ ] Use client_order_id in all order submissions

### Phase 4: API Resilience
- [ ] Implement circuit breaker for Alpaca API
- [ ] Add request timeouts to all API calls
- [ ] Wrap all API calls with circuit breaker

### Phase 5: Integration & Testing
- [ ] Integrate all checks into `run_once()` flow
- [ ] Ensure freeze mechanism works for all conditions
- [ ] Test in paper mode with $55k scaling
- [ ] Test all freeze conditions trigger correctly
- [ ] Validate exposure limits work correctly

---

## 🔧 **Code Integration Points**

### Where to Add Checks in `run_once()`:

```python
def run_once():
    # ... existing code ...
    
    # After position reconciliation:
    current_equity = float(api.get_account().equity)
    
    # 1. Check account equity floor
    check_account_equity_floor(current_equity)
    
    # 2. Update and check peak equity (drawdown)
    peak_equity = update_peak_equity(current_equity)
    check_drawdown(current_equity, peak_equity)
    
    # 3. Check daily loss limit
    daily_pnl = calculate_daily_pnl(current_equity)
    check_daily_loss_limit(daily_pnl, current_equity)
    
    # 4. Check exposure limits (before new orders)
    if not check_symbol_exposure(symbol, positions, current_equity):
        log_blocked_trade(symbol, "symbol_exposure_limit")
        continue
    
    if not check_sector_exposure(positions, current_equity):
        log_blocked_trade(symbol, "sector_exposure_limit")
        continue
    
    # 5. Validate order before submission
    try:
        validate_order(symbol, qty, side)
    except Exception as e:
        log_blocked_trade(symbol, "order_validation_failed", error=str(e))
        continue
    
    # ... rest of code ...
```

---

## ✅ **Final Verdict**

**SPECIFICATION STATUS: APPROVED FOR IMPLEMENTATION**

The specification is **excellent** and addresses all critical gaps. The recommendations above are:
- **Minor clarifications** (mode detection, exposure calculation basis)
- **Implementation details** (peak equity tracking, daily P&L calculation)
- **Enhancements** (sector lookup, idempotency)

**Ready to implement** with the clarifications provided.

---

## 🚀 **Next Steps**

1. Create new module: `risk_management.py` with all risk checks
2. Implement peak equity tracking
3. Implement daily P&L tracking
4. Integrate checks into `run_once()` flow
5. Test thoroughly in paper mode
6. Verify all freeze conditions work

**Estimated Implementation Time**: 2-3 hours for core functionality, 1-2 hours for testing
