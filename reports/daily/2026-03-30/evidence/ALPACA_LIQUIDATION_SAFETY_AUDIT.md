# ALPACA LIQUIDATION SAFETY AUDIT

## Governance (alpaca-safe-liquidation-skill)

- **stock-bot must be stopped before `--execute`:** operational requirement; dry-run does not send orders.
- Script implements: `cancel_all_orders`, SDK `close_position` with `TypeError` fallback, poll until flat, second wave, evidence MD under `reports/daily/<ET>/evidence/`, exit code **3** if not flat after execute.

## Script path exists

- `/root/stock-bot/scripts/repair/alpaca_controlled_liquidation.py` → **PASS**

## Dry-run (no orders)

```
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=$150,000
{
  "evidence_md": "/root/stock-bot/reports/daily/2026-03-30/evidence/ALPACA_FULL_LIQUIDATION_20260330_203008Z.md",
  "positions_before": 33,
  "executed": false,
  "positions_after": null,
  "flat": false
}

```

- exit code: `0`

- JSON summary (parsed): `evidence_md` = `/root/stock-bot/reports/daily/2026-03-30/evidence/ALPACA_FULL_LIQUIDATION_20260330_203008Z.md`

## Contract checklist

| Check | Verdict |
| --- | --- |
| Script exists | PASS |
| Dry-run exit 0 | PASS |
| stdout JSON includes evidence_md | PASS |
| execute path uses cancel_all_orders + close_position + poll | PASS (verified in repo source) |
| exit code 3 if not flat after execute | PASS (see script `return 3`) |
