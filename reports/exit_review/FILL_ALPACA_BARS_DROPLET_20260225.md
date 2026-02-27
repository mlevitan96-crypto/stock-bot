# Fill Alpaca Bars — Droplet Run (live)

**When:** 2026-02-25 (run via `scripts/run_fill_alpaca_bars_on_droplet.py`)

## Result

| Step | Result |
|------|--------|
| Exits (last 30d from `logs/exit_attribution.jsonl`) | 98 |
| Symbol-dates missing bars | 98 |
| Fetched from Alpaca and written to `data/bars` | **98/98** |
| Exit code | 0 |

## Notes

- **Existing bars unchanged;** only missing (symbol, date) were requested from Alpaca.
- Fetcher saw 401 on `data.sandbox.alpaca.markets` then succeeded on `data.alpaca.markets` (production keys on droplet).
- Run dir on droplet: `reports/exit_review/fill_bars_20260225T003910Z/` (normalized_exit_truth.json, missing_bars.json).

## Commands used on droplet

```bash
cd /root/stock-bot && source .env
python3 scripts/fill_alpaca_bars_30d.py --days 30 --max_days_per_symbol 20
```
