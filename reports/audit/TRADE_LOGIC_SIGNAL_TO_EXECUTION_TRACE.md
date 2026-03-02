# Trade Logic: Signal → Execution Trace (Why No Trades)

**Date:** 2026-03-02  
**Scope:** Trace from signal ingestion to order execution using **droplet production data**.  
**Conclusion:** Trades are not happening because **zero clusters** reach `decide_and_execute`; composite scoring runs but **every symbol is rejected** by `should_enter_v2` (score below threshold).

---

## 1. End-to-end flow (code path)

| Step | Location | What happens |
|------|----------|----------------|
| 1 | `main.py` → `run_once()` | Entry. Enforces paper-only, reads UW cache, runs reconciliation and risk checks. |
| 2 | `read_uw_cache()` | Reads `data/uw_flow_cache.json` (CacheFiles.UW_FLOW_CACHE). If missing/empty → `cache_symbol_count = 0`. |
| 3 | `run_once()` | `use_composite = (cache_symbol_count > 0)`. If true, composite scoring runs; else only `flow_clusters` from API/cache. |
| 4 | Composite loop (main.py ~10774–11424) | For each ticker in cache: enrich → `compute_composite_score_v2()` → `should_enter_v2(composite, ticker, "base", api)`. Only if `gate_result` is True is a cluster appended to `filtered_clusters`. |
| 5 | `clusters = filtered_clusters` | Only composite clusters that passed the gate are used. If none pass → `clusters = []`. |
| 6 | Pre-execution gates | `trading_is_armed()` (paper URL), `ensure_reconciled()`, `degraded_mode`. If any fail → `orders = []` without calling `decide_and_execute`. |
| 7 | `engine.decide_and_execute(clusters, ...)` | If `len(clusters) == 0`, returns `[]`; no orders. Otherwise runs per-cluster gates (regime, concentration, score, cooldown, position exists, etc.) and `submit_entry()`. |
| 8 | `submit_entry()` → Alpaca | Size validation, route order, submit. |

---

## 2. Droplet evidence (real state)

- **Run:** `python scripts/run_zero_trades_signal_review_via_droplet.py` (and `scripts/fetch_droplet_run_and_cache_status.py`).

### 2.1 Zero-trades preflight (reports/signal_review/zero_trades_preflight.md)

- **ZERO TYPE: A** — Zero candidates in the last 24h.
- **Main loop:** `logs/run.jsonl` newest ts = 2026-03-02 15:33 → loop is running.
- **Decision ledger:** Newest 2026-02-20; **last 24h: 0 events**.
- **Score snapshot:** Newest 2026-02-20; **last 24h: 0 lines**.
- **Blocked trades:** Newest 2026-02-27; **last 24h: 0 lines**.
- **submit_entry:** 0 lines in 24h → execution path never reached.

### 2.2 Last 5 run.jsonl lines (droplet)

Every cycle shows:

- `"clusters": 0`, `"orders": 0`
- `"composite_enabled": true`
- `"engine_status": "ok"`, `"market_open": true`

So: composite is on, but **no cluster is ever produced** in the composite step.

### 2.3 UW cache on droplet

- `data/uw_flow_cache.json` exists, ~6.4 MB, updated Mar 2 15:32.
- So the cache is populated and recent → `cache_symbol_count > 0` → composite scoring **does** run.

### 2.4 Signal funnel (Phase 1, older window)

- `reports/signal_review/signal_funnel.md` (e.g. 7-day window): **Stage 5_expectancy_gate** is the dominant choke.
- **Reason:** `expectancy_gate:score_floor_breach` — 100% of candidates below score floor.
- Example scores: 0.172, 0.316, 1.055 (all below MIN_EXEC_SCORE 2.5 and below base threshold 2.7).

---

## 3. Root cause (why 0 clusters)

- The main loop runs, composite is enabled, and the UW cache is populated.
- For each symbol, the code:
  - Enriches and computes `composite_score`,
  - Calls `should_enter_v2(composite, ticker, "base", api)`.
- **No symbol passes `should_enter_v2`** → `filtered_clusters` stays empty → `clusters = []` → `decide_and_execute` is called with 0 clusters → 0 orders.

So the choke is **before** `decide_and_execute`: at the **composite gate** (`should_enter_v2`).

### 3.1 `should_enter_v2` (uw_composite_v2.py)

