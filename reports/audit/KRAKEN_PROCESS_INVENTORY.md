# Kraken process inventory (Phase 3 — SRE)

**Host:** Droplet reached via `DropletClient` (SSH config host **alpaca** / same machine as user **kraken** alias per `DROPLET_ACCESS_STATUS.md`).

## Running services (relevant)

| Unit | State (probe) |
|------|----------------|
| `stock-bot` | **active** (Alpaca/stock-bot stack) |
| `kraken*.service` | **Not observed** in probe slice (no dedicated Kraken trading unit listed in partial output) |

**Note:** Full `systemctl list-units --all` was not pasted in probe; absence of **kraken** in running set is consistent with **no Kraken bot**.

## Cron (observed on host)

All entries pointed at `/root/stock-bot` — telemetry extract, EOD, fast-lane (Alpaca), SRE scan, rolling PnL, etc. **None** reference a separate Kraken app root.

## Kraken-specific processes

**None identified** for live trading. Research: possible manual/cron runs of Kraken download scripts under `stock-bot` (not captured as dedicated service).

## Disk / inode (host-level)

| Resource | Observation |
|----------|-------------|
| `/` usage | ~32% used (~49G / 154G) |
| Inode use | ~2% |

**No disk pressure** for host.
