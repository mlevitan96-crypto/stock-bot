# Options Wheel Pivot — Sovereign Board Strategy Review & Data-Path Verdict (2026-05-01)

This document satisfies **Phase 1** (persona standoff), **Phase 2** (data integrity trace), and records implementation touchpoints for **Phases 3–4**. Deployment (**Phase 5**) requires operator credentials on the Alpaca droplet; local verification is complete (`pytest tests/` green).

---

## Phase 1 — Sovereign board standoff (advisory personas)

### 1. Quant (Sterling) — Put wall, delta, DTE

- **Put wall (operational definition in code):** Strike **at or below spot** with the **largest put `curr_oi`** from UW `/api/stock/{ticker}/oi-change` (paginated list, default `limit=200`). This is a **liquidity / positioning deck proxy**, not a guarantee of “smart money” intent. Minimum OI at the wall defaults to **5,000** contracts (`risk.put_wall_min_oi` in `config/strategies.yaml`).
- **Institutional floor gate:** A CSP at strike **K** is allowed only if `wall_strike ≤ K` and the wall meets minimum OI — i.e. concentrated put interest **at or below** the sold strike (support stack under the chosen strike).
- **Delta / DTE (unchanged defaults in `wheel_strategy`):** CSP target delta band **−0.30 to −0.20** (estimated from moneyness until broker greeks are wired), DTE **5–10**; CC **0.20–0.30** delta, DTE **7–21**. Sterling would tighten CSP delta toward **−0.18 to −0.25** and lengthen DTE slightly in low-VIX regimes to reduce gamma blow-ups; that remains **config-driven**, not silently changed here.

### 2. SRE (Vane) — Alpaca spot → options → state

- **Spot / chain:** `_resolve_spot` → Alpaca `get_quote` + 1m bar fallback → `/v2/options/contracts` for puts in DTE window (same as before).
- **`state/wheel_state.json`:** Schema already tracks `open_csps`, `open_ccs`, `assigned_shares`, `csp_history`, `cc_history`, `recent_orders`. **`src/wheel_manager.reconcile_assignments_from_broker`** now promotes CSP → stock when the **option leg is absent** from broker positions and **underlying qty ≥ 100** (100-lot heuristic; clears legs that expired OTM without assignment).
- **Fractional shares:** Wheel CC path assumes **100-share** covered lots; fractional post-assignment is **out of scope** for this module — Alpaca must reconcile to whole shares or the operator adjusts `wheel_state` manually.

### 3. Adversary (Marcus) — Swarm audit & circuit breakers

| Failure mode | Why the wheel dies | Automated mitigations (code) |
|----------------|-------------------|------------------------------|
| **50% gap down** | Short puts explode vs cash collateral | `options_engine.circuit_breaker_gap_down` (default 35% vs prior close) — wire to `main`/wheel runner when prev-close feed exists. |
| **Illiquid chains** | Wide spreads, no fill, bad marks | Existing `MIN_OPEN_INTEREST` / volume filters + **put wall min OI**; `circuit_breaker_illiquid_chain`. |
| **Pin risk (gamma into expiry)** | Max pain squeezes | `circuit_breaker_pin_risk` (short DTE + last hours) — optional gate before open. |

**UW / Alpaca silent failure:** Put wall and IV gates are **fail-closed** when UW returns blocked/empty (except `UW_MOCK` soft mode for CI). Staleness is bounded by **UW client TTL** (wheel oi-change cache **120s**, iv-rank **300s** in `UwCachePolicy`).

### 4. Archaeologist (Chen) — Join integrity (UW ↔ Alpaca)

- **Path:** `[UW REST oi-change + iv-rank + earnings]` → **`src/options_engine`** gates → **Alpaca option contracts + quote/bar spot** → **order submit** (`strategies/wheel_strategy`).
- **Anti-stale-OI:** Do not trust WebSocket flow alone for OI walls; wheel uses **REST oi-change** through **`uw_http_get`** (quota + cache + error log). On `_blocked` or non-200, **no CSP** on put-wall-dependent path.
- **Ticker normalization:** `uw_ticker_for_rest` maps `BRK-B` → `BRK.B` for UW paths while **SP100 membership** uses hyphen-normalized roots.

---

## Phase 2 — Data-path verdict

| Segment | Status | Notes |
|---------|--------|-------|
| UW → put wall | **Green** when UW healthy | Fail-closed on empty/blocked. |
| UW → IV rank ≥ 50 | **Green** when payload valid | Default `min_iv_rank: 50` in `config/strategies.yaml`. |
| UW → earnings 21d | **Green** when earnings endpoint returns parseable next date | `avoid_earnings_window_days: 21`. |
| SP100 gate | **Green / hard** | `SP100_CONSTITUENTS` frozen set (101 names, Wikipedia 2025-09-22 snapshot); **no env bypass**. |
| Alpaca chain + submit | **Amber** on paper | `min_credit_usd: 0` until real NBBO-based limits replace the `0.05` stub; set **`min_credit_usd: 200`** for live with live quotes. |
| Assignment auto-state | **Green (heuristic)** | `wheel_manager.reconcile_assignments_from_broker`; review false positives if non-wheel stock buys overlap. |

---

## Phase 3 — Implementation map

| Deliverable | Location |
|-------------|----------|
| Put wall, IV rank, earnings, SP100, dust helper, circuit helpers | `src/options_engine.py` |
| Reconciliation + `run_wheel` | `src/wheel_manager.py` |
| CSP wiring (SP100, put wall, dust, IV/earnings defaults) | `strategies/wheel_strategy.py` |
| Premium + NAV milestone watcher | `scripts/wheel_premium_milestone_watcher.py` |
| Tests | `tests/test_options_wheel_engine.py` |

**Note:** Existing callers that import `strategies.wheel_strategy.run` directly **do not** auto-reconcile; use **`src.wheel_manager.run_wheel`** when assignment detection should run first.

---

## Phase 4 — Regression

- **Pytest:** `294 passed, 3 skipped` (full `tests/` run on 2026-05-01).
- **Simulation CSP → assignment → CC:** Not automated end-to-end (requires broker + UW); manual checklist: sell CSP → observe fill telemetry → force assignment on paper → confirm `reconcile_assignments_from_broker` + CC phase in logs.

---

## Phase 5 — Deployment (operator)

Per `MEMORY_BANK_ALPACA.md` workflow (not executed from this session without droplet auth):

1. `git push origin main`
2. On droplet: `git fetch origin && git reset --hard origin/main` then `sudo systemctl restart stock-bot.service`
3. `python3 scripts/reset_epoch.py --write --epoch-label options_wheel_v1`
4. (Optional) Schedule `scripts/wheel_premium_milestone_watcher.py` alongside `telemetry_milestone_watcher.py`.

---

## First-live trade checklist

- [ ] Set `risk.min_credit_usd` to **200** only when option quotes feed limit prices (replace `0.05` stub).
- [ ] Confirm wheel universe tickers ⊆ **SP100** (non-SP100 names will skip with `not_sp100`).
- [ ] Confirm `UW_*` quota healthy; watch `reports/uw_health/uw_api_errors.jsonl`.
- [ ] Run one dry cycle on paper with `logs/system_events.jsonl` tail for `subsystem=wheel`.
