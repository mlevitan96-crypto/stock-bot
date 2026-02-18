# Snapshot fix — adversarial plan review

**Purpose:** Multi-model hypotheses for why `score_snapshot.jsonl` has 0 records. Evidence that would falsify each.

---

## 1. How could the snapshot hook never fire?

**Adversarial:** The hook lives inside `for candidate_rank, c in enumerate(clusters_sorted)`, after the expectancy gate call and before `if not should_trade: continue`. So it runs only for candidates that reach that line. If `clusters_sorted` is always empty, or every candidate hits a `continue` before the expectancy block (e.g. position flip, max_one_position_per_symbol), the hook is never entered.

**Quant:** Gate counts in `logs/gate.jsonl` would show blocks; no `SCORE_SNAPSHOT_DEBUG: hook entered` lines would appear if the loop body never reaches the snapshot.

**Product:** If users see blocked_trades/gate logs but no snapshot, the pipeline is filtering everyone before the snapshot.

**Falsification:** With `SCORE_SNAPSHOT_DEBUG=1`, seeing any `SCORE_SNAPSHOT_DEBUG: hook entered` line falsifies “hook never fires”.

---

## 2. How could it fire but never write?

**Adversarial:** (a) Relative path `Path("logs/score_snapshot.jsonl")` is resolved against CWD. If the process is started with a different CWD (e.g. from `board/eod/` or a wrapper that `cd`s elsewhere), the file is created under that CWD; `tail logs/score_snapshot.jsonl` from repo root would show nothing. (b) An exception in `append_score_snapshot` (e.g. `json.dumps(..., allow_nan=False)` on a value that slips past `_sanitize`, or non-string key in composite_meta) is caught and swallowed when debug is off.

**Quant:** Debug logs would show `path=...` and either `write attempt`/`write done` or `EXCEPTION`. If path is under a different directory than repo root, that explains empty file at expected location.

**Product:** Same file must be written regardless of how/where the process is started; path must be CWD-independent.

**Falsification:** (a) Resolving path from `__file__` and still seeing 0 records falsifies “wrong CWD”. (b) Seeing `SCORE_SNAPSHOT_DEBUG: append_score_snapshot EXCEPTION` with debug on falsifies “no exception”.

---

## 3. How could writes succeed but file remain empty?

**Adversarial:** Writes go to a different path than the one inspected (same as 2a). Or file is opened and flushed but another process/rotation clears it (unlikely for append-only JSONL). Or the process that writes is not the same as the one whose logs we tail (e.g. multiple instances).

**Quant:** Compare resolved path in debug output to the path used by `tail`/`wc -l`. If they differ, that’s the cause.

**Product:** Single canonical path for snapshot file, documented and used by all consumers.

**Falsification:** One process, one path, and `wc -l` on that path shows >0 after hook+write logs.

---

## 4. How could orchestration prevent scoring cycles?

**Adversarial:** Paper run exits before the first `decide_and_execute` cycle, or the main loop never calls it (e.g. market closed, wait logic, or exception before the loop). Then no candidates are ever processed.

**Quant:** Check that the paper process stays up and that “Processing N clusters” appears in logs; if N is always 0 or the loop never runs, snapshot has nothing to record.

**Product:** Runbook should start the process from repo root and keep it running; health checks should confirm cycles are running.

**Falsification:** Seeing “Processing N clusters” with N>0 and later `SCORE_SNAPSHOT_DEBUG: hook entered` shows orchestration is not preventing scoring.

---

## Ranked hypotheses

| Rank | Hypothesis | Evidence to falsify |
|------|------------|----------------------|
| 1 | **Path is CWD-relative** — file written to a different directory than where we look | Resolve path from `__file__`; if file still empty at that path, falsified. Debug path output matches inspected path. |
| 2 | **Hook never reached** — no candidates reach the expectancy gate (0 clusters or all continue earlier) | With DEBUG=1, any “hook entered” line falsifies. |
| 3 | **Write fails with exception** — serialization or I/O error, swallowed when debug off | With DEBUG=1, “EXCEPTION” or “FAILED” in logs; fix serialization or path. |
| 4 | **Orchestration** — no scoring cycles run (process exit or loop never reached) | “Processing N clusters” with N>0 and hook logs falsify. |

---

## Next step

Run on droplet with `SCORE_SNAPSHOT_DEBUG=1`, capture hook/write/exception logs and `tail`/`wc -l` on the path printed in debug. Use that evidence for root_cause.md and the minimal fix.
