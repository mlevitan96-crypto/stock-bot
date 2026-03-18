# Alpaca Telemetry Deploy — Memory Bank Load (Phase 0)

| Field | Value |
|-------|--------|
| **MEMORY_BANK.md SHA256** | `605E72546DA23BE424898C0B8BDB43AC6571064795D281E8D9C929A598F2E271` |
| **mtime UTC** | 2026-03-18T15:32:23Z |

## Target service & paths

| Item | Expected |
|------|----------|
| **systemd** | `stock-bot.service` (MEMORY_BANK: deploy_supervisor / main trading engine) |
| **Droplet repo** | `/root/trading-bot-current` **if present**, else `/root/stock-bot` (per droplet_config / MB history) |
| **Deploy** | `git fetch --all && git reset --hard origin/main` then `systemctl restart stock-bot` |

## Repo contract files (verified in workspace)

| File | Role |
|------|------|
| `reports/audit/ALPACA_TELEMETRY_CONTRACT.md` | Required telemetry contract |
| `scripts/write_alpaca_telemetry_repair_epoch.py` | Cutover epoch writer |
| `scripts/alpaca_telemetry_forward_proof.py` | 100% join proof + journalctl emit-fail check |

**Governing rule:** No decision-grade analysis until forward proof **PASS** (MEMORY_BANK Truth Gate).
