# PHASE 5 — LABELING, NAMING, AND MISMATCHES

**Date:** 2026-01-10  
**Scope:** Active codebase (excluding `archive/`)

## EXECUTIVE SUMMARY

This document audits naming consistency, log message accuracy, and config key alignment across the codebase. Issues found are categorized by severity, with fixes applied where safe and low-risk.

---

## 1. CONFIG KEY CONSISTENCY

### 1.1 Environment Variable Names

**Status:** ✅ **CONSISTENT**

**Findings:**
- `TRADING_MODE` - used consistently (defaults to "PAPER")
- `LIVE_TRADING_ACK` - used consistently (required for LIVE mode)
- `REQUIRE_LIVE_ACK` - used consistently (boolean flag)
- `ALPACA_KEY`, `ALPACA_SECRET`, `ALPACA_BASE_URL` - used consistently
- `UW_API_KEY` - used consistently

**Recommendation:** ✅ No action needed - environment variable names are consistent

---

### 1.2 JSON Config Keys

**Status:** ✅ **CONSISTENT**

**Findings:**
- `config/theme_risk.json` - uses nested structure (no direct `trading_mode` key)
- `config/execution_router.json` - uses nested structure
- `config/startup_safety_suite_v2.json` - uses nested structure
- No conflicts between JSON keys and environment variables

**Recommendation:** ✅ No action needed - JSON config structure is separate from environment variables

---

### 1.3 Config Access Patterns

**Location:** `main.py:255`, `config/registry.py`

**Status:** ✅ **CONSISTENT**

**Findings:**
- `Config.TRADING_MODE` accessed via `get_env("TRADING_MODE", "PAPER")` (line 255)
- `Config.LIVE_TRADING_ACK` accessed via `get_env("LIVE_TRADING_ACK", "")` (line 258)
- `Config.REQUIRE_LIVE_ACK` accessed via `get_env("REQUIRE_LIVE_ACK", "true").lower() == "true"` (line 259)
- All config access uses consistent pattern: `Config.KEY_NAME`

**Recommendation:** ✅ No action needed - config access is consistent

---

## 2. FUNCTION NAMING

### 2.1 Mode Checking Functions

**Status:** ✅ **CONSISTENT AND CLEAR**

**Findings:**

#### `trading_is_armed()` (`main.py:562`)
- **Name:** `trading_is_armed`
- **Behavior:** Returns True if bot can place NEW entry orders
- **Accuracy:** ✅ Name accurately reflects behavior
- **Documentation:** Clear docstring (lines 563-566)

#### `_is_paper_endpoint()` (`main.py:556`)
- **Name:** `_is_paper_endpoint`
- **Behavior:** Checks if URL contains "paper-api.alpaca.markets"
- **Accuracy:** ✅ Name accurately reflects behavior
- **Note:** Private function (leading underscore) - appropriate

#### `_is_live_endpoint()` (`main.py:550`)
- **Name:** `_is_live_endpoint`
- **Behavior:** Checks if URL contains "api.alpaca.markets" and NOT "paper-api"
- **Accuracy:** ✅ Name accurately reflects behavior
- **Note:** Private function (leading underscore) - appropriate

#### `is_paper_mode()` (`risk_management.py:52`)
- **Name:** `is_paper_mode`
- **Behavior:** Returns True if `Config.TRADING_MODE.upper() == "PAPER"`
- **Accuracy:** ✅ Name accurately reflects behavior
- **Usage:** Used consistently in `risk_management.py`

**Recommendation:** ✅ No action needed - function names are clear and accurate

---

### 2.2 Reconciliation Functions

**Status:** ✅ **CONSISTENT AND CLEAR**

**Findings:**

#### `ensure_reconciled()` (`main.py:2996`)
- **Name:** `ensure_reconciled`
- **Behavior:** Lazy reconciliation - calls `_safe_reconcile()` if not yet reconciled
- **Accuracy:** ✅ Name accurately reflects behavior (ensures reconciliation happens)
- **Documentation:** Clear docstring (line 2997)

#### `_safe_reconcile()` (`main.py:2979`)
- **Name:** `_safe_reconcile`
- **Behavior:** Reconciles positions with retry and exponential backoff
- **Accuracy:** ✅ Name accurately reflects behavior (safe = with retries)
- **Documentation:** Clear docstring (line 2980)

**Recommendation:** ✅ No action needed - function names are clear and accurate

---

### 2.3 Entry/Exit Functions

**Status:** ✅ **CONSISTENT AND CLEAR**

**Findings:**

