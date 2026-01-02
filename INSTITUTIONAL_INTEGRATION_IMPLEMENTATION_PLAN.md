# Total Institutional Integration & Shadow Risk Mitigation - Implementation Plan

**Date:** 2026-01-02  
**Status:** IMPLEMENTATION IN PROGRESS  
**Authoritative Source:** MEMORY_BANK.md

---

## Overview

This document outlines the implementation plan for eliminating technical debt, mismatched labels, and data leaks across UW, Alpaca, and the Bayesian Loop. All fixes are designed to meet institutional-grade standards.

---

## 1. Trade Persistence & State Recovery

### Current State
- Position metadata stores: `entry_score`, `components`, `market_regime`, `direction`
- Missing: `regime_modifier`, `ignition_status` (momentum filter result)

### Required Changes

#### A. Enhance `_persist_position_metadata()` in `main.py`

**Location:** `main.py::AlpacaExecutor._persist_position_metadata()` (line ~3615)

**Add Parameters:**
- `regime_modifier: float` - The regime multiplier applied to composite score
- `ignition_status: str` - Momentum ignition filter status ("passed", "blocked", "not_checked")

**Enhanced Metadata Structure:**
```python
metadata[symbol] = {
    "entry_ts": entry_ts.isoformat(),
    "entry_price": entry_price,
    "qty": qty,
    "side": side,
    "entry_score": entry_score,
    "components": components or {},
    "market_regime": market_regime,
    "direction": direction,
    "regime_modifier": regime_modifier,  # NEW
    "ignition_status": ignition_status,  # NEW
    "updated_at": datetime.utcnow().isoformat()
}
```

#### B. Update `mark_open()` to capture and persist new fields

**Location:** `main.py::AlpacaExecutor.mark_open()` (line ~3580)

**Changes:**
1. Extract `regime_modifier` from composite score calculation
2. Capture `ignition_status` from momentum filter check
3. Pass both to `_persist_position_metadata()`

#### C. Enhance `PositionReconciliationLoop` to serialize FULL state

**Location:** `position_reconciliation_loop.py::reconcile()` (line ~252)

**Changes:**
1. Load existing metadata and preserve ALL fields (not just entry_score)
2. When creating metadata for missing positions, include default values:
   - `regime_modifier: 1.0` (default)
   - `ignition_status: "unknown"` (if not available)
3. Ensure `executor_opens` dict includes all metadata fields

#### D. Update `reload_positions_from_metadata()` to restore ALL fields

**Location:** `main.py::AlpacaExecutor.reload_positions_from_metadata()` (line ~3679)

**Changes:**
1. Restore `regime_modifier` to `self.opens[symbol]`
2. Restore `ignition_status` to `self.opens[symbol]`
3. Ensure all fields are available for exit evaluation

---

## 2. API Resilience (UW & Alpaca)

### Implementation

#### A. Exponential Backoff Decorator

**File:** `api_resilience.py` (ALREADY CREATED)

**Features:**
- Exponential backoff with configurable parameters
- Retries on 429, 500, 502, 503, 504 errors
- Maximum delay cap (60 seconds)

#### B. Signal Queue for Rate Limits

**File:** `api_resilience.py` (ALREADY CREATED)

**Features:**
- Queue signals when 429 (rate limit) is hit
- Persistent queue on disk (`state/signal_queue.json`)
- Queue processing on next cycle

#### C. Integration Points

**UW API Calls:**
- `uw_flow_daemon.py` - Wrap all UW API calls with `@api_call_with_backoff()`
- `uw_enrichment_v2.py` - Wrap enrichment API calls
- `main.py::UWClient._get()` - Wrap HTTP requests

**Alpaca API Calls:**
- `main.py::AlpacaExecutor` - Wrap order submission, position fetching
- `position_reconciliation_loop.py` - Wrap Alpaca API calls

**Panic Regime Queueing:**
- Check if current regime is PANIC before queuing
- Queue signals on 429 errors during PANIC regimes
- Process queue on next cycle when API available

---

## 3. Portfolio Heat Map (Concentration Gate)

### Implementation

#### A. Calculate Portfolio Long-Delta

**Location:** `main.py::decide_and_execute()` (line ~4210)

**New Function:**
```python
def calculate_portfolio_long_delta(positions: list, account_equity: float) -> float:
    """
    Calculate portfolio long-delta exposure as percentage of account equity.
    
    Long-delta = sum of (position_value * delta) for all long positions
    Short-delta = sum of (position_value * delta) for all short positions
    Net delta = long_delta - short_delta
    
    Returns: net_delta_pct (as percentage of account equity)
    """
    # For stock positions, delta = 1.0 for long, -1.0 for short
    net_delta = 0.0
    for pos in positions:
        qty = float(getattr(pos, "qty", 0))
        market_value = float(getattr(pos, "market_value", 0))
        if qty > 0:  # Long position
            net_delta += market_value
        elif qty < 0:  # Short position
            net_delta -= abs(market_value)
    
    net_delta_pct = (net_delta / account_equity * 100) if account_equity > 0 else 0.0
    return net_delta_pct
```

#### B. Add Concentration Gate Check

**Location:** `main.py::decide_and_execute()` (after position loading, before entry loop)

