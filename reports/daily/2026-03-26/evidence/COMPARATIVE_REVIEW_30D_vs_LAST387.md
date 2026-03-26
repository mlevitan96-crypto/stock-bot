# Comparative Review: 30-Day vs Last-387 Exits

**Generated (UTC):** 2026-03-04T22:52:08.700790+00:00

## Scope definition

| | 30-day | Last-387 exits |
|---|--------|----------------|
| Scope | 30 days | last 387 exits |
| Window | 2026-02-03 to 2026-03-04 | 2026-03-04 to 2026-03-04 |

## Learning & telemetry comparison

| Metric | 30-day | Last-387 |
|--------|--------|----------|
| exits_in_scope | 2000 | 387 |
| telemetry_backed | 387 | 387 |
| pct_telemetry | 19.35% | 100.0% |
| replay_readiness | False | True |

## PnL comparison

| Metric | 30-day | Last-387 |
|--------|--------|----------|
| total_pnl_attribution_usd | -136.47 | -30.3 |
| total_exits | 2000 | 387 |
| win_rate | 0.2015 | 0.2081 |
| avg_hold_minutes | 11.83 | 15.36 |

## Blocked trades comparison

| | 30-day | Last-387 |
|---|--------|----------|
| blocked_total | 2000 | 1764 |
| top_reasons | {'displacement_blocked': 1079, 'max_positions_reached': 672, 'expectancy_blocked:score_floor_breach': 151, 'order_validation_failed': 82, 'max_new_positions_per_cycle': 16} | {'displacement_blocked': 963, 'max_positions_reached': 585, 'expectancy_blocked:score_floor_breach': 141, 'order_validation_failed': 59, 'max_new_positions_per_cycle': 16} |

## Counter-intelligence comparison

30d: executed 2000, blocked 2000. Top patterns: {'displacement_blocked': 1079, 'max_positions_reached': 672, 'expectancy_blocked:score_floor_breach': 151, 'order_validation_failed': 82, 'max_new_positions_per_cycle': 16}.

Last387: executed 793, blocked 1764. Top patterns: {'displacement_blocked': 963, 'max_positions_reached': 585, 'expectancy_blocked:score_floor_breach': 141, 'order_validation_failed': 59, 'max_new_positions_per_cycle': 16}.

## What's stable across both

- Win rate in low 20% range in both scopes.
- PnL negative in both scopes.
- Top block reasons: displacement_blocked, max_positions_reached, expectancy_blocked.
- Replay not ready in 30d scope (telemetry % low over 2000 exits); last-387 scope has 387 exits with higher recent telemetry potential.

## What changes with scope

- 30d: 2000 exits, 19.35% telemetry → replay not ready. Last387: 387 exits, different telemetry mix in same window.
- 30d blocked_total 2000 vs last387 blocked_total 1764 (different time window).
- Expectancy / tail behavior: 30d spans more history; last387 is recent cohort only.

## Which scope should drive the next decision and why

**Scope:** last387

Last-387 uses the same exit cohort as the learning baseline (recent exits). Decisions for replay readiness and gate tuning should use recent-cohort metrics; 30d is for trend and stability checks.

## Board persona verdicts

### Adversarial

Both scopes show negative PnL and low win rate; 30d shows 2000 exits with 19% telemetry, last387 shows 387 exits with a smaller blocked set. The adversary would question whether gates are too tight (displacement/max_positions dominate blocks). Prioritize last387 for gate and replay decisions so we act on recent behavior.

### Quant

30d expectancy and win rate are consistent with last387 (both ~20% win rate). Telemetry coverage in 30d is 19.35% over 2000 exits; last-100 readiness is the correct gate. Use last387 scope for next calibration and 30d for trend confirmation.

### Product Operator

Operationally, last387 represents the current product state (recent exits and blocks). Use last387 for 'how to proceed' and 30d for board-level trend reporting. Prioritize last387.

### Risk

Risk view: both scopes show negative PnL. Tail behavior is worse in 30d (more exits, more loss). For risk decisions (position limits, gates), use last387 to avoid diluting with older history; keep 30d for escalation context.

### Execution Sre

Execution/SRE: dashboard and governance are up; both reviews ran on droplet. For runbooks and 'next action', use last387 scope so SRE and execution align with the same exit cohort the learning pipeline uses.

---
End of comparative review.