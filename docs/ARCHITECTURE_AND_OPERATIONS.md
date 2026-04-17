# Stock-Bot: Architecture & Operations Reference

**Source:** MEMORY_BANK_ALPACA.md, droplet client, and repo config. No secrets.  
**Droplet-derived:** Live status and branch info obtained via `DropletClient` where required.

---

## 1. Architecture: Cursor and Droplet Roles

### High-level flow (Golden Workflow)

```
USER → CURSOR → GITHUB → DROPLET → GITHUB → CURSOR → USER
```

- **Cursor:** Authoring, push to GitHub, trigger droplet deploy via SSH (`droplet_client.py`), pull results, analyze, report. Must complete the full cycle; no task is complete until deploy + verification are done.
- **GitHub:** Single source of code; all changes are pushed before deployment. Branch strategy below.
- **Droplet:** Production runtime. Runs trading engine, dashboard, and data pipelines. **Canonical host:** `104.236.102.57` (stock-bot); SSH alias **alpaca** preferred. Project dir: `/root/stock-bot`.

### Cursor responsibilities (from MEMORY_BANK)

- Always push code to GitHub before deployment.
- Always trigger droplet deployment via SSH (e.g. `DropletClient().deploy()`).
- Always wait for verification and pull results from GitHub.
- Reports must use production data from the droplet (e.g. `ReportDataFetcher`); no local-only report data.

### Droplet roles

- **Runtime:** `deploy_supervisor.py` orchestrates `dashboard.py` (port 5000), `uw_flow_daemon.py`, and `main.py` (trading engine). Systemd service: `stock-bot.service`.
- **Data authority:** Logs, state, telemetry, and EOD bundles are produced on the droplet. Audits and daily/weekly reviews must run on the droplet or fetch droplet artifacts.
- **Deploy sequence (on droplet):** `git pull origin main` → `pkill -f 'dashboard\.py'` → `sudo systemctl restart stock-bot` so a single dashboard binds to port 5000.

### Entry points and layout

| Role        | Entry point / path |
|------------|---------------------|
| Orchestrator | `deploy_supervisor.py` |
| Trading engine | `main.py` |
| Dashboard  | `dashboard.py` (port 5000) |
| UW ingestion | `uw_flow_daemon.py` |
| Health     | `heartbeat_keeper.py` |
| Risk       | `risk_management.py` |
| Strategies | `strategies/equity_strategy.py` |

Canonical repo layout: **`reports/repo_audit/CANONICAL_REPO_STRUCTURE.md`**.

---

## 2. GitHub Repo and Branch Strategy

- **Repo:** `https://github.com/mlevitan96-crypto/stock-bot` (origin; fetch/push).
- **Primary branch:** `main`. All deployments use `git pull origin main` on the droplet.
- **Other branches:** Feature/cleanup branches (e.g. `cursor/repo-cleanup-20260227`) are merged into `main`; no long-lived alternate deploy branches.
- **Droplet (live):** Current branch on droplet is **main**; project dir `/root/stock-bot`. Service status and git state can be checked via `DropletClient().get_status()` and `DropletClient().get_git_status()`.

No secrets are stored in the repo; credentials live in `/root/stock-bot/.env` on the droplet (and locally in `.env`, gitignored).

---

## 3. Backtest Results / Summary Metrics

- **Documented backtest (droplet run):** `reports/DROPLET_BACKTEST_RUN_SUMMARY.md`  
  - Run ID: `alpaca_backtest_20260222T022321Z`  
  - **Net PnL:** +$16,623.74  
  - **Trades:** 10,715  
  - **Win rate:** 51.47%  
  - **Min exec score (config):** 1.8  
  - Data: Alpaca 1m snapshot (lab-mode). Governance: PASS; board: ACCEPT.

- **Older aggregate (3g run):** `reports/BACKTEST_RESULTS_CHECK.md`  
  - One 3g run: 2,243 trades, -$162.15, 15.16% win rate; per-signal buckets were missing (pre–injection). Current data-driven tuning depends on runs with replay-time signal injection and updated edge reports.

- **Expectancy / drawdown:**  
  - Win rate, avg PnL, avg win, avg loss, and expectancy are defined in MEMORY_BANK (Section 8.6 long/short asymmetry; telemetry contracts).  
  - No single “max drawdown” summary is canonical in the doc set; governance and CSA verdicts reference giveback, baseline comparison, and circuit-breaker/brake (e.g. MIN_EXEC_SCORE or pause) in runbooks.

For latest backtest artifacts and re-runs: `scripts/run_alpaca_backtest_orchestration_via_droplet.py` (run on droplet; optionally fetch-only with a run ID).

---

## 4. Current Risk Parameters and Position Sizing

**Source:** `config/registry.py` (Thresholds), `config/theme_risk.json`. Env overrides where noted.

| Parameter | Default (env override) | Notes |
|-----------|------------------------|--------|
| **MIN_EXEC_SCORE** | 2.5 | Entry score floor (lowered per blocked-trade analysis). |
| **MAX_CONCURRENT_POSITIONS** | 16 | Cap on open positions. |
| **MAX_NEW_POSITIONS_PER_CYCLE** | 6 | New entries per cycle. |
| **POSITION_SIZE_USD** | 500 | Fixed position size per trade. |
| **MAX_THEME_NOTIONAL_USD** | 50,000 (registry) | Theme cap; theme_risk.json can set 150,000 for Tech_Growth. |
| **Theme risk (theme_risk.json)** | ENABLE_THEME_RISK: true, MAX_THEME_NOTIONAL_USD: 150,000 | Tech_Growth max 150k; default theme 100k. |
| **TRAILING_STOP_PCT** | 0.015 | Trailing stop. |
| **PROFIT_SCALE_PCT** | 0.02 | Profit scaling. |
| **TIME_EXIT_MINUTES** | 240 | Time-based exit (4h). |
| **TIME_EXIT_DAYS_STALE** | 12 | Stale position exit. |
| **DISPLACEMENT_MIN_AGE_HOURS** | 4 | Min age before displacement. |
| **DISPLACEMENT_MAX_PNL_PCT** | 0.01 | Max PnL % for displacement. |
| **DISPLACEMENT_SCORE_ADVANTAGE** | 2.0 | Score advantage for displacement. |
| **DISPLACEMENT_COOLDOWN_HOURS** | 6 | Cooldown after displacement. |

