# Repository report visibility (sidebar contract)

## Operator-visible (exactly two filenames per session)

Only these files are treated as **first-class** for operators (sidebar / daily closeout paste source):

```
reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.md
reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.json
```

No other `.md`, `.json`, or `.csv` under `reports/` is operator-primary.

## Evidence (everything else under the session tree)

```
reports/daily/<YYYY-MM-DD>/evidence/**
```

All detailed audits, CSA packets, reconciliation CSVs, truth JSON, dashboard proofs, and learning summaries live here. They are **disposable** per retention policy and **not** the canonical daily paste target.

## Outside `reports/daily/`

Top-level `reports/*.md|json|csv`, `reports/audit/*`, and similar paths are **legacy or mistaken** for new work. New automation **must not** add report artifacts there. CI enforces allowed paths for new files.

## Pruning vs permanence

- **Canonical `DAILY_*`:** retained indefinitely (not deleted by the report pruner).
- **Session `evidence/`:** deleted in bulk when the session calendar date is older than **N** days (default **3**), rule-driven.
- **Legacy `reports/**`:** `.md`/`.json`/`.csv` not under the allowed daily layout are deleted when **mtime** age exceeds **N** days.
- **Logs / telemetry:** permanent; not “reports” for this rule.

## Enforcement

- Pull requests: `.github/workflows/report-layout.yml` — path guard + evidence-without-daily check.
- Local: `make verify_report_layout`.

## See also

- `docs/CANONICAL_DAILY_REPORT_CONTRACT.md`
- `docs/REPORT_OUTPUT_CONTRACT.md`
- `memory_bank/report_output_contract.md`
