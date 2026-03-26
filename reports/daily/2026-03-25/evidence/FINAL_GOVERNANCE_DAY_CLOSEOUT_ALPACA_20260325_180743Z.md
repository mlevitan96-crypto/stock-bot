# Final governance day closeout — Alpaca (production droplet)

**Bot:** Alpaca (stock trading + operator dashboard on production droplet)  
**Closeout generated (UTC):** 2026-03-25T18:12:00Z  
**Policy:** No application code changes; no trading, execution, scheduler, or learning logic changes.

---

## Phase 0 — Service model (SRE)

| Item | Value |
|------|--------|
| **Dashboard service name** | `stock-bot-dashboard.service` (systemd) |
| **How it is started** | `ExecStart=/usr/bin/python3 /root/stock-bot/dashboard.py` with `WorkingDirectory=/root/stock-bot`, `PORT=5000`, `EnvironmentFile=-/root/stock-bot/.env` (see `deploy/stock-bot-dashboard.service`) |
| **Manual / duplicate process risk** | A second dashboard process was observed **not** bound to port 5000: `/root/stock-bot/venv/bin/python -u dashboard.py` (older PID). The listener on `:5000` was the **systemd-spawned** `/usr/bin/python3 /root/stock-bot/dashboard.py` after restart. |
| **Hot-reload supported** | **No** — production Flask under systemd loads code at process start; route/UI changes require a process restart (no dev auto-reloader in this unit). |

---

## Phase 1 — Dashboard restart (required)

| Item | Value |
|------|--------|
| **What was restarted** | **Only** `stock-bot-dashboard.service` via `systemctl restart stock-bot-dashboard`. |
| **Why** | Pick up the current on-disk `dashboard.py` and journal-defined environment for port 5000; operational activation step after shipping dashboard work (per runbook intent). |
| **Restart timestamp (UTC)** | **2026-03-25T18:07:43Z** |
| **Confirmation** | `systemctl is-active stock-bot-dashboard` → **active**. `ss` showed `LISTEN 0.0.0.0:5000` owned by the **new** systemd `python3` PID. |
| **What was NOT restarted** | **`stock-bot.service`** (trading / `main.py`), **UW flow daemon**, timers, learning jobs, and any other non-dashboard processes — to avoid touching execution or learning paths. |

---

## Phase 2 — Post-restart verification (CSA)

### 1) System Health / data integrity API

- **GET** `http://127.0.0.1:5000/api/dashboard/data_integrity` **with HTTP Basic Auth** (credentials from `/root/stock-bot/.env`).
- **Result:** **HTTP 404** — route **not present** in the deployed `/root/stock-bot/dashboard.py` (confirmed: no `data_integrity` string in that file on the droplet; local repo contains this route but production copy is behind).
- Therefore: **`generated_at_utc` not available**, **strict status cannot be compared to latest proofs via this API**, and the System Health integrity cockpit **cannot** be validated as live on this host until **`dashboard.py` (and any co-requisites) are deployed** to match the shipped design.

Unauthenticated calls correctly return **401** (expected for protected surface).

### 2) UI rationalization

- **Not verified as effective on production** — without the new bundle, the deployed HTML/JS cannot be assumed to include the merged System Health panel or removed tabs at the level described in local rationalization docs. **Browser confirmation still recommended** after deploy.

### 3) Trade tables / closed trades API

- **GET** `/api/stockbot/closed_trades` → **HTTP 200** with auth.
- Sample first row keys on droplet: `assigned`, `called_away`, `close_reason`, `delta_at_entry`, `dte`, `expiry`, `option_type`, `pnl_usd`, `premium`, `strategy_id`, `strike`, `symbol`, `timestamp`, `wheel_phase`.
- **Missing vs target truthful surface:** `strict_alpaca_chain`, `entry_reason_display`, `fees_display`, top-level `alpaca_strict_summary` — **not present** on the live API response inspected during this closeout.
- **Conclusion:** Trade table **truthfulness upgrades** from the rationalization work are **not active** on the production dashboard code path yet.

---

## Phase 3 — Readiness confirmation (CSA)

| Domain | Status | Notes |
|--------|--------|--------|
| **Trading** | **ACTIVE** (service-level) | `stock-bot.service` remained **active** throughout; only the dashboard unit was restarted. |
| **Learning** | **BLOCKED** (relative to the new dashboard strict-learning control surface) | The integrity endpoint and strict-enriched closed-trade payload **are not deployed**, so learning cannot be **armed/verified** through the intended operator API on this host. Separately, on-disk audit markdown (e.g. `reports/audit/LEARNING_VISIBILITY_BLOCKERS.md`) may be stale; do not treat it as current without re-run. |
| **Action before learning can arm (dashboard-mediated)** | Deploy updated `dashboard.py` (and any required helpers) so that `/api/dashboard/data_integrity` returns **200 JSON** with fresh `generated_at_utc` and `alpaca_strict`, and `/api/stockbot/closed_trades` exposes strict completeness badges and fee/entry-exit display fields per design. |

---

## Phase 4 — Summary (mandatory answers)

1. **What was restarted and why**  
   **`stock-bot-dashboard.service` only**, to reload the dashboard process on port 5000 after governance-day activation protocol, without touching trading or learning engines.

2. **What was NOT restarted and why**  
   **Trading (`stock-bot.service`), UW flow daemon, schedulers/timers, learning** — restarting those would change execution or data-pipeline behavior, which was explicitly out of scope.

3. **Dashboard verification results**  
   **Partial:** auth and `/api/stockbot/closed_trades` work; **`/api/dashboard/data_integrity` is 404**; closed trades **lack** strict / fees / entry-display fields on the live API. The dashboard is **not** yet the **truthful** strict-gate control surface on production.

4. **Current trading status**  
   **ACTIVE** (trading service remained running).

5. **Current learning status**  
   **BLOCKED** for dashboard-mediated strict learning visibility until the new dashboard build is deployed.

6. **Exact remaining condition for learning to arm (dashboard path)**  
   **Production `dashboard.py` must include** `/api/dashboard/data_integrity` and the closed-trade enrichments, then **restart only the dashboard** again and re-verify JSON + UI.

7. **No further action required today — or list**  
   **Further action required:** **(1)** Align production tree with the rationalized dashboard (deploy), **(2)** stop or reconcile the **extra** `venv` `dashboard.py` process so only one operational owner of the operator surface is intentional, **(3)** re-run this verification checklist (data_integrity JSON, UI tabs, closed-trade strict badges).

---

*Operational evidence: systemd dashboard restart at 2026-03-25T18:07:43Z; post-restart listener on 5000; HTTP 404 on `/api/dashboard/data_integrity`; closed_trades schema without strict enrichment on live host.*
