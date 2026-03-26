# Alpaca Tier 3 Board Review

**Generated:** 2026-03-16T021929Z
**Base dir:** C:\Dev\stock-bot

## 1. Cover — inputs loaded

- **comprehensive_review:** yes
- **shadow_comparison:** yes
- **weekly_ledger:** no
- **csa_verdict_latest:** yes
- **sre_status:** yes

Input mtimes (UTC):
- last_review: 2026-03-13T22:17:00.764150+00:00
- shadow_comparison: 2026-03-05T00:09:11.319371+00:00
- weekly_ledger: N/A
- csa_verdict_latest: 2026-03-13T22:28:27.535206+00:00
- sre_status: 2026-03-05T21:07:05.168028+00:00

---

## 2. Tier 3 summary

- **Scope:** last387
- **Window:** 2026-03-04 to 2026-03-05
- **Total PnL (attribution):** -97.76
- **Total PnL (exit attribution):** -97.87
- **Win rate:** 0.2002
- **Total exits:** 387
- **Blocked total:** 2287
- **Shadow nomination:** Advance to live paper test
- **CSA verdict:** HOLD
- **CSA confidence:** LOW

---

## 3. Executed trades and attribution

- Total PnL (attribution): -97.76
- Total exits: 387
- Canonical logs: ['logs/exit_attribution.jsonl', 'logs/attribution.jsonl']

---

## 4. Blocked trades and counter-intelligence

- **Blocked total:** 2287
  - `displacement_blocked`: 2014
  - `max_positions_reached`: 238
  - `expectancy_blocked:score_floor_breach`: 22
  - `order_validation_failed`: 13
  - Opportunity cost: displacement_blocked (count=2014, est_cost=-509.35)
  - Opportunity cost: max_positions_reached (count=238, est_cost=-60.19)
  - Opportunity cost: expectancy_blocked:score_floor_breach (count=22, est_cost=-5.56)
  - Opportunity cost: order_validation_failed (count=13, est_cost=-3.29)

---

## 5. Shadow comparison

- **Nomination:** Advance to live paper test
- **Ranked by expected improvement:** ['B2_shadow', 'B1_shadow', 'A3_shadow', 'A2_shadow', 'A1_shadow', 'C2_shadow']
- Risk: A1_shadow: Displacement relaxation increases exposure.
- Risk: A2_shadow: Max positions increase concentration risk.
- Risk: A3_shadow: Lower score floor may admit worse entries.
- Risk: B1_shadow: Min hold extension may increase drawdown in fast reversals.
- Risk: B2_shadow: Removing early signal_decay may hold losers longer.

---

## 6. Learning and replay readiness

- Exits in scope: 387
- Telemetry-backed: 387 (100.0%)
- Ready for replay: True
- Replay gate met (≥100 exits with ≥90% telemetry in scope). Run direction replay when ready.
- Review blocked trades: top reason 'displacement_blocked' (2014 blocks). Consider counter-intel report for missed opportunities.
- PnL negative in scope; use board personas for top 5 recommendations (entry/exit/gates).
- Board task: each persona 3 ideas → agree top 5 with owner, metric, success criteria.

---

## 7. SRE and automation

- **SRE overall status:** OK
- **Governance anomalies detected:** False
- **SRE events path:** reports/audit/SRE_EVENTS.jsonl (tail count: 0)

---

## 8. Appendices (optional paths)

- reports/POSTMARKET_*.md
- reports/SHADOW_TRADING_CONFIRMATION_*.md

*End of Alpaca Tier 3 Board Review.*