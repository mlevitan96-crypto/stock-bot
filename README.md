# Stock Bot - Production Deployment Guide

## Overview
The stock-bot is a trading bot that processes Unusual Whales (UW) API signals and executes trades via Alpaca API.

## Service Management

The bot runs as a systemd service: `stockbot.service`

### Start/Stop/Restart Commands
```bash
sudo systemctl start stockbot
sudo systemctl stop stockbot
sudo systemctl restart stockbot
sudo systemctl status stockbot
```

### View Logs
```bash
# Follow logs in real-time
journalctl -u stockbot -f

# View last 100 lines
journalctl -u stockbot -n 100

# View logs since boot
journalctl -u stockbot -b
```

## Credentials

Credentials are stored in: `/root/stock-bot/.env`

The file contains:
- `ALPACA_KEY=...` - Alpaca API key
- `ALPACA_SECRET=...` - Alpaca API secret
- `ALPACA_BASE_URL=...` - Alpaca API base URL (default: https://paper-api.alpaca.markets)
- `UW_API_KEY=...` - Unusual Whales API key

**Important:** The systemd service automatically loads these credentials via `EnvironmentFile=/root/stock-bot/.env`

## Architecture

### Entry Point
- **deploy_supervisor.py** - Main orchestrator that manages all services
  - This is the entrypoint used by systemd
  - No trading logic modifications were made during systemd migration

### Services Managed by Supervisor
1. **dashboard.py** - Web dashboard (port 5000)
2. **uw_flow_daemon.py** - UW API ingestion daemon
3. **main.py** - Core trading engine

### Directory Structure
```
/root/stock-bot/
├── .env                    # Credentials (DO NOT COMMIT)
├── deploy_supervisor.py    # Service orchestrator
├── main.py                 # Trading engine
├── venv/                   # Python virtual environment
├── logs/                   # Application logs
├── state/                  # State files
└── data/                   # Data files
```

## Systemd Service Details

Service file location: `/etc/systemd/system/stockbot.service`

The service:
- Loads environment variables from `/root/stock-bot/.env`
- Activates the virtual environment automatically
- Runs `deploy_supervisor.py` as the entrypoint
- Restarts automatically on failure (5 second delay)
- Starts automatically on boot
- Logs to journalctl

## Troubleshooting

### Service won't start
1. Check if .env file exists: `ls -la /root/stock-bot/.env`
2. Check service status: `sudo systemctl status stockbot`
3. Check logs: `journalctl -u stockbot -n 50`
4. Verify credentials are correct in .env file

### Bot not trading
1. Check if market is open
2. Check logs: `journalctl -u stockbot -f`
3. Verify Alpaca credentials are correct
4. Check UW API key is valid

### Port conflicts
If port 5000 is already in use:
1. Find process: `sudo lsof -i :5000`
2. Stop conflicting service
3. Restart stockbot: `sudo systemctl restart stockbot`

## Self-Healing Features

The bot includes comprehensive self-healing capabilities:

### State Persistence (Risk #6)
- Trading state persisted to `state/trading_state.json`
- Automatic reconciliation with Alpaca on startup
- Self-healing: detects and recovers from corrupted state files
- Prevents unsafe re-entry after restarts

### Aggregated Health (Risk #9)
- Supervisor tracks health of all services
- Overall system health computed and persisted to `state/health.json`
- Dashboard displays aggregated health status
- Prevents "fake green" states where dashboard is up but trading is dead

### API Contract Protection (Risk #11)
- Startup compatibility checks for Alpaca and UW APIs
- Explicit response contracts with schema validation
- Error classification: TRANSIENT vs PERSISTENT
- Automatic retry for transient errors, fail-fast for persistent errors

### Trade Guard (Risk #15)

## Permanent System Events (Global Observability)

STOCK-BOT now emits a **single, append-only, structured event stream** for reliability and auditability:

- **Location**: `logs/system_events.jsonl` (always exists; append-only)
- **Schema**:
  - `timestamp` (UTC ISO)
  - `subsystem` (e.g. `scoring`, `decision`, `gate`, `order`, `exit`, `data`, `uw_cache`, `signals`, `uw_poll`)
  - `event_type` (string)
  - `severity` (`INFO|WARN|ERROR|CRITICAL`)
  - `symbol` (optional)
  - `details` (dict)

### What gets logged

- **All exceptions** inside wrapped subsystems via `@global_failure_wrapper(subsystem)` (includes traceback).
- **First-class operational events**:
  - **Counter-signals**: `signals.counter_signal_detected`
  - **Blocked candidates**: `gate.blocked` (reason + context in `details`)
  - **Missed candidates**: `decision.missed_candidate`
  - **Exit failures**: `exit.close_position_failed`, `exit.close_position_all_attempts_failed`

### How to interpret

- **CRITICAL**: the subsystem hit an exception/failure that may require intervention (or repeated self-heal attempts failed).
- **ERROR**: a retryable failure happened (order/exit attempts, transient subsystem exception).
- **WARN**: degraded/stale data or fallback behavior (cycle skipped, stale bars detected, fallback return).
- **INFO**: expected control-flow events (gates blocked a candidate; counter-signal detected).

### Regression detection

- Watch for increasing rates of:
  - `event_type=exception` with `severity in {ERROR,CRITICAL}`
  - `exit.close_position_all_attempts_failed`
  - `decision.missed_candidate`
  - `data.stale_bars_detected`
- Dashboard panel (optional): `GET /system-events` (filters by subsystem/severity/symbol).
- Mandatory sanity checks before every order
- Validates position size, exposure, price sanity, cooldowns
- All orders must pass trade guard before submission
- Rejections logged for analysis

### Chaos Testing (Risk #12)
- Controlled failure scenarios for testing
- Set `CHAOS_MODE` environment variable to enable
- Modes: `alpaca_down`, `invalid_creds`, `supervisor_crash`, `state_corrupt`

For detailed documentation, see `SELF_HEALING_IMPLEMENTATION.md`.

## Migration Notes

This bot was migrated from manual supervisor execution to systemd management. The migration:
- ✅ Preserved all trading logic
- ✅ Preserved supervisor architecture
- ✅ Added automatic restart on failure
- ✅ Added automatic start on boot
- ✅ Centralized logging via journalctl
- ❌ Did NOT modify trading logic
- ❌ Did NOT modify deploy_supervisor.py logic
- ❌ Did NOT modify .env file contents

## Maintenance

### Update Code
1. Pull latest code: `cd /root/stock-bot && git pull`
2. Restart service: `sudo systemctl restart stockbot`

### Update Credentials
1. Edit .env file: `nano /root/stock-bot/.env`
2. Restart service: `sudo systemctl restart stockbot`

### View Real-time Activity
```bash
# Follow all logs
journalctl -u stockbot -f

# Or check dashboard
curl http://localhost:5000/api/positions
```
