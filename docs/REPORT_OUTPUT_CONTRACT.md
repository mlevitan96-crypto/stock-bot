# Report output contract

Full required sections for the markdown report are specified in **`docs/CANONICAL_DAILY_REPORT_CONTRACT.md`**. Sidebar visibility is summarized in **`docs/REPO_REPORT_VISIBILITY_RULES.md`**.

## Operator-visible (first-class)

Per **ET market session date** `YYYY-MM-DD`, exactly these files under `reports/daily/<YYYY-MM-DD>/`:

| File | Purpose |
|------|---------|
| `DAILY_MARKET_SESSION_REPORT.md` | Single copy-paste-ready summary: session scope (ET), trades executed/blocked, net PnL, promotion decision (YES/NO), embedded tables/snippets from analyses, **links** (not full inline) to evidence files |
| `DAILY_MARKET_SESSION_REPORT.json` | Same facts, structured (optional but recommended) |

## Everything else: `EVIDENCE_ONLY`

All detailed audit outputs, CSA/Board drafts, reconciliation CSVs, truth JSON, alignment proofs, etc. MUST live under:

`reports/daily/<YYYY-MM-DD>/evidence/`

They are **not** operator-visible in the sidebar contract; they exist for reproducibility and machine consumption.

## Non-goals

- Logs and raw telemetry (`logs/`, `data/`, `state/`, etc.) remain **permanent** and are not “reports” under this contract.
- Historical `reports/audit/*` paths are **legacy**; new writers MUST NOT add there.

## Assembly order

1. Producers write only into `evidence/`.
2. A final step (`assemble_daily_market_session_report.py`) reads evidence, embeds key sections into `DAILY_*`, and writes canonical files last.

## Reference vs inline

Canonical report embeds **small tables and verdict lines**. Large JSON blobs and raw paths are **linked** as relative paths from `reports/daily/<date>/`.
