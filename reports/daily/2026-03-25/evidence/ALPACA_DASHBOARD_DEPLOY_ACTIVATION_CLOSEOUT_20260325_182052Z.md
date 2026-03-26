# Alpaca dashboard deploy & activation — closeout

**Scope:** Alpaca production droplet only. **Changed artifact:** `/root/stock-bot/dashboard.py` (sync + permissions). **Not changed:** trading (`stock-bot.service`), execution logic, learning pipelines, telemetry collectors, or `main.py`.

**Generated (UTC):** 2026-03-25T18:21:30Z

---

## 1) Dashboard code deployed (commit hash)

| Item | Value |
|------|--------|
| **Git commit deployed** | `4a6d31f81ab2553e88ad458fcad95f13f3c6acf5` |
| **Remote path** | `/root/stock-bot/dashboard.py` |
| **Ownership / mode** | `root:root`, `644` (`-rw-r--r--`) |

**Pre-flight (repo) confirmation:** `dashboard.py` includes `GET /api/dashboard/data_integrity`, System Health tab (`data-tab="system_health"`), `loadSystemHealth` calling that API, and closed-trade enrichments (`strict_alpaca_chain`, `entry_reason_display`, `fees_display`, response-level `alpaca_strict_summary`).

---

## 2) Stray processes removed

| Before hygiene | After single `systemctl restart` |
|----------------|----------------------------------|
| Two dashboard PIDs: `/root/stock-bot/venv/bin/python -u dashboard.py` (stray) and `/usr/bin/python3 /root/stock-bot/dashboard.py` (systemd) | **One** PID: `/usr/bin/python3 /root/stock-bot/dashboard.py` |

**Actions taken:** `pkill` patterns targeting venv and `nohup` dashboard invocations, then **one** `systemctl restart stock-bot-dashboard` (no separate stop/start cycle beyond that single restart command).

**Port 5000:** Held by the systemd-spawned `python3` process after restart.

---

## 3) Dashboard restart timestamp (UTC)

| Field | Value |
|-------|--------|
| **Restart** | `systemctl restart stock-bot-dashboard` |
| **Timestamp (UTC)** | **2026-03-25T18:20:52Z** |
| **Post-restart PID (sample)** | `1532036` (`/usr/bin/python3 /root/stock-bot/dashboard.py`) |
| **Listener** | `0.0.0.0:5000` |

---

## 4) Verification results (CSA)

### Data integrity API — `GET /api/dashboard/data_integrity` (HTTP Basic)

| Check | Result |
|-------|--------|
| HTTP status | **200** |
| `generated_at_utc` | Present (e.g. `2026-03-25T18:20:55.762143+00:00` at verify time) |
| `data_sources` | **Present** |
| `alpaca_strict` / learning gate | `LEARNING_STATUS` = **ARMED**, `learning_fail_closed_reason` = **None** |

**Proofs alignment:** No separate `reports/audit/*STRICT*` files were found on the droplet at closeout time for a file-to-file diff. Alignment is taken as **the live strict evaluator inside the dashboard** (same gate used for `alpaca_strict` and closed-trade badges), reporting **ARMED** consistently on both integrity and closed-trades summary.

### Closed trades API — `GET /api/stockbot/closed_trades`

| Check | Result |
|-------|--------|
| HTTP status | **200** |
| Row fields | `strict_alpaca_chain`, `entry_reason_display`, `fees_display` **present** on sample row |
| Top-level summary | `alpaca_strict_summary` **present**; `LEARNING_STATUS` **ARMED** |
| Row count (sample) | 500 |

*Note: `alpaca_strict_summary` is a **response-level** field (not duplicated inside each row), which matches the implementation.*

### UI truth — `GET /` (authenticated)

| Check | Result |
|-------|--------|
| System Health tab | **Present** (`data-tab="system_health"`) |
| XAI as top-level tab | **Absent** (`data-tab="xai"` not present) |
| “Natural Language Auditor” in primary UI | **Absent** (checked within first ~200k chars of HTML) |
| Legacy `telemetry_health-tab` panel id | **Absent** |
| `loadSystemHealth` wired to `/api/dashboard/data_integrity` | **Yes** |

---

## 5) Trading status

**ACTIVE** — `stock-bot.service` remained **active** throughout; only the dashboard unit was restarted.

---

## 6) Learning status

**ARMED** — `LEARNING_STATUS` from `/api/dashboard/data_integrity` and from `alpaca_strict_summary` on `/api/stockbot/closed_trades` both reported **ARMED** with **`learning_fail_closed_reason`: None** at verification time.

---

## 7) Truth surface statement

**The Alpaca dashboard is now the truthful strict control surface** for operator visibility: integrity JSON is served on **`/api/dashboard/data_integrity`**, closed trades expose **strict chain / entry reason / fees** fields and **alpaca strict summary**, and the **System Health** tab is wired to that API without presenting removed legacy health tabs as primary surfaces.

---

*Operational scripts used (local repo): `scripts/alpaca_dashboard_deploy_activate.py`, `scripts/_alpaca_dashboard_verify_remote.py` (uploaded temporarily to `/tmp` on the droplet for verification, then removed).*
