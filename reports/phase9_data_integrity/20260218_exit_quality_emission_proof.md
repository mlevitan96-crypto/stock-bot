# Exit quality emission proof (2026-02-18)

## A) Paper run state (no overlay)
```json
{
  "status": "live_paper_run_started",
  "timestamp": 1771435516,
  "details": {
    "trading_mode": "paper",
    "process": "python3 main.py",
    "session": "stock_bot_paper_run",
    "governed_tuning_config": ""
  }
}
```

## B) Last exit_attribution record ts
2026-02-18T17:25:49.208953+00:00

## C) Newest 500 exit_attribution lines
```
sample_records 500 with_exit_quality_metrics 0
examples []
```

- **sample_records:** 500
- **with_exit_quality_metrics:** 0

## Example exit_quality_metrics (1–2 redacted)
```
(none yet)
```

## Attribution: last 200 lines, entry_score in context or top-level
```
sample 200 with_entry_score 200
```

- **sample:** 200, **with_entry_score:** 200

## Diagnosis (with_exit_quality_metrics == 0)

Possible reasons: (1) No new exits since deploy—last exit_attribution ts 2026-02-18T17:25:49 may be before or around pull. (2) Paper process not restarted after pull, so the running process may still be old code. (3) Exits use a path that does not call log_exit_attribution. **To get non-zero:** Restart paper after pull so the new process has the high_water fix, then wait for at least one time/trail or displacement exit and re-sample. Attribution already has entry_score (200/200 in sample); blame 100% unclassified may be due to join key mismatch (entry_timestamp vs entry_ts bucket) rather than missing entry_score.
