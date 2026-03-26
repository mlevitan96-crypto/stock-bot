# Innovation: Signal Blind Spots

**Date:** 2026-03-08

## Assumptions that could be false
- That UW cache freshness and conviction flow through to composite unchanged.
- That all components use the same regime/weight source (adaptive vs static).
- That score_snapshot coverage is representative of live funnel.

## Structural blind spots
- No A/B on weight sets; tuning is global.
- Exit scoring not audited in this packet (entry-only signal contribution).
- No per-symbol contribution rank (only aggregate).

## Catastrophic silent failure
- Adaptive weights collapsing to 0.25x for many components => all scores below floor.
- UW API key rotation or rate limit => flow/dark_pool always zero.

## Fast experiment
- Run 24h with DISABLE_ADAPTIVE_WEIGHTS=1 and compare score distribution to current.
