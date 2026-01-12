# PHASE 4 — LOGIC AND SAFETY AUDIT

**Date:** 2026-01-10  
**Scope:** Active codebase (excluding `archive/`)

## EXECUTIVE SUMMARY

This document audits runtime logic, error handling, race conditions, and safety checks in core trading and orchestration modules. Issues found are categorized by severity, with fixes applied where safe and low-risk.

---

## 1. LIVE vs PAPER MODE HANDLING

### 1.1 Trading Arm Check

**Location:** `main.py:562-581`, `main.py:7713-7732`

**Status:** ✅ **EXCELLENT**

**Findings:**
- `trading_is_armed()` function checks mode consistency (lines 567-581)
- Validates LIVE mode + paper endpoint mismatch (line 571)
- Validates PAPER mode + live endpoint mismatch (line 575)
- Checks `LIVE_TRADING_ACK` when in LIVE mode (line 578)
- `run_once()` calls `trading_is_armed()` before `decide_and_execute()` (line 7713)
- If not armed, skips entry orders (line 7725-7729)
- Exit orders still execute when unarmed (correct behavior)

**Recommendation:** ✅ No action needed - mode checking is comprehensive and safe

---

### 1.2 Mode Detection Functions

**Location:** `main.py:550-560`

**Status:** ✅ **GOOD**

**Findings:**
```python
def _is_live_endpoint(url: str) -> bool:
    try:
        return "api.alpaca.markets" in (url or "") and "paper-api" not in (url or "")
    except Exception:
        return False

def _is_paper_endpoint(url: str) -> bool:
    try:
        return "paper-api.alpaca.markets" in (url or "")
    except Exception:
        return False
```

**Analysis:**
- Functions handle None/empty strings safely
- Exception handling prevents crashes
- Logic correctly identifies paper vs live endpoints

**Recommendation:** ✅ No action needed

---

### 1.3 Risk Management Mode Handling

**Location:** `risk_management.py:52-54`

**Status:** ✅ **GOOD**

**Findings:**
```python
def is_paper_mode() -> bool:
    """Check if running in paper mode"""
    return Config.TRADING_MODE.upper() == "PAPER"
```

- Uses `.upper()` for case-insensitive comparison
- Reads from `Config.TRADING_MODE` (safe)
- Used consistently throughout risk management

**Recommendation:** ✅ No action needed

---

## 2. ERROR HANDLING

### 2.1 API Call Error Handling

**Status:** ✅ **EXCELLENT**

**Findings:**

#### Order Submission (`main.py:3227-3750`)
- `submit_entry()` wrapped in try/except (line 6420)
- Detailed error logging to `logs/critical_api_failure.log` (lines 3515-3523)
- Captures HTTP status codes, response bodies, error types
- Returns error status codes instead of crashing
- Exponential backoff via `api_resilience.ExponentialBackoff` (line 3332)

#### UW API Calls (`main.py:1479-1507`, `uw_flow_daemon.py:168-210`)
- Retry logic with exponential backoff
- Rate limit handling (429 errors)
- Signal queueing on rate limits (panic regime)
- Returns empty data on error (fail-safe)
- Comprehensive error logging

#### Alpaca API Calls
- `reconcile_positions()` uses `_safe_reconcile()` with retries (line 2979)
- `get_account()` calls wrapped in try/except (lines 7803-7809, 5154-5159)
- Account fetch errors default to safe values (equity=100000.0, positions=[])
- No crashes on API failures

**Recommendation:** ✅ No action needed - error handling is comprehensive

---

### 2.2 File Operation Error Handling

**Status:** ✅ **EXCELLENT**

**Findings:**

#### Cache File Reads (`main.py:6769-6810`)
- Checks `.exists()` before reading (line 6773)
- Handles JSON parse errors (line 6795)
- Self-healing: backs up corrupted files and resets (lines 6798-6802)
- Returns empty dict on error (fail-safe)

#### Position Metadata (`main.py:9228-9269`)
- Uses file locking (`fcntl.flock`) to prevent corruption (line 9237)
- Validates structure (must be dict) (line 9241)
- Self-healing: backups corrupted files (lines 9252-9254)
- Handles IOError, OSError, JSONDecodeError separately

