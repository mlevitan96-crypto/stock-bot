# Cursor Final Autonomous Remediation — Run on Droplet

**Purpose:** Identify why live trades are blocked, validate signal ingestion and scoring with real droplet data, produce evidence and decision. No placeholders, no gate loosening.

**Script (adapted):** `scripts/CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh`  
**Runner (from local):** `python scripts/run_cursor_final_remediation_on_droplet.py`

---

## What Was Done

1. **Adapted your remediation script** to the actual codebase:
   - **No `main.py --dry-run`** — that entry point doesn’t exist. The script uses **`run_scoring_pipeline_audit_on_droplet.py`** (full_signal_review + signal_audit_diagnostic) for real droplet data.
   - **Score distribution** comes from **signal_funnel.json** (expectancy_distributions, pct_above_min_exec_post) and optionally **signal_audit_diagnostic_droplet.json**.
   - **No pkill of collectors** — “repair” step only runs **build_expanded_intel** and **premarket/postmarket intel** scripts (no killing of uw_flow_daemon or unknown processes).
   - **Decision:** `ALLOW_TRADING` if `above_2_5 > 10`, else `REJECT`. Report is always written; script exits 1 when decision is REJECT.

2. **Runner** (`run_cursor_final_remediation_on_droplet.py`):
   - Pulls on droplet (no `git reset --hard` to avoid overwriting in-use files).
   - Uploads the bash script via base64 (avoids SFTP issues).
   - Runs the script on the droplet.
   - Fetches `RUN_DIR` artifacts and `reports/signal_review` outputs into **`reports/cursor_final_remediation/`**.

---

## Droplet Run Result (2026-02-23)

- **Git pull on droplet** failed with **“Out of disk space”** and “unable to write file” for several paths. The runner continued and uploaded/ran the script.
- **Remediation script** likely exited early (e.g. at UW cache check) because of disk space; **no RUN_DIR** was created, so only **signal_funnel.json** (from an earlier run) was fetched.
- **Funnel (real data):** 2922 candidates, 100% blocked at **5_expectancy_gate** (score_floor_breach). **pct_above_min_exec_post = 0**, median score 0.172. So **decision = REJECT** (no candidates above MIN_EXEC_SCORE).

---

## What You Should Do

1. **Free disk space on the droplet**  
   Then re-run from local:
   ```bash
   python scripts/run_cursor_final_remediation_on_droplet.py
   ```

2. **Or run the script directly on the droplet** (after SSH and freeing space):
   ```bash
   cd /root/stock-bot
   chmod +x scripts/CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh
   bash scripts/CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh
   ```
   Then copy from droplet:
   - `reports/backtests/promotion_candidate_final_<RUN_TAG>/cursor_final_summary.txt`
   - `reports/backtests/promotion_candidate_final_<RUN_TAG>/cursor_report.md`
   - `reports/signal_review/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md`
   - `/tmp/cursor_final_autonomous_remediation.log`

3. **Until scores are fixed:** Funnel shows 0% above MIN_EXEC_SCORE; the blocker is **score level** (see `reports/signal_review/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md` and `docs/SIGNAL_DATA_SOURCES_AND_CHECKLIST.md`).

---

## Files

| File | Purpose |
|------|--------|
| `scripts/CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh` | Remediation script (run on droplet) |
| `scripts/run_cursor_final_remediation_on_droplet.py` | Local runner: SSH, run script, fetch artifacts |
| `reports/cursor_final_remediation/` | Fetched artifacts (summary, report, funnel, log) |
