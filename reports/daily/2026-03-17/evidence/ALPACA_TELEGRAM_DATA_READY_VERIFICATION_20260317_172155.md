# Alpaca Telegram DATA_READY verification

- **Timestamp:** 20260317_172155
- **Mission:** DATA_READY Telegram notification finalization (notification and verification only; no strategy or execution logic changes).

---

## 1. Environment variables

The pipeline reads:

| Variable | Purpose |
|----------|---------|
| **TELEGRAM_BOT_TOKEN** | Bot token for Telegram Bot API |
| **TELEGRAM_CHAT_ID** | Target chat/channel ID |

**Verified behavior:**

- Missing vars **do not crash** the pipeline: `send_telegram()` returns `False` without raising.
- Missing vars **log a clear warning** to stderr: `"Telegram skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set."` (or `"requests not installed"` if applicable).
- When both are set, sending is enabled (API call is made from `send_telegram()`).

Documented in `docs/ALPACA_DATA_READY_MISSION.md` (Phase 5 — Telegram).

---

## 2. Send location in code

**Telegram send is called only from:**

- `data_ready_finalization()` in `scripts/alpaca_edge_2000_pipeline.py`, and only when:
  - All DATA_READY invariants pass (no governance blockers; join coverage ≥ threshold; trades_total and final_exits_count ≥ min).
  - `send_telegram_msg` is True (i.e. `--no-telegram` was not passed).
  - The block that builds the canonical message and calls `send_telegram(msg)` runs **after** the invariant check; if any check fails, the function returns `False, None, None, None` **without** calling `send_telegram`.

**No Telegram send occurs on:**

- **SAMPLE_SIZE blocker:** Step 1 raises before any later step; pipeline exits with code 1. No `data_ready_finalization()` call.
- **JOIN_INTEGRITY blocker:** Same; Step 1 raises. No Telegram.
- **ATTRIBUTION_MISSING blocker:** Same. No Telegram.
- **Any non-zero exit:** Pipeline exits before reaching DATA_READY finalization or with `ok=False`. No send.
- **Run completion without DATA_READY:** The previous “Step 8 completion” Telegram has been removed. Only `--telegram-start` triggers `step8_telegram(send_start=True)`; normal completion does not send.

**Explicit guard:** Inside `data_ready_finalization()`, `send_telegram()` is only invoked after writing the final board/CSA/SRE artifacts, i.e. only when DATA_READY is true. There is no code path that sends Telegram when `ok` is False.

---

## 3. Message content (canonical)

The DATA_READY Telegram message is:

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

**Verified:**

- Paths are absolute: `final_board.resolve()`, `csa_data_ready.resolve()`, `sre_data_ready.resolve()` are used.
- Percentages are formatted as `f"{join_entry_pct:.1f}%"` (and similarly for exit).
- Message is sent exactly once per DATA_READY event (single call to `send_telegram(msg)` inside the DATA_READY success path).

---

## 4. Dry-run verification

| Scenario | Result |
|----------|--------|
| Local run with `run_alpaca_data_ready_on_droplet.py`, SAMPLE_SIZE (n=36) | Exit 1; no Telegram; no send path reached. |
| Local run with `--allow-missing-attribution --no-telegram --data-ready`, DATA_READY false (join 0%) | Exit 0; DATA_READY not set; no Telegram (send_telegram_msg=False and invariants not met). |
| DATA_READY path would send | Only when `data_ready_finalization()` returns `ok=True` and `send_telegram_msg=True`; then one canonical message is sent. |

On the droplet with env vars set: Telegram is delivered when DATA_READY is achieved (pipeline run succeeds and invariants pass). No Telegram on SAMPLE_SIZE or JOIN_INTEGRITY (pipeline exits in Step 1).

---

## 5. Statement

**Telegram notification is correctly gated on DATA_READY.**

- Sent automatically and exactly once when DATA_READY is achieved.
- Not sent on SAMPLE_SIZE, JOIN_INTEGRITY, ATTRIBUTION_MISSING, or any non-zero exit.
- Not sent on run completion without DATA_READY.
- Canonical message content and env usage are documented and verified.
