# Truth Migration Contract — Canonical Truth Root (CTR)

**Status:** Phase 1 (mirror mode). **Droplet-first; multi-model; reversible.**

## 1. Intent
- Work backwards from what is **already live on the droplet**; freeze working truth.
- Introduce a **Canonical Truth Root (CTR)** with a **Truth Router** as the single authoritative write/read surface.
- Phase 1: routing + mirroring only (CTR write + legacy write). No logic changes. No reader switch until Phase 2.

## 2. Operating rules
- **Droplet-first:** Baseline = what the live bot writes/reads on droplet today.
- **No behavior change first:** Phase 1 = mirror only (CTR + legacy).
- **No silent inference:** If CTR is missing/stale, audits MUST FAIL loudly.
- **Everything reversible:** One flag `TRUTH_ROUTER_ENABLED=0` restores legacy-only.
- **Multi-model sign-off:** Prosecutor, Defender, SRE, Quant, Board (see `reports/truth_migration/board_review/`).

---

## 3. Acceptance criteria

| ID | Criterion |
|----|-----------|
| AC1 | CTR root configurable via `STOCKBOT_TRUTH_ROOT` (default `/var/lib/stock-bot/truth`). |
| AC2 | Truth Router provides `truth_path(rel)`, `append_jsonl(rel, record)`, `write_json(rel, obj)` with atomic JSON and mkdir -p. |
| AC3 | On every write: update `meta/last_write_heartbeat.json` and `health/freshness.json` (per stream). |
| AC4 | When `TRUTH_ROUTER_ENABLED=1` and `TRUTH_ROUTER_MIRROR_LEGACY=1`: write to CTR **and** legacy; readers unchanged. |
| AC5 | When `TRUTH_ROUTER_ENABLED=0`: no CTR write; legacy-only; no exception. |
| AC6 | Dashboard truth contract and EOD can point to CTR paths (Phase 2); EOD fails when CTR heartbeat/stale. |
| AC7 | Deprecation doc: legacy path → CTR path mapping; removal gate; migration notes. |

---

## 4. Promotion gates (all must pass before turning off mirror)

| Gate | Description |
|------|-------------|
| G1 | Droplet baseline captured; path map complete. |
| G2 | CTR streams written and fresh during runtime (dashboard truth audit PASS). |
| G3 | EOD enforces CTR freshness + heartbeat; fails correctly when stale. |
| G4 | No regressions in trading execution (fills evidence present). |
| G5 | Mirror parity: CTR vs legacy counts match within tolerance. |
| G6 | Rollback validated: `TRUTH_ROUTER_ENABLED=0` + restart → legacy-only. |

---

## 5. Rollback (must be documented and tested)

1. Set `TRUTH_ROUTER_ENABLED=0` in systemd env (override or EnvironmentFile).
2. `sudo systemctl daemon-reload && sudo systemctl restart stock-bot`.
3. Confirm legacy paths are updating; dashboard/EOD use legacy contract.
4. Leave CTR directory in place (no deletion) for postmortem.

---

## 6. Persona outputs (references)

- **Prosecutor:** `reports/truth_migration/board_review/prosecutor_output.md` — edge cases, permissions, partial writes, rollback.
- **Defender:** `reports/truth_migration/board_review/defender_output.md` — rollback procedure, legacy intact.
- **SRE:** `reports/truth_migration/board_review/sre_output.md` — heartbeat, freshness, EOD, systemd.
- **Quant:** `reports/truth_migration/board_review/quant_output.md` — no data loss, schemas/joins.
- **Board:** `reports/truth_migration/board_review/board_output.md` — gates, SAFE_TO_APPLY.

---

## 7. CTR directory layout (minimum viable)

```
<STOCKBOT_TRUTH_ROOT>/
  execution/   # orders, fills, attribution (if migrated)
  gates/       # expectancy gate truth
  health/      # signal_health + freshness
  exits/       # exit_truth + exit_attribution
  telemetry/   # score_telemetry, score_snapshot
  meta/        # schema_version, producer_versions, last_write_heartbeat, truth_manifest
```

---

## 8. Env flags

| Variable | Default | Meaning |
|----------|---------|---------|
| TRUTH_ROUTER_ENABLED | 0 | When 1, router writes to CTR (and legacy if MIRROR_LEGACY=1). |
| TRUTH_ROUTER_MIRROR_LEGACY | 1 | When 1 (and enabled), write to both CTR and legacy. |
| STOCKBOT_TRUTH_ROOT | /var/lib/stock-bot/truth | CTR root directory. |
