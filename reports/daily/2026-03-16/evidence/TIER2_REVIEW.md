# Alpaca Tier 2 Board Review

**Generated:** 2026-03-16T02:31:59.383629+00:00
**Base dir:** C:\Dev\stock-bot

## 1. Cover — inputs loaded

- **7d_review:** yes
- **30d_review:** yes
- **last100_review:** no
- **csa_board_review:** no

---

## 2. Tier 2 summary

### 7d
- Window: 2026-02-26 to 2026-03-04
- Total PnL (attribution): -136.47
- Win rate: 0.2015
- Total exits: 2000
- Blocked total: 2000
- Continue capture: need 387/100 telemetry-backed in last-100 window; run replay when ≥90%.
- Review blocked trades: top reason 'displacement_blocked' (1079 blocks). Consider counter-intel report for missed opportunities.
- PnL negative in scope; use board personas for top 5 recommendations (entry/exit/gates).
- Board task: each persona 3 ideas → agree top 5 with owner, metric, success criteria.

### 30d
- Window: 2026-02-03 to 2026-03-04
- Total PnL (attribution): -136.47
- Win rate: 0.2015
- Total exits: 2000
- Blocked total: 2000
- Continue capture: need 387/100 telemetry-backed in last-100 window; run replay when ≥90%.
- Review blocked trades: top reason 'displacement_blocked' (1079 blocks). Consider counter-intel report for missed opportunities.
- PnL negative in scope; use board personas for top 5 recommendations (entry/exit/gates).
- Board task: each persona 3 ideas → agree top 5 with owner, metric, success criteria.

### last100
- Not found.

---

## 3. Counter-intelligence

- `displacement_blocked`: 1079
- `max_positions_reached`: 672
- `expectancy_blocked:score_floor_breach`: 151
- `order_validation_failed`: 82
- `max_new_positions_per_cycle`: 16
- Opportunity cost: displacement_blocked (count=1079, est_cost=-150.95)
- Opportunity cost: max_positions_reached (count=672, est_cost=-94.01)
- Opportunity cost: expectancy_blocked:score_floor_breach (count=151, est_cost=-21.12)
- Opportunity cost: order_validation_failed (count=82, est_cost=-11.47)
- Opportunity cost: max_new_positions_per_cycle (count=16, est_cost=-2.24)

---

## 4. Rolling promotion (CSA_BOARD_REVIEW)

CSA_BOARD_REVIEW not found.

---

## 5. Appendices (paths)

- reports/board/7d_comprehensive_review.json
- reports/board/30d_comprehensive_review.json
- reports/board/last100_comprehensive_review.json
- reports/board/CSA_BOARD_REVIEW_*.json

*End of Alpaca Tier 2 Board Review.*