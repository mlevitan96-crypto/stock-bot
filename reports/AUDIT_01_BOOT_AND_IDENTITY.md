# Audit §1: Boot and Identity

**Generated:** 2026-01-27T03:41:27.025785+00:00
**Date:** 2026-01-26

## Result
- **PASS:** True
- **Reason:** OK

## Evidence
- **runtime_identity:** # Phase-2 Runtime Identity

**Generated:** 2026-01-27T03:41:22.776395+00:00

---

## 1. Systemd service(s)

### Unit: `stock-bot.service`

- ExecStart={ path=/root/stock-bot/systemd_start.sh ; argv[]=/root/stock-bot/systemd_start.sh ; ignore_errors=no ; start_time=[Tue 2026-01-27 03:38:15 UTC] ; stop_time=[n/a] ; pid=1848251 ; code=(null) ; status=0/0 }
- WorkingDirectory=/root/stock-bot
- User=root

### Unit: `trading-bot-doctor.service`

- ExecStart={ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /root/stock-bot/doctor.py ; ignore_errors=no ; start_time=[Tue 2026-01-27 03:40:44 UTC] ; stop_time=[Tue 2026-01-27 03:40:44 UTC] ; pid=1848450 ; code=exited ; status=2 }
- WorkingDirectory=/root/stock-bot
- User=root

### Unit: `uw-flow-daemon.service`

- ExecStart={ path=/root/stock-bot/venv/bin/python ; argv[]=/root/stock-bot/venv/bin/python /root/stock-bot/uw_flow_daemon.py ; ignore_errors=no ; start_time=[Sat 2026-01-24 02:45:22 UTC] ; stop_time=[Sun 2026-01-25 16:53:25 UTC] ; pid=1743133 ; code=exited ; status=0 }
- WorkingDirectory=/root/stock-bot
- User=

## 2. Repo and executable

- **CWD (WorkingDirectory):** `/root/stock-bot`
- **Git commit (repo root):** `a5d430bcdafda7fbb390e2beedbc4a74a125229a` (exit 0)
- **Python executable:** `/usr/bin/python3`
- **site-packages (example):** `n/a`

## 3. Stdout/stderr

Services typically use journald (StandardOutput=journal, StandardError=journal) unless overridden.

- **log_sink_count:** 8
- **phase2_heartbeat_count:** 53