# Gate Input Audit

## Design (post-fix)

- **Min-score gate:** Uses `score` (adjusted: signal_quality, UW, survivorship, regime/macro). Threshold: Config.MIN_EXEC_SCORE (2.5) or 1.5 in bootstrap; self-healing can raise.
- **Expectancy gate:** Uses same `score` as composite_exec_score (so aligned with min gate). expectancy_floor = Config.MIN_EXEC_SCORE; score_floor_breach = (composite_exec_score < expectancy_floor). ExpectancyGate.calculate_expectancy(composite_score=composite_exec_score, ...); should_enter(..., score_floor_breach=...).

## Verification for 20 recent candidates

To generate from droplet:

1. Tail state/score_snapshot.jsonl (or logs/score_snapshot.jsonl) for last 20 records; or
2. Parse logs/gate.jsonl for last cycle_summary and preceding gate events with symbol, composite_score, block_reason.

Each record should show:

- composite_score (now = adjusted score used by both gates)
- expectancy_floor (= MIN_EXEC_SCORE)
- block_reason (expectancy_blocked:score_floor_breach | score_below_min | expectancy_passed | etc.)

## Contract

- Expectancy gate uses the **same** composite score as the min-score gate (the adjusted `score`).
- Expectancy floor is derived from Config.MIN_EXEC_SCORE (getattr(Config, "MIN_EXEC_SCORE", 3.0)).
- If candidate passes min gate (score >= min_score), then score_floor_breach is false (for non-bootstrap, min_score >= MIN_EXEC_SCORE), so expectancy gate does not block on floor alone.
