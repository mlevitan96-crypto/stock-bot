# BOARD_CSA — Paper caps

## Still paper-only?

Yes: evaluation uses **counterfactual JSON + local bars** only; cap module has **zero** broker imports; `verify_paper_caps_wired` and Phase 0 attest paper service configuration sample.

## Fail-closed?

`PAPER_CAP_FAIL_CLOSED=1` default; invalid ts → block when caps on.

## Counterfactual vs realized?

Metrics remain **Variant A / emulator proxy**, not Alpaca fills — do not treat as realized PnL.
