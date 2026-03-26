# CSA Review — Alpaca Diagnostic Promotion

---

## Intent compliance

| Requirement | Met |
|-------------|-----|
| **DIAGNOSTIC** (not performance-final) | **Yes** — documented in intent + active.json `meta.diagnostic` |
| **Live paper only** | **Yes** — `meta.mode: paper`; no real-money |
| **Single rule** | **Yes** — `SCORE_DETERIORATION_EMPHASIS` |
| **Tag** | `PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS` |
| **Others SHADOW** | **Yes** — no other overlays activated |

---

## Governance

- **Evaluation window** and **KEEP / MODIFY / REVERT** matrix defined in [ALPACA_DIAGNOSTIC_PROMOTION_EVAL_CRITERIA.md](./ALPACA_DIAGNOSTIC_PROMOTION_EVAL_CRITERIA.md).
- **Data integrity** parallel track: daily scanner + known 2-row quarantine tracked.
- **Next step:** After window, complete [ALPACA_DIAGNOSTIC_PROMOTION_REVIEW.md](./ALPACA_DIAGNOSTIC_PROMOTION_REVIEW.md); **iterate** only with explicit MODIFY decision and version bump.

---

## CSA approval

| Milestone | Status |
|-----------|--------|
| Proceed with diagnostic on paper | **APPROVED** |
| Real-money or profit-final promotion | **NOT APPROVED** (out of scope) |

---

*CSA*
