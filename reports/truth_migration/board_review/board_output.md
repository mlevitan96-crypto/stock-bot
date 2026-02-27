# Board — Promotion gates and SAFE_TO_APPLY checklist

**Persona:** Board. **Intent:** Promotion gates, acceptance criteria, and SAFE_TO_APPLY checklist.

## Promotion gates (all must pass)
- **G1:** Droplet baseline captured; path map complete.
- **G2:** CTR streams written and fresh during runtime (PASS in dashboard truth audit when contract points to CTR).
- **G3:** EOD enforces CTR freshness + heartbeat; fails correctly when stale.
- **G4:** No regressions in trading execution (fills evidence still present in logs/orders.jsonl and attribution).
- **G5:** Mirror parity check: CTR vs legacy counts match within tolerance.
- **G6:** Rollback validated: disable TRUTH_ROUTER_ENABLED and restart — system returns to legacy-only.

## Acceptance criteria (summary)
- Phase 1: CTR introduced; mirror mode only; legacy write unchanged; no reader change.
- Phase 2: Dashboard and EOD can read from CTR; contract updated; EOD fails loud if CTR missing/stale.
- Phase 3: Deprecation; mirror off after gates pass; startup fails if CTR not writable when router enabled.

## SAFE_TO_APPLY checklist (pre-deploy)
- [ ] TRUTH_ROUTER_ENABLED default is 0 in code and docs.
- [ ] Legacy write paths unchanged; every migrated writer still writes legacy first.
- [ ] Rollback steps documented and tested (G6).
- [ ] EOD and dashboard contract documented; Phase 1 contract still points to legacy.
- [ ] No silent inference: audit/EOD fail with clear message when CTR required but missing/stale.

## Sign-off
- Prosecutor: Edge cases documented; mitigations in place.
- Defender: Rollback and legacy integrity ensured.
- SRE: Heartbeat, freshness, EOD, systemd paths and permissions specified.
- Quant: No data loss; schemas and joins valid.
- Board: Gates and SAFE_TO_APPLY defined.
