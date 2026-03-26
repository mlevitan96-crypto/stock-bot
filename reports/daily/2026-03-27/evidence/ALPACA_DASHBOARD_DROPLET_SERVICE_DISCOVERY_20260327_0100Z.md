# Alpaca dashboard — droplet service discovery (Phase 0)

**Timestamp:** `20260327_0100Z`  
**Environment:** Cursor agent workspace (Windows); **not** Alpaca droplet.

## Verdict

**NOT EXECUTED — BLOCKED**

## Blocker (deterministic)

| Item | Evidence |
|------|----------|
| SSH / shell on `/root/stock-bot` | No droplet hostname, no SSH key, and no `ProxyJump` / `Host` entry in this workspace. Agent cannot run `systemctl` on the remote host. |
| Required commands | `systemctl list-units --type=service \| egrep -i "dash\|dashboard\|stock-bot"` and `systemctl list-unit-files \| egrep -i "dash\|dashboard\|stock-bot"` were **not** run here. |

## Operator copy-paste (run on droplet)

```bash
systemctl list-units --type=service | egrep -i "dash|dashboard|stock-bot" || true
systemctl list-unit-files | egrep -i "dash|dashboard|stock-bot" || true
```

Record the **exact** unit name(s) chosen for restart (do not guess from docs alone).

## Non-goals

No telemetry contract or trading logic changes.
