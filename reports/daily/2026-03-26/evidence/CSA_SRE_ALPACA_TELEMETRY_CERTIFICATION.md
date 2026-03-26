# CSA + SRE Joint Certification — Alpaca Telemetry

**Date:** 2026-03-18

## CSA (completeness / causality)

| Criterion | Verdict |
|-----------|---------|
| Entry stream exists for every new fill | **NOT CERTIFIED** until droplet runs repaired code + forward proof PASS |
| Exit stream complete | **OK** — `exit_attribution.jsonl` populated on droplet |
| Join entry→exit for causal claims | **NOT_DATA_READY** pre-proof |

**CSA verdict:** **NOT_DATA_READY** — analysis that depends on entry-level contributions + unified stream is **forbidden** until Phase 4 passes.

## SRE (integrity / ops)

| Criterion | Verdict |
|-----------|---------|
| Append-only protected logs | **OK** per policy; inventory shows growing exit/attribution logs |
| Emitter failures visible | **IMPROVED** — `emit_entry_attribution_failed` event on failure |
| Schema stability | **OK** — 1.2.0 emitter, 1.0.0 exit row schema |
| Single-writer discipline | **OK** — append-only JSONL |

**SRE verdict:** **NOT_DATA_READY** for unified/entry pipeline until files exist and forward proof green.

---

## Combined certification

**STATUS: NOT_DATA_READY**

**Unblocks to DATA_READY when:**

1. Repair deployed to droplet.  
2. `alpaca_entry_attribution.jsonl` + `alpaca_unified_events.jsonl` **OK** on inventory.  
3. `alpaca_telemetry_forward_proof.py` exits **0** with ≥50 trades.

**No spin:** Until then, **no reassurance** — only proof artifacts above.
