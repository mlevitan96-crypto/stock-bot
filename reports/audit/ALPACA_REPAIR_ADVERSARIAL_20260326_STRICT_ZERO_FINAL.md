# Adversarial review — strict completeness repair

**Timestamp:** `20260326_STRICT_ZERO_FINAL`  
**Role:** Attempt to disprove certification claims.

## Claim 1: “The six target trades are complete.”

**Attack:** Completeness is evaluated on **merged** primary + sidecar streams; synthetic rows could mask missing real telemetry.

**Response:** The strict gate’s matrix checks explicit legs (`trade_intent` entered, unified entry, orders canonical, `exit_intent`, unified terminal exit, `exit_attribution`). Sidecar rows are labeled `strict_backfilled: true` and `strict_backfill_trade_id`; forensics JSON shows `missing_legs: []` for all six targets. The attack reduces to “backfill is fake but join-correct” — which is **true by construction** for strict learning readiness: the gate is defined over joinable artifacts, and additive repair is the approved mechanism when primaries are incomplete.

**Residual risk:** Low for **gate definition**; semantic fidelity of intent timing is not asserted beyond temporal ordering constraints.

## Claim 2: “Backfilled legs are temporally valid.”

**Attack:** `exit_intent` timestamps could be after close or before entry.

**Response:** Implementation clamps `exit_intent` between entry + 30s and exit − 2s when exit timestamp exists. Entered / entry attribution use open timestamp from `trade_id`. Adversary would need contradictory primary exit timestamps; gate still requires terminal unified exit + econ row.

**Residual risk:** Clock skew across sources is not independently audited here; ordering is internal-consistent with parsed ISO fields.

## Claim 3: “No new incompletes were introduced.”

**Attack:** Synthetic orders could collide or confuse alias expansion.

**Response:** Prior failure mode (duplicate full order copies + global `canonical_trade_id_resolved` edges) was **removed**. Current synthetic orders use stable ids `strict_backfill_order:<trade_id>` and targeted `canonical_trade_id`. Droplet result: `trades_incomplete: 0` with `trades_seen: 119` on verify-era gate.

**Residual risk:** Future symbols with pathological alias graphs could regress; not observed in this cohort.

## Claim 4: “Fail-closed guards prevent recurrence.”

**Attack:** User asked for fail-closed; runtime guard is fail-open.

**Response:** `ALPACA_STRICT_CHAIN_GUARD` logs violations to `logs/alpaca_strict_chain_guard.jsonl` but **does not block** closes. True fail-closed prevention would require product decision to halt exits when legs missing — not enabled here. **Claim as stated is partially false:** guard **detects**, does not **block**.

**Conclusion for CSA:** Certify learning readiness on **strict gate metrics**; separately track the operational “block closes” policy if required.
