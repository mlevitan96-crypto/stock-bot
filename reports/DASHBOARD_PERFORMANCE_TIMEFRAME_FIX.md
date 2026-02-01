# Dashboard Performance Tab — Timeframe Fix Report

**Date:** 2026-01-31  
**Scope:** Performance metrics on the dashboard (Executive Summary tab) and mapping to canonical data/log paths per MEMORY_BANK.md. No changes to trade logic or execution.

---

## Issues Encountered

### 1. **No timeframe toggle for Performance metrics**
- The Executive Summary tab showed only fixed **2-Day P&L** and **5-Day P&L**.
- There was no way to view **24h**, **48h**, or **7d** windows, so timeframes could not be toggled as requested.

### 2. **Performance window not calculated from selected window**
- P&L metrics were always computed for 2d and 5d only; the backend had no concept of a user-selected window (24h, 48h, etc.).
- The Telemetry tab showed 24h/48h/5d from pre-computed telemetry bundles (`pnl_windows.json`, `live_vs_shadow_pnl.json`), but the Executive Summary (performance view) did not use a selectable timeframe.

### 3. **Paths not fully aligned with MEMORY_BANK 5.5**
- MEMORY_BANK 5.5 defines canonical paths: `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`, `logs/master_trade_log.jsonl`, plus state files.
- `config.registry` had `LogFiles.ATTRIBUTION` but did **not** define `MASTER_TRADE_LOG` or `EXIT_ATTRIBUTION`.
- The executive summary generator used hardcoded fallback paths (`Path("logs/attribution.jsonl")`, `Path("data/attribution.jsonl")`) instead of a single source of truth from the registry.

### 4. **Dashboard not explicitly using canonical paths**
- The telemetry health endpoint used `_DASHBOARD_ROOT / "logs" / "master_trade_log.jsonl"` instead of `config.registry.LogFiles.MASTER_TRADE_LOG` for consistency.

---

## Fixes Applied

### 1. **Canonical paths in `config/registry.py`**
- **Added** to `LogFiles`:
  - `MASTER_TRADE_LOG = Directories.LOGS / "master_trade_log.jsonl"`
  - `EXIT_ATTRIBUTION = Directories.LOGS / "exit_attribution.jsonl"`
- Ensures all dashboard and report code can use the same paths as MEMORY_BANK 5.5.

### 2. **Executive summary generator (`executive_summary_generator.py`)**
- **Paths:** Uses `config.registry` (`LogFiles.ATTRIBUTION`, `LogFiles.MASTER_TRADE_LOG`, `Directories.DATA`, `Directories.STATE`) resolved from repo root `Path(__file__).resolve().parent`. Removed ad-hoc fallback list of paths.
- **Timeframe support:**
  - Added `SUPPORTED_TIMEFRAMES = {"24h", "48h", "7d", "2d", "5d"}` and `DEFAULT_TIMEFRAME = "24h"`.
  - `calculate_pnl_metrics(trades, timeframe=...)` now takes a single window (24h, 48h, 7d, 2d, 5d), filters trades by `ts` within that window, and returns:
    - `timeframe`, `pnl`, `trades`, `win_rate` (primary)
    - Backward-compat keys `pnl_2d`/`pnl_5d`/`trades_2d`/`trades_5d`/`win_rate_2d`/`win_rate_5d` set only when that window is selected (otherwise `None`).
  - `generate_executive_summary(timeframe=...)` accepts `timeframe` and passes it to `calculate_pnl_metrics`; written summary uses the selected window label (e.g. "P&L (24h)").

### 3. **Dashboard API (`dashboard.py`)**
- **`/api/executive_summary`:** Reads query parameter `timeframe` (default `24h`), validates against `SUPPORTED_TIMEFRAMES`, and calls `generate_executive_summary(timeframe=timeframe)`.
- **Telemetry health:** Master trade log path now uses `( _DASHBOARD_ROOT / LogFiles.MASTER_TRADE_LOG ).resolve()` when registry is available, with fallback to `logs/master_trade_log.jsonl`.

### 4. **Executive Summary tab UI**
- **Timeframe dropdown:** Added a "Timeframe" select with options **24h**, **48h**, **7d**, **2d**, **5d**.
- **Refetch on change:** Changing the dropdown calls `loadExecutiveSummary(this.value)`, which fetches `/api/executive_summary?timeframe=<value>` and re-renders.
- **Labels:** Performance section title remains "📊 Performance Metrics"; the selected window is shown as "P&L (24h)" (or 48h, 7d, etc.) with trades count and win rate for that window. Added note: "Data from canonical logs (MEMORY_BANK 5.5)".
- **Backward compatibility:** `renderExecutiveSummary` still supports old `pnl_2d`/`pnl_5d`/`trades_2d`/`trades_5d`/`win_rate_2d`/`win_rate_5d` if present (e.g. from cached or older API responses).

---

## What Was Not Changed

- **Trade logic:** No changes to `main.py`, order submission, scoring, exits, or any trading code.
- **Data written by the bot:** No changes to what is written to `logs/attribution.jsonl`, `logs/master_trade_log.jsonl`, or `logs/exit_attribution.jsonl`; only **consumption** by the dashboard and executive summary generator was aligned to canonical paths and timeframes.
- **Telemetry tab:** 24h/48h/5d panels still read from `telemetry/YYYY-MM-DD/computed/pnl_windows.json` and `live_vs_shadow_pnl.json`; no change to how those artifacts are produced (they remain sourced from `logs/master_trade_log.jsonl` per existing scripts).

---

## Verification

- `executive_summary_generator`: `generate_executive_summary(timeframe='48h')` returns `pnl_metrics` with `timeframe: '48h'`, `pnl`, `trades`, `win_rate`; `_timeframe_to_timedelta` correctly maps 24h, 48h, 7d, 2d, 5d.
- Paths: `(REPO_ROOT / LogFiles.ATTRIBUTION).resolve()` and `(REPO_ROOT / LogFiles.MASTER_TRADE_LOG).resolve()` point to `logs/attribution.jsonl` and `logs/master_trade_log.jsonl` when run from repo root.
- Lint: No new linter errors in `executive_summary_generator.py`, `dashboard.py`, or `config/registry.py`.

---

## How to Use

1. Open the dashboard and go to the **📈 Executive Summary** tab.
2. Use the **Timeframe** dropdown to select **24h**, **48h**, **7d**, **2d**, or **5d**.
3. The "Performance Metrics" section updates to show P&L, trade count, and win rate for the selected window; data is read from canonical `logs/attribution.jsonl` (and registry paths).
4. To see how everything is working and whether it is profitable, use the same tab with the desired window; no internal data or trade logic was altered to fit the dashboard—only the dashboard was changed to fit the defined data sources and timeframes.
