# ALPACA SPI — commit record (`20260328_190000Z`)

## Commit

- **Hash:** `2532c72`
- **Branch:** `main` → `origin/main` (pushed)

## Files in commit

- `MEMORY_BANK.md` — Alpaca SPI subsection (`#### Alpaca Signal Path Intelligence (SPI)`).
- `scripts/audit/alpaca_pnl_massive_final_review.py` — PnL review + SPI artifacts + closeout SPI section.
- `scripts/audit/alpaca_pnl_market_session_unblock_pipeline.py` — docstring note pointing to SPI / MEMORY_BANK.
- `src/analytics/__init__.py`
- `src/analytics/alpaca_signal_path_intelligence.py`
- `tests/test_alpaca_signal_path_intelligence.py`

## Not committed (per scope)

- `reports/daily/2026-03-28/evidence/*` — generated locally for this mission; re-run the review script on the droplet or CI to reproduce.

## Reproduce SPI artifacts

```bash
PYTHONPATH=. python scripts/audit/alpaca_pnl_massive_final_review.py \
  --ts <TS> --output-dir reports/daily/<ET-date>/evidence \
  --cohort-ids <cohort.json> --truth-json <truth.json> \
  --window-start-epoch <w0> --window-end-epoch <w1> \
  --root /root/trading-bot-current
```

Optional: `ALPACA_SPI_FETCH_BARS=true` to allow bar fetch/cache writes via `data/bars_loader.py` (operator opt-in; see MEMORY_BANK.md).
