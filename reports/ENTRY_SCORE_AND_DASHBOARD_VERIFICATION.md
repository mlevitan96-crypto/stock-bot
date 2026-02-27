# Entry Score & Dashboard Verification (Open Positions)

**Date:** 2026-02-16  
**Scope:** Confirm entry scores are not broken (trading life cycle is correct) and the "0.00" Entry column is a dashboard/display issue; review trading life cycle for other issues.

---

## 1. Are entry scores broken?

**No. Entry scores are computed, validated, and persisted correctly in the trading life cycle.**

### Where entry_score is set and stored

| Step | Location | Behavior |
|------|----------|----------|
| **Compute** | `main.py` (strategy engine) | Composite score computed before entry; must be > 0 or entry is blocked (`invalid_entry_score_blocked`). |
| **Pass to executor** | `main.py` → `executor.mark_open(..., entry_score=score)` | Score is passed when order is filled (or when reconciliation later calls mark_open). |
| **Persist** | `main.py` `AlpacaExecutor._persist_position_metadata()` | Writes `state/position_metadata.json` with `metadata[symbol]["entry_score"] = entry_score`. |
| **Recovery** | `utils/entry_score_recovery.py` | For positions added by reconciliation (e.g. fill detected later), score is recovered from `state/pending_fill_scores.json` or `logs/attribution.jsonl` and written into metadata. |

- **Pending fill:** When an order is submitted but not yet filled, `persist_pending_fill_score(symbol, score)` is called so reconciliation can apply the score when the fill is detected.
- **Reconciliation** (`position_reconciliation_loop.py`, `main.py` health/reload) uses `recover_entry_score_for_symbol(symbol)` when metadata is missing or has 0.0 and updates metadata.

So the **backend** never “breaks” entry scores: they are enforced at entry and persisted (or recovered) for open positions.

---

## 2. Why the dashboard shows "0.00" for Entry (and why it’s a display issue)

The Open Positions table was showing **0.00** in the Entry score column for most symbols while **Current**, **Prev**, and **Delta** showed non-zero values. That implies:

- **Current/Prev/Delta** come from live/composite scoring and caches that the dashboard *does* read correctly.
- **Entry** comes from `state/position_metadata.json` keyed by symbol. If the dashboard doesn’t read that file from the same place the bot writes it, or doesn’t fall back to recovery, it will show 0.00.

### Root cause (dashboard side)

1. **Path resolution**  
   Position metadata was loaded with `StateFiles.POSITION_METADATA`, which is `Path("state/position_metadata.json")` — **relative to the process current working directory**. If the dashboard is started with a different cwd (e.g. systemd or a different directory), it would read the wrong file or an empty one and get no `entry_score`.

2. **No fallback when missing**  
   When `metadata.get(symbol, {}).get("entry_score", 0.0)` was missing or 0, the dashboard always showed 0.00 and did not try recovery (pending_fill_scores or attribution).

### Fixes already in the codebase

- **Position metadata path:** In `dashboard.py` `_api_positions_impl()`, metadata is loaded from  
  `(Path(_DASHBOARD_ROOT) / StateFiles.POSITION_METADATA).resolve()`  
  so the same `state/position_metadata.json` the bot uses is read regardless of cwd.

- **Entry score recovery in the dashboard:** When `entry_score` is missing or ≤ 0, the dashboard now calls  
  `recover_entry_score_for_symbol(symbol, pop_pending=False)`  
  and uses the recovered value for display when available.

- **Other state/cache paths:** UW flow cache, regime files, and signal_strength_cache are resolved against `_DASHBOARD_ROOT` in the positions API so they are cwd-independent.

- **Working directory:** The dashboard does `os.chdir(_DASHBOARD_ROOT)` at startup so any code using relative paths (e.g. entry_score_recovery when called from the dashboard) sees the repo root.

So the **0.00 Entry column is a dashboard/display issue** (wrong path and no recovery), not a failure of the trading life cycle. With the current code deployed, the dashboard should show the correct entry scores for open positions.

---

## 3. Trading life cycle review — other issues

| Phase | Check | Status |
|-------|--------|--------|
| **Entry** | Score computed, validated > 0, passed to `mark_open`, persisted in metadata; blocked if invalid. | OK |
| **Pending fill** | `persist_pending_fill_score` called when order submitted but not filled. | OK |
| **Reconciliation** | Restores positions from Alpaca; pulls entry_score from metadata or recovery; updates metadata when missing. | OK |
| **Reload / health** | Metadata reload and entry_score recovery on startup and health checks. | OK |
| **Exit** | Attribution uses `info.get("entry_score")` from opens/metadata for exit attribution. | OK |
| **Dashboard** | Reads metadata (now repo-root path), shows entry_score, falls back to recovery. | Fixed in code |

No other entry-score or lifecycle bugs were found. Current/Prev/Delta and P&L columns behaving correctly supports that scoring and position tracking are working; the only inconsistency was the Entry column due to path and missing recovery on the dashboard.

---

## 4. What you should do

1. **Deploy the latest dashboard** to the droplet (or wherever you run it) so the path and recovery changes are in effect. After deploy, refresh Open Positions and confirm Entry scores are no longer 0.00 for positions that were opened with a valid score.

2. **If some positions still show 0.00 after deploy:**  
   - On the droplet, inspect `state/position_metadata.json`: do those symbols have an `entry_score` key?  
   - If not, those positions may have been opened before metadata/recovery was in place, or reconciliation may have run before the fill was linked to a pending score. New entries should persist correctly.

3. **Optional check:** Run a quick audit (e.g. `score_audit_open_positions.py` or a small script that reads `state/position_metadata.json` and Alpaca positions) to compare file vs dashboard for a few symbols.

---

## 5. Summary

- **Entry scores are not broken.** They are computed, validated, persisted, and recovered in the trading life cycle.
- **The 0.00 Entry column was a dashboard issue:** metadata was read with a cwd-relative path and there was no recovery fallback. The codebase now uses a repo-root–resolved path and recovery for display.
- **Trading life cycle review:** No other issues identified; deploy the dashboard and re-check Open Positions to confirm.
