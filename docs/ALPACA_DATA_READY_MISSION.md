# Alpaca DATA_READY finalization — mission

## Authority

Cursor is the sole executor. CSA and SRE are embedded reviewers with veto authority. No human intervention unless Cursor hard-fails with evidence.

## DATA_READY invariants (Phase 0)

**DATA_READY = true** if and only if:

- No `reports/audit/GOVERNANCE_BLOCKER_*` present
- Entry join coverage ≥ `MIN_JOIN_COVERAGE_PCT` (default 98)
- Exit join coverage ≥ `MIN_JOIN_COVERAGE_PCT` (default 98)
- `trades_total` ≥ `MIN_TRADES` (default 200)
- `final_exits_count` ≥ `MIN_FINAL_EXITS` (default 200)

## Phase 1 — Droplet execution (real data)

On the droplet, from repo root:

```bash
PYTHONPATH=. python scripts/alpaca_edge_2000_pipeline.py \
  --max-trades 2000 \
  --min-join-coverage-pct 98 \
  --min-trades 200 \
  --min-final-exits 200 \
  --data-ready
```

Or use the wrapper (runs pipeline + blocker loop + failure report on repeat failure):

```bash
PYTHONPATH=. python scripts/run_alpaca_data_ready_on_droplet.py
```

Override via env: `MAX_TRADES`, `MIN_JOIN_COVERAGE_PCT`, `MIN_TRADES`, `MIN_FINAL_EXITS`.

**Artifacts captured:** `TRADES_FROZEN.csv`, `ENTRY_ATTRIBUTION_FROZEN_NORMALIZED.jsonl`, `EXIT_ATTRIBUTION_FROZEN_NORMALIZED.jsonl`, `INPUT_FREEZE.md`, board packet, CSA review, SRE review. On DATA_READY: `ALPACA_BOARD_REVIEW_FINAL_<TS>.md`, `CSA_REVIEW_ALPACA_DATA_READY_<TS>.md`, `SRE_REVIEW_ALPACA_DATA_READY_<TS>.md`.

## Phase 2 — Blocker loop (fail-closed)

If Step 1 fails:

1. Read `reports/audit/ALPACA_JOIN_INTEGRITY_BLOCKER_<TS>.md`.
2. Classify: **JOIN_INTEGRITY** | **SAMPLE_SIZE** | **ATTRIBUTION_MISSING**.
3. Resolve:
   - **JOIN_INTEGRITY:** normalize trade_key derivation or attribution emission.
   - **SAMPLE_SIZE:** wait for more trades (no code change).
   - **ATTRIBUTION_MISSING:** add missing telemetry emission (no behavior change).
4. Re-run Phase 1 after fix.

**Hard stop:** Same blocker persists after 2 fix attempts → emit `ALPACA_DATA_READY_FAILURE_REPORT_<TS>.md` and exit.

`run_alpaca_data_ready_on_droplet.py` implements this loop.

## Phase 3 — DATA_READY confirmation

Pipeline (with `--data-ready`) confirms invariants and sets **DATA_READY = true** only when all are met. No separate manual step.

## Phase 4 — Final artifacts (close-out)

When DATA_READY is set, the pipeline writes:

- `reports/ALPACA_BOARD_REVIEW_FINAL_<TS>.md` — states **DATA_READY = true**
- `reports/audit/CSA_REVIEW_ALPACA_DATA_READY_<TS>.md` — Verdict: **APPROVED FOR GOVERNED TUNING**
- `reports/audit/SRE_REVIEW_ALPACA_DATA_READY_<TS>.md` — Verdict: **OPERATIONALLY SAFE**

## Phase 5 — Telegram (DATA_READY only)

A Telegram message is sent **automatically and exactly once** when DATA_READY is achieved, and **never** on SAMPLE_SIZE, JOIN_INTEGRITY, ATTRIBUTION_MISSING, or run completion without DATA_READY.

### Environment variables

The pipeline reads:

- **TELEGRAM_BOT_TOKEN** — Bot token from BotFather.
- **TELEGRAM_CHAT_ID** — Target chat/channel ID.

**Behavior:**

- Missing vars **do not crash** the pipeline; `send_telegram()` returns `False` and logs a clear warning to stderr: `"Telegram skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set."`
- When both are set, Telegram is sent (from `data_ready_finalization()` only when DATA_READY is true).
- Use `--no-telegram` to suppress sending (e.g. local dry-runs).

### Canonical DATA_READY message

```
Alpaca DATA_READY achieved.

- trades_total: <N>
- final_exits_count: <N>
- entry join coverage: <X>%
- exit join coverage: <Y>%

Artifacts:
- Board: <absolute path>
- CSA: <absolute path>
- SRE: <absolute path>

System is approved for governed tuning.
```

Paths are absolute (resolved from repo root). Message is sent exactly once per DATA_READY event.

### Droplet

On the droplet, set env before running:

```bash
export TELEGRAM_BOT_TOKEN="<token>"
export TELEGRAM_CHAT_ID="<chat_id>"
PYTHONPATH=. python scripts/run_alpaca_data_ready_on_droplet.py
```

Or use a `.env` or shell profile; the pipeline does not load `.env` itself.

---

No strategy or execution logic changes. Telemetry, dataset, and analysis only.
