# Alpaca dashboard — deploy (origin/main + hotfix)

**Timestamp:** 20260326_1815Z  
**Path:** `/root/stock-bot`

## Git (remote tracking)

```bash
cd /root/stock-bot
git fetch origin main
git reset --hard origin/main
git rev-parse HEAD
```

**`origin/main` after reset:** `1c2c94648d60bda9df61e296948dd2aef923bf3f`

## Hotfix (required for verifier gate)

`origin/main` at the above commit did **not** register `GET /api/alpaca_operational_activity` (verifier returned **404**). To pass the **23/23** hard gate, these files were copied from the Cursor workspace with `scp` **after** the reset:

- `dashboard.py` — adds `/api/alpaca_operational_activity` and UI truth wiring
- `scripts/dashboard_verify_all_tabs.py` — `--json-out` and full 23-endpoint list

**Running process** (`GET /api/version`) reports `git_commit`: `ecc4216d420917d50f96b194c3650f33d6b65a72` (dirty tree vs `1c2c9464…` until `dashboard.py` / verifier are committed and pushed to `main`).

## Follow-up

Commit and push `dashboard.py` + `scripts/dashboard_verify_all_tabs.py` (+ `scripts/droplet_dashboard_screenshots.js` if desired) to `main` so a future `git reset --hard origin/main` does not drop the route.