**Position sizing rule:** Fixed **$500 per position** (POSITION_SIZE_USD); theme notional caps apply per theme (see `config/theme_risk.json`). Startup safety and execution limits (e.g. daily notional cap, max concurrent orders) are in `config/startup_safety_suite_v2.json`.

---

## 5. Monitoring and Alerting: Endpoints and Runbooks

### Dashboard and health endpoints

- **Dashboard URL:** http://104.236.102.57:5000/ (Basic Auth: `DASHBOARD_USER`, `DASHBOARD_PASS` from `.env`).
- **Health check (on droplet):**  
  `curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health`  
  Returns `{"status":"healthy"|"degraded",...}`.

**Endpoint → data map:** **`reports/DASHBOARD_ENDPOINT_MAP.md`**. Key API endpoints include:

| Endpoint | Purpose |
|----------|---------|
| `/api/ping` | Health check |
| `/api/health_status` | Alpaca, orders, heartbeat |
| `/api/system/health` | Supervisor health (`state/health.json`) |
| `/api/sre/health` | SRE health (localhost:8081 or fallback) |
| `/api/scores/distribution`, `/api/scores/components`, `/api/scores/telemetry` | Score telemetry |
| `/api/regime-and-posture` | Market context and regime |
| `/api/rolling_pnl_5d` | 5-day rolling PnL |
| `/api/executive_summary` | Executive summary (timeframe query) |
| `/api/positions`, `/api/stockbot/closed_trades` | Positions and closed trades |

### Runbooks (canonical names)

| Runbook | Path / description |
|---------|--------------------|
| **Full day trading intelligence audit** | `reports/audit/FULL_DAY_TRADING_INTELLIGENCE_AUDIT_RUNBOOK.md` — run on droplet; phases 0–10, CSA + SRE + board. |
| **Weekly board audit** | `reports/audit/WEEKLY_BOARD_AUDIT_RUNBOOK.md` — weekly CSA board audit sequence (evidence, ledger, verdict, persona memos, cockpit, deploy). |
| **CSA & Profitability Cockpit (droplet)** | `reports/audit/DROPLET_CSA_AND_COCKPIT.md` — CSA 100-trade trigger, cockpit refresh, backup cron. |
| **Monday open readiness** | Referenced in `reports/audit/MONDAY_OPEN_READINESS_*.md` — 30s operator steps (e.g. pre-open checks, kill switch: TRADING_MODE=HALT or stop stock-bot). |
| **Phase 9 droplet runbook** | `reports/phase9_droplet_runbook.md` — canonical overlay/exit lever runbook (Steps 1–7). |
| **Cursor automations UI** | `reports/audit/CURSOR_AUTOMATIONS_UI_RUNBOOK.md` — setup for PR risk, bug review, security, governance integrity, weekly summary. |
| **Droplet investigation** | `reports/investigation/DROPLET_RUNBOOK.md`, `DROPLET_RUNBOOK_SIGNALS_ENTRIES.md`. |
| **Equity governance orchestrator** | `reports/governance/EQUITY_GOVERNANCE_ORCHESTRATOR_RUNBOOK.md` (see MEMORY_BANK_INDEX). |

### Telegram (Alpaca governance)

- **Where Telegram vars live on droplet:** (1) `/root/stock-bot/.env` — loaded by systemd for `stock-bot.service` (main bot, dashboard). (2) `/root/.alpaca_env` — for cron or manual runs (e.g. daily governance). (3) Venv `activate` — when you `source venv/bin/activate` in a shell.
- **Sync venv/.alpaca_env → .env:** If you add Telegram to venv or `.alpaca_env` only, run on droplet: `source /root/.alpaca_env 2>/dev/null; source venv/bin/activate && python3 scripts/sync_telegram_to_dotenv.py` so `.env` gets them (systemd uses .env; restart stock-bot to pick up changes).
- **E2E audit:** `scripts/run_alpaca_e2e_audit_on_droplet.py` sources `.alpaca_env` and `venv/bin/activate` before running governance scripts and sync_telegram_to_dotenv, so Telegram is present from venv/.alpaca_env; sync then writes to `.env` for future runs.

### Alerts and governance

- **Stagnation alerts:** Score stagnation (e.g. 20+ consecutive score=0.00; funnel stagnation >50 alerts, 0 trades in 30 min in RISK_ON). Diagnostics: `state/signal_weights.json`, `comprehensive_score_diagnostic.py`.
- **UW daemon health:** `scripts/run_daemon_health_check.py`; state in `state/uw_daemon_health_state.json`; endpoint error spikes in `logs/system_events.jsonl`.
- **CSA verdict:** Latest verdict and summary: `reports/audit/CSA_VERDICT_LATEST.json`, `reports/audit/CSA_SUMMARY_LATEST.md`. Profitability cockpit: `reports/board/PROFITABILITY_COCKPIT.md`.

---

*Generated from MEMORY_BANK_ALPACA.md and droplet client. For deployment steps and SSH config, see MEMORY_BANK Section 6 and `droplet_config.example.json`.*
