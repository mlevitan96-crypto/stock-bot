# ALPACA ERA CUT — LIQUIDATION EVIDENCE

- Engine stopped: **yes** (`systemctl stop stock-bot`)
- `systemctl is-active` after stop: `inactive`

## Controlled liquidation stdout (tail)

```
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=$150,000
{
  "evidence_md": "/root/stock-bot/reports/daily/2026-03-30/evidence/ALPACA_FULL_LIQUIDATION_20260330_204330Z.md",
  "positions_before": 33,
  "executed": true,
  "positions_after": 33,
  "flat": false
}

```

## Parsed JSON summary

```json
{
  "evidence_md": "/root/stock-bot/reports/daily/2026-03-30/evidence/ALPACA_FULL_LIQUIDATION_20260330_204330Z.md",
  "positions_before": 33,
  "executed": true,
  "positions_after": 33,
  "flat": false
}
```

- **flat:** `False` positions_after=`33`
- **Liquidation evidence_md:** `/root/stock-bot/reports/daily/2026-03-30/evidence/ALPACA_FULL_LIQUIDATION_20260330_204330Z.md`
