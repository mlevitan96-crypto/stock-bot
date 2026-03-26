# Alpaca Loss Forensics — Process Inventory (SRE)

**Droplet run:** `20260318_192535` UTC

## systemd (running)
```
  UNIT                        LOAD   ACTIVE SUB     DESCRIPTION
  cron.service                loaded active running Regular background program processing daemon
  dbus.service                loaded active running D-Bus System Message Bus
  do-agent.service            loaded active running The DigitalOcean Monitoring Agent
  droplet-agent.service       loaded active running The DigitalOcean Droplet Agent
  getty@tty1.service          loaded active running Getty on tty1
  ModemManager.service        loaded active running Modem Manager
  multipathd.service          loaded active running Device-Mapper Multipath Device Controller
  polkit.service              loaded active running Authorization Manager
  rsyslog.service             loaded active running System Logging Service
  serial-getty@ttyS0.service  loaded active running Serial Getty on ttyS0
  ssh.service                 loaded active running OpenBSD Secure Shell server
  stock-bot-dashboard.service loaded active running STOCK-BOT Dashboard (Flask :5000)
  stock-bot.service           loaded active running Algorithmic Trading Bot
  systemd-journald.service    loaded active running Journal Service
  systemd-logind.service      loaded active running User Login Management
  systemd-networkd.service    loaded active running Network Configuration
  systemd-resolved.service    loaded active running Network Name Resolution
  systemd-timesyncd.service   loaded active running Network Time Synchronization
  systemd-udevd.service       loaded active running Rule-based Manager for Device Events and Files
  udisks2.service             loaded active running Disk Manager
  unattended-upgrades.service loaded active running Unattended Upgrades Shutdown
  user@0.service              loaded active running User Manager for UID 0
  uw-flow-daemon.service      loaded active running Unusual Whales Flow Daemon (single instance)

Legend: LOAD   → Reflects whether the unit definition was properly loaded.
        ACTIVE → The high-level unit activation state, i.e. generalization of SUB.
        SUB    → The low-level unit activation state, values depend on unit type.

23 loaded units listed.

```

## cron
```
0 * * * * cd ~/stock-bot && ./report_status_to_git.sh >> /tmp/git_sync.log 2>&1
30 20 * * 1-5 cd /root/stock-bot && venv/bin/python specialist_tier_monitoring_orchestrator.py >> logs/orchestrator.log 2>&1
30 20 * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py >> logs/telemetry_extract.log 2>&1
31 21 * * 1-5 cd /root/stock-bot && /usr/bin/python3 scripts/run_exit_join_and_blocked_attribution_on_droplet.py --date $(date -u +\%Y-\%m-\%d) >> logs/learning_pipeline.log 2>&1
32 21 * * 1-5 cd /root/stock-bot && bash scripts/droplet_sync_to_github.sh >> /root/stock-bot/logs/cron_sync.log 2>&1
20 21 * * 1-5 /usr/bin/python3 /root/stock-bot/board/eod/cron_health_check.py >> /var/log/cron_health.log 2>&1
*/5 9-21 * * 1-5 cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/governance/check_direction_readiness_and_run.py >> logs/direction_readiness_cron.log 2>&1
*/10 * * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/sre/run_sre_anomaly_scan.py --base-dir . >> logs/sre_anomaly_scan.log 2>&1
*/10 * * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/performance/update_rolling_pnl_5d.py >> logs/rolling_pnl_5d.log 2>&1
0 14-21 * * 1-5 cd /root/stock-bot && python3 scripts/update_profitability_cockpit.py >> /root/stock-bot/logs/cockpit_refresh.log 2>&1
30 16 * * 1-5 cd /root/stock-bot && source venv/bin/activate && set -a && . /etc/telegram-governance.env && set +a && DATE=$(date +\%Y-\%m-\%d) ./scripts/notify/run_daily_telegram_update.sh >> reports/notify/telegram_cron.log 2>&1
*/15 * * * * . /root/.alpaca_env && cd /root/stock-bot && python3 scripts/run_fast_lane_shadow_cycle.py >> /root/fast_lane_shadow.log 2>&1
0 */4 * * * . /root/.alpaca_env && cd /root/stock-bot && python3 scripts/run_fast_lane_supervisor.py >> /root/fast_lane_supervisor.log 2>&1
30 21 * * 1-5 cd /root/stock-bot && /usr/bin/python3 /root/stock-bot/board/eod/eod_confirmation.py >> /root/stock-bot/logs/cron_eod.log 2>&1

```

## python processes
```
root         965  0.0  0.2 110012 23020 ?        Ssl  Feb23   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
root      981953  7.8  1.3 118984 111160 ?       Ss   Mar12 675:32 /root/stock-bot/venv/bin/python /root/stock-bot/uw_flow_daemon.py
root     1194620  0.0  2.8 824600 232692 ?       Ssl  06:35   0:34 /usr/bin/python3 /root/stock-bot/dashboard.py
root     1194630  0.2  7.9 1110732 643644 ?      Sl   06:35   2:14 /root/stock-bot/venv/bin/python deploy_supervisor.py
root     1194770  0.0  1.2 405864 102408 ?       Sl   06:35   0:09 /root/stock-bot/venv/bin/python -u dashboard.py
root     1195106 29.8  6.2 1548864 512068 ?      Sl   06:36 229:59 /root/stock-bot/venv/bin/python -u main.py
root     1195125  0.4  1.3 397032 110484 ?       Sl   06:36   3:10 /root/stock-bot/venv/bin/python heartbeat_keeper.py
root     1215612 77.7  0.2  25324 17352 ?        Ss   19:25   0:00 python3 scripts/alpaca_loss_forensics_droplet.py --max-trades 2000 --min-join-pct 80.0

```

## disk
```
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           795M   74M  721M  10% /run
/dev/vda1       154G   49G  106G  32% /
tmpfs           3.9G     0  3.9G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/vda16      881M  117M  703M  15% /boot
/dev/vda15      105M  6.2M   99M   6% /boot/efi
tmpfs           795M   12K  795M   1% /run/user/0

```

## memory
```
               total        used        free      shared  buff/cache   available
Mem:            7941        2518        1193          76        4612        5422
Swap:           2047           1        2046

```

## git HEAD
```
76b55130aadaee9eb7ca4972bf2d9d52394a872c
76b5513 EOD report auto-sync 2026-03-17

```

## log line counts
```
    2006 logs/exit_attribution.jsonl
    2015 logs/attribution.jsonl
    2129 state/blocked_trades.jsonl
    6150 total

```

## log file sizes
```
-rw-r--r-- 1 root root 18158307 Mar 18 19:14 logs/exit_attribution.jsonl

```
