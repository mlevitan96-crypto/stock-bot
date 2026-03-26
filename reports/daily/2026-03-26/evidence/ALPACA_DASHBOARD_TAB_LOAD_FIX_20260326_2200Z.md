# Alpaca dashboard — tab load & routing hardening (SRE)

**Timestamp:** 20260326_2200Z  
**Scope:** Main trading dashboard HTML/JS in `dashboard.py` (Alpaca-focused primary UI).

## Tab inventory (registered in `switchTab`)

| Tab key | Route (client) | Primary data loaders / APIs |
|--------|----------------|-----------------------------|
| `positions` | `#positions-tab` | `GET /api/positions` |
| `closed_trades` | `#closed_trades-tab` | `GET /api/stockbot/closed_trades` |
| `system_health` | `#system_health-tab` | `GET /api/dashboard/data_integrity`, `GET /api/telemetry/latest/index` |
| `executive` | `#executive-tab` | `GET /api/executive_summary` |
| `sre` | `#sre-tab` | `GET /api/sre/health` |
| `signal_review` | `#signal_review-tab` | `GET /api/signal_history` |
| `failure_points` | `#failure_points-tab` | `GET /api/failure_points` |
| `telemetry` | `#telemetry-tab` | `GET /api/telemetry/latest/*`, computed artifacts, `GET /api/paper-mode-intel-state` |
| `learning_readiness` | `#learning_readiness-tab` | `GET /api/learning_readiness` |
| `profitability_learning` | `#profitability_learning-tab` | `GET /api/profitability_learning` |
| `fast_lane` | `#fast_lane-tab` | `GET /api/stockbot/fast_lane_ledger` |

## Global / strip (not separate tabs)

- `GET /api/version` — version badge  
- `GET /api/alpaca_operational_activity` — top operational activity panel (public GET allowlist)  
- `GET /api/sre/health`, `GET /api/executive_summary` — top strip  
- `GET /api/direction_banner`, `GET /api/situation` — banners  

## Hardening rules applied

1. **HTTP 200 + structured body** for dashboard-owned fallbacks (e.g. missing XAI export returns `{ ok: false, state: "DISABLED", reason: ... }` rather than raw 404).  
2. **No silent empty failure states** for tab loaders: use `panel-info` / explanatory copy and `#tab-state-line-*` via `setTabStateLine`.  
3. **Auth failures** are **PARTIAL** + explicit “sign in” copy, not unlabeled errors.  
4. **Verification script:** `scripts/dashboard_verify_all_tabs.py` includes `GET /api/alpaca_operational_activity?hours=72` alongside other tab APIs.

## CSA / SRE note

This document describes **UI routing and client behavior**. It does not assert droplet deployment or live HTTP proof (see `ALPACA_DASHBOARD_DROPLET_PROOF_20260326_2200Z.*`).
