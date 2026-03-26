# Alpaca dashboard — permanentize (Phase 3: droplet redeploy proof)

**Timestamp:** `20260326_2015Z`  
**Host:** SSH `alpaca` → `/root/stock-bot`

## Preconditions

- `origin/main` at **`1bab716d51aca0373878612b1f66d20ccb53639f`** (includes `dashboard.py` + verifier; **no** `scp` hotfix required).

## Commands

```bash
cd /root/stock-bot
git fetch origin main
git reset --hard origin/main
# HEAD = 1bab716d51aca0373878612b1f66d20ccb53639f
systemctl restart stock-bot-dashboard.service
set -a && source .env && set +a
python3 -u scripts/dashboard_verify_all_tabs.py \
  --json-out reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260326_2020Z.json
```

## Results

| Check | Result |
|-------|--------|
| `git rev-parse HEAD` after reset | `1bab716d51aca0373878612b1f66d20ccb53639f` |
| `stock-bot-dashboard.service` | **active** after restart |
| Verifier **exit code** | **0** |
| Endpoints OK | **23 / 23** HTTP **200** |

## Artifact

- `reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260326_2020Z.json` (copied from droplet into repo; `all_pass`: true).

## Hard gate

**PASS** — clean `git reset --hard origin/main` preserves `/api/alpaca_operational_activity` and full verifier list.
