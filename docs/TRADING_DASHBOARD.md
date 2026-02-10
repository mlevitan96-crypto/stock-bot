# Trading Dashboard — Canonical Layout & Data

**Purpose:** Single reference for the rationalized trading cockpit. Use this and MEMORY_BANK for what is canonical.

---

## 1. Tab layout (post–rationalization)

### 1.1 Core cockpit (top-level, always visible)

| Tab | Purpose | User value | Data source |
|-----|---------|------------|-------------|
| **Positions** | Open positions (equity + wheel), P&L, signal strength | Daily | `/api/positions` — Alpaca + `state/position_metadata.json`, `data/uw_flow_cache.json` |
| **Closed Trades** | Recent closed trades with P&L, strategy, wheel fields | Daily | `/api/stockbot/closed_trades` — attribution + exit_attribution + telemetry |
| **Executive Summary** | Daily/multi-day P&L, health summary, Board verdict, wheel summary | Daily | `/api/executive_summary`, `/api/stockbot/wheel_analytics`, `/api/sre/health` |
| **SRE Monitoring** | Bot status, broker connectivity, failure points, self-heal | Daily | `/api/sre/health`, `/api/failure_points`, `/api/sre/self_heal_events` |

### 1.2 Strategy-specific

| Tab | Purpose | User value | Data source |
|-----|---------|------------|-------------|
| **Wheel Strategy** | Wheel P&L, premium, assignments, call-aways, open/closed wheel, universe health | As needed | `/api/stockbot/wheel_analytics`, `/api/wheel/universe_health` |
| **Strategy Comparison** | Equity vs wheel, promotion readiness, recommendation | As needed | `/api/strategy/comparison` — `reports/*_stock-bot_combined.json` |

### 1.3 Advanced (under “More” dropdown)

| Tab | Purpose | User value | Data source |
|-----|---------|------------|-------------|
| **Signal Review** | Last 50 signal-level diagnostics | Occasional | `/api/signal_history` |
| **Natural Language Auditor** | NL summaries and audits | Occasional | `/api/xai/auditor`, `/api/xai/export` |
| **Trading Readiness** | Pre-market checks, failure points, “Why am I not trading?” | As needed | `/api/failure_points` |
| **Telemetry** | Raw telemetry, computed artifacts, logs | Deep dive | `/api/telemetry/latest/*` |

### 1.4 Removed / merged

- **Wheel Universe Health** — Merged into **Wheel Strategy** tab as a sub-panel (Universe Health section).
- No data sources were removed from the backend; only UX/layout changed.

---

## 2. Where to find what

- **Health:** Executive Summary (summary), SRE Monitoring (full), Top Strip (status).
- **P&L:** Executive Summary (daily + multi-day), Positions (unrealized + day), Closed Trades (realized), Top Strip (today + 7d).
- **Wheel:** Wheel Strategy tab (full), Executive Summary (summary), Closed Trades (filter by Wheel), Strategy Comparison.
- **Scoring:** Positions table columns “Entry Signal Strength” and “Current Signal Strength” (from engine + live composite). Canonical: `state/position_metadata.json` → `entry_score`; current from `uw_composite_v2` when cache fresh.

---

## 3. Scoring fields (canonical)

- **Entry Signal Strength** (UI label) = `entry_score` from position metadata at entry. Real value from engine.
- **Current Signal Strength** (UI label) = live composite score when UW cache is fresh; otherwise 0 or last known. Displayed as “Current Signal Strength” with decay styling when &lt; 80% of entry.
- Backend and logs keep using `entry_score` and `current_score`; only the dashboard labels were renamed for clarity.

---

## 4. Top strip

A small header strip shows:

- **Health** — green / yellow / red from SRE.
- **P&L today** — from executive summary 24h (or health_status day_pnl).
- **P&L 7d** — from executive summary 7d.
- **Last signal** — from signal history or heartbeat.
- **Last update** — dashboard data refresh time.

---

## 5. API endpoint map

See `reports/DASHBOARD_ENDPOINT_MAP.md` for the full endpoint → data location map. Dashboard reads only from logs/state/config; it does not modify the trading engine.

---

## 6. Wheel data (live)

- **Wheel trades** are logged when the wheel strategy places orders: `strategies/wheel_strategy.py` writes to `logs/telemetry.jsonl` with `strategy_id=wheel`, and optionally records **premium** after polling for order fill.
- **Ground truth:** `state/wheel_state.json`, `logs/telemetry.jsonl` (strategy_id=wheel), `logs/attribution.jsonl` (wheel if written by engine), `reports/*_stock-bot_wheel.json` (from `scripts/generate_daily_strategy_reports.py`).
- **Dashboard** shows wheel data from these sources; no UI hacks. When no wheel trades exist, Wheel Strategy tab shows zeros and a short note on data sources.
- **Scoring** in the Positions table is real: Entry Signal Strength = `entry_score` from position metadata; Current Signal Strength = live composite from `uw_composite_v2` when UW cache is fresh. No static placeholders.

