# Axis 4 — Gate Alignment

## Grep (composite_exec_score, score_floor_breach)
```
371:    MIN_EXEC_SCORE = float(get_env("MIN_EXEC_SCORE", "3.0"))  # V3.0: Increased to 3.0 for predatory entry filter
7594:                if float(score) >= float(Config.MIN_EXEC_SCORE):
8192:                composite_exec_score = float(c.get("composite_score", score))
8194:                composite_exec_score = float(score)
8195:            expectancy_floor = float(getattr(Config, "MIN_EXEC_SCORE", 3.0))
8196:            score_floor_breach = (composite_exec_score < expectancy_floor)
8199:                composite_score=composite_exec_score,
8214:                composite_score=composite_exec_score,
8219:                score_floor_breach=score_floor_breach,
8224:                print(f"EXPECTANCY_DEBUG {symbol}: composite_score={composite_exec_score:.4f}, score_used_by_expectancy={composite_exec_score:.4f}, expectancy_floor={expectancy_floor}, decision={'pass' if should_trade else 'fail'} ({gate_reason})", flush=True)
8293:            min_score = Config.MIN_EXEC_SCORE
11117:            alerts_this_cycle.append("composite_score_floor_breach")
11119:            fix_result = auto_heal_on_alert("composite_score_floor_breach")

```

## Result
**PASS**