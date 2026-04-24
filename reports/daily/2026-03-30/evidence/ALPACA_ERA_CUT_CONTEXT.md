# ALPACA ERA CUT — CONTEXT SNAPSHOT

- UTC: `2026-03-30T20:43:25Z`
- ET date: `2026-03-30`

## Alpaca clock

- market_open: `False` (closed expected)

## Broker positions

- count: **33**
- symbols: `AAPL, AMD, BAC, C, COIN, COP, CVX, F, GM, GOOGL, HOOD, INTC, JPM, MRNA, MS, MSFT, NIO, NVDA, PFE, PLTR, RIVN, SLB, SOFI, TGT, TSLA, UNH, WFC, WMT, XLE, XLF, XLI, XLP, XOM`

## Git HEAD

`3e902a9339d0749340495152a10fd8f461e48e30`

## date -u

`2026-03-30T20:43:26Z`

## systemctl status stock-bot (excerpt)

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Mon 2026-03-30 18:32:35 UTC; 2h 10min ago
   Main PID: 1756284 (systemd_start.s)
      Tasks: 35 (limit: 9483)
     Memory: 768.2M (peak: 827.2M)
        CPU: 1h 11min 18.385s
     CGroup: /system.slice/stock-bot.service
             ├─1756284 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1756285 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1756316 /root/stock-bot/venv/bin/python -u main.py
             ├─1756339 /root/stock-bot/venv/bin/python heartbeat_keeper.py
             └─1757855 /root/stock-bot/venv/bin/python -u dashboard.py

Mar 30 20:43:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] WARNING EXITS: XLP could not be verified as closed after 3 attempts - keeping in tracking for retry
Mar 30 20:43:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] DEBUG EXITS: Closing XLF (decision_px=48.35, entry=48.23, hold=66.8min)
Mar 30 20:43:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] ERROR EXITS: Failed to close XLF (attempt 1/3): close_position_api_once returned None
Mar 30 20:43:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] ERROR EXITS: Failed to close XLF (attempt 2/3): close_position_api_once returned None
Mar 30 20:43:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] ERROR EXITS: Failed to close XLF (attempt 3/3): close_position_api_once returned None
Mar 30 20:43:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] ERROR EXITS: All 3 attempts to close XLF failed
Mar 30 20:43:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] WARNING EXITS: XLF could not be verified as closed after 3 attempts - keeping in tracking for retry
Mar 30 20:43:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Mar 30 20:43:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 30 20:43:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()

```
