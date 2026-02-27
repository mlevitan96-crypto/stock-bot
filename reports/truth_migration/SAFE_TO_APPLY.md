# SAFE_TO_APPLY — Truth migration (Phase 1 mirror)

**Pre-deploy checklist.** All must be true before enabling CTR on droplet.

## Checklist

- [ ] **TRUTH_ROUTER_ENABLED default is 0** in code (no env set = no CTR write). Confirmed in `src/infra/truth_router.py`.
- [ ] **Legacy write paths unchanged** — every migrated writer still writes to legacy first; CTR write is additive only.
- [ ] **Rollback steps documented and tested (G6):** Set `TRUTH_ROUTER_ENABLED=0`, restart stock-bot; confirm legacy paths update.
- [ ] **EOD and dashboard contract:** Phase 1 contract points to legacy paths; when `TRUTH_USE_CTR=1`, contract uses CTR and EOD validates heartbeat.
- [ ] **No silent inference:** When CTR is required (`TRUTH_USE_CTR=1`), EOD fails with clear message if heartbeat missing or stale.
- [ ] **Droplet baseline captured (G1):** Run `scripts/truth/capture_droplet_baseline.sh` on droplet; `reports/truth_migration/droplet_baseline/path_map.md` and freshness_scan.json populated.
- [ ] **Unit tests pass:** `python -m unittest tests.test_truth_router -v`
- [ ] **Smoke test (optional):** With `TRUTH_ROUTER_ENABLED=1` and `STOCKBOT_TRUTH_ROOT` set to a test dir, run `scripts/truth/run_truth_smoke_test.sh` (bash on Linux/droplet).

## Rollback (exact steps)

1. Set in systemd override or env file: **TRUTH_ROUTER_ENABLED=0**
2. Run: **sudo systemctl daemon-reload && sudo systemctl restart stock-bot**
3. Confirm legacy paths are updating (e.g. `tail -1 logs/expectancy_gate_truth.jsonl`, `stat state/score_telemetry.json`).
4. Confirm dashboard/EOD use legacy contract (do not set `TRUTH_USE_CTR=1`).
5. Leave CTR directory in place (no deletion) for postmortem.

## Promotion gates (reminder)

- **G1:** Droplet baseline captured; path map complete.
- **G2:** CTR streams written and fresh (dashboard truth audit PASS with CTR contract).
- **G3:** EOD enforces CTR freshness + heartbeat; fails when stale.
- **G4:** No regressions in trading execution.
- **G5:** Mirror parity: CTR vs legacy counts match within tolerance.
- **G6:** Rollback validated as above.
