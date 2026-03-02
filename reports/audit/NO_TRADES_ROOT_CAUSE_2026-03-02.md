# No Trades — Root Cause and Fix (2026-03-02)

## Root cause

1. **Composite scores were all below the entry threshold (2.7).**
   - Diagnostic on droplet (`scripts/run_why_no_trades_on_droplet.py`) showed best symbol PLTR at **0.94**, next SOFI/HOOD/LCID at **0.93**. All others &lt; 0.9.
   - So **0 clusters** every cycle → **0 orders**.

2. **Adaptive weights had crushed every component to the minimum (0.25).**
   - `state/signal_weights.json` on the droplet had `"current": 0.25` for options_flow, dark_pool, insider, etc. (min_weight).
   - Effective weights became base × 0.25 → composite scores collapsed to &lt; 1.0.

## Fixes applied

| Fix | Where | Effect |
|-----|--------|--------|
| **DISABLE_ADAPTIVE_WEIGHTS=1** | `uw_composite_v2.get_adaptive_weights()` returns `None` when env set | Composite uses base WEIGHTS_V3 instead of crushed adaptive weights. |
| **Rename crushed weights file** | `run_live_real_trades_fix_on_droplet.py` + one-off `mv state/signal_weights.json state/signal_weights.json.bak_crushed` on droplet | New optimizer instances get default 1.0 multipliers when file missing. |
| **ENTRY_THRESHOLD_BASE=0.94** | `.env` on droplet; `uw_composite_v2.get_threshold()` reads env | Symbols with score ≥ 0.94 (e.g. PLTR 0.942) can pass the composite gate until base weights are restored. |
| **Diagnostic script** | `scripts/run_why_no_trades_on_droplet.py` | Run on droplet to see per-symbol score, threshold, pass/fail, reason. |

## Droplet .env (ensure present)

- `UW_MISSING_INPUT_MODE=passthrough`
- `INJECT_SIGNAL_TEST=0`
- `DISABLE_ADAPTIVE_WEIGHTS=1`
- `ENTRY_THRESHOLD_BASE=0.94`

`main.py` calls `load_dotenv()` so the process loads `.env` from cwd.

## Verification

- After deploy + restart, wait ~90s then: `tail -1 logs/run.jsonl` → expect `clusters` ≥ 1 and possibly `orders` ≥ 1 when a symbol passes.
- Re-run diagnostic: `python3 scripts/run_why_no_trades_on_droplet.py` → should show some symbols with `pass	True` when threshold is 0.94.

## Optional next steps

- **Re-enable adaptive weights later** with a reset or better learning (so weights don’t collapse to 0.25).
- **Raise threshold back to 2.7** once scores are healthy (after removing or resetting crushed weights and/or using DISABLE_ADAPTIVE_WEIGHTS=0 with a clean state).
