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

## 6. Validation

- Run `python scripts/generate_daily_strategy_reports.py` to ensure wheel and strategy comparison data exist.
- Dashboard checks: `scripts/verify_dashboard_contracts.py`, `scripts/verify_wheel_endpoints_on_droplet.py`.
- After deployment: confirm Health and P&L on Top Strip and in Executive Summary; Wheel metrics when wheel has traded; Signal Strength columns show non-zero when positions exist and cache is fresh.
