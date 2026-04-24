# SRE verdict — Alpaca Signal Path Intelligence (`20260328_190000Z`)

**Authority:** `MEMORY_BANK.md` (SPI constraints; bar IO via `data/bars_loader.py`).

## Data integrity

| Check | Result |
|-------|--------|
| Inputs read-only: `exit_attribution.jsonl` rows + optional `data/bars/` cache | **PASS** |
| No writes to canonical logs, orders, or broker APIs in default configuration | **PASS** |
| SPI build wrapped in non-throwing path in `alpaca_pnl_massive_final_review.py` | **PASS** |

## Runtime / performance

| Check | Result |
|-------|--------|
| Default `fetch_if_missing=False` — avoids network and cache writes during review | **PASS** |
| Per-trade bar load is O(hold window); scales with cohort size (offline batch job) | **PASS** |
| Optional fetch env `ALPACA_SPI_FETCH_BARS` — operator-controlled; may increase runtime and disk use | **Noted** |

## Non-blocking behavior

SPI failures or import errors produce a degraded JSON payload; **PnL review exit code and primary CSA verdict are unchanged** by SPI alone.

## Verdict token

**`SRE_SPI_OK`**
