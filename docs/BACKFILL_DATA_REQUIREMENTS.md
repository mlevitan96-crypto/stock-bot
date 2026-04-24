# Exit-Lag Backfill: Why Past Dates Can Be Missing

## What backfill needs

The exit-lag backfill (and the "why we didn't win" forensic) need **per-date data** from:

- **`logs/exit_attribution.jsonl`** — one line per closed trade (timestamp/entry_timestamp/ts).
- **`reports/state/exit_decision_trace.jsonl`** — unrealized PnL snapshots over time.
- **`state/blocked_trades.jsonl`** — blocked trades (optional for some steps).

These are **single append-only files**, not per-date. The forensic filters by the requested date when reading them.

## Why you can't get data for some dates

Backfill will mark a date as **`no_data_for_date`** or **`forensic_fail`** when:

1. **No attribution for that day** — `exit_attribution.jsonl` has no record with that date (no closed trades, or that day’s data was never written).
2. **Trace/attribution were truncated or rotated** — e.g. only “today” or last N days are kept, so older dates are gone.
3. **Bot wasn’t running** — no trades (and no logs) for that day.
4. **Trace was added recently** — `exit_decision_trace.jsonl` only exists from a certain day onward; earlier dates have no trace even if attribution exists (forensic may then fail on join or no-trace ratio).

So **there is no way to “get” data for a date that was never written or was removed.** Backfill only uses what’s already on the droplet in those files.

## How to get data for more dates going forward

1. **Retention**  
   Don’t truncate or rotate `exit_decision_trace.jsonl` or `logs/exit_attribution.jsonl`. Keep them append-only for at least the number of days you want to backfill (e.g. 30+ days). The repo **data retention policy** (`docs/DATA_RETENTION_POLICY.md`) defines which paths are protected from rotation and how disk cleanup works.

2. **Daily archive (optional)**  
   If you want to support backfill even after a future rotation, add a daily job (e.g. after market close) that:
   - Copies that day’s lines from `exit_attribution.jsonl` and `exit_decision_trace.jsonl` into date-scoped files, e.g.  
     `logs/archive/YYYY-MM-DD/exit_attribution.jsonl` and  
     `reports/state/archive/YYYY-MM-DD/exit_decision_trace.jsonl`,  
   - or appends to a “by date” store that forensic/backfill can read later.

   The current forensic and backfill scripts do **not** yet read from such archive paths; they only read the main files. Adding support for optional archive paths would allow backfill to use archived data when the main files no longer contain that date.

3. **Run backfill regularly**  
   Run backfill (e.g. weekly or after each trading day) so that shadow results are produced while the data for those dates is still in the main files.

## Manifest reasons

- **`no_data_for_date`** — No exit_attribution records for that date on the droplet; forensic was skipped.
- **`phase0_fail`** / **`phase0_fail_closed`** — Required files missing or phase0 failed.
- **`forensic_fail`** — Forensic ran but exited non-zero (e.g. no-trace ratio too high, or other blocker).
- **`surgical_fail`** / **`replay_fail`** — Downstream step failed after forensic succeeded.
