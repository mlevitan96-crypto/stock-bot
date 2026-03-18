# SRE review — Kraken retention (Phase 3)

## Kraken-specific telemetry files

**N/A.** No Kraken live `*.jsonl` attribution streams on droplet → **nothing to protect** under Kraken name.

## Host running stock-bot (same machine)

| Item | Finding |
|------|---------|
| `deploy_supervisor.py` | Droplet copy contains **`RETENTION_PROTECTED_BASENAMES`** (grep count **3** lines referencing pattern — supervisor loaded) |
| Protected truncation | Alpaca-critical logs (e.g. `exit_attribution.jsonl`) protected **for stock-bot** per recent main; **not** a Kraken claim |

## Log rotation / append-only

- **Kraken live:** no files → **unverifiable**.
- **Risk if Kraken deployed later:** apply same basename protection pattern as Alpaca telemetry; never truncate venue-attributed exit logs in `startup_cleanup`.

## SRE verdict (Kraken scope)

- **Retention rules for Kraken:** **NOT APPLICABLE** — system not present.  
- **Host hygiene:** disk/inode comfortable.  
- **Gap:** Deploying Kraken without dedicated retention entries would be **HIGH RISK** — require pre-deploy contract + protection list.

**Signed (embedded SRE):** Block Kraken DATA_READY until live streams exist and retention is explicitly proven.
