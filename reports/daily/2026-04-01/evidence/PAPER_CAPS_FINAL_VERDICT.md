# PAPER_CAPS_FINAL_VERDICT

- **Better under caps-on (p05 heuristic):** `QUANT_EMU_001` — see `BOARD_QUANT_PAPER_CAPS_VERDICT.md`.
- **CF p05 delta (caps_on − baseline):** `0.12112500000000015` (USD per trade proxy).
- **Recommended caps (evidence snapshot):** see `PAPER_CAPS_FINAL_VERDICT.json` → `recommended_caps_from_evidence`.
- **Next single paper lever:** Re-run weekly `run_paper_extension_caps_evaluation.py` with frozen cap env; archive JSON.
- **Verify:** `python3 scripts/audit/verify_paper_caps_wired.py && diff PAPER_EXTENSION_EVALUATION.json week-over-week`
- **Rollback:** Unset PAPER_CAPS_* env; delete cap JSONL; stop scheduling evaluation script.
