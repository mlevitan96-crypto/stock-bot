# SRE Review — Alpaca Runtime Health (Loss Forensics)

**Snapshot:** Droplet run aligned with `ALPACA_LOSS_FORENSICS_PROCESS_INVENTORY.md` (same session as forensics).

## Services (systemd)

| Service | Expected |
|---------|----------|
| `stock-bot.service` | Running (trading bot) |
| `stock-bot-dashboard.service` | Running (Flask :5000) |
| `uw-flow-daemon.service` | Running |
| `cron.service` | Running (telemetry, fast-lane, EOD, direction readiness, etc.) |

## Processes observed

- `deploy_supervisor.py` + `main.py` + `dashboard.py` + `heartbeat_keeper.py` + `uw_flow_daemon.py` — consistent with MEMORY_BANK entry points.
- Bot `main.py` active CPU consistent with live session.

## Git / version drift

- **HEAD (at run):** `76b55130aadaee9eb7ca4972bf2d9d52394a872c` — verify against expected deploy SHA.

## Log retention & telemetry

| File | Lines (approx at run) | Notes |
|------|----------------------|--------|
| `logs/exit_attribution.jsonl` | ~2006 | Canonical closed-trade stream; protected from rotation per MB |
| `logs/attribution.jsonl` | ~2015 | Entry-side; **sparse vs last-2000 exit window** → join gap |
| `alpaca_unified_events.jsonl` | absent/empty | **Gap:** no unified entry stream on disk |
| `alpaca_entry_attribution.jsonl` | absent/empty | **Gap** |
| `state/blocked_trades.jsonl` | ~2058 | Present for gating forensics |

## Disk / memory

- Root FS ~32% used (~49G/154G); headroom OK for append-only logs.
- No OOM signal in this snapshot.

## Cron (telemetry / governance)

- Hourly git sync; daily telemetry extract; exit join + blocked attribution; fast-lane 15m; direction readiness 5m; SRE anomaly 10m; rolling PnL; cockpit; Telegram governance; EOD confirmation.

## Verdict (runtime)

**Services stable; disk OK.** Forensic **data-plane gap**: unified + entry_attr missing; attribution volume insufficient for full entry-exit join on 2000-trade window. Not a “bot down” incident — **telemetry completeness** issue for entry-path causality.

See **`SRE_REVIEW_ALPACA_LOSS_FORENSICS.md`** for Truth Gate integrity verdict.
