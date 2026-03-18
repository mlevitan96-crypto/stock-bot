# Alpaca Telemetry Emission Trace (Phase 2)

## Root cause — missing entry attribution + unified stream

### Bug A: Impossible gate (`FILLED` vs `filled`)

**Path:** `main.py` after `submit_entry()`.

**Expected:** When an order fills, run XAI + entry attribution emit.

**Actual:** Code checked `entry_status == "FILLED"` (uppercase). `AlpacaExecutor.submit_entry()` returns `"filled"` (lowercase) on success paths (e.g. lines 4883, 5039, 5180).

**Effect:** The entire block (including explainable trade entry logging tied to that condition, and the **former** `emit_entry_attribution` call) **never executed** for normal fills.

### Bug B: Emit placement vs `trade_id` contract

**Former emit** used wall-clock `datetime.now(timezone.utc)` and a truncated `trade_id`, while **`mark_open()`** persists `entry_ts` from `datetime.utcnow().isoformat()` into `state/position_metadata.json`.

**Effect:** Even if Bug A were fixed only by case-fold, `trade_id` / `trade_key` could still **mismatch** exit records keyed by metadata `entry_ts`.

### Correct wiring (post-repair)

1. **`mark_open()`** runs on `entry_status == "filled"` (already true).
2. **`emit_entry_attribution()`** runs **immediately after** `mark_open()`, reading **`entry_ts` from `position_metadata.json`** for that symbol.
3. **`trade_id`** = `open_{SYMBOL}_{entry_ts}` — matches `build_exit_attribution_record(..., trade_id=open_trade_id)` where `entry_ts_iso_attr` comes from the same metadata at exit.

### Code paths

| Stream | Emitter | Called from |
|--------|-----------|-------------|
| `alpaca_entry_attribution.jsonl` + unified entry | `src/telemetry/alpaca_attribution_emitter.py` → `emit_entry_attribution` | `main.py` after `mark_open` (repair) |
| `alpaca_exit_attribution.jsonl` + unified exit | `emit_exit_attribution` | `src/exit/exit_attribution.py` → `append_exit_attribution` (try/except wrapped) |
| `exit_attribution.jsonl` | `append_exit_attribution` | `main.py` exit path |

### Why `alpaca_exit_attribution.jsonl` was MISSING on droplet (pre-repair)

Possible contributors (not mutually exclusive):

1. File never created if no successful `emit_exit_attribution` write (silent `_append_jsonl` swallow).  
2. Env `ALPACA_EXIT_ATTRIBUTION_PATH` redirect (verify on droplet).  
3. Primary exit truth remains `exit_attribution.jsonl` — **acceptable** for PnL; unified **exit** rows still desired for single-stream joins.

### Deferred / partial fill path

Orders with `submitted_unfilled`: **`mark_open` not called** until reconciliation. **Entry attribution not emitted** on that path in this repair. Reconciliation may create metadata without going through `emit_entry_attribution`. Documented as **residual gap** in backfill / forward proof (majority of Alpaca paper entries fill immediately).

### Rotation / truncation

Per MB, `exit_attribution.jsonl` and `attribution.jsonl` must not be rotated away. No evidence of truncation causing MISSING unified files — files were **never created** because emit never ran.
