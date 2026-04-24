# ALPACA MEMORY_BANK unified diff (20260328_213500Z)

**Commit:** 7064fba

`diff
commit 7064fba017631fa6221df1a51b568491354fd26c
Author: Mark <mlevitan96@gmail.com>
Date:   Sat Mar 28 14:19:08 2026 -0700

    Alpaca MEMORY_BANK: reconcile to live droplet operational reality
    
    Read-only SSH verify 2026-03-28: add Alpaca droplet canon (systemd, paths, secrets, port 5000); fix stock-bot ExecStart, trading-bot.service not-found, dashboard dual-process nuance, fast-lane crontab conditional, Tier 3 stale bullet; align §6.5/6.6 and STOCK-BOT ISOLATION. Evidence: reports/daily/2026-03-28/evidence/ALPACA_DROPLET_REALITY_20260328_213500Z.md.
    
    Made-with: Cursor

diff --git a/MEMORY_BANK.md b/MEMORY_BANK.md
index c023642..c262efa 100644
--- a/MEMORY_BANK.md
+++ b/MEMORY_BANK.md
@@ -1010,6 +1010,26 @@ Cursor MUST NOT apply changes unless explicitly instructed.
 - **Alpaca-specific context:** Market type: US equities (session-based). Validation windows: trade-count and session-based. Metrics: expectancy, PnL/day, capital efficiency, slippage, drawdown. Ledger path: `state/governance_experiment_1_hypothesis_ledger_alpaca.json`.
 - **Alpaca Data Sources (canonical — live bot writes here):** Closed-trade count and PnL MUST use the same paths the live bot writes to. **canonical_closed_trade_log_path:** `logs/exit_attribution.jsonl` (v2 equity exits; one line per closed trade). **Secondary:** `logs/attribution.jsonl` (closed trades with PnL/close_reason; filter out `trade_id` starting with `open_`). **Fallback:** `logs/master_trade_log.jsonl` (records with `exit_ts` set = closed trade). Paths are relative to repo root (e.g. `/root/stock-bot` on droplet). Config registry: `config.registry.LogFiles.EXIT_ATTRIBUTION`, `LogFiles.ATTRIBUTION`, `LogFiles.MASTER_TRADE_LOG`. If these paths change, update `scripts/experiment_1_status_check_alpaca.py` and this section.
 
+#### Alpaca droplet — live operational canon (SSH read-only verify: 2026-03-28)
+- **Goals:** Single source of operational truth for the **live Alpaca equity droplet**; align scripts and operators on paths, units, and secrets **without** implying trading or deploy authorization from this text.
+- **Constraints:** This canon is descriptive. It does not replace CSA/SRE review artifacts, hypothesis ledger rules, or SPI non-prescriptive outputs. When host configuration changes, re-run a read-only audit and update this subsection + evidence under `reports/daily/<ET-date>/evidence/`.
+- **SSH (canonical):** Prefer `Host alpaca` in `~/.ssh/config` resolving to **`104.236.102.57`**; **`droplet_config.json`** is the repo anchor (`use_ssh_config: true`, `username: root`, **`project_dir: /root/stock-bot`**). Scripted path: **`droplet_client.py`** (Paramiko). **Never** use **`147.182.255.165`** for stock-bot.
+- **Hostname (verified):** `ubuntu-s-1vcpu-2gb-nyc3-01-alpaca`.
+- **Canonical repo root on this droplet:** **`/root/stock-bot` only** — present and active. **`/root/stock-bot-current`** and **`/root/trading-bot-current`** were **not present** at verify; tools such as `scripts/diagnose_cron_and_git.py` may still probe those paths first — do not assume they exist on every host.
+- **Python:** Trading stack **`/root/stock-bot/venv`** (Python **3.12.3**). **`stock-bot-dashboard.service`** runs **`/usr/bin/python3 /root/stock-bot/dashboard.py`** (not the venv interpreter).
+- **systemd — core active units (verified):**
+  - **`stock-bot.service`:** `WorkingDirectory=/root/stock-bot`, `EnvironmentFile=/root/stock-bot/.env`, **`ExecStart=/root/stock-bot/systemd_start.sh`** → activates venv and runs **`venv/bin/python deploy_supervisor.py`**. Drop-ins observed: logging flags, **`MIN_EXEC_SCORE=2.7`**, truth router mirror, **`STOCKBOT_TRUTH_ROOT=/var/lib/stock-bot/truth`**.
+  - **`stock-bot-dashboard.service`:** Flask dashboard, **`PORT=5000`**, `EnvironmentFile=-/root/stock-bot/.env`.
+  - **`uw-flow-daemon.service`:** **`venv/bin/python uw_flow_daemon.py`**, `EnvironmentFile=-/root/stock-bot/.env`.
+- **Port 5000 (verified):** Bound by the **`python3`** process started as **`/usr/bin/python3 .../dashboard.py`** (dashboard unit). **`deploy_supervisor.py`** may also spawn a **venv** `dashboard.py` child; at verify only the **systemd dashboard** process held the port — treat duplicate dashboard processes as an operational risk to inspect (`ss -tlnp`, `ps aux`) after deploys.
+- **systemd — `trading-bot.service`:** **not-found** on this host (do not use that unit name here).
+- **systemd — units in `failed` state (observed 2026-03-28, non-exhaustive):** `alpaca-forward-truth-contract.service` (timer still triggers; journal showed **exit 2 INCIDENT**), `alpaca-postclose-deepdive.service`, `stock-bot-dashboard-audit.service`, `trading-bot-doctor.service`. These are **SRE signals**, not automatic instructions to restart or reconfigure during audits.
+- **Timers (observed):** `alpaca-forward-truth-contract.timer`, `alpaca-postclose-deepdive.timer`, `stock-bot-dashboard-audit.timer`.
+- **Telegram / secrets:** **`/root/.alpaca_env`** (mode `600`) — sourced by **cron** jobs (e.g. trade milestones). **`/root/stock-bot/.env`** — API keys, dashboard Basic Auth, **`EnvironmentFile`** for systemd units above. Sync path when needed: **`scripts/sync_telegram_to_dotenv.py`**.
+- **Cron (root, verified slice):** `scripts/notify_alpaca_trade_milestones.py` on a 10-minute cadence during NY session weekdays, with `source /root/.alpaca_env`. **Full fast-lane 15m / 4h entries were not present** in root crontab at verify — if MEMORY references those schedules, confirm with `crontab -l` and `scripts/install_fast_lane_cron_on_droplet.py` install state before assuming they are live.
+- **Logs / evidence:** Runtime under **`logs/`** relative to repo; governance JSON under **`state/`** (e.g. `state/alpaca_*.json`, `state/fast_lane_experiment/`). Packaged evidence: **`reports/daily/<ET-date>/evidence/`** (see repo visibility rules).
+- **Offline PnL + SPI:** `scripts/audit/alpaca_pnl_massive_final_review.py` with **`--root /root/stock-bot`**; strict cohort from `telemetry/alpaca_strict_completeness_gate.py` and session truth runners (**SPI does not authorize behavior change** — see below).
+
 #### Alpaca Signal Path Intelligence (SPI)
 - **Purpose:** Post-trade, read-only path analytics on **executed Alpaca trades** already selected by the strict / session PnL cohort (`complete_trade_ids` joined to `logs/exit_attribution.jsonl`). Describes distributions (time-to-threshold, MAE/MFE-style path stats, volatility ratio vs a pre-entry window of comparable length, descriptive path-shape buckets). **Not** price targets, forecasts, or recommendations.
 - **Constraints:** No strategy, execution, exit/stop, or signal changes. No mutation of canonical logs or broker state. Default bar load is **cache-only** (`fetch_if_missing=False`); optional `ALPACA_SPI_FETCH_BARS=true` may populate `data/bars/` via existing `data/bars_loader.py` (operator opt-in only).
@@ -1050,7 +1070,7 @@ Cursor MUST NOT apply changes unless explicitly instructed.
 - **CSA/SRE requirements:** CSA approves ledger schema and cycle scoring; SRE approves directory layout and disk safety. Both review-only; activation and cron installation are opt-in and documented in verification doc.
 
 ### Alpaca Fast-Lane Live Activation
-- **Cron:** Installed via `scripts/install_fast_lane_cron_on_droplet.py`: cycle every 15 min, supervisor every 4h. Uses `/root/.alpaca_env` and `/root/stock-bot`.
+- **Cron / scheduling:** Installer: `scripts/install_fast_lane_cron_on_droplet.py` (intended: cycle every 15 min, supervisor every 4h; uses `/root/.alpaca_env` and `/root/stock-bot`). **Live verify (2026-03-28):** root `crontab -l` showed **only** the trade-milestones job — **no** fast-lane lines. Confirm on-host with `crontab -l` / install script before assuming schedules are active.
 - **Scripts:** `run_fast_lane_shadow_cycle.py`, `run_fast_lane_supervisor.py`, `notify_fast_lane_summary.py` (--kind cycle | board).
 - **25-trade Telegram (promotions every 25 trades):** After each completed 25-trade cycle the cycle script calls `notify_fast_lane_summary.py --kind cycle` with --cycle-id, --pnl-usd, --promoted, --runner-ups. One Telegram per cycle (e.g. "🔬 Alpaca Fast-Lane (25-trade promotion)", Promoted: …, Window PnL). **Verify on droplet:** `state/fast_lane_experiment/fast_lane_ledger.json`, `logs/fast_lane_shadow.log` (grep "Cycle.*completed"), and that `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` are in `/root/.alpaca_env` (cron sources this). No cycle completes until there are 25 post-epoch exits; until then log shows "No post-epoch exit trades; skip cycle".
 - **Go-forward / historical cancelled:** Epoch start in `state/fast_lane_experiment/config.json` → `epoch_start_iso`. Only trades with exit timestamp ≥ epoch are counted. **If you have 25+ trades but no cycle completing:** check on droplet that `post_epoch_count` (exits with timestamp ≥ epoch) is ≥ next window (e.g. 100 for 4th cycle). If zero post-epoch, set epoch to an earlier date (e.g. `2026-03-14T00:00:00Z`) so recent trades count; then run cycle once with `. /root/.alpaca_env` and `python3 scripts/run_fast_lane_shadow_cycle.py`. On droplet, epoch was set to 2026-03-14 so cycles run on recent data (verified 2026-03-16: cycle_0004 completed, promoted angle and state updated).
@@ -1072,7 +1092,6 @@ Cursor MUST NOT apply changes unless explicitly instructed.
 - **Script:** `scripts/run_alpaca_board_review_tier3.py` — Alpaca Tier 3 (long-horizon) Board Review packet generation. Args: --base-dir, --date, --force, --dry-run. Reads last387/last750/30d comprehensive review, SHADOW_COMPARISON_LAST387, weekly ledger (optional), CSA_VERDICT_LATEST, SRE_STATUS, etc.; writes `reports/ALPACA_BOARD_REVIEW_<YYYYMMDD>_<HHMM>/BOARD_REVIEW.md` and `BOARD_REVIEW.json`; updates `state/alpaca_board_review_state.json`. No cron, no promotion logic, no heartbeat, no convergence logic.
 - **Packet directory:** `reports/ALPACA_BOARD_REVIEW_<timestamp>/` (timestamp UTC YYYYMMDD_HHMM).
 - **CSA/SRE approval:** Plan reviewed in `reports/audit/ALPACA_TIER3_PLAN_CSA_REVIEW.md` (ACCEPT) and `ALPACA_TIER3_PLAN_SRE_REVIEW.md` (OK); packet reviewed in `ALPACA_TIER3_PACKET_CSA_REVIEW.md` (ACCEPT) and `ALPACA_TIER3_PACKET_SRE_REVIEW.md` (OK).
-- **Not yet implemented:** Tier 1/2 packet generation, convergence logic, promotion gate changes, heartbeat.
 
 ### Alpaca Tier 1 + Tier 2 Board Reviews — IMPLEMENTED
 - **Scripts:** `scripts/run_alpaca_board_review_tier1.py` (Tier 1 short-horizon), `scripts/run_alpaca_board_review_tier2.py` (Tier 2 medium-horizon). Tier 1: 1d/3d/5d rolling windows, 5d rolling PnL state, trade visibility (since-hours), fast-lane ledger, daily pack; writes `reports/ALPACA_TIER1_REVIEW_<YYYYMMDD>_<HHMM>/TIER1_REVIEW.md` and `.json`. Tier 2: 7d/30d/last100 comprehensive review (read-only), CSA_BOARD_REVIEW (latest); writes `reports/ALPACA_TIER2_REVIEW_<YYYYMMDD>_<HHMM>/TIER2_REVIEW.md` and `.json`. Both merge-update `state/alpaca_board_review_state.json` (tier1_last_run_ts, tier1_last_packet_dir, tier2_last_run_ts, tier2_last_packet_dir); existing Tier 3 keys preserved.
@@ -1193,10 +1212,10 @@ Ensure `~/.ssh/config` has a `Host alpaca` block that resolves to `104.236.102.5
 - SSH key must be authorized on droplet (user fixed key mismatch on 2026-01-12)
 
 ### STOCK-BOT ISOLATION
