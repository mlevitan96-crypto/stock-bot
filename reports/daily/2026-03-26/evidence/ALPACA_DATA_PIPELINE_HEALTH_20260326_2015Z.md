# Phase 1 — Alpaca data pipeline health (SRE)

**Artifact:** `ALPACA_DATA_PIPELINE_HEALTH_20260326_2015Z`  
**Status:** **NOT EXECUTED ON DROPLET** — this workspace has no shell access to the Alpaca droplet; journal captures are **absent**.

---

## Required operator actions (hard stop until done)

On the Alpaca droplet, for each unit below, run and paste output into a superseding artifact (same filename with new `<TS>`):

```bash
# Discover Alpaca / stock-bot related units
systemctl list-units --type=service --all '*stock*' '*alpaca*' '*bot*' 2>/dev/null

# Example pattern (adjust to actual unit names on host):
for u in stock-bot-dashboard uw-flow-daemon alpaca-postclose-deepdive stock-bot stock-bot-trading; do
  systemctl is-active "$u" 2>/dev/null || true
  journalctl -u "$u" -n 500 --no-pager 2>/dev/null | tail -n 5
done
```

---

## Units referenced in this repository (may not match droplet names)

| Role | File in repo | Notes |
|------|----------------|-------|
| Dashboard | `deploy/stock-bot-dashboard.service` | `python3 .../dashboard.py` |
| Dashboard audit | `deploy/stock-bot-dashboard-audit.service` | Read-only audit timer |
| UW flow | `deploy/systemd/uw-flow-daemon.service` | Not Alpaca execution |
| Post-close | `deploy/systemd/alpaca-postclose-deepdive.service` | Scheduled deepdive |

**Gap:** No `alpaca-trading-loop.service` or `alpaca-execution-sidecar.service` is committed here; **telemetry writers** and **integrity refresh** may be timers/cron — **must be enumerated on droplet**.

---

## Verdict (Phase 1)

**INCOMPLETE.** Without active-state + last-500-lines journals, **no claim** of service health is allowed. Certification **cannot** proceed to GO on Phase 1 alone.
