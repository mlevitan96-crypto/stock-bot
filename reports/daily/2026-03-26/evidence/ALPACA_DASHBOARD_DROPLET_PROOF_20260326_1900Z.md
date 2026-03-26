# Alpaca dashboard droplet deploy and proof

**Artifact ID:** `ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1900Z`  
**Status:** **NOT EXECUTED** from this workspace (no SSH / remote shell to the Alpaca droplet).

---

## Required operator steps (Alpaca droplet)

1. `cd /root/stock-bot` (or deployed repo root)
2. `git pull` (no SCP)
3. Restart **only** the dashboard service (per your unit name, e.g. `systemctl restart <dashboard>.service`)
4. Export auth and run:
   ```bash
   set -a && source .env && set +a
   python3 scripts/dashboard_verify_all_tabs.py
   python3 scripts/alpaca_dashboard_truth_probe.py --json reports/ALPACA_DASHBOARD_DATA_SANITY_<DROPLET_TS>.json
   ```
5. In browser (logged in): confirm every tab opens; Telemetry shows **STALE** banner if computeds missing; no blank banner/situation strip.

---

## Machine-readable stub

See [`reports/ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1900Z.json`](../ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1900Z.json).

---

## Adversarial note

Until this file is replaced with real command output + timestamps, **any claim of production restoration is invalid**.
