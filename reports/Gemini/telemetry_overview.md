# Telemetry extract overview (Gemini)

## Extraction window

- **Script window (UTC):** `2026-04-23T00:13:08.858181+00:00` → `2026-04-25T00:13:08.858181+00:00` (last 48 hours from run time)
- **Run executed at (UTC):** `2026-04-25T00:13:08.861280+00:00`
- **Earliest event in extracted rows:** `(no rows)`
- **Latest event in extracted rows:** `(no rows)`

## Output files (under `reports/Gemini/`)

| File | Rows written |
|------|----------------|
| `entries_and_exits.csv` | 0 |
| `blocked_and_rejected.csv` | 0 |
| `shadow_and_ab_testing.csv` | 0 |
| `signal_intelligence_spi.csv` | 0 |

## High-level counts (this batch)

- **Harvester-era unique exit rows (`entries_and_exits.csv`):** 0
- **Blocked / rejected rows:** 0
- **Rows with numeric realized P&L:** 0
- **Wins (P&L > 0):** 0
- **Losses (P&L < 0):** 0
- **Breakeven (P&L = 0):** 0
- **Win rate (wins / (wins+losses)):** `n/a`
- **Sum realized P&L (where present):** `n/a`

## Data sources consulted (non-exhaustive)

- **`entries_and_exits.csv`:** unique closed trades from `logs/exit_attribution.jsonl` only — same rules as `compute_canonical_trade_count` (`STRICT_EPOCH_START` exit floor, era cut, `trade_key` dedupe). No merged fills/orders.
- **Blocked / other CSVs:** `logs/orders.jsonl` (blocked actions), `logs/gate_diagnostic.jsonl`, `logs/run.jsonl` (trade_intent blocked_reason), `logs/critical_api_failure.log`, `logs/system_events.jsonl`
- `logs/shadow.jsonl`, `logs/paper_exec_mode_decisions.jsonl`
- `data/uw_attribution.jsonl`, `logs/uw_attribution.jsonl`, `logs/alpaca_entry_attribution.jsonl`, `logs/score_snapshot.jsonl`, `telemetry/score_snapshot.jsonl`

## Notes

- Parsing is **best-effort**; malformed JSONL lines are skipped.
- **IPs** in free-text fields are replaced with `[REDACTED_IP]` where string redaction applies.
- No API keys are emitted as dedicated columns; avoid copying raw `error_details` blobs into external systems without review.

