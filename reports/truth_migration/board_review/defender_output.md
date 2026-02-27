# Defender — Rollback and legacy integrity

**Persona:** Defender. **Intent:** Ensure rollback is instant and legacy remains intact until gates pass.

## 1. Rollback procedure (exact)
1. Set in systemd override or env file: `TRUTH_ROUTER_ENABLED=0`.
2. Run: `sudo systemctl daemon-reload && sudo systemctl restart stock-bot`.
3. Confirm: Legacy paths (e.g. `logs/expectancy_gate_truth.jsonl`, `logs/exit_attribution.jsonl`, `state/score_telemetry.json`) are still being updated (e.g. `stat`, `tail`).
4. Confirm: Dashboard and EOD use legacy contract (no reads from CTR).
5. Do **not** delete CTR directory; keep for postmortem.

## 2. Legacy remains intact
- **Phase 1 (mirror):** Every writer that is migrated to CTR must continue to write to the existing legacy path with the same content. No removal of legacy writes until Phase 3 and only after SAFE_TO_APPLY gates pass.
- **Readers:** In Phase 1 and Phase 2, dashboard and EOD scripts continue to read from legacy paths. Only after reader migration (Phase 2) do we point audits to CTR; and we do that behind a contract that can be reverted (e.g. env “use CTR for audit”).
- **No dual-write removal before gate G5:** Mirror parity check (G5) must pass before we consider setting `TRUTH_ROUTER_MIRROR_LEGACY=0`.

## 3. Reversibility
- **Single kill switch:** `TRUTH_ROUTER_ENABLED=0` disables all CTR writes. No feature flag per-stream for Phase 1; one flag only.
- **Code paths:** When disabled, truth_router.append_jsonl / write_json are no-ops for CTR (legacy write is in caller). Callers must retain their existing legacy write logic unchanged.

## 4. Acceptance
- Rollback validated (G6): With TRUTH_ROUTER_ENABLED=0 and restart, system returns to legacy-only behavior and dashboard/EOD pass using legacy paths.
