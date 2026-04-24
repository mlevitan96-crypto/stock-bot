# BOARD_CSA — Second-chance displacement (paper)

## Does this resolve OVERRIDE_CONFLICT without weakening protection?

**Partially, audit-only.** The conflict (strong challenger vs policy-denied displacement) is **observed** with a bounded second look; **live** displacement still denies on first pass. Protection is not weakened because **no** auto-admit to live trading is implemented.

## Reversible and bounded?

**Yes.** Env-gated hook + single delayed re-eval + explicit log rows; disable flag removes new scheduling.

## Integrity / governance risk?

**Low** if logs are retained and joins to counterfactuals are documented. **Risk:** operators confuse paper `allowed` with live approval — mitigated by `paper_only` flags and this spec.
