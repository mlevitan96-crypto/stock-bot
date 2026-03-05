# Clawdbot Removal Changelog

**Mission:** Remove all Clawdbot integration, references, configs, hooks, and assumptions.  
**Date:** 2026-03-05  
**Ethos:** CURSOR → GITHUB → DROPLET → VERIFY → REPORT.

---

## Phase 0 — Discovery + Safety

- **Result:** No critical path blocker. Deploy (`scripts/run_deploy_to_droplet.py`), CSA (`scripts/audit/run_chief_strategy_auditor.py`), SRE, and mission runners do not reference Clawdbot.
- Clawdbot was used only in EOD (board/eod) and Molt synthesis (scripts/run_openclaw_molt_synthesis.py). No CLAWDBOT_REMOVAL_BLOCKER.md written.

---

## Removed / Changed

### Code (integration removed)

| File | Change |
|------|--------|
| `board/eod/run_stock_quant_officer_eod.py` | Removed `CLAWDBOT_PATH`, `run_clawdbot_prompt`, subprocess call. EOD board is now generated locally via `_generate_eod_board_stub()`. No `CLAWDBOT_SESSION_ID` or external agent. |
| `scripts/run_openclaw_molt_synthesis.py` | Removed `CLAWDBOT_PATH`, subprocess call, `_load_text`, `_extract_json`, `_write_stub_failure`, PROMPT_TEMPLATE. Always writes stub synthesis (no OpenClaw call). |
| `board/eod/install_eod_cron_on_droplet.py` | Removed `CLAWDBOT_SESSION_ID` from EOD cron line. |
| `board/eod/cron_health_check.py` | Removed `CLAWDBOT_SESSION_ID` from repair_cron line. |
| `board/eod/cron_diagnose_and_fix.py` | Removed `CLAWDBOT_SESSION_ID` from eod_line and force_run_eod cmd. |
| `board/eod/run_eod_on_droplet.py` | Removed CLAWDBOT from docstring and run command. |
| `board/eod/run_eod_on_droplet_and_sync.py` | Removed CLAWDBOT from doc and cmd. |
| `board/eod/apply_cursor_plan.py` | Removed `CLAWDBOT_SESSION_ID` from EOD recovery command. |
| `board/eod/run_data_integrity_patch.py` | Removed `CLAWDBOT_SESSION_ID` from EOD force-run command. |
| `scripts/diagnose_cron_and_git.py` | Removed `CLAWDBOT_SESSION_ID` from env in run_eod_dry_run and from build_cron_lines EOD line. |
| `scripts/investigate_eod_github_sync.py` | Removed `CLAWDBOT_SESSION_ID` from eod_cmd. |
| `scripts/audit_stock_bot_readiness.py` | Removed `CLAWDBOT_SESSION_ID` from subprocess env (two call sites). |
| `scripts/run_stock_eod_integrity_on_droplet.sh` | Removed `export CLAWDBOT_SESSION_ID`. |

### Docs / reports (references removed or updated)

| File | Change |
|------|--------|
| `docs/EOD_DATA_PIPELINE.md` | Removed session/env and manual-run CLAWDBOT; EOD described as local generation. |
| `reports/EOD_DAILY_CRON_VERIFICATION.md` | EOD memo described as local; removed Clawdbot row from issues table. |
| `reports/DROPLET_UPSIZE_RECOMMENDATION.md` | Removed "clawdbot-gateway" from RAM rationale. |
| `reports/EOD_FAILURE_MODES_AND_PREVENTION.md` | Python/clawdbot → Python; removed Clawdbot not found/timeout row; updated JSON parse row. |
| `reports/AI_LEVERAGE_OPENCLAW_CURSOR_2026-02-17.md` | Replaced with short note: Clawdbot removed; see this changelog. |
| `MEMORY_BANK.md` | §5.5 Runner: removed CLAWDBOT_SESSION_ID; OpenClaw subsection replaced with "REMOVED" and link to this changelog. |

### Not modified (historical / generated)

- `reports/archive/`, `reports/STOCKBOT_CRON_AND_GIT_DIAGNOSTIC_*.md`, `reports/EOD_RCA_*.md`, `reports/phase9_*`, `reports/expectancy_gate_fix/`, `reports/DROPLET_PROCESS_INVENTORY_*`: left as historical snapshots.
- No `.clawdbot` or `clawdbot.json` files existed in repo.

---

## Confirmation: No Critical Path Dependency

- **Deploy:** `scripts/run_deploy_to_droplet.py` — no Clawdbot reference.
- **CSA:** `scripts/audit/run_chief_strategy_auditor.py`, `scripts/audit/enforce_csa_gate.py` — no Clawdbot reference.
- **SRE / mission runners:** No Clawdbot reference in deploy, CSA, or CI paths.
- **EOD cron:** Runs `run_stock_quant_officer_eod.py` (or `eod_confirmation.py`) without any env var; script now uses local stub only.

---

*Changelog complete. Proceed to push, deploy, CSA, and proof.*
