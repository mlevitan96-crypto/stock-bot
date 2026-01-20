# STRUCTURAL_UPGRADE_SUMMARY_2026-01-20.md
**Date:** 2026-01-20  
**Scope:** Structural upgrade of strategy stack (data → features → scores → regime → posture → decisions), preserving reliability + observability.

---

## Summary of changes (additive, safe-by-default)

- **Architecture contracts documented**
  - `reports/ARCHITECTURE_CONTRACTS_CURRENT.md`
  - `reports/ARCHITECTURE_CONTRACTS_DATA.md`

- **Market context ingestion (premarket + vol term proxy)**
  - New: `structural_intelligence/market_context_v2.py`
  - Writes: `state/market_context_v2.json`
  - System events: `subsystem="data"` with stale + premarket-critical alerts.
  - Wired into `main.py:run_once()` as best-effort (never blocks).

- **Volatility + beta features (symbol selection inputs)**
  - New: `structural_intelligence/symbol_risk_features.py`
  - Writes: `state/symbol_risk_features.json`
  - Enrichment: `uw_enrichment_v2.enrich_signal()` now attaches:
    - `realized_vol_5d`, `realized_vol_20d`, `beta_vs_spy`
  - No scoring weights changed yet (log-only).

- **Regime + posture layer (separate from scoring/gates)**
  - New: `structural_intelligence/regime_posture_v2.py`
  - Writes: `state/regime_posture_state.json`
  - System events: `subsystem="regime"`, `event_type="posture_update"`
  - Wired into `main.py:run_once()` as best-effort (no gating changes yet).

- **Composite v2 + shadow A/B**
  - New: `uw_composite_v2.compute_composite_score_v3_v2()` (additive adjustment layer)
  - New: `telemetry/shadow_ab.py` → append-only `logs/shadow.jsonl`
  - Shadow compares v1 vs v2 at:
    - **scoring stage** (score + composite gate)
    - **decision stage** (score floor + expectancy gate + hypothetical execution markers)
  - System events:
    - `subsystem="scoring"`, `event_type="composite_version_used"`
    - `subsystem="shadow"`, `event_type="divergence"`

- **Dashboard support**
  - New endpoint: `GET /api/regime-and-posture`
    - returns market context, regime/posture, and shadow/composite config flags.

- **Report tooling (droplet-source-of-truth)**
  - `report_data_fetcher.py` extended to fetch `logs/shadow.jsonl` from droplet.
  - New generators:
    - `reports/_daily_review_tools/generate_shadow_audit.py`
    - `reports/_daily_review_tools/generate_daily_health.py`

---

## Rollout plan (per mandate)

- **Phase 1 (current)**
  - Keep `COMPOSITE_VERSION="v1"` (default)
  - Keep `SHADOW_TRADING_ENABLED=true` (default)
  - Review `logs/shadow.jsonl` + `reports/SHADOW_TRADING_AUDIT_YYYY-MM-DD.md`

- **Phase 2 (after shadow review)**
  - Optionally set `COMPOSITE_VERSION="v2"` while shadow stays on (still safe-by-default if decision wiring remains v1-only).

- **Phase 3 (explicit, later)**
  - Consider enabling short entries in bear/crash regimes with explicit contracts and gates.

---

## How to toggle

- **Shadow A/B**
  - `SHADOW_TRADING_ENABLED=true|false`

- **Composite version**
  - `COMPOSITE_VERSION=v1|v2`

---

## Key files added/updated

- `structural_intelligence/market_context_v2.py`
- `structural_intelligence/symbol_risk_features.py`
- `structural_intelligence/regime_posture_v2.py`
- `telemetry/shadow_ab.py`
- `uw_composite_v2.py` (adds `compute_composite_score_v3_v2`)
- `main.py` (wires context + features + posture + shadow logging)
- `dashboard.py` (adds `/api/regime-and-posture`)
- `report_data_fetcher.py` (adds `shadow` log fetching)

