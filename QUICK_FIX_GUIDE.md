# Quick Fix Guide - Audit Issues

## How to Fix All Audit Issues

### Option 1: Automated Fix Script

```bash
python APPLY_AUDIT_FIXES.py
```

This will:
- Synchronize signal component lists
- Add registry imports
- Create TODO for missing endpoints

### Option 2: Manual Fixes (Recommended for Safety)

Follow `FIX_AUDIT_ISSUES.md` for detailed step-by-step instructions.

---

## Priority Order

### 1. Signal Component Sync (5 min)
**File:** `config/registry.py`
- Add `"flow"` and `"freshness_factor"` to `SignalComponents.ALL_COMPONENTS`

### 2. Registry Imports (5 min)
**Files:** `deploy_supervisor.py`, `signals/uw_adaptive.py`
- Add: `from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles`

### 3. Hardcoded Paths (15 min)
- Replace `Path("logs/...")` with `LogFiles.XXX`
- Replace `Path("state/...")` with `StateFiles.XXX`
- Replace `Path("data/...")` with `CacheFiles.XXX`

### 4. API Endpoints (10 min)
**Files:** `main.py`, `uw_flow_daemon.py`
- Add: `from config.registry import APIConfig`
- Replace hardcoded URLs with `APIConfig.ALPACA_BASE_URL` and `APIConfig.UW_BASE_URL`

### 5. Missing Endpoints (30-60 min)
**File:** `uw_flow_daemon.py`
- Add polling methods for: `insider`, `calendar`, `congress`, `institutional`
- See `FIX_AUDIT_ISSUES.md` for implementation details

---

## Verification

After fixes:
```bash
python COMPREHENSIVE_CODE_AUDIT.py
```

Should show reduced issues.

---

**See `FIX_AUDIT_ISSUES.md` for complete details.**
