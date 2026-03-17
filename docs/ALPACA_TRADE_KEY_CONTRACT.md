# Alpaca canonical trade_key contract

**Purpose:** Single join key for TRADES_FROZEN.csv, ENTRY_ATTRIBUTION, and EXIT_ATTRIBUTION so lever attribution analysis is correct and complete.

---

## Definition

```text
trade_key = "{symbol}|{side}|{entry_time_iso}"
```

- **symbol:** Normalized ticker (uppercase, stripped).
- **side:** `LONG` or `SHORT` (BUY/SELL mapped deterministically).
- **entry_time_iso:** Entry time in UTC, second precision (no subsecond, no timezone suffix required but stored as ISO).

---

## Rules

1. **Symbol:** `normalize_symbol(s)` → upper, strip. Empty → `"?"`.
2. **Side:** `normalize_side(s)` → `LONG` or `SHORT`. `buy`/`long` → `LONG`; `sell`/`short` → `SHORT`. Default `LONG` if ambiguous.
3. **Entry time:** `normalize_time(t)` → UTC ISO to second precision (e.g. `2026-03-17T16:00:00` or `2026-03-17T16:00:00+00:00`). Truncate to seconds; ensure UTC.

---

## Build

- `build_trade_key(symbol, side, entry_time)` returns `f"{normalize_symbol(symbol)}|{normalize_side(side)}|{normalize_time(entry_time)}"`.

---

## Usage

- All attribution events (entry + exit) must include both `trade_id` (existing) and `trade_key` (canonical).
- Frozen dataset join uses `trade_key` as primary key. Fallback to `trade_id` only when explicitly allowed.
- Join coverage is computed as: (number of frozen trades with a matching `trade_key` in attribution) / (number of frozen trades).
