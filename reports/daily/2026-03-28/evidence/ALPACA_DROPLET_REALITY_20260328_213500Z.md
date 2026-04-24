# Alpaca droplet — live reality (`20260328_213500Z`)

**Method:** Read-only SSH from operator workstation using `Host alpaca` (BatchMode). **No restarts, no config edits, no mutations.**

**Authority note:** This file is evidence from live inspection. Canonical policy text remains **`MEMORY_BANK.md`** after Phase 3 merge.

---

## 1. Identity & SSH

| Field | Value |
|--------|--------|
| **hostname** | `ubuntu-s-1vcpu-2gb-nyc3-01-alpaca` |
| **IPv4** | `104.236.102.57` (matches repo `droplet_config.json` / MEMORY_BANK stock-bot target) |
| **SSH user** | `root` |
| **Preferred access** | SSH config **`Host alpaca`** + repo **`droplet_config.json`** (`use_ssh_config: true`, `project_dir: /root/stock-bot`, Windows `key_file` optional) |
| **Scripted client** | `droplet_client.py` (Paramiko) |

---

## 2. Repo roots & Python

| Path | Status (2026-03-28) |
|------|---------------------|
| `/root/stock-bot` | **Exists** — primary clone, `git` activity current |
| `/root/stock-bot-current` | **Not present** |
| `/root/trading-bot-current` | **Not present** |
| **venv** | `/root/stock-bot/venv/bin/python` → **Python 3.12.3** |

---

## 3. Environment & Telegram

| File | Purpose |
|------|---------|
| `/root/.alpaca_env` | Root `600`; sourced by **cron** jobs (e.g. trade milestones) |
| `/root/stock-bot/.env` | **`EnvironmentFile`** for `stock-bot`, `stock-bot-dashboard`, `uw-flow-daemon` (API keys, dashboard auth, etc.) |

---

## 4. systemd — active / listening

### Active `running`

- **`stock-bot.service`** — `WorkingDirectory=/root/stock-bot`, `EnvironmentFile=/root/stock-bot/.env`, **`ExecStart=/root/stock-bot/systemd_start.sh`** (bash: `cd`, `venv/bin/activate`, `venv/bin/python deploy_supervisor.py`).  
  **Drop-ins:** `EXPECTANCY_GATE_TRUTH_LOG=1`, `SIGNAL_SCORE_BREAKDOWN_LOG=1`, `MIN_EXEC_SCORE=2.7`, `TRUTH_ROUTER_ENABLED=1`, `TRUTH_ROUTER_MIRROR_LEGACY=1`, `STOCKBOT_TRUTH_ROOT=/var/lib/stock-bot/truth`.
- **`stock-bot-dashboard.service`** — `ExecStart=/usr/bin/python3 /root/stock-bot/dashboard.py`, `PORT=5000`, `EnvironmentFile=-/root/stock-bot/.env`.
- **`uw-flow-daemon.service`** — `ExecStart=/root/stock-bot/venv/bin/python /root/stock-bot/uw_flow_daemon.py`.

### Port 5000

- **`ss -tlnp`:** `0.0.0.0:5000` bound by **`python3` PID** matching **dashboard** process started as **`/usr/bin/python3 .../dashboard.py`** (systemd dashboard unit).

### Processes (sample)

- Separate **`uw_flow_daemon.py`** under venv (PID distinct from supervisor children).
- **`deploy_supervisor.py`** under venv with children including **`venv/bin/python -u dashboard.py`** and **`main.py`**.
- **Two dashboard-related PIDs** observed; only **system python** instance held `:5000` at check time.

### Unit not installed

- **`trading-bot.service`** → **not-found** (inactive dead).

### Loaded but **failed** (observed)

- `alpaca-forward-truth-contract.service` — timer fires; journal shows **exit 2 / INCIDENT** on recent runs.
- `alpaca-postclose-deepdive.service`
- `stock-bot-dashboard-audit.service`
- `trading-bot-doctor.service`

*(No remedial action taken per mission constraints.)*

---

## 5. Timers (observed)

- `alpaca-forward-truth-contract.timer`
- `alpaca-postclose-deepdive.timer`
- `stock-bot-dashboard-audit.timer`

---

## 6. Cron (root)

Full `crontab -l` at inspection:

- `*/10 13-21 * * 1-5 cd /root/stock-bot && source /root/.alpaca_env && PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py >> logs/notify_milestones.log 2>&1`

**Note:** Fast-lane 15m / 4h schedules described in MEMORY_BANK were **not** present in this root crontab at inspection (may be absent, different user, or managed elsewhere).

---

## 7. Repo `deploy/systemd/` (reference templates on disk)

Present under `/root/stock-bot/deploy/systemd/`: `alpaca-forward-truth-contract.*`, `alpaca-postclose-deepdive.*`, `telegram-failure-detector.*`, `uw-flow-daemon.service`, etc.

---

## 8. Governance / Alpaca state on disk

Examples under `/root/stock-bot/state/`: `alpaca_board_review_state.json`, `alpaca_convergence_state.json`, `alpaca_heartbeat_state.json`, `alpaca_promotion_gate_state.json`, `fast_lane_experiment/` (ledger, cycles, config).

---

## 9. Bot entry points (operational)

- **Live trading / supervisor:** `systemd_start.sh` → `deploy_supervisor.py` → `main.py`, child processes per supervisor config.
- **Dashboard (public :5000):** **`stock-bot-dashboard.service`**.
- **UW ingestion:** **`uw-flow-daemon.service`** (plus any supervisor-managed overlap to be aware of).
- **Offline review / PnL / SPI:** Python scripts under `scripts/audit/` (e.g. `alpaca_pnl_massive_final_review.py`, `alpaca_forward_truth_contract_runner.py`) with `--root /root/stock-bot`.

---

## 10. Logging & evidence

- **Runtime logs:** `/root/stock-bot/logs/` (e.g. `exit_attribution.jsonl`, milestone log).
- **Daily evidence (repo):** `reports/daily/<ET-date>/evidence/` relative to clone (push/pull per workflow).

**End.**
