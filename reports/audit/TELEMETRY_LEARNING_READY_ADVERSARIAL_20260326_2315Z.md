# Adversarial review — telemetry learning readiness (whole system)

**TS:** `20260326_2315Z`

## Attacker goals

Disprove claims of `incomplete==0`, parity, join propagation, replay honesty, segmentation, and Kraken Telegram readiness.

## Findings

1. **Alpaca `incomplete==0`:** Local baseline shows `trades_seen=0` at `STRICT_EPOCH_START` — vacuous **true negative** (no completes, no incompletes in cohort). **Cannot** claim learning-ready from this workspace snapshot. Prior droplet evidence showed **non-zero** `legacy_trades_incomplete` — forward vacuous did not erase legacy debt.

2. **Parity:** With empty forward cohort, `0==0` parity is **misleading** (documented in forward cert mission). Adversarial **PASS** on calling out vacuity.

3. **Join keys:** Strict gate uses alias expansion; **risk** if `canonical_trade_id_resolved` edges are missing for a fill — would mark incomplete. No evidence in this run that all historical rows are healed.

4. **Replay lab:** Same binary as production evaluator — **no relaxed joins**. **Risk:** choosing `--open-ts-epoch` to force cohort inclusion without CSA label would be cheating; contract forbids.

5. **Segmentation:** Forward vs legacy uses **open time** from `trade_id`; malformed `trade_id` → excluded with reason — good fail-closed behavior; **risk** if schema drifts.

6. **Kraken:** Absent strict gate and suite — any green dashboard for Kraken direction is **not** strict completeness. **Telegram 250/500** unproven.

## Conclusion

Adversarial review **supports STILL_BLOCKED** for both venues at final CSA gates, with Alpaca infrastructure substantially ahead of Kraken but **not** final-certified on this evidence set.
