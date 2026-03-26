# Wheel hard removal — full inventory (SRE)

**Generated (UTC):** 2026-03-25T19:30:00Z  
**Scope note:** Historical artifacts under `reports/**`, `board/eod/out/**`, and frozen JSON exports may still contain the substring “wheel” until archived or purged separately; **active code, runtime config, and operator docs** are in scope for zero-wheel.

---

## STOP-GATE 0 — Plan (CSA)

1. **Plan (restated):** Remove the options wheel strategy from execution (`main.py`, `strategies/*`), capital split (`config/strategies.yaml`, `capital/strategy_allocator.py`), governance JSON, dashboard UI/APIs, daily report generators, and wheel-only scripts; delete wheel implementation modules; keep equity/Alpaca paths intact; avoid changing telemetry **collection** in `main.py` beyond removing wheel runs (no new emitters).
2. **Touchpoints:** Dashboard tabs (`wheel_strategy`, `strategy_comparison`), JS loaders, `/api/stockbot/wheel_analytics`, `/api/wheel/universe_health`, `/api/strategy/comparison`, positions `strategy_id` inference from `wheel_state.json`, closed-trades telemetry wheel slice, `_aggregate_wheel_reports`, `run_all_strategies` wheel branch, `strategies.yaml` / `strategy_governance.json`, `StateFiles.WHEEL_STATE`, `generate_daily_strategy_reports.py`, board EOD wheel review hooks, 15+ wheel-only scripts, `docs/WHEEL_STRATEGY_EXTERNAL.md`, `MEMORY_BANK.md` wheel sections.
3. **Failure modes / mitigations:** (a) Import errors after deleting modules → grep imports; `python -m py_compile` on `main.py` / `dashboard.py`. (b) Broken dashboard JS → remove tab branches entirely. (c) Empty `strategy_comparison` in combined JSON → learning panel still reads optional fields; keep `{}`. (d) Historical logs with `strategy_id=wheel` → omit from closed-trades API list or exclude wheel strategy_id from merged output.
4. **PLAN_VERDICT:** **APPROVE** (execute with mitigations above).

---

## STOP-GATE 1 — Inventory verdict (CSA)

- **Completeness:** High for runtime + dashboard; board/EOD Python still references wheel strings until patched in the same change set.
- **Risk ranking:** P0 — `dashboard.py`, `main.py`, `strategies.yaml`; P1 — daily reports + board EOD; P2 — audit scripts (`audit_stock_bot_readiness.py`) may still mention wheel until a follow-up trim.
- **PLAN_VERDICT:** **APPROVE**.

---

## Dashboard (`dashboard.py`)

| Area | Description |
|------|-------------|
| Tabs | `wheel_strategy`, `strategy_comparison` buttons and tab panes |
| JS | `loadWheelUniverseHealth`, `loadStrategyComparison`, `loadWheelAnalytics`, `switchTab` branches, `loadClosedTrades` wheel filter/labels/column, `loadPositions` Wheel/Equity label |
| Executive | Extended script fetching `wheel_analytics` / wheel blurb — remove |
| Positions API | `wheel_symbols` / `wheel_state.json`, `_underlying_for_position` wheel match, `strategy_id == wheel` |
| Closed trades | Docstring + telemetry block `strategy_id=wheel`, filter wheel rows out of response |
| Routes | `api_wheel_universe_health`, `api_strategy_comparison`, `api_stockbot_wheel_analytics`, `_aggregate_wheel_reports` |
| Version panel | Grep `/api/stockbot/wheel_analytics` in allowed list if present |

---

## Backend execution

| Path | Role |
|------|------|
| `main.py` | `run_all_strategies()` wheel branch, `wheel_orders` metric |
| `strategies/wheel_strategy.py` | **Delete** |
| `strategies/wheel_universe_selector.py` | **Delete** |
| `strategies/strategy_comparison.py` | **Delete** (only consumer was daily reports) |
| `src/exit/wheel_exit_v1.py` | **Delete** if unused (no `wheel_exit` import found) |
| `strategies/__init__.py` | Docstring |

---

## Config

| File | Change |
|------|--------|
| `config/strategies.yaml` | Equity 100% allocation; remove `wheel` under `strategies` and `capital_allocation` |
| `config/strategy_governance.json` | Remove `WHEEL`; equity `capital_fraction` 1.0 |
| `config/registry.py` | Remove `WHEEL_STATE` |
| `config/universe_wheel.yaml` | **Delete** |
| `config/universe_wheel_expanded.yaml` | **Delete** |
| `config/ai_board_roles.json` | Grep wheel — trim if present |

---

## Scripts (wheel-dedicated — delete)

- `scripts/verify_wheel_endpoints_on_droplet.py`
- `scripts/test_wheel_analytics_contract.py`
- `scripts/test_wheel_governance.py`
- `scripts/wheel_dry_run_rank.py`
- `scripts/check_wheel_skips_on_droplet.py`
- `scripts/check_wheel_on_droplet_quick.py`
- `scripts/diagnose_wheel_data_on_droplet.py`
- `scripts/generate_wheel_daily_review.py`
- `scripts/wheel_root_cause_report.py`
- `scripts/wheel_spot_resolution_verification.py`
- `scripts/run_wheel_check_on_droplet.py`
- `scripts/inspect_wheel_blocks.py`
- `scripts/test_wheel_watchlists.py`

## Scripts (partial edits)

- `scripts/generate_daily_strategy_reports.py` — equity-only combined; no wheel file
- `scripts/verify_dashboard_contracts.py` — drop wheel_analytics contract
- `scripts/audit/run_dashboard_full_validation_on_droplet.py` — drop wheel endpoints
- `scripts/run_stockbot_daily_reports.py` — remove wheel attribution artifact path if safe
- `board/eod/run_stock_quant_officer_eod.py` — `ensure_wheel_daily_review` no-op; trim wheel bundle sections where feasible
- `board/eod/eod_confirmation.py` — remove `--skip-wheel-closure` if obsolete or keep harmless

---

## Docs

- `docs/WHEEL_STRATEGY_EXTERNAL.md` — **Delete**
- `docs/TRADING_DASHBOARD.md`, `MEMORY_BANK.md` — remove wheel sections / replace with one-line decommission note

---

## Tests / CI

- Grep `pytest` / `test_wheel` — remove or skip deleted modules
- `scripts/run_regression_checks.py` if it references wheel

---

## Telemetry (read-only note)

- Historical `telemetry.jsonl` may contain past `strategy_id=wheel`; **no backfill**. Runtime no longer emits wheel strategy events after `main.py` change.
