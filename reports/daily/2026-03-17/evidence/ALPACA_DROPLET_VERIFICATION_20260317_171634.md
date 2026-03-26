# Alpaca droplet verification report

- **Timestamp:** 20260317_171634
- **Verification context:** Local proxy (Windows); droplet-specific env not verified on target host.
- **Pipeline script:** `scripts/alpaca_edge_2000_pipeline.py`
- **Droplet runner:** `scripts/run_alpaca_data_ready_on_droplet.py`

---

## Verdict: **FAIL**

DATA_READY is not achieved. Current blocker is **SAMPLE_SIZE**. Invariants are enforced correctly; resolution requires more data (wait for more trades).

---

## Phase 1 — Environment check (local proxy)

| Check | Result |
|-------|--------|
| Repo version | `31dc1016dc3c8cc3f9d79d8c8c4bd6ca577903ad` (main, ahead of origin) |
| PYTHONPATH | Required; set to repo root for pipeline and droplet script |
| Env vars (pipeline) | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (optional; send_telegram returns False if unset) |
| Logging paths | Exit log: `logs/exit_attribution.jsonl`; entry: `logs/alpaca_entry_attribution.jsonl`; canonical exit: `logs/alpaca_exit_attribution.jsonl` |
| GOVERNANCE_BLOCKER_* | None present in `reports/audit/` |

**Note:** On the droplet, confirm Alpaca API keys and log paths exist; this run was local.

---

## Phase 2 — Pipeline dry-run

**Command run:** `PYTHONPATH=. python scripts/run_alpaca_data_ready_on_droplet.py`

| Item | Result |
|------|--------|
| Exit code | 1 |
| Console output | Step 1 failed: Sample size below threshold (n=36, min_trades=200, min_final_exits=200). Blocker written. Attempt 1 failed; classification SAMPLE_SIZE; failure report written. |
| GOVERNANCE_BLOCKER_* written | No (only ALPACA_JOIN_INTEGRITY_BLOCKER_* and ALPACA_DATA_READY_FAILURE_REPORT_*) |
| Blocker written | `reports/audit/ALPACA_JOIN_INTEGRITY_BLOCKER_20260317_171605.md` |
| Failure report written | `reports/audit/ALPACA_DATA_READY_FAILURE_REPORT_20260317_171605.md` |
| Dataset artifacts (this run) | None (Step 1 fails before writing INPUT_FREEZE.md for this run; prior run dir `reports/alpaca_edge_2000_20260317_1708` has TRADES_FROZEN.csv and INPUT_FREEZE.md from a run with --allow-missing-attribution) |

---

## Phase 3 — Invariant verification

| Invariant | Enforced | Evidence |
|-----------|----------|----------|
| trades_total from TRADES_FROZEN.csv | Yes | Step 1 uses n = len(rows); INPUT_FREEZE.md records "Trade count"; data_ready_finalization uses n_trades. |
| final_exits_count | Yes | Same as trades_total (frozen rows from exit log). |
| entry join coverage % | Yes | Step 1 computes join_coverage_entry_pct; written to INPUT_FREEZE.md; data_ready_finalization checks >= min_join_coverage_pct. |
| exit join coverage % | Yes | Step 1 computes join_coverage_exit_pct; same flow. |
| min-trades gate | Yes | Step 1: `if not allow_missing_attribution and (n < min_trades or n < min_final_exits):` → raise + blocker. |
| min-final-exits gate | Yes | Same condition. |
| join-coverage gate | Yes | Step 1: `if not allow_missing_attribution and (join_coverage_entry_pct < min_join_coverage_pct or ...)` → raise + blocker. |
| No silent bypass via --allow-missing-attribution | Yes | Droplet script calls run_pipeline(allow_missing_attribution=False). Pipeline uses flag only when explicitly passed. |

**Behavior confirmed:**

- **SAMPLE_SIZE blocks when expected:** n=36 < 200 triggered blocker and failure report; classification SAMPLE_SIZE.
- **JOIN_INTEGRITY blocks when expected:** Code path writes blocker with classification JOIN_INTEGRITY when join coverage < threshold (not exercised in this run).
- **DATA_READY only when all invariants pass:** data_ready_finalization checks GOVERNANCE_BLOCKER_*, join coverage, min_trades, min_final_exits; returns False and does not write final artifacts if any fail.

**Current snapshot (from prior run with --allow-missing-attribution):**

- trades_total / final_exits_count: **36**
- join_coverage_entry_pct: **0.0%**
- join_coverage_exit_pct: **0.0%**

---

## Phase 4 — Artifact integrity

**DATA_READY not achieved** in this run.

| Check | Result |
|-------|--------|
| Blocker classification correct | Yes — blocker file states SAMPLE_SIZE and "wait for more trades (no code change)." |
| Blocker contents accurate and actionable | Yes — counts (trades_total=36, required_trades=200, required_final_exits=200) and resolution are clear. |
| Failure report | Accurate; references blocker path and classification; resolution "Wait for more trades. No code change." |

If DATA_READY were achieved, the pipeline would write:

- `reports/ALPACA_BOARD_REVIEW_FINAL_<TS>.md` (states DATA_READY = true)
- `reports/audit/CSA_REVIEW_ALPACA_DATA_READY_<TS>.md` (verdict: APPROVED FOR GOVERNED TUNING)
- `reports/audit/SRE_REVIEW_ALPACA_DATA_READY_<TS>.md` (verdict: OPERATIONALLY SAFE)

Content of these artifacts is implemented in data_ready_finalization() and matches the mission.

---

## Phase 5 — Telegram path verification

| Check | Result |
|-------|--------|
| Telegram sent on success | Yes — when DATA_READY is set, data_ready_finalization(..., send_telegram_msg=True) sends the close-out message unless --no-telegram was passed. |
| Message includes join coverage %, board path, CSA/SRE paths | Yes — message includes "Join coverage >= 98%", "Artifacts: Board: ..., CSA: ..., SRE: ...". |
| --no-telegram suppresses sending | Yes — data_ready_finalization is called with send_telegram_msg=not args.no_telegram; step8_telegram is skipped when args.no_telegram. |

send_telegram() returns False if TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing (no exception).

---

## Phase 6 — Final verdict summary

- **Verdict:** **FAIL**
- **Current blocker:** SAMPLE_SIZE (trades_total=36, min_trades=200, min_final_exits=200).
- **trades_total / final_exits_count:** 36 (from exit log; insufficient for gate).
- **Join coverage entry/exit:** 0.0% / 0.0% (from last INPUT_FREEZE.md with frozen dataset).
- **Invariants enforced:** Yes. Min-trades, min-final-exits, and join-coverage gates are enforced in Step 1; DATA_READY finalization re-checks all invariants and only writes final artifacts when all pass. No silent bypass when run via droplet script.

**Statement:** System behavior matches the DATA-READY contract. Gates fail closed; blocker and failure report are written; classification and resolution are correct.

**What condition is unmet:**

1. trades_total (36) < MIN_TRADES (200).
2. final_exits_count (36) < MIN_FINAL_EXITS (200).
3. Join coverage (0%) < MIN_JOIN_COVERAGE_PCT (98%) for both entry and exit.

**Resolution required:**

- **More data (wait):** Accumulate more trades so that trades_total and final_exits_count ≥ 200, and ensure entry/exit attribution emission so join coverage can reach ≥ 98%.
- **Code fix:** None for SAMPLE_SIZE.
- **Configuration fix:** None for SAMPLE_SIZE. On the droplet, ensure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set if Telegram close-out is desired on DATA_READY.
