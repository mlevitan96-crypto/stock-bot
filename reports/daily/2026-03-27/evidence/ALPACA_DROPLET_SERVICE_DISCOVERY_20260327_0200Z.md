# Alpaca droplet service discovery (20260327_0200Z)

## Git sync

`
HEAD is now at 1c2c9464 audit: telemetry learning readiness closure pack (Alpaca+Kraken), baselines, replay lab, poll script
1c2c94648d60bda9df61e296948dd2aef923bf3f
`

## list-units (egrep)

`
● alpaca-postclose-deepdive.service              loaded    failed   failed  Alpaca post-close deep dive (reports + Telegram, read-only)
● stock-bot-dashboard-audit.service              loaded    failed   failed  STOCK-BOT Dashboard Endpoint Audit (nightly)
  stock-bot-dashboard.service                    loaded    active   running STOCK-BOT Dashboard (Flask :5000)
  stock-bot.service                              loaded    active   running Algorithmic Trading Bot
`

## list-unit-files (eggrep)

`
alpaca-postclose-deepdive.service            disabled        enabled
stock-bot-dashboard-audit.service            disabled        enabled
stock-bot-dashboard.service                  enabled         enabled
stock-bot.service                            enabled         enabled
alpaca-postclose-deepdive.timer              enabled         enabled
stock-bot-dashboard-audit.timer              enabled         enabled
`