#### `submit_entry()` (`main.py:3227`)
- **Name:** `submit_entry`
- **Behavior:** Submits entry order with validation and error handling
- **Accuracy:** ✅ Name accurately reflects behavior

#### `evaluate_exits()` (`main.py:4606`)
- **Name:** `evaluate_exits`
- **Behavior:** Evaluates and executes exit orders for open positions
- **Accuracy:** ✅ Name accurately reflects behavior

#### `execute_displacement()` (`main.py:4278`)
- **Name:** `execute_displacement`
- **Behavior:** Executes displacement - exits old position to make room for new signal
- **Accuracy:** ✅ Name accurately reflects behavior
- **Documentation:** Clear docstring (lines 4279-4282)

**Recommendation:** ✅ No action needed - function names are clear and accurate

---

## 3. LOG MESSAGE ACCURACY

### 3.1 Mode-Related Log Messages

**Status:** ✅ **ACCURATE**

**Findings:**

#### Log: "not_armed_skip_entries" (`main.py:7726-7728`)
```python
log_event("run_once", "not_armed_skip_entries",
          trading_mode=Config.TRADING_MODE, base_url=Config.ALPACA_BASE_URL,
          require_live_ack=Config.REQUIRE_LIVE_ACK)
```
- **Location:** Called when `not armed` (line 7725)
- **Behavior:** Skips entry orders, sets `orders = []` (line 7729)
- **Accuracy:** ✅ Log message accurately reflects behavior

#### Log: "reduce_only_broker_degraded" (`main.py:7723`)
```python
log_event("run_once", "reduce_only_broker_degraded", action="skip_entries")
```
- **Location:** Called when `degraded_mode` is True (line 7720)
- **Behavior:** Skips entry orders, allows exits (line 7724)
- **Accuracy:** ✅ Log message accurately reflects behavior

#### Log: "not_reconciled_skip_entries" (`main.py:7731`)
```python
log_event("run_once", "not_reconciled_skip_entries", action="skip_entries")
```
- **Location:** Called when `not reconciled_ok` (line 7730)
- **Behavior:** Skips entry orders, sets `orders = []` (line 7732)
- **Accuracy:** ✅ Log message accurately reflects behavior

**Recommendation:** ✅ No action needed - log messages are accurate

---

### 3.2 Trading Mode in Metrics

**Location:** `main.py:7791`

**Status:** ✅ **ACCURATE**

**Findings:**
```python
"mode": "PAPER" if Config.TRADING_MODE == "PAPER" else "LIVE"
```
- **Behavior:** Returns "PAPER" or "LIVE" string based on `Config.TRADING_MODE`
- **Accuracy:** ✅ Accurate - correctly maps config to string
- **Note:** Ternary expression is clear and correct

**Recommendation:** ✅ No action needed

---

## 4. COMMENTS ACCURACY

### 4.1 Code Comments

**Status:** ✅ **MOSTLY ACCURATE - MINOR NOTES**

**Findings:**

#### Comment: "EXECUTION & POSITION MGMT (Alpaca paper)" (`main.py:2965`)
- **Location:** Section header for `AlpacaExecutor` class
- **Issue:** Comment says "Alpaca paper" but class supports both PAPER and LIVE modes
- **Current Behavior:** Class works with both modes (uses `Config.ALPACA_BASE_URL`)
- **Recommendation:** ⚠️ **MINOR:** Comment is outdated - class supports both modes

**Action:** Update comment to reflect that it supports both PAPER and LIVE modes.

---

#### Comment: "CRITICAL FIX: Only register signals when script is run directly" (`main.py:9190`)
- **Location:** Before signal registration
- **Accuracy:** ✅ Comment accurately explains why signal registration is conditional
- **Status:** Comment is accurate and helpful

**Recommendation:** ✅ No action needed

---

#### Comment: "Live-trading arming gate (prevents accidental real-money trading)" (`main.py:256`)
- **Location:** Before `LIVE_TRADING_ACK` config
- **Accuracy:** ✅ Comment accurately explains purpose
- **Status:** Comment is accurate and helpful

**Recommendation:** ✅ No action needed

---

### 4.2 Docstrings

**Status:** ✅ **ACCURATE**

**Findings:**
- `trading_is_armed()` has clear docstring (lines 563-566)
- `ensure_reconciled()` has clear docstring (line 2997)
- `execute_displacement()` has clear docstring (lines 4279-4282)
- `submit_entry()` has clear docstring (lines 3228-3234)

**Recommendation:** ✅ No action needed - docstrings are accurate

---

## 5. VARIABLE NAMING

### 5.1 Mode-Related Variables

**Status:** ✅ **CONSISTENT AND CLEAR**