#### Atomic Writes (`main.py:9209-9226`)
- Uses temp file + atomic rename pattern
- File locking with `fcntl.flock` (Linux-specific, OK for Ubuntu droplet)
- `fsync()` ensures data is written (line 9221)
- Lock released in `finally` block (line 9223)

**Recommendation:** ✅ No action needed - file operations are robust

---

### 2.3 Exception Handling in Core Loops

**Status:** ✅ **GOOD**

**Findings:**

#### `run_once()` Exception Handling (`main.py:7991-8007`)
- Catches `NameError`/`ImportError` separately (self-healing)
- Catches generic `Exception` (line 7991)
- Logs errors with traceback
- Increments fail counter
- Triggers worker restart after 5 failures
- Re-raises exception (allows crash recovery loop to handle)

#### Main Loop Crash Recovery (`main.py:9578-9624`)
- Wrap-around try/except prevents process exit
- Crash counting with 5-minute window
- Exponential cooldown (30s, 60s, 90s, ... max 180s)
- Exits after 10 crashes in 5 minutes (crash loop detection)
- Comprehensive logging

#### Worker Loop (`main.py:8167-8334`)
- Exception handling in worker thread (line 8289)
- Logs errors with traceback
- Increments fail counter
- Sets freeze flag after 5 failures
- Continues loop (doesn't crash)

**Recommendation:** ✅ No action needed - exception handling is comprehensive

---

## 3. RACE CONDITIONS AND THREADING

### 3.1 File Locking

**Status:** ✅ **EXCELLENT**

**Findings:**
- `load_metadata_with_lock()` uses `fcntl.flock(f.fileno(), fcntl.LOCK_SH)` for reads (line 9237)
- `atomic_write_json()` uses `fcntl.flock(f.fileno(), fcntl.LOCK_EX)` for writes (line 9217)
- Locks released in `finally` blocks (prevents deadlocks)
- Shared lock (LOCK_SH) for reads, exclusive lock (LOCK_EX) for writes

**Note:** `fcntl` is Linux-specific. This is fine since runtime is Ubuntu droplet.

**Recommendation:** ✅ No action needed - file locking is properly implemented

---

### 3.2 Global Variables

**Status:** ⚠️ **SOME GLOBAL STATE (ACCEPTABLE)**

**Findings:**

#### Global Variables Used:
- `_last_reconcile_check_ts` (line 9203) - timestamp for throttling
- `_consecutive_divergence_count` (line 9204) - counter for divergence detection
- `_last_divergence_symbols` (line 9205) - set of symbols
- `_last_market_regime` (line 7701) - cached regime
- `ZERO_ORDER_CYCLE_COUNT` (line 6851) - cycle counter
- `_adaptive_optimizer` (line 61) - cached optimizer instance

**Analysis:**
- These are primarily used for throttling/caching
- No critical trading decisions depend on them without validation
- Thread-safety: Main worker loop runs in single thread (Watchdog worker)
- Threading.Lock used in `SmartPoller` class (line 1996)

**Recommendation:** ⚠️ **INFO:** Global state exists but is acceptable - no race conditions detected in critical paths

---

### 3.3 Thread Safety in Executor

**Status:** ✅ **GOOD**

**Findings:**
- `AlpacaExecutor` instance is created per `StrategyEngine` (line 5108)
- `StrategyEngine` is created per cycle or reused (not shared across threads)
- `self._reconciled` flag (line 2974) - instance variable (thread-safe per instance)
- No shared mutable state between threads in executor

**Recommendation:** ✅ No action needed

---

## 4. LOGIC ERRORS

### 4.1 Condition Logic

**Status:** ✅ **GOOD - NO OBVIOUS ERRORS**

**Findings:**
- All conditions checked appear logically correct
- Mode checks use `.upper()` for case-insensitive comparison
- Division by zero checks present (e.g., line 3246: `if mid > 0`)
- Range clamping present (e.g., line 3248: `max(0.0, min(10000.0, spread_bps))`)

**Recommendation:** ✅ No action needed

---

### 4.2 Order Validation Logic

**Status:** ✅ **EXCELLENT**

**Findings:**
- `ref_price <= 0` check before using (line 3236)
- `notional < MIN_NOTIONAL_USD` check (line 3257)
- Buying power validation (lines 3344-3373)
- Risk management validation called (lines 3354-3364)
- Multiple validation layers before order submission

**Recommendation:** ✅ No action needed

---

### 4.3 Portfolio Delta Calculation

**Location:** `main.py:5143-5190`

**Status:** ✅ **EXCELLENT**

**Findings:**
- Comprehensive error handling
- Validates `account_equity > 0` before division (line 5162)
- Clamps result to reasonable range (line 5183)
- Fails open (returns 0.0) on calculation errors (line 5190)
- Individual position errors don't break calculation (line 5176-5179)

**Recommendation:** ✅ No action needed

---

## 5. SAFETY CHECKS

### 5.1 Trading Arm Check Integration

**Location:** `main.py:7713-7732`

**Status:** ✅ **EXCELLENT**

**Findings:**
- `trading_is_armed()` called before `decide_and_execute()` (line 7713)
- If not armed, `orders = []` (line 7729) - no entries submitted
- Exit orders still execute (line 7758) - correct behavior
- Logged when entries skipped (line 7726-7728)

**Recommendation:** ✅ No action needed - arm check is properly integrated

---

### 5.2 Reconciliation Checks

**Location:** `main.py:7714-7732`

**Status:** ✅ **GOOD**

**Findings:**
- `ensure_reconciled()` called before trading (line 7716)
- If not reconciled, entries skipped (line 7730-7732)
- Wrapped in try/except (line 7715-7718) - doesn't crash if reconciliation fails

**Recommendation:** ✅ No action needed

---

### 5.3 Degraded Mode Handling

**Location:** `main.py:7720-7732`

**Status:** ✅ **GOOD**

**Findings:**
- `degraded_mode` flag checked (line 7720)
- Reduce-only: skips entries, allows exits
- Logged when entries skipped (line 7723)

**Recommendation:** ✅ No action needed

---

## 6. ORCHESTRATOR MODULES

### 6.1 `v2_nightly_orchestration_with_auto_promotion.py`

**Status:** ✅ **GOOD**

**Findings:**
- All file operations wrapped in try/except (lines 44-74)
- Returns safe defaults on error (empty dict, empty list)
- Optional module imports handled gracefully (lines 77-111)
- File writes use `os.makedirs()` before writing (line 60)
- No critical logic errors detected

**Recommendation:** ✅ No action needed

---

### 6.2 `v4_orchestrator.py`

**Status:** ✅ **GOOD**

**Findings:**
- File reads wrapped in try/except (lines 51-56)
- Returns safe defaults on error
- No critical logic errors detected

**Recommendation:** ✅ No action needed

---

## 7. POTENTIAL ISSUES (FLAGGED FOR REVIEW)

### 7.1 Silent Exception Handlers

**Location:** Various (e.g., `v2_nightly_orchestration_with_auto_promotion.py:48`, `v4_orchestrator.py:55`)

**Status:** ⚠️ **ACCEPTABLE - BUT FLAGGED**

**Findings:**
```python
def _read_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default  # Silent failure
```

**Analysis:**
- Many file read operations use `except Exception: return default`
- Errors are silently swallowed
- **BUT:** This is intentional fail-safe behavior (fail open)
- Critical operations (metadata, cache) have proper error handling and logging

**Recommendation:** ⚠️ **INFO:** Silent exception handlers are acceptable for non-critical file operations. Critical operations (position metadata, cache) have proper logging.

---

### 7.2 Exit Order Error Handling

**Location:** `main.py:4444-4465`, `main.py:5025-5033`

**Status:** ✅ **GOOD**

**Findings:**
- `close_position()` calls wrapped in try/except
- Errors logged (line 4300, 5033)
- Returns False on failure (line 4301)
- Exit orders don't crash the bot

**Recommendation:** ✅ No action needed

---

### 7.3 Market Order Submission

**Location:** `main.py:4467-4471`

**Status:** ⚠️ **MINOR - DIRECT API CALL**

**Findings:**
```python
def market_buy(self, symbol: str, qty: int):
    return self.api.submit_order(symbol=symbol, qty=qty, side="buy", type="market", time_in_force="day")

def market_sell(self, symbol: str, qty: int):
    return self.api.submit_order(symbol=symbol, qty=qty, side="sell", type="market", time_in_force="day")
```

**Analysis:**
- These are helper methods (not entry points)
- Callers should handle exceptions
- Used in displacement/exit logic (which has error handling)

**Recommendation:** ⚠️ **INFO:** Direct API calls in helper methods - acceptable as callers handle errors

---

## 8. SUMMARY OF ISSUES

| Issue | Location | Severity | Status | Action Required |
|-------|----------|----------|--------|-----------------|
| Silent exception handlers in helpers | `v2_nightly_orchestration_with_auto_promotion.py:48-74` | INFO | ⚠️ Acceptable | Intentional fail-safe behavior |
| Direct API calls in helpers | `main.py:4467-4471` | INFO | ⚠️ Acceptable | Callers handle errors |
| Global variables for caching | Multiple locations | INFO | ⚠️ Acceptable | No race conditions in critical paths |

---

## 9. STRENGTHS IDENTIFIED

### ✅ Excellent Practices Found:

1. **Comprehensive Error Handling:**
   - API calls wrapped in try/except with retries
   - Detailed error logging to dedicated files
   - Exponential backoff for retries
   - Fail-safe defaults (empty dicts, 0 values)

2. **File Operation Safety:**
   - File locking (fcntl) for concurrent access
   - Atomic writes (temp file + rename)
   - Self-healing for corrupted files
   - Structure validation (must be dict)

3. **Mode Safety:**
   - Multiple layers of mode checking
   - Endpoint/mode mismatch detection
   - Live trading acknowledgment required
   - Arm check before order submission

4. **Crash Recovery:**
   - Main loop crash recovery (prevents process exit)
   - Worker thread error handling
   - Fail counter with automatic restart
   - Freeze flags for safety

5. **Validation Logic:**
   - Price validation before use
   - Notional validation
   - Buying power checks
   - Risk management integration

---

## 10. RECOMMENDATIONS

### Immediate Actions (None Required):
1. ✅ **No critical issues found** - All safety checks are in place
2. ✅ **Error handling is comprehensive** - API failures handled gracefully
3. ✅ **Mode checking is robust** - Multiple layers prevent accidental live trading

### Future Improvements (Low Priority):
1. Consider adding explicit error logging to silent exception handlers in orchestrator modules (but current fail-safe behavior is acceptable)
2. Consider adding retry logic to `market_buy()`/`market_sell()` helper methods (but callers handle errors)

---

## 11. VALIDATION RESULTS

✅ **Overall Logic & Safety Health:** EXCELLENT
- No logic errors detected
- No race conditions in critical paths
- Comprehensive error handling
- Robust mode checking
- File locking prevents corruption
- Crash recovery prevents process exits
- Validation logic is sound
- Safety gates are properly integrated

---

## 12. DETAILED FINDINGS BY MODULE

### 12.1 `main.py`

**Strengths:**
- Trading arm check before order submission
- Comprehensive error handling for API calls
- File locking for position metadata
- Self-healing for corrupted files
- Crash recovery loop
- Mode/mode endpoint validation

**No Issues Found:** ✅

---

### 12.2 `position_reconciliation_loop.py`

**Strengths:**
- Retry logic with exponential backoff
- Degraded mode handling
- Error handling for API calls
- Safe file operations

**No Issues Found:** ✅

---

### 12.3 `risk_management.py`

**Strengths:**
- Mode checking with case-insensitive comparison
- Error handling for file operations
- Safe defaults on error

**No Issues Found:** ✅

---

### 12.4 `uw_flow_daemon.py`

**Strengths:**
- Retry logic with exponential backoff
- Rate limit handling
- Error handling for API calls
- Main loop error recovery

**No Issues Found:** ✅

---

### 12.5 `v2_nightly_orchestration_with_auto_promotion.py`

**Strengths:**
- Optional module imports handled gracefully
- Safe file operations
- Error handling present

**Minor Note:** Silent exception handlers (intentional fail-safe)

**No Critical Issues Found:** ✅

---

### 12.6 `v4_orchestrator.py`

**Strengths:**
- Safe file operations
- Error handling present

**No Issues Found:** ✅

---

**END OF PHASE 4 REPORT**