**Implementation:**
```python
# PORTFOLIO CONCENTRATION GATE: Block bullish entries if >70% long-delta
try:
    account = self.executor.api.get_account()
    account_equity = float(account.equity)
    open_positions = self.executor.api.list_positions()
    
    net_delta_pct = calculate_portfolio_long_delta(open_positions, account_equity)
    
    if net_delta_pct > 70.0 and c.get("direction") == "bullish":
        log_event("gate", "concentration_blocked_bullish",
                 symbol=symbol, net_delta_pct=round(net_delta_pct, 2),
                 reason="portfolio_already_70pct_long_delta")
        log_blocked_trade(symbol, "concentration_gate", score,
                         direction=c.get("direction"),
                         decision_price=ref_price_check,
                         components=comps,
                         net_delta_pct=net_delta_pct)
        continue  # Skip this bullish entry
except Exception as conc_error:
    log_event("concentration_gate", "error", symbol=symbol, error=str(conc_error))
    # Continue on error (fail open)
```

---

## 4. UW-to-Alpaca Pipeline (Correlation ID)

### Implementation

#### A. Generate Correlation ID at UW Alert

**Location:** Where UW alerts are processed (likely in signal generation)

**Implementation:**
```python
import uuid
correlation_id = f"uw_{uuid.uuid4().hex[:16]}"  # 16-char hex ID
```

#### B. Pass Correlation ID Through Pipeline

**Flow:**
1. UW Alert → Signal Generation → Store correlation_id in cluster/composite dict
2. Signal Generation → Entry Decision → Pass correlation_id to `submit_entry()`
3. Entry Decision → Order Submission → Include correlation_id in `client_order_id`
4. Order Submission → Attribution Logging → Include correlation_id in attribution

#### C. Update Attribution Logging

**Location:** `main.py::log_exit_attribution()` (line ~960)

**Add to context:**
```python
context = {
    ...
    "correlation_id": metadata.get("correlation_id") or info.get("correlation_id"),  # NEW
    ...
}
```

#### D. Update Order Submission

**Location:** `main.py::AlpacaExecutor.submit_entry()` (line ~2956)

**Include correlation_id in client_order_id:**
```python
if client_order_id_base:
    # Include correlation_id if available
    correlation_id = kwargs.get("correlation_id") or client_order_id_base.split("_")[-1] if "_" in client_order_id_base else None
    client_order_id = f"{client_order_id_base}-{correlation_id or 'nocid'}"
```

---

## 5. Bayesian Loop (Regime-Specific Isolation)

### Current State
- `SignalWeightModel.update_regime_beta()` exists (line ~303 in adaptive_signal_optimizer.py)
- `LearningOrchestrator.record_trade_outcome()` calls `update_regime_beta()` (line ~732)

### Verification Required

**Location:** `adaptive_signal_optimizer.py::LearningOrchestrator.record_trade_outcome()`

**Verify:**
1. `update_regime_beta()` is called with correct regime parameter
2. Each regime has separate Beta distribution
3. Wins in PANIC regime do NOT affect MIXED regime weights

**Current Code (VERIFIED):**
```python
# Line ~732 in adaptive_signal_optimizer.py
self.entry_model.update_regime_beta(component, regime, win, pnl)
```

**Verification:**
- `update_regime_beta()` (line ~303) updates regime-specific Beta distribution
- Each component has separate Beta distributions per regime
- Isolation is correct - no cross-regime contamination

**Status:** ✅ **ALREADY IMPLEMENTED CORRECTLY** - No changes needed

---

## 6. Monitoring Protocol

### Observational Lockdown
- NO further code changes permitted after this block is deployed
- System enters "Observational Lockdown" for Friday EOW Audit
- All changes must be committed and pushed to GitHub

### Final System Health Report

**Generate report with:**
1. All fixes applied and verified
2. System state snapshot
3. Configuration status
4. Integration points verified
5. Ready for EOW Audit

---

## Implementation Order

1. ✅ API Resilience Module (CREATED - `api_resilience.py`)
2. ⏳ Trade Persistence Enhancements (position metadata)
3. ⏳ Portfolio Concentration Gate
4. ⏳ Correlation ID Tracking
5. ⏳ Verify Bayesian Regime Isolation (ALREADY CORRECT)
6. ⏳ Final Health Report

---

## Files to Modify

1. `main.py` - Multiple locations:
   - `_persist_position_metadata()` - Add regime_modifier, ignition_status
   - `mark_open()` - Capture and pass new fields
   - `reload_positions_from_metadata()` - Restore new fields
   - `decide_and_execute()` - Add concentration gate, correlation ID
   - `log_exit_attribution()` - Include correlation_id
   - `submit_entry()` - Include correlation_id in order ID

2. `position_reconciliation_loop.py`:
   - `reconcile()` - Preserve all metadata fields

3. Signal generation code:
   - Add correlation_id generation at UW alert processing

4. `adaptive_signal_optimizer.py`:
   - ✅ VERIFIED - Regime isolation already correct

---

## Testing Checklist

- [ ] Position metadata includes all fields after entry
- [ ] Position reconciliation preserves all metadata
- [ ] Positions reload correctly with all fields on restart
- [ ] API calls use exponential backoff
- [ ] Signals queued on 429 errors during PANIC
- [ ] Concentration gate blocks bullish entries >70% long-delta
- [ ] Correlation IDs flow from UW → Alpaca → Attribution
- [ ] Regime-specific weights remain isolated
- [ ] Final health report generated and committed

---

## Next Steps

1. Implement trade persistence enhancements
2. Integrate API resilience module
3. Add portfolio concentration gate
4. Implement correlation ID tracking
5. Generate final health report
6. Commit all changes to GitHub
7. Enter Observational Lockdown
