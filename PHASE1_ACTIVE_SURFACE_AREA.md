# PHASE 1 — ACTIVE SURFACE AREA MAPPING

**Date:** 2026-01-10  
**Scope:** Active codebase (excluding `archive/`)

## EXECUTIVE SUMMARY

This document maps all active entry points, core modules, supporting modules, configuration files, and runtime scripts in the stock-bot repository. This is a **mapping-only** phase—no code changes were made.

---

## 1. ENTRY POINTS (Standalone Executables)

These are Python modules with `if __name__ == "__main__"` blocks that can be run directly:

### Primary Entry Points (Managed by `deploy_supervisor.py`):
1. **`main.py`** — Main trading bot (Flask server on port 8081, trading loop)
2. **`dashboard.py`** — Web dashboard (Flask server on port 5000)
3. **`uw_flow_daemon.py`** — Unusual Whales API polling daemon
4. **`heartbeat_keeper.py`** — Health monitoring supervisor
5. **`v4_orchestrator.py`** — Research orchestrator (one-shot, not restarted)

### Secondary Entry Points (Called by main.py or scheduled):
6. **`startup_contract_check.py`** — Contract validation (called at startup by main.py)
7. **`position_reconciliation_loop.py`** — Position reconciliation module (imported by main.py)
8. **`risk_management.py`** — Risk management module (imported by main.py)
9. **`momentum_ignition_filter.py`** — Momentum filter (has `__main__`, used by main.py)
10. **`comprehensive_learning_scheduler.py`** — Learning scheduler (background thread or scheduled)
11. **`v2_nightly_orchestration_with_auto_promotion.py`** — Nightly orchestrator (scheduled)

### Other Executable Scripts (Diagnostic/Deployment):
- Many diagnostic/deployment scripts exist in root (e.g., `force_position_reconciliation.py`, `FIX_TRADING_NOW.py`, etc.)
- These are **NOT** part of the core runtime stack but are available for manual execution

---

## 2. CORE MODULES (Imported by Entry Points)

### Signals Module (`signals/`):
- **`signals/__init__.py`** — Package init
- **`signals/uw.py`** — Core UW signal processing
- **`signals/uw_composite.py`** — Composite scoring
- **`signals/uw_adaptive.py`** — Adaptive gate
- **`signals/uw_weight_tuner.py`** — Weight tuning
- **`signals/uw_macro.py`** — Macro signals

### Root-Level Core Modules:
- **`uw_enrichment_v2.py`** — UW enrichment (imported by main.py)
- **`uw_composite_v2.py`** — V2 composite scoring (imported by main.py)
- **`uw_execution_v2.py`** — V2 execution logic (imported by main.py)
- **`cross_asset_confirmation.py`** — Cross-asset confirmation (imported by main.py)
- **`feature_attribution_v2.py`** — Feature attribution (imported by main.py)
- **`adaptive_signal_optimizer.py`** — Adaptive optimization (lazy-loaded by main.py)

### Structural Intelligence (`structural_intelligence/`):
- **`structural_intelligence/regime_detector.py`**
- **`structural_intelligence/structural_exit.py`**
- **`structural_intelligence/macro_gate.py`**
- (4 files total in directory)

### Learning (`learning/`):
- **`learning/__init__.py`**
- **`learning/thompson_sampling_engine.py`**

### API Management (`api_management/`):
- **`api_management/__init__.py`**
- **`api_management/token_bucket.py`**

### Telemetry (`telemetry/`):
- **`telemetry/`** — 2 Python files (exact files to be verified)

### XAI (`xai/`):
- **`xai/`** — 2 Python files (exact files to be verified)

### Self-Healing (`self_healing/`):
- **`self_healing/`** — 2 Python files (exact files to be verified)

---

## 3. SUPPORTING MODULES (Utility/Helper)

Many utility modules exist in root that support core functionality:
- **`config/registry.py`** — Centralized configuration registry (CRITICAL: used by all modules)
- **`health_supervisor.py`** — Health supervisor (imported by main.py)
- **`failure_point_monitor.py`** — Failure point monitoring
- **`profitability_tracker.py`** — Profitability tracking
- **`sre_monitoring.py`** — SRE monitoring
- **`signal_history_storage.py`** — Signal history storage
- **And many more...** (see full list in file listing)

---

## 4. CONFIGURATION FILES

### Core Config (`config/`):
1. **`config/registry.py`** — Centralized path/threshold registry (Python module)
2. **`config/theme_risk.json`** — Risk profiles and limits
3. **`config/execution_router.json`** — Execution routing strategies
4. **`config/startup_safety_suite_v2.json`** — Startup safety configuration
5. **`config/uw_signal_contracts.py`** — Signal contracts (Python module)

### Environment Configuration:
- **`.env`** — Environment variables (not found in repo, likely gitignored)
  - Loaded via `python-dotenv` in `main.py`, `deploy_supervisor.py`, and other entry points
  - Expected variables: `ALPACA_KEY`, `ALPACA_SECRET`, `UW_API_KEY`, `TRADING_MODE`, etc.

---

## 5. RUNTIME SCRIPTS (Shell/PowerShell)

### Shell Scripts (Linux/Ubuntu):
1. **`guardian_wrapper.sh`** — Guardian wrapper script
2. **`systemd_start.sh`** — Systemd service starter

### PowerShell Scripts (Windows):
1. **`add_git_to_path.ps1`** — Git path setup
2. **`check_status.ps1`** — Status checking
3. **`setup_windows.ps1`** — Windows setup

---

## 6. MODULE DEPENDENCY SUMMARY

### `main.py` Imports:
- `config.registry` — Paths, thresholds, config
- `signals.uw*` — Signal processing modules
- `uw_enrichment_v2`, `uw_composite_v2`, `uw_execution_v2` — V2 modules
- `cross_asset_confirmation`, `feature_attribution_v2` — Intelligence modules
- `position_reconciliation_loop` — Position reconciliation
- `startup_contract_check` — Contract validation (called at startup)
- `heartbeat_keeper` — Health monitoring (HealthSupervisor)
- `v2_nightly_orchestration_with_auto_promotion` — Promotion flag check
- `adaptive_signal_optimizer` — Lazy-loaded optimizer

### `deploy_supervisor.py` Manages:
- `dashboard.py` (port 5000)
- `uw_flow_daemon.py`
- `main.py` (port 8081)
- `v4_orchestrator.py` (one-shot)
- `heartbeat_keeper.py`

### `dashboard.py` Imports:
- `config.registry` — Paths and config
- Flask for web server
- Alpaca API client (lazy-loaded)

---

## 7. KEY OBSERVATIONS

1. **Centralized Config**: `config/registry.py` is the single source of truth for paths and thresholds
2. **Environment Variables**: `.env` file is expected but not in repo (gitignored by design)
3. **Multiple Entry Points**: Many scripts have `__main__` blocks, but only a subset are core runtime
4. **Deployment Supervisor**: `deploy_supervisor.py` orchestrates the core services
5. **Import Structure**: Core modules use explicit imports, with some lazy-loading for optional features
6. **No Virtual Environment**: Droplet uses system Python (per user's assumptions)

---

## 8. NEXT PHASE PREVIEW

**Phase 2** will audit:
- Import statements across all active modules
- Broken or incorrect imports
- References to archived/deleted modules
- Import path consistency

---

**END OF PHASE 1 REPORT**