### 6.1 How wheel selects tickers (PATH B — UW-first)

- **Order of operations:** (1) Load universe from `config/universe_wheel_expanded.yaml` (or `universe_source`). (2) Filter by sector (excluded sectors), earnings window, and per-symbol position count. (3) **Rank by UW intelligence:** read `data/uw_flow_cache.json`, compute UW composite score per symbol via `uw_composite_v2.compute_composite_score_v2(symbol, enriched, regime)`; sort by score descending. (4) Take top N (`universe_max_candidates`, e.g. 10). (5) For each ticker in that order, run hard filters in `_run_csp_phase`: earnings, IV rank, **spot quote** (no_spot skip), **option contracts** in DTE/delta range (no_contracts skip), capital/position limits. (6) First ticker that passes gets the CSP order (if any).
- **UW is primary:** Ticker choice is driven by UW composite score when the cache is available; liquidity/OI/spread are attached for telemetry and secondary sort when UW is missing.
- **Verify:** Each cycle emits `wheel_candidate_ranked` in `logs/system_events.jsonl` (subsystem=wheel) with `top_5_symbols`, `top_5_uw_scores`, `chosen` or `reason_none`. Run `grep '"subsystem": "wheel"' logs/system_events.jsonl | grep wheel_candidate_ranked` on the droplet.
- **Validate wheel intelligence without market hours:** Run the dry-run script from repo root: `python3 scripts/wheel_dry_run_rank.py`. It loads the wheel universe and UW cache, ranks by UW intelligence (same as live PATH B), and emits `wheel_candidate_ranked` to `logs/system_events.jsonl` with `reason_none="dry_run_rank_only"` and no broker/quote/options calls. Confirm with: `grep '"event_type": "wheel_candidate_ranked"' logs/system_events.jsonl | tail -1`. See MEMORY_BANK § Wheel Dry-Run Validation.

## 7. Validation

- Run `python scripts/generate_daily_strategy_reports.py` to ensure wheel and strategy comparison data exist.
- Dashboard checks: `scripts/verify_dashboard_contracts.py`, `scripts/verify_wheel_endpoints_on_droplet.py`.
- After deployment: confirm Health and P&L on Top Strip and in Executive Summary; Wheel metrics when wheel has traded; Signal Strength columns show non-zero when positions exist and cache is fresh.
- Wheel lifecycle events: `logs/system_events.jsonl` (subsystem=wheel) for wheel_run_started, wheel_regime_audit, wheel_candidate_ranked, wheel_csp_skipped, wheel_order_submitted, wheel_order_filled.

### Wheel spot resolution
- **Contract:** All spot comes from `normalize_alpaca_quote(api.get_quote())` + optional 1Min bar close, then `resolve_spot_from_market_data()`. Order: ask → bid → last_trade → bar_close. No inline quote field access elsewhere.
- **Events (exactly one per symbol attempt):**  
  - **wheel_spot_resolved** — symbol, spot_price, spot_source ("ask"|"bid"|"last_trade"|"bar_close"), quote_fields_present, bar_used.  
  - **wheel_spot_unavailable** — symbol, quote_fields_present, bar_attempted.  
  no_spot skip is only emitted when wheel_spot_unavailable was emitted for that symbol.
- **Verification report:** `python3 scripts/wheel_spot_resolution_verification.py --days 7` writes `reports/wheel_spot_resolution_verification_<date>.md` with resolved vs unavailable counts, spot_source distribution, first option-chain reach, wheel_order_submitted/filled, and next blocker with evidence.
- **Debugging:** If all cycles are wheel_spot_unavailable, run_wheel_check_on_droplet.py exits 1. Inspect quote_fields_present in events to see which Alpaca fields were present; ensure normalize_alpaca_quote and bar fallback are correct for your Alpaca API shape.

