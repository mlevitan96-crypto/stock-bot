# ALPACA — Context snapshot (Phase 0)

**Evidence TS:** `20260327_224500Z`  
**ET date bucket:** `2026-03-27` (from droplet `TZ=America/New_York date +%Y-%m-%d`)

## Commands (droplet)

```text
TZ=America/New_York date +%Y-%m-%d && hostname && date -u && uptime -p
```

**Output:**

```text
2026-03-27
ubuntu-s-1vcpu-2gb-nyc3-01-alpaca
Fri Mar 27 22:36:20 UTC 2026
up 4 weeks, 4 days, 5 hours, 36 minutes
```

## Git (droplet `/root/stock-bot`)

```text
git rev-parse HEAD
git status --porcelain | head -200
```

**Output (abbrev):**

- **HEAD:** `a885c5c90e3efc01640f9dff5f3aca2383affe71`
- **Porcelain:** dirty tree (many untracked `reports/ALPACA_*`, modified `data/uw_flow_cache.json`, `profiles.json`, `weights.json`, etc.). Full list captured in live SSH session (2026-03-27 mission).

## Disk

```text
df -h . | tail -1
```

**Output:**

```text
/dev/vda1       154G   54G  101G  35% /
```
