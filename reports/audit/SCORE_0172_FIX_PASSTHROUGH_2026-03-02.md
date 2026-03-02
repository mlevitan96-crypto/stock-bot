# Score 0.172 / No Open Positions — Fix (2026-03-02)

## Problem
- `run.jsonl`: `clusters=51`, `orders=0` every cycle.
- `blocked_trades`: all `expectancy_blocked:score_floor_breach` with **score=0.172** (e.g. META, AMZN, BA).
- Composite pass showed 14/15 symbols with score ≥ 2.7, so clusters were built with good composite scores.

## Root cause
In `decide_and_execute`, the score used for the expectancy gate is adjusted by:
1. `apply_signal_quality_to_score`
2. `apply_uw_to_score`
3. `apply_survivorship_to_score`

**`apply_uw_to_score`** loads `board/eod/out/<date>/uw_root_cause.json`. When that file has **per-candidate** (or global) `uw_signal_quality_score` present but **below 0.25** (e.g. 0.172), the code treated it as "low quality" and **rejected** the candidate by returning `-inf` (or in some paths a heavily penalized score). So the composite-approved score (2.7+) was replaced by a killed/low score before the expectancy gate, and every candidate failed the score floor.

Passthrough previously only applied when **no** UW root-cause data existed (`use_quality is None`). On the droplet, UW root-cause data exists with low quality (e.g. 0.172), so passthrough did not apply and the score was rejected/down-scored.

## Fix
**`board/eod/live_entry_adjustments.py`**: When `UW_MISSING_INPUT_MODE=passthrough`, preserve the composite score **whenever** passthrough is set — including when UW data exists but has low quality. So:
- Before: passthrough only when `use_quality is None`.
- After: passthrough whenever `UW_MISSING_INPUT_MODE == "passthrough"` (missing **or** low quality).

Result: composite-approved clusters keep their score (2.7+) into the expectancy gate, so some candidates can pass the score floor and orders can be placed.

## Droplet checklist
1. Set in `.env`: **`UW_MISSING_INPUT_MODE=passthrough`** (so composite score is preserved).
2. Deploy latest code (includes this fix).
3. Restart the live/paper daemon so the new code and env are used.
4. Run trace: `python scripts/run_live_trading_trace_via_droplet.py` and confirm:
   - `UW_MISSING_INPUT_MODE: passthrough`
   - After a cycle or two: `orders` > 0 in `run.jsonl` and no longer all `score_floor_breach` with score=0.172.

## Verification
- After fix, `apply_uw_to_score` returns `(composite_score, details)` when passthrough is set, so the score passed to the expectancy gate is the same as the cluster’s composite score.
- Real trades / open positions should appear once orders > 0 and execution completes (paper or live per TRADING_MODE / PAPER_TRADING).
