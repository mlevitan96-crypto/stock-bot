# Canonical daily market session report

This document defines the **only** operator-first-class human report per US equity market session (ET calendar date). It complements `docs/REPORT_OUTPUT_CONTRACT.md` with required content.

## Paths (mandatory)

| Output | Path |
|--------|------|
| Primary | `reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.md` |
| Structured (recommended) | `reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.json` |

`<YYYY-MM-DD>` is the **ET session date** for that run.

## Required content (`DAILY_MARKET_SESSION_REPORT.md`)

1. **Market session scope** — ET date, window description, and epoch bounds (from scope evidence or truth JSON).
2. **Trades executed / blocked** — Counts and pointers to cohort IDs in evidence (not full ID dumps in chat-sized paste).
3. **Net PnL** — Cohort-level number and a **verbatim embedded** reconciliation table (bounded row count) when a reconciliation CSV exists.
4. **Promotion decision** — **YES** or **NO**, aligned to the CSA closeout verdict line in evidence.
5. **Learning status** — Verdict and key fields from `ALPACA_LEARNING_STATUS_SUMMARY.*` in `evidence/` when present.
6. **Embedded verbatim sections from evidence** (bounded size):
   - PnL / reconciliation table (from CSV-derived markdown table).
   - **Signal attribution** — excerpt from the latest `ALPACA_PNL_SIGNAL_ATTRIBUTION_*.md` (or equivalent) in `evidence/`.
   - **CSA verdict block** — excerpt containing `CSA_VERDICT:` from closeout and/or last-window verdict evidence.
7. **Links to raw evidence** — Relative paths under `reports/daily/<date>/evidence/`; no large inline JSON blobs.

## Assembly order (non-negotiable)

1. All producers write **only** under `reports/daily/<date>/evidence/`.
2. **`scripts/audit/assemble_daily_market_session_report.py`** runs **last**, reads evidence, fills the sections above, writes `DAILY_*`.

## Non-goals

- Logs, raw telemetry, and warehouse JSON under `logs/`, `data/`, `replay/`, etc. are **not** reports and are out of scope for this contract.
- Legacy paths (`reports/audit/`, top-level `reports/*.md`) must not receive **new** automation output; see `docs/REPO_REPORT_VISIBILITY_RULES.md`.
