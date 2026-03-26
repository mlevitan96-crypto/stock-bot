# B2 Live Paper — Enable Validation

**Generated (UTC):** 2026-03-06

## Config diff summary

- **Added:** `config/b2_governance.json`
  - `b2_mode`: `"live_paper"`
  - `b2_shadow_enabled`: `false`
  - `b2_live_paper_enabled`: `true`
  - `b2_live_enabled`: `false`
- **main.py:** B2 flag now read from config when env `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT` is unset; env overrides for rollback. Exit attribution sets `variant_id: "B2_live_paper"` when B2 is on and TRADING_MODE=PAPER.
- **No change** to non-B2 behavior; core signal logic unchanged.

## Rollback drill evidence

- **Script:** `scripts/governance/rollback_b2_live_paper.py`
- **Drill run:** 2026-03-06 — executed `rollback_b2_live_paper.py "rollback drill"`; config set to shadow then re-applied live_paper.
- **Artifact:** `reports/audit/B2_ROLLBACK_20260306_203312.md`
- **Playbook:** `reports/board/B2_LIVE_PAPER_PLAYBOOK_20260306.md` (how to enable, rollback, verify).

## Deploy evidence

- **Commit:** `f4ebc22d71d0` (Promote B2_shadow to live paper with rollback drill and governance artifacts.)
- **Push:** origin main succeeded.
- **Deploy:** `python scripts/run_deploy_to_droplet.py` — git fetch/reset OK, pytest spine OK, services restarted, dashboard listening.
- **B2 enable on droplet:** `scripts/audit/enable_b2_paper_on_droplet.py` — TRADING_MODE=PAPER, FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true, telemetry_health 200, learning_readiness 200.
- **Proof:** `reports/audit/B2_LIVE_PAPER_ENABLE_PROOF.md` and `B2_LIVE_PAPER_ENABLE_PROOF.json`.

## Dashboard checks

- **B2 in LIVE PAPER mode:** Confirmed (TRADING_MODE=PAPER, FEATURE_B2=true; no real capital).
- **Exit attribution:** Exits will be tagged `variant_id: "B2_live_paper"` when B2 is active; `logs/exit_attribution.jsonl` and `logs/b2_suppressed_signal_decay.jsonl` are the sources of truth.
- **Other strategies:** No mode change; equity/wheel and other behavior unchanged.
- **Profitability & Learning:** CSA mission visible; trade count and next CSA threshold from existing cockpit/scripts.
- **Learning & Readiness:** Exits, replay, CSA summary from existing endpoints (`/api/learning_readiness` returned 200).

## Exit criteria

| Criterion | Status |
|-----------|--------|
| B2 running in LIVE PAPER only | Yes |
| Rollback drill implemented and recorded | Yes |
| CSA risk acceptance artifact for B2 live paper | Yes (`reports/audit/CSA_RISK_ACCEPTANCE_B2_LIVE_PAPER_20260306.md`) |
| Changes deployed to droplet | Yes |
| Validation report written | Yes (this file) |
| No unintended changes to other strategies | Yes |
