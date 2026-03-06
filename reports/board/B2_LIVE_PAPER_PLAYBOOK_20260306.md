# B2 Live Paper — Playbook

**Created:** 2026-03-06 (repo-execution: promote B2_shadow to LIVE PAPER)

## How B2 was enabled for live paper

1. **Config (source of truth):** `config/b2_governance.json`
   - `b2_mode`: `"live_paper"`
   - `b2_shadow_enabled`: `false`
   - `b2_live_paper_enabled`: `true`
   - `b2_live_enabled`: `false`

2. **Runtime:** Main reads config; env `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT` overrides (for rollback).
   - When B2 live paper is on: early signal_decay exits (hold < 30 min) are **suppressed**; events logged to `logs/b2_suppressed_signal_decay.jsonl`.
   - Exits are tagged `variant_id: "B2_live_paper"` in `logs/exit_attribution.jsonl` when B2 is active and TRADING_MODE=PAPER.

3. **Droplet:** After deploy, ensure `.env` has:
   - `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true` (or omit to use config from repo)
   - `TRADING_MODE=PAPER`
   Run: `scripts/audit/enable_b2_paper_on_droplet.py` to set and verify.

## How to run rollback

**Local (config only):**
```bash
python scripts/governance/rollback_b2_live_paper.py [reason]
```
- Updates `config/b2_governance.json` to shadow-only (live_paper OFF).
- Writes `reports/audit/B2_ROLLBACK_<timestamp>.md`.

**On droplet (full rollback):**
1. SSH to droplet, set in `.env`: `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false`
2. Restart: `sudo systemctl restart stock-bot`
3. Or run from repo: `python scripts/audit/b2_rollback_drill_on_droplet.py` (drill: OFF then ON again; for rollback leave OFF and do not re-enable).

## Where to verify state

- **Config:** `config/b2_governance.json` — `b2_mode`, `b2_live_paper_enabled`.
- **Droplet .env:** `grep FEATURE_B2 .env` → `true` = B2 active, `false` = B2 off.
- **Dashboard:** Profitability & Learning tab — CSA mission, trade count; Learning & Readiness — exits, replay, CSA summary.
- **Exit attribution:** `logs/exit_attribution.jsonl` — records with `variant_id: "B2_live_paper"` when B2 is on.

## Rollback drill

Rollback drill executed and verified on 2026-03-06: ran `scripts/governance/rollback_b2_live_paper.py "rollback drill"` (config set to shadow), then re-applied live_paper config. Artifact: `reports/audit/B2_ROLLBACK_20260306_203312.md`.
