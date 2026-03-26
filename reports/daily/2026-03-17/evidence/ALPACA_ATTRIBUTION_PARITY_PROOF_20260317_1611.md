# Alpaca Attribution Parity Proof

**Timestamp:** 2026-03-17 16:11 UTC  
**Purpose:** Confirm telemetry is faithful and non-invasive.

---

## A) Entry parity

| Test | Assertion | Result |
|------|-----------|--------|
| `test_entry_contributions_sum_equals_composite_score` | Emitted composite_score equals decision composite_score; contributions sum equals composite_score (within tolerance) | PASS |
| `test_entry_dominant_component_matches_max_abs_contribution` | Dominant component name and value match computed max abs(contribution); entry_margin_to_threshold = composite_score − threshold | PASS |

---

## B) Exit parity

| Test | Assertion | Result |
|------|-----------|--------|
| `test_exit_pressure_equals_sum_contributions_dominant_and_margins` | exit_pressure_total equals sum(exit_contributions); dominant component correct; exit_pressure_margin_exit_now / exit_pressure_margin_exit_soon computed correctly | PASS |

---

## C) Non-invasive hot path

| Test | Assertion | Result |
|------|-----------|--------|
| `test_entry_emitter_does_not_raise_on_invalid_input` | Emitter accepts empty/invalid input; does not raise; logs/skips only | PASS |
| `test_exit_emitter_does_not_raise_on_invalid_input` | Emitter accepts empty/invalid input; does not raise | PASS |

---

## Confirmation

All parity tests in `tests/test_alpaca_attribution_parity.py` pass. Telemetry does not change trading decisions and does not raise into the execution loop.
