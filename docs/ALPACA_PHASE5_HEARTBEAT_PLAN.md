# Alpaca Phase 5 — Heartbeat — Implementation Plan

**Status:** Plan only. No code until CSA + SRE approve.  
**Scope:** Time-based heartbeat that records last run and Tier 1/2/3 packet timestamps. No decisions, no tuning, no promotion. Advisory only.  
**Context:** alpaca_board_review_state.json, alpaca_convergence_state.json. Alpaca-only scope.

---

## 1. Purpose

- Record **last heartbeat run** timestamp.
- Record **Tier 1 / Tier 2 / Tier 3** last-run timestamps (from alpaca_board_review_state.json) and optionally packet dirs.
- Optionally report **stale** if any tier’s last run is older than a configurable interval (e.g. 24h). No automatic action; informational only.

No decisions, no tuning, no promotion. Heartbeat does not trigger reviews or change any lever.

---

## 2. Required Surfaces

| Surface | Source | Used for |
|---------|--------|----------|
| Board review state | state/alpaca_board_review_state.json | last_run_ts (Tier 3), tier1_last_run_ts, tier2_last_run_ts, packet dirs |
| Convergence state | state/alpaca_convergence_state.json | last_run_ts (optional: last convergence check) |

All read-only. Single write: state/alpaca_heartbeat_state.json.

---

## 3. Output File

**Path:** `state/alpaca_heartbeat_state.json`

**Schema (design):**
- `last_heartbeat_ts`: ISO8601 (this run)
- `tier1_last_run_ts`: str | null (from board state)
- `tier2_last_run_ts`: str | null
- `tier3_last_run_ts`: str | null (from board state last_run_ts)
- `convergence_last_run_ts`: str | null (from convergence state)
- `stale_interval_hours`: float (e.g. 24.0) — configurable via arg or default
- `stale`: bool — true if any of tier1/tier2/tier3 last run is older than stale_interval_hours (or missing)
- `one_liner`: str (e.g. "Heartbeat OK; all tiers fresh." or "Heartbeat: Tier2 stale (>24h).")

Overwrite each run.

---

## 4. Script

**Path:** `scripts/run_alpaca_board_review_heartbeat.py`

**Behavior:**
- Args: `--base-dir`, `--stale-hours` (default 24.0), `--dry-run`.
- Load alpaca_board_review_state.json and alpaca_convergence_state.json.
- Compute stale: for each of tier1_last_run_ts, tier2_last_run_ts, last_run_ts (Tier3), if present, parse and compare to now; if any older than stale_interval_hours or missing, stale = true.
- Write state/alpaca_heartbeat_state.json. No decisions, no tuning, no promotion.

**Idempotency:** Overwrite each run. Safe to run on a schedule (e.g. every 12h or 24h) or manually.

---

## 5. Testing Plan

1. **Dry-run:** `--dry-run` → exit 0; print one_liner and stale; no file write.
2. **Full run:** Run script → state/alpaca_heartbeat_state.json updated; exit 0.
3. **CSA/SRE review:** Confirm no side effects; OK.

---

## 6. Architecture Fit

- Reads existing state files only; writes one state file. No new entry points. Fits ARCHITECTURE_AND_OPERATIONS. Alpaca-only.

---

STOP for CSA + SRE review.
