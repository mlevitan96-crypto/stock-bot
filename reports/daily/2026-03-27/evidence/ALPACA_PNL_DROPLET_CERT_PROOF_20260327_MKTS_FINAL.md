# Droplet cert proof (20260327_MKTS_FINAL)

## Command (authoritative on Alpaca host)

```bash
python scripts/audit/alpaca_forward_truth_contract_runner.py --root /root/stock-bot --window-start-epoch 1774531800.0 --window-end-epoch 1774555200.0 --json-out reports/ALPACA_MARKET_SESSION_TRUTH_20260327_MKTS_FINAL.json --md-out reports/audit/ALPACA_MARKET_SESSION_TRUTH_20260327_MKTS_FINAL.md --incident-md reports/audit/_incident_ms.md --incident-json reports/audit/_incident_ms.json
```

## Workspace demo

- Fixture root: `C:\Dev\stock-bot\artifacts\alpaca_pnl_session_et_20260326`
- Truth JSON: `reports\ALPACA_MARKET_SESSION_TRUTH_20260327_MKTS_FINAL.json`
- `complete_trade_ids` count: **2**
