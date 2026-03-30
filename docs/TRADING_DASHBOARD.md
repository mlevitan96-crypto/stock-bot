# Trading Dashboard — Canonical Layout & Data

**Purpose:** Single reference for the trading cockpit (equity cohort). Use this and MEMORY_BANK for what is canonical.

**Note (2026-03):** A retired options-income path was fully removed from runtime and dashboard APIs. Historical reports under `reports/` may still mention it; ignore for operations.

---

## 1. Tab layout

### 1.1 Core cockpit (top-level)

| Strip / panel | Purpose | Data source |
|---------------|---------|-------------|
| **Top strip** | Health + P&amp;L line without blocking the Flask worker on two executive summaries | **`GET /api/dashboard/header_strip`** — `overall_health` from bot `:8081` (2s) or `state/bot_heartbeat.json` mtime; **Day (broker)** matches Positions “Day P&amp;L” (Alpaca + `state/daily_start_equity.json`); **24h / 7d (closed)** = `executive_summary_generator.calculate_pnl_metrics` on the **tail** of `logs/attribution.jsonl` (~18k lines; see JSON `definitions`, `attribution_tail_note`). On failure, UI falls back to `/api/sre/health` + `/api/executive_summary`. |
| **Alpaca operational activity** | Log-based counts (not learning-certified) | **`GET /api/alpaca_operational_activity`** — tails JSONL logs |

| Tab | Purpose | Data source |
|-----|---------|---------------|
| **Positions** | Open positions, P&L, signal strength | `/api/positions` — Alpaca + `state/position_metadata.json`, `data/uw_flow_cache.json` |
| **Closed Trades** | Recent closed trades with P&L, optional `option_phase` context | `/api/stockbot/closed_trades` — `logs/attribution.jsonl`, `logs/exit_attribution.jsonl` |
| **Executive Summary** | Daily/multi-day P&L, health summary | `/api/executive_summary`, `/api/sre/health` |
| **SRE Monitoring** | Bot status, broker connectivity, failure points | `/api/sre/health`, `/api/failure_points`, `/api/sre/self_heal_events` |

### 1.2 Advanced (under “More” dropdown)

| Tab | Purpose | Data source |
|-----|---------|---------------|
| **Signal Review** | Last 50 signal-level diagnostics | `/api/signal_history` |
| **Natural Language Auditor** | NL summaries and audits | `/api/xai/auditor`, `/api/xai/export` |
| **Trading Readiness** | Pre-market checks, failure points | `/api/failure_points` |
| **Telemetry** | Telemetry index and computed artifacts | `/api/telemetry/latest/*` |

---

## 2. Where to find what

- **Health:** Top strip (fast via `header_strip`), Executive Summary (summary), SRE Monitoring (full).
- **P&L:** Top strip = broker day + closed-trade rolling 24h/7d from attribution tail; Positions = unrealized + broker day; Executive Summary = full `attribution.jsonl` scan; Closed Trades = per-row realized.
- **Scoring:** Positions table “Entry Signal Strength” and “Current Signal Strength” (from engine + live composite).

---

## 3. Scoring fields (canonical)

- **Entry Signal Strength** (UI) = `entry_score` from position metadata at entry.
- **Current Signal Strength** (UI) = live composite when UW cache is fresh; see `state/signal_strength_cache.json`.
- Backend keeps `entry_score` and `current_score`; dashboard labels are for clarity.

---

## 4. Top strip

- **Health** — from SRE.
- **P&L today / 7d** — from executive summary.
- **Last signal** — from signal history or heartbeat.
- **Last update** — refresh time.

---

## 5. API endpoint map

See `reports/DASHBOARD_ENDPOINT_MAP.md` if present (may lag code). Dashboard reads logs/state/config only; it does not modify the trading engine.

**Smoke checks:** `scripts/verify_dashboard_contracts.py` (requires running dashboard).

---

## 6. Board watchlists (governance only)

- **Source:** `state/signal_strength_cache.json`, `state/signal_correlation_cache.json`.
- **Artifact:** `reports/board_watchlists_<date>.json` from `board/eod/run_stock_quant_officer_eod.py` (merged input + Board responses). Thresholds are review-only and must not gate trades.

---

## 7. Validation

- `python scripts/generate_daily_strategy_reports.py` — equity + combined reports.
- `python scripts/verify_dashboard_contracts.py` — contract smoke (local dashboard on port 5000).
- After deploy: hard-refresh browser; confirm `/api/sre/health` and `/api/stockbot/closed_trades` return 200.