-- **Repository identity:** stock-bot (equities only). Do NOT reference trading-bot paths, IPs, or repos.
+- **Repository identity:** stock-bot (equities only). Do not conflate with other bots’ IPs or repos.
 - **Droplet binding:** `droplet_config.json` is the single source for host/key; DropletClient MUST use it.
 - **Forbidden IP:** `147.182.255.165` — never use for stock-bot. That IP is for a different bot.
-- **Canonical droplet:** Prefer SSH alias **alpaca** (use_ssh_config true); else `104.236.102.57`. Project dir `/root/stock-bot` or `/root/trading-bot-current` per deployment.
+- **Canonical droplet (live verify 2026-03-28):** Prefer SSH alias **alpaca** (use_ssh_config true); else **`104.236.102.57`**. **Active clone:** **`/root/stock-bot`** only on that host. Alternate path names (`/root/stock-bot-current`, `/root/trading-bot-current`) appear in **diagnostic scripts** for portability — they were **absent** on the verified Alpaca droplet; see **§ Alpaca droplet — live operational canon** under Alpaca quantified governance.
 
 ---
 
@@ -1229,16 +1248,16 @@ The `.env` file contains:
 ## 6.5 SYSTEMD SERVICE MANAGEMENT
 
 ### Service Details
-**NOTE (2026-01-12):** Systemd service `trading-bot.service` may not exist. Dashboard can be started manually.
+**NOTE (2026-03-28 live verify):** On the Alpaca droplet, **`trading-bot.service` is not installed** (`not-found`). Use **`stock-bot.service`**.
 