### Strategy capital allocation
- **Fixed partitioning:** Wheel 25%, equity 75% of total account equity (config: `config/strategies.yaml` → `capital_allocation`). No strategy may consume the other’s capital; enforced at order time via `capital/strategy_allocator.can_allocate()`.
- **Wheel independence:** Wheel budget = total_equity × 0.25; wheel_used = sum(open CSP notionals from `state/wheel_state.json`). Before each CSP, the wheel calls the allocator; if allocation would be exceeded, it emits **wheel_capital_blocked** and continues to the next candidate. Equity trades cannot starve the wheel.
- **Per-position limit (wheel budget fraction):** Per-position limits are a fraction of the **wheel budget**, not total equity. `per_position_limit = wheel_budget × per_position_fraction_of_wheel_budget` (config: `strategies.wheel.per_position_fraction_of_wheel_budget`, e.g. 0.5). A CSP is allowed only if `required_notional (= strike × 100) ≤ per_position_limit`. When blocked, the wheel emits **wheel_position_limit_blocked** and continues to the next candidate.
- **Audit:** In `logs/system_events.jsonl` (subsystem=wheel): **wheel_capital_check** (wheel_budget, wheel_used, wheel_available, required_notional, decision, reason); **wheel_capital_blocked** when blocked (includes full budget math). **wheel_position_limit_check** (wheel_budget, per_position_limit, required_notional, decision, reason); **wheel_position_limit_blocked** when blocked. Run `python3 scripts/run_wheel_check_on_droplet.py` and inspect “LAST 5 wheel_capital_check / wheel_capital_blocked” to verify budget and per-position decisions (inspect both wheel_capital_* and wheel_position_limit_* sections).

---

## 8. Wheel troubleshooting (A/B/C/D)

When wheel analytics stay at zero or no FILLED trades appear, determine the single root cause using the outcome framework below. **Where to look first:**

| Check | Location | What to look for |
|-------|----------|------------------|
| **1. System events** | `logs/system_events.jsonl` | Filter `subsystem=wheel`. Counts: wheel_run_started, wheel_spot_resolved, wheel_spot_unavailable, wheel_capital_check, wheel_capital_blocked, wheel_position_limit_check, wheel_position_limit_blocked, wheel_csp_skipped (by reason), wheel_order_submitted, wheel_order_filled, wheel_order_failed. |
| **2. Telemetry** | `logs/telemetry.jsonl` | Filter `strategy_id=wheel`. Count rows; confirm premium present when orders filled. |
| **3. Attribution** | `logs/attribution.jsonl` | Filter `strategy_id=wheel`. Count rows; sample for wheel phase/premium. |
| **4. State** | `state/wheel_state.json` | File mtime and content (open_csps, etc.) changing across cycles/days. |
| **5. Dashboard API** | `GET /api/stockbot/wheel_analytics` | total_trades, premium_collected; must match telemetry/attribution when pipeline is correct. |

**Diagnostic script (run on droplet):**  
`python3 scripts/wheel_root_cause_report.py --days 5`  
Outputs counts, samples, and a single outcome (A/B/C/D) with evidence and fix hints. Report written to `reports/WHEEL_ROOT_CAUSE_REPORT_YYYY-MM-DD.md`.

**How to interpret outcomes:**

- **A) Wheel NOT RUNNING** — `wheel_run_started` count is 0. Cause: strategy not scheduled, feature flag disabled, dispatcher not calling wheel, or runtime exception before wheel runs. Fix: ensure `config/strategies.yaml` has `wheel.enabled: true`; confirm main loop calls wheel when enabled (even if strategy_context import fails); check logs for wheel_run_failed or import errors.
- **B) Wheel RUNNING but ALWAYS SKIPPING** — `wheel_run_started` > 0, `wheel_order_submitted` == 0. Cause: eligibility filters (earnings_window, iv_rank, no_spot, no_contracts_in_range, capital_limit, per_position_limit, insufficient_buying_power, existing_order, max_positions_reached). Use report’s ranked skip-reason table; fix universe, DTE/contract availability, or limits as needed (do not relax risk limits broadly).
- **C) SUBMITTING but NOT FILLING** — `wheel_order_submitted` > 0, `wheel_order_filled` == 0. Cause: broker/paper options, liquidity, or limit price. Inspect last submitted orders (order_id, status, limit/price); improve fill probability via order type/price within existing policy; add “not filled because …” instrumentation.
- **D) Pipeline/counting bug** — Telemetry/attribution have strategy_id=wheel rows but dashboard shows zero. Cause: dashboard filter, wrong strategy_id, or missing fields. Trace `dashboard._load_stock_closed_trades()` and `/api/stockbot/wheel_analytics`; ensure wheel trades are not filtered out and required fields (strategy_id, premium) exist. Contract test: `python3 scripts/test_wheel_analytics_contract.py` (given fixture with strategy_id=wheel, analytics must report total_trades ≥ 1 and premium_collected ≥ 0).

**Regime:** Regime is modifier-only; it must not gate or short-circuit wheel. If any gating is found, remove or disable it by default and document.
