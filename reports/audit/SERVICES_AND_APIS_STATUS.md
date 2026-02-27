# Phase 1 — Services, Endpoints, and APIs Status

**Audit date:** 2026-02-27  
**Scope:** Core services on droplet, API/broker integration (Alpaca).  
**Note:** Live droplet checks require SSH/DropletClient; this report combines codebase verification and instructions for droplet evidence.

---

## 1. Core Services (Codebase & Contract)

| Service | Location | What it runs | Healthy criteria |
|---------|----------|--------------|-------------------|
| **stock-bot.service** | `/etc/systemd/system/stock-bot.service` (droplet); refs in scripts, MEMORY_BANK | Starts `systemd_start.sh` → deploy_supervisor → main, dashboard, heartbeat | active; logs updating; no recurring errors |
| **uw-flow-daemon.service** | `deploy/systemd/uw-flow-daemon.service` (repo template) | `uw_flow_daemon.py` in repo root; single instance | active if UW flow needed; lock file `state/uw_flow_daemon.lock` |
| **Governance loop** | Not a systemd unit | `scripts/run_equity_governance_loop_on_droplet.sh` (manual/tmux/cron) | When run: writes `state/equity_governance_loop_state.json` and latest `reports/equity_governance/equity_governance_*/lock_or_revert_decision.json` |

**Verified from code:**
- `scripts/governance/system_state_check_droplet.py` expects `stock-bot.service` active and checks Environment.
- `MEMORY_BANK.md` states service name `stock-bot.service`, deploy_supervisor orchestrates.
- `uw-flow-daemon.service` uses `EnvironmentFile=-/root/stock-bot/.env`; WorkingDirectory `/root/stock-bot`.

**DROPLET_REQUIRED (run on droplet):**
```bash
systemctl is-active stock-bot.service
systemctl is-active uw-flow-daemon.service
systemctl show stock-bot.service -p Environment --no-pager | tr ' ' '\n' | grep -E '^[A-Z_]=' | sed 's/=.*/=***/'
journalctl -u stock-bot.service --since "1 hour ago" --no-pager | tail -100
```
Capture: status output, masked env, last 100 log lines (no secrets).

---

## 2. What’s Running vs Orphans

**From prior reports (DROPLET_PROCESS_INVENTORY):**
- Two `main.py` (one from stock-bot.service, one from tmux) = redundant; tmux one should be stopped.
- `uw_flow_daemon.py` sometimes running without uw-flow-daemon.service (manually started).
- `cache_enrichment_service.py` may run outside stock-bot.service.

**Recommendation:** On droplet run `python scripts/list_droplet_processes.py` (or equivalent) and optionally `scripts/kill_droplet_duplicates.py --dry-run` to list orphans. Do not kill during audit unless needed for health.

---

## 3. Alpaca / Broker Integration

**Verified from code (main.py, dashboard):**
- Credentials: `ALPACA_KEY`, `ALPACA_SECRET`, `ALPACA_BASE_URL` from env (Config); paper-only enforcement via base URL check.
- Account/positions: `get_account()`, positions via Alpaca REST; dashboard `/api/positions` uses Alpaca + `state/position_metadata.json`, `data/uw_flow_cache.json`, `data/live_orders.jsonl`.
- PnL reconcile: `/api/pnl/reconcile` uses Alpaca API, `state/daily_start_equity.json`, `logs/attribution.jsonl`.

**API keys loaded (without printing secrets):**
- Confirmed: keys loaded from env (EnvironmentFile or systemd drop-in). No code path prints raw secrets in normal operation.
- **DROPLET_REQUIRED:** `systemctl show stock-bot.service -p Environment` and confirm ALPACA_* vars exist (values redacted).

**Cross-check with Alpaca dashboard:**
- Open positions: compare `/api/positions` (or Alpaca API) with Alpaca dashboard.
- Recent fills: `logs/orders.jsonl`, `logs/trading.jsonl` vs Alpaca activity.
- Cash balance: `get_account()` equity/cash vs dashboard.
- PnL for week: `state/daily_start_equity.json` + attribution vs Alpaca.

**Discrepancies to document:** Count of positions, last fill time, cash balance delta, any order_id in logs not in Alpaca.

---

## 4. Failures and Fixes

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| Droplet status not verified in this run | Info | Run Phase 1 commands on droplet and paste results into this doc or a linked file. |
| Orphan main.py / uw_flow_daemon (from prior docs) | Yellow | Standardize: run UW daemon via `uw-flow-daemon.service` only; kill tmux main if present. |
| Root disk 100% (from past incident) | Red if recurring | Monitor disk; ensure log rotation and cleanup of old reports. |

---

## 5. Summary

- **Codebase:** Service names, Alpaca env vars, and usage in main/dashboard are consistent. No code bugs found in loading API keys or calling Alpaca.
- **Running state:** Not verified (no droplet SSH in this run). Use checklist in WEEKLY_FULL_SYSTEM_AUDIT.md and capture evidence on droplet.
- **Recommended fixes:** (1) Run droplet verification commands above. (2) Remove duplicate processes per runbook. (3) Confirm Alpaca paper base URL and key scope (paper vs live).
