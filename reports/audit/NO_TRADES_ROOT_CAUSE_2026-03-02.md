# No Trades — Root Cause and Fix (2026-03-02)

## Root cause (scoring)

1. **Enrichment passed conviction=0 when the key was missing.**  
   In `uw_enrichment_v2.py`, `enriched_symbol["conviction"] = data.get("conviction", 0.0)` meant that when the UW cache had no `conviction` key, we sent **0.0** to the composite. The composite only uses the neutral default **0.5** when `conv_raw is None`. Because enrichment always sent a number (0.0), the composite’s default never ran, so **flow_conv = 0** and the primary flow component (weight 2.4) was **0** instead of ~1.2. That collapsed scores for every symbol with missing conviction.

2. **Adaptive weights had crushed every component to 0.25.**  
   `state/signal_weights.json` had `"current": 0.25` for options_flow, dark_pool, etc., so effective weights were base × 0.25 and further reduced scores.

## Fixes applied (no workarounds)

| Fix | Where | Effect |
|-----|--------|--------|
| **Conviction default 0.5 when missing** | `uw_enrichment_v2.py`: `data.get("conviction", 0.5)` | Enrichment now passes 0.5 when the cache has no conviction, so the primary flow term contributes and scores return to normal (2.5+). |
| **DISABLE_ADAPTIVE_WEIGHTS=1** | `uw_composite_v2.get_adaptive_weights()` returns `None` when env set | Composite uses base WEIGHTS_V3 instead of crushed adaptive weights. |
| **Rename crushed weights file** | Deploy script / one-off `mv state/signal_weights.json state/signal_weights.json.bak_crushed` | New optimizer instances use default 1.0 multipliers when file is missing. |
| **Diagnostic script** | `scripts/run_why_no_trades_on_droplet.py` | Run on droplet to see per-symbol score, threshold, pass/fail, reason. |

Entry threshold remains **2.7**; no lowered threshold.

## Droplet .env (ensure present)

- `UW_MISSING_INPUT_MODE=passthrough`
- `INJECT_SIGNAL_TEST=0`
- `DISABLE_ADAPTIVE_WEIGHTS=1`

`main.py` loads `.env` from repo root (`Path(__file__).resolve().parent / ".env"`).

## Verification

- After deploy + restart, wait ~90s then: `tail -1 logs/run.jsonl` → expect `clusters` ≥ 1 when symbols have score ≥ 2.7.
- Re-run diagnostic: `python3 scripts/run_why_no_trades_on_droplet.py` → scores should be in normal range (e.g. 2–4) and some symbols should show `pass	True`.
