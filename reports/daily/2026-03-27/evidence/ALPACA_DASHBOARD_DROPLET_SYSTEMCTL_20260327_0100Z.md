# Alpaca dashboard — systemctl restart + status (Phase 2)

**Timestamp:** `20260327_0100Z`  
**Environment:** Cursor agent workspace; **not** Alpaca droplet.

## Verdict

**NOT EXECUTED — BLOCKED**

## Blocker

`systemctl restart <DASHBOARD_UNIT>` and `systemctl status <DASHBOARD_UNIT> --no-pager` require the unit name from Phase 0 **on the droplet**.

## Operator copy-paste (after Phase 0 names unit, e.g. `trading-dashboard.service`)

```bash
sudo systemctl restart <DASHBOARD_UNIT>
sudo systemctl status <DASHBOARD_UNIT> --no-pager
```

Capture full stdout in the next artifact revision.
