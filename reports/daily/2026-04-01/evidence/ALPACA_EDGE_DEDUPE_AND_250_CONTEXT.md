# Phase 0 — Context snapshot (Alpaca droplet)

**Host:** `/root/stock-bot` (evidence captured from `ssh alpaca` commands, UTC **2026-04-01T19:11–19:13Z**).

## Git

```
git rev-parse HEAD
0d9ec04088ec28cb15d2995df1fcba7b5736f3a7
```

(Includes SRE-EDGE-001 dedupe commit.)

## Time

| Field | Value |
|-------|--------|
| UTC (ISO) | `2026-04-01T19:11:24+00:00` (at context capture) |
| ET calendar date | **2026-04-01** (`TZ=America/New_York date +%Y-%m-%d`) |

## stock-bot.service

```
systemctl is-active stock-bot.service
active
```

```
systemctl show stock-bot.service -p ActiveState,SubState,MainPID --no-pager
ActiveState=active
SubState=running
MainPID=1847213
```

## Note on `system_events.jsonl` / startup banner

`grep -c startup_banner /root/stock-bot/logs/system_events.jsonl` → **0** matches on this droplet at capture time. No `telemetry_chain` lines found in tail/grep of that file. **Strict runlog proof for this snapshot is not present in current `system_events.jsonl`** (see Phase 3 / SRE packet for implication).
