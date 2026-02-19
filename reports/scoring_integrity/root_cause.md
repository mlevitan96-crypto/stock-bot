# Root Cause Decision

## Chosen root cause: **F) Expectancy gate using wrong score**

## Evidence

1. **Min-score gate** (main.py ~8315–8354) uses variable `score`, which is the **adjusted** score after apply_signal_quality_to_score, apply_uw_to_score, apply_survivorship_to_score, and (for composite clusters) structural_intelligence (regime_mult * macro_mult). So `score` can be higher than the raw cluster composite.

2. **Expectancy gate** (main.py ~8190–8196) previously used `composite_exec_score = float(c.get("composite_score", score))`. For clusters that have `c["composite_score"]` set, this is the **raw** cluster score. So a candidate could have raw composite 2.4 and adjusted score 2.8: min gate sees 2.8 >= 2.5 → pass; expectancy sees composite_exec_score 2.4 → score_floor_breach True → block.

3. Gate counts showed both `score_below_min` and `expectancy_blocked:score_floor_breach` dominating; lowering MIN_EXEC_SCORE to 2.5 did not admit trades because the expectancy gate was still evaluating the raw score and blocking on score_floor_breach.

## Fix applied

- **Single change:** Use the same score for the expectancy gate as for the min gate. Set `composite_exec_score = float(score)` so that score_floor_breach and expectancy both see the adjusted score. Fallback to `c.get("composite_score", 0.0)` only on TypeError/ValueError when converting score.

## Not chosen

- **B/C/D/E:** No evidence of signal/provider/feature/cache or composite construction bug; scores and clusters were present.
- **G:** Expectancy floor was derived correctly from Config.MIN_EXEC_SCORE; the wrong input (raw vs adjusted score) was the issue.
- **H:** No scaling mismatch; same scale, different value used.
- **I:** Diagnostic/live divergence is a consequence of using raw composite in one path and adjusted in another; fixing F addresses consistency.
