# Weekly Board Audit — Runbook

Run this sequence for a full weekly CSA board audit. Date format: `YYYY-MM-DD` (e.g. `2026-03-06`).

## Prerequisites

- Droplet accessible via SSH (e.g. `droplet_config.json` or `DROPLET_*` env vars).
- Repo at latest `main`; Python 3 with repo dependencies.

## Sequence

```bash
# 0. Set date (e.g. today)
DATE=2026-03-06

# 1. Pull evidence from droplet (writes manifest or blocker)
python scripts/audit/collect_weekly_droplet_evidence.py --date $DATE
# If WEEKLY_EVIDENCE_BLOCKER_*.md is written, fix sources and re-run.

# 2. Build weekly trade decision ledger (from repo or stage)
python scripts/audit/build_weekly_trade_decision_ledger.py --date $DATE
# Optional: --base-dir reports/audit/weekly_evidence_stage if you pulled to stage

# 3. Run CSA weekly review (writes verdict, findings, board packet)
python scripts/audit/run_csa_weekly_review.py --date $DATE

# 4. Write persona memos (7 files)
python scripts/audit/write_weekly_persona_memos.py --date $DATE

# 5. Update profitability cockpit (adds Weekly Review section)
python scripts/update_profitability_cockpit.py

# 6. Deploy to droplet (git pull on droplet + restart + capture proof)
git add -A && git commit -m "Weekly board audit $DATE: cockpit weekly section, artifacts"
git push origin main
python scripts/run_deploy_to_droplet.py
```

## Verification

- `reports/audit/WEEKLY_EVIDENCE_MANIFEST_<date>.json` exists and has no `critical_missing`.
- `reports/audit/WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_<date>.json` has counts.
- `reports/audit/CSA_VERDICT_CSA_WEEKLY_REVIEW_<date>.json` and `CSA_FINDINGS_*.md` exist.
- `reports/board/WEEKLY_REVIEW_<date>_<PERSONA>.md` for all 7 personas.
- `reports/board/PROFITABILITY_COCKPIT.md` contains **## 8. Weekly Review (last 7d)**.
- After deploy: dashboard Profitability & Learning tab shows Weekly Review with link to board packet.

## Artifacts produced

| Phase | Artifact |
|-------|----------|
| 0 | reports/board/WEEKLY_BOARD_PERSONAS_<date>.md (one-time or per audit) |
| 1 | reports/audit/WEEKLY_EVIDENCE_MANIFEST_<date>.json or WEEKLY_EVIDENCE_BLOCKER_<date>.md |
| 2 | reports/audit/WEEKLY_TRADE_DECISION_LEDGER_<date>.jsonl, _SUMMARY_.json |
| 3 | reports/audit/CSA_VERDICT_CSA_WEEKLY_REVIEW_<date>.json, CSA_FINDINGS_*.md, reports/board/CSA_WEEKLY_REVIEW_<date>_BOARD_PACKET.md |
| 4 | reports/board/WEEKLY_REVIEW_<date>_{CSA,SRE_Operations,Risk_Officer,Execution_Microstructure,Research_Lead,Innovation,Owner_CEO}.md |
| 5 | reports/board/WEEKLY_REVIEW_<date>_PIVOT_ANALYSIS.md |
| 6 | reports/audit/WEEKLY_UNTURNED_ROCKS_<date>.md |
| 7 | reports/board/PROFITABILITY_COCKPIT.md (updated); deploy to droplet |
| 8 | reports/board/WEEKLY_DECISION_PACKET_<date>.md |