-**If systemd service exists:**
-- **SERVICE_NAME:** `trading-bot.service` or `stock-bot.service`
-- **Service file location:** `/etc/systemd/system/trading-bot.service` or `/etc/systemd/system/stock-bot.service`
+**stock-bot.service (live configuration):**
+- **SERVICE_NAME:** `stock-bot.service`
+- **Service file location:** `/etc/systemd/system/stock-bot.service` (+ drop-ins under `stock-bot.service.d/`)
 - **Service configuration:**
   - **WorkingDirectory:** `/root/stock-bot`
   - **EnvironmentFile:** `/root/stock-bot/.env`
-  - **ExecStart:** `/root/stock-bot/venv/bin/python /root/stock-bot/deploy_supervisor.py`
-  - **Restart:** `always` (with 5 second delay)
+  - **ExecStart:** **`/root/stock-bot/systemd_start.sh`** (sources venv, runs **`venv/bin/python deploy_supervisor.py`**)
+  - **Restart:** `always` (`RestartSec=10` observed)
   - **User:** `root`
   - **Start on boot:** `enabled`
 
@@ -1272,11 +1291,9 @@ journalctl -u stock-bot -b          # Since boot
 ```
 
 ### Service Architecture
-- **Entry Point:** `deploy_supervisor.py` (NOT modified during systemd migration)
-- **Supervisor manages:**
-  - `dashboard.py` (port 5000)
-  - `uw_flow_daemon.py` (UW API ingestion)
-  - `main.py` (core trading engine)
+- **Entry Point:** `deploy_supervisor.py` (started from `systemd_start.sh` under `stock-bot.service`)
+- **Supervisor typically manages child processes:** `dashboard.py`, `uw_flow_daemon.py` (UW API ingestion), `main.py` (core trading engine).
+- **Live droplet nuance (2026-03-28):** **`uw-flow-daemon.service`** also runs a dedicated venv `uw_flow_daemon.py`. **`stock-bot-dashboard.service`** runs **`dashboard.py`** with **system** Python and **owns TCP :5000**; the supervisor may still spawn a **second** `dashboard.py` under venv — see **Alpaca droplet — live operational canon** before assuming one dashboard process or one UW daemon instance.
 
 ### Migration Notes
 The bot was migrated from manual supervisor execution to systemd management:
@@ -1304,8 +1321,8 @@ If service won't start:
 Ensure the Alpaca dashboard remains a truthful trust surface and cannot silently regress after deploys or resets.
 
 ### Canonical service
-- **systemd unit:** stock-bot-dashboard.service
-- **Runtime:** Flask on :5000
+- **systemd unit:** `stock-bot-dashboard.service`
+- **Runtime:** Flask on **:5000**; **`ExecStart=/usr/bin/python3 /root/stock-bot/dashboard.py`** with `EnvironmentFile=-/root/stock-bot/.env` and `PORT=5000` (live verify 2026-03-28). **`ss -tlnp`** showed **only** this process bound to `:5000`; `deploy_supervisor.py` may still spawn an additional venv `dashboard.py` child — see **Alpaca droplet — live operational canon**.
 - **Authoritative source:** origin/main (no SCP hotfixes permitted)
 
 ### Canonical endpoints
@@ -1352,12 +1369,13 @@ Ensure the Alpaca dashboard remains a truthful trust surface and cannot silently
 
 ---
 
-## 6.6 DASHBOARD DEPLOYMENT (VERIFIED 2026-01-12, UPDATED 2026-02-17)
+## 6.6 DASHBOARD DEPLOYMENT (VERIFIED 2026-01-12, UPDATED 2026-03-28)
 
 ### Dashboard URL and How It Runs
 - **Live URL:** http://104.236.102.57:5000/
-- **Service:** `stock-bot.service` (systemd) runs **one** process: `deploy_supervisor.py`.
-- **deploy_supervisor.py** starts **child processes**: `dashboard.py` (port 5000), `uw_flow_daemon.py`, `main.py` (trading engine). The dashboard is **not** a separate systemd unit; it is a subprocess of the supervisor.
+- **Primary service for :5000 (live verify 2026-03-28):** **`stock-bot-dashboard.service`** — **`/usr/bin/python3 /root/stock-bot/dashboard.py`**, `PORT=5000`. **`ss -tlnp`** showed this PID as the listener.
+- **Supervisor stack:** `stock-bot.service` → **`systemd_start.sh`** → **`deploy_supervisor.py`** → child processes including **`venv` `dashboard.py`**, **`main.py`**, and often **`uw_flow_daemon.py`** (while **`uw-flow-daemon.service`** may also run UW ingestion separately — see **Alpaca droplet — live operational canon**).
+- **Stale-PID warning still applies:** Any **extra** `dashboard.py` not under the intended unit can hold or confuse port binding; **`pkill -f 'dashboard\.py'`** before restarts remains the safe deploy hygiene when changing dashboard code.
 - **CRITICAL — Stale dashboard PIDs:** When you run `sudo systemctl restart stock-bot`, systemd kills only the **supervisor** process. The supervisor’s **child** (e.g. `dashboard.py`) may **survive as an orphan** and keep holding port 5000. A **new** supervisor then starts a **new** dashboard, which may bind to another port (e.g. 5001). Users hitting :5000 then see **old code** (e.g. no Strategy column, no Wheel open positions). So **every deploy must kill all dashboard processes** before or when restarting, so the **new** supervisor’s dashboard is the only one and binds 5000.
 
 ### Deploy Steps (Use This Every Time)

`
