# Alpaca certification run — LIVE forward poll (droplet)

**TS:** `20260327_0200Z`

## Command

```bash
python scripts/audit/alpaca_forward_poll_droplet.py \
  --max-wait-seconds 360 \
  --poll-interval-seconds 60 \
  --json-out reports/ALPACA_FORWARD_POLL_20260327_0200Z.json
```

(Shorter wait than default 21600 for captured evidence; script default remains 21600.)

## Result

**status:** `timeout` — forward cohort remained **vacuous** relative to `/tmp/alpaca_deploy_ts_utc.txt` (`deploy_epoch` ≈ 1774544849): `forward_economic_closes=0` across all iterations.

## Machine JSON

`reports/audit/ALPACA_CERT_RUN_LIVE_20260327_0200Z.json` (iteration bundles included).

## Note

Live-forward certification is **LIVE_FORWARD_PENDING**; **replay path** carried the non-vacuous strict cohort for this mission.
