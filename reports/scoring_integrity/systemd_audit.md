# Systemd Audit (Droplet)

## Units
```
stock-bot-dashboard-audit.service                                               loaded    inactive dead      STOCK-BOT Dashboard Endpoint Audit (nightly)
  stock-bot-dashboard.service                                                     loaded    inactive dead      STOCK-BOT Dashboard (Flask :5000)
  stock-bot.service                                                               loaded    active   running   Algorithmic Trading Bot
● trading-bot-doctor.service                                                      loaded    failed   failed    Trading Bot Doctor (self-healing)
● trading-bot.service                                                             not-found inactive dead      trading-bot.service
  uw-flow-daemon.service                                                          loaded    inactive dead      Unusual Whales Flow Daemon (single instance)
  stock-bot-dashboard-audit.timer                                                 loaded    active   waiting   STOCK-BOT Dashboard Audit (daily 02:00 UTC)
  trading-bot-doctor.timer                                                        loaded    active   waiting   Run Trading Bot Doctor periodically
```

## trading-bot.service
active: inactive
not-found
```
-- No entries --
```

## stockbot.service
active: inactive
not-found
```
-- No entries --
```

## uw-flow-daemon.service
active: inactive
not-found
```
-- No entries --
```