**Findings:**
- `mode` - used for mode string (e.g., line 567: `mode = (Config.TRADING_MODE or "PAPER").upper()`)
- `armed` - used for trading arm status (e.g., line 7713: `armed = trading_is_armed()`)
- `reconciled_ok` - used for reconciliation status (e.g., line 7714: `reconciled_ok = False`)
- `degraded_mode` - used for broker connectivity status (e.g., line 7720)

**Recommendation:** ✅ No action needed - variable names are clear and consistent

---

### 5.2 Config Class Variables

**Status:** ✅ **CONSISTENT**

**Findings:**
- All config variables use UPPERCASE (e.g., `TRADING_MODE`, `LIVE_TRADING_ACK`)
- Pattern is consistent throughout `Config` class
- Matches Python convention for constants

**Recommendation:** ✅ No action needed - naming convention is consistent

---

## 6. IDENTIFIED ISSUES AND FIXES

### 6.1 Outdated Comment

**Location:** `main.py:2965`

**Issue:**
```python
# =========================
# EXECUTION & POSITION MGMT (Alpaca paper)
# =========================
```

**Problem:**
- Comment says "(Alpaca paper)" but class supports both PAPER and LIVE modes
- Misleading - suggests class only works with paper trading

**Fix:**
Update comment to reflect that it supports both modes:

```python
# =========================
# EXECUTION & POSITION MGMT (Alpaca API - PAPER/LIVE)
# =========================
```

**Action:** ✅ **APPLIED** - Comment updated to accurately reflect behavior

---

## 7. SUMMARY OF ISSUES

| Issue | Location | Severity | Status | Action Taken |
|-------|----------|----------|--------|--------------|
| Outdated comment: "Alpaca paper" | `main.py:2965` | LOW | ✅ Fixed | Updated to "Alpaca API - PAPER/LIVE" |

---

## 8. STRENGTHS IDENTIFIED

### ✅ Excellent Naming Practices Found:

1. **Consistent Naming Conventions:**
   - Config variables use UPPERCASE
   - Private functions use leading underscore
   - Function names clearly describe behavior
   - Boolean functions use `is_` prefix

2. **Clear Function Names:**
   - `trading_is_armed()` - clearly indicates boolean check
   - `ensure_reconciled()` - clearly indicates action with guarantee
   - `submit_entry()` - clearly indicates action
   - `evaluate_exits()` - clearly indicates action

3. **Accurate Log Messages:**
   - Log messages accurately reflect code behavior
   - Event names are descriptive (e.g., "not_armed_skip_entries")
   - Log context includes relevant config values

4. **Helpful Comments:**
   - Comments explain "why" not just "what"
   - CRITICAL FIX comments explain rationale
   - Docstrings are clear and accurate

---

## 9. RECOMMENDATIONS

### Immediate Actions (Completed):
1. ✅ **Fixed outdated comment** - Updated "Alpaca paper" to "Alpaca API - PAPER/LIVE"

### Future Improvements (None Required):
1. ✅ **No other naming issues found** - Naming is consistent and clear

---

## 10. VALIDATION RESULTS

✅ **Overall Naming & Labeling Health:** EXCELLENT
- Config keys are consistent
- Function names are clear and accurate
- Log messages accurately reflect behavior
- Comments are mostly accurate (1 minor fix applied)
- Variable names are consistent
- No misleading names detected

---

## 11. DETAILED FINDINGS BY CATEGORY

### 11.1 Config Key Consistency

**Status:** ✅ **EXCELLENT**
- Environment variables use consistent naming
- JSON config uses nested structure (separate from env vars)
- Config access uses consistent pattern (`Config.KEY_NAME`)
- No spelling inconsistencies found

---

### 11.2 Function Naming

**Status:** ✅ **EXCELLENT**
- Function names accurately describe behavior
- Naming conventions are consistent
- Private functions properly marked with underscore
- Boolean functions use `is_` prefix

---

### 11.3 Log Message Accuracy

**Status:** ✅ **EXCELLENT**
- Log messages accurately reflect code behavior
- Event names are descriptive
- Context includes relevant values
- No misleading log messages found

---

### 11.4 Comments Accuracy

**Status:** ✅ **GOOD** (1 minor fix applied)
- Most comments are accurate and helpful
- CRITICAL FIX comments explain rationale
- Docstrings are clear
- 1 outdated comment found and fixed

---

### 11.5 Variable Naming

**Status:** ✅ **EXCELLENT**
- Variable names are clear and consistent
- Config variables use UPPERCASE convention
- Local variables use lowercase_with_underscores
- No misleading variable names found

---

**END OF PHASE 5 REPORT**
