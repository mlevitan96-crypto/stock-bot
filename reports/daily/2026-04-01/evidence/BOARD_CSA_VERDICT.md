# Board — CSA verdict (chain repair)

- **Root cause:** Correctly classified as **emitter gating (Class A)** — strict runlog events were not appended under production flags; historical cohort lacked merged backfill rows.
- **Fix quality:** **Minimal and governance-safe** — additive sinks, no strict semantic bypass, no strategy/threshold edits in the chain commit.
- **Remaining integrity risk:** **Warehouse DATA_READY** still **NO** (blocked-intent bucket coverage). CSA should treat strict **ARMED** as necessary but not sufficient for milestone / 100-trade precheck until warehouse green.
