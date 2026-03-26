# SRE Review — Alpaca Diagnostic Promotion

---

## Telemetry & plumbing

| Item | Status |
|------|--------|
| `config/tuning/active.json` deployed | **Yes** (droplet) |
| `compute_exit_score_v2` reads **`get_merged_exit_weights`** | **Yes** — `exit_score_v2.py` updated |
| **Restart** `stock-bot` after code deploy | **Done** — unit **active** |
| Daily scan | `scripts/audit/alpaca_data_readiness_droplet_scan.py` documented in completeness log |

---

## Data completeness

- **Baseline scan (2026-03-20):** 2 `exit_attribution` rows with missing critical fields — **track**; not introduced by this promotion.
- **Append-only** logs unchanged in policy.

---

## Risk

- **Paper only** — no capital exposure.
- **Code path:** Tuning loader read each overlay load; invalid JSON in `active.json` fails open to defaults in loader (empty overlay) — **monitor** after edits.

---

## SRE sign-off

**ACCEPT** — diagnostic promotion deployed with restart; completeness **process** in [ALPACA_DAILY_DATA_COMPLETENESS_LOG.md](./ALPACA_DAILY_DATA_COMPLETENESS_LOG.md).

---

*SRE*
