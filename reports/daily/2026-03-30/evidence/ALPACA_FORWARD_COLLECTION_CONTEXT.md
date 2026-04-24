# ALPACA FORWARD COLLECTION — Phase 0 context

- ET date (evidence bucket): `2026-03-30`
- `git rev-parse HEAD`: `a87e681bd3f49d1825d8a313649776b94f6ff6bc`
- `date -u`: `Mon Mar 30 21:29:51 UTC 2026`

## Alpaca clock

```json
{
  "is_open": false,
  "next_open": "2026-03-31 09:30:00-04:00",
  "next_close": "2026-03-31 16:00:00-04:00",
  "timestamp": "2026-03-30 17:29:52.524065201-04:00"
}
```

## stock-bot service

- `systemctl is-active stock-bot`: **`inactive`**

```text
○ stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: inactive (dead) since Mon 2026-03-30 20:54:29 UTC; 35min ago
   Duration: 5min 54.748s
    Process: 1762692 ExecStart=/root/stock-bot/systemd_start.sh (code=killed, signal=TERM)
   Main PID: 1762692 (code=killed, signal=TERM)
        CPU: 42.353s

Mar 30 20:54:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1762693]: [SUPERVISOR] [2026-03-30 20:54:26 UTC] Shutdown signal received
Mar 30 20:54:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1762693]: [SUPERVISOR] [2026-03-30 20:54:26 UTC] Terminating dashboard...
```