- `score >= get_threshold(symbol, "base")` (default **2.7** from ENTRY_THRESHOLDS["base"]).
- `toxicity <= 0.90`.
- `freshness >= 0.25`.
- Exhaustion check: price vs 20-period EMA and ATR (can block if price > 2.5 ATR from EMA).

If **scores are consistently below 2.7** (and/or freshness/toxicity/exhaustion block), every symbol is rejected and no cluster is added.

### 3.2 Why scores are low (likely)

- **Stale or weak data:** Freshness decay, or UW/options flow not delivering strong conviction.
- **Component mix:** Flow conviction, dark pool, insider, etc. defaulting or weak → low composite.
- **Adaptive weights:** `state/signal_weights.json` reducing component weights (see MEMORY_BANK 7.5).
- **Expectancy/snapshot history:** Funnel and ledger show scores well below 2.5–2.7 (e.g. 0.17–1.05).

---

## 4. Gates that can block (reference)

| Gate | Location | Effect if failed |
|------|----------|------------------|
| Freeze | `check_freeze_state()` | Early return, 0 clusters/orders. |
| Risk limits | `run_risk_checks()` | Early return, 0 orders. |
| Heartbeat staleness | `check_heartbeat_staleness()` | Alert; may auto-heal. |
| UW cache empty | `cache_symbol_count == 0` | No composite; only flow_clusters (often empty if no API flow). |
| **Composite gate** | **`should_enter_v2()`** | **No cluster appended → 0 clusters.** ← **Current blocker** |
| Armed | `trading_is_armed()` | Skip entries (paper URL check). |
| Reconciled | `ensure_reconciled()` | Skip entries. |
| Kill switch | `kill_switch_active()` | Return [] from decide_and_execute. |
| Score below min | decide_and_execute | Block that candidate. |
| Cooldown / position exists / spread / etc. | decide_and_execute | Block that candidate. |

---

## 5. Recommended next steps

1. **Confirm score vs threshold on droplet**
   - Run a single cycle with extra logging, or run `scripts/run_scoring_pipeline_audit_on_droplet.py` (or equivalent) and inspect:
     - Distribution of composite scores per symbol.
     - Count of symbols with `score >= 2.7` and with `should_enter_v2 == True`.
   - Or add a one-off diagnostic that logs, for a few symbols, `(symbol, score, threshold, gate_result)` after `should_enter_v2`.

2. **Check adaptive weights**
   - On droplet: `state/signal_weights.json`. If options_flow or other key components are heavily reduced, scores can be suppressed (see MEMORY_BANK 7.5).

3. **Data freshness and UW daemon**
   - Confirm `uw_flow_daemon` is running and writing `data/uw_flow_cache.json` with fresh data.
   - Check `_last_update` (or equivalent) per symbol; if data is old, freshness decay will lower scores.

4. **Decision ledger and funnel**
   - Run `python3 scripts/run_decision_ledger_capture.py` on the droplet so the last 24h have ledger events (from score_snapshot + blocked_trades).
   - Re-run zero-trades preflight and full signal review to get an up-to-date funnel and dominant blocker.

5. **Thresholds (only if intended)**
   - ENTRY_THRESHOLDS["base"] = 2.7 (uw_composite_v2.py), Config.MIN_EXEC_SCORE = 2.5 (config/registry.py). Lowering either would allow more clusters through; do only with explicit intent and risk review.

---

## 6. Files and scripts used

- **Preflight (on droplet):** `scripts/zero_trades_preflight_on_droplet.py`, `scripts/run_zero_trades_preflight_and_signal_review_on_droplet.py`, `scripts/run_zero_trades_signal_review_via_droplet.py`.
- **Droplet run/cache check:** `scripts/fetch_droplet_run_and_cache_status.py`.
- **Core logic:** `main.py` (`run_once`, composite loop, decide_and_execute), `uw_composite_v2.py` (`should_enter_v2`, `get_threshold`).
- **Config:** `config/registry.py` (MIN_EXEC_SCORE, CacheFiles), `uw_composite_v2.py` (ENTRY_THRESHOLDS).

---

**Summary:** The pipeline from signal to execution is intact; the bottleneck is that **no composite cluster passes `should_enter_v2`** (scores below 2.7 and/or other gate conditions). Fixes should target raising composite scores (data, weights, freshness) or, if desired, revisiting entry thresholds with proper governance.
