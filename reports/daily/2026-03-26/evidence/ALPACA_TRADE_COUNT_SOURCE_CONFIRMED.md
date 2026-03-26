# Alpaca Trade Count Source — Confirmed (SRE)

**Authority:** [ALPACA_DATA_SURFACE_INVENTORY.md](./ALPACA_DATA_SURFACE_INVENTORY.md), [ALPACA_DATA_INTEGRITY_RESULTS.md](./ALPACA_DATA_INTEGRITY_RESULTS.md)

---

## Authoritative source

| Source | Path | Rationale |
|--------|------|-----------|
| **Primary** | `logs/exit_attribution.jsonl` | **Canonical closed-trade ledger** per MEMORY_BANK; one row per closed trade; self-contained PnL + exit intel |

---

## Counting method

1. **Filter:** Rows where `exit_ts` / `timestamp` ≥ **`activated_utc`** from `state/alpaca_diagnostic_promotion.json`.
2. **Deduplicate:** Use **canonical join key** `live:SYMBOL:entry_ts` (second-precision UTC) via `src/telemetry/alpaca_trade_key.normalize_symbol` + `normalize_time`.
3. **Count:** Unique canonical keys since activation.

**Implementation:**
```python
from src.telemetry.alpaca_trade_key import normalize_symbol, normalize_time

def _canonical_live_key(symbol, entry_ts):
    sym = normalize_symbol(symbol)
    ts = normalize_time(entry_ts)
    if not sym or not ts:
        return ""
    return f"live:{sym}:{ts}"
```

---

## Why not master_trade_log

- **ID namespace mismatch:** `master_trade_log` uses `live:*` but **join overlap is ~1/2204** (see integrity results).
- **Self-contained:** `exit_attribution` has all fields needed (symbol, entry_ts, exit_ts, pnl) without cross-file joins.

---

## Guarantees

| Property | Status |
|----------|--------|
| **Increments only on closed trades** | **Yes** — `exit_attribution.jsonl` contains only closed trades (one row per close) |
| **No dependency on master/unified joins** | **Yes** — single-file read; canonical key derived from exit row fields |
| **Idempotent** | **Yes** — set of unique keys is deterministic; re-counting same file yields same count |

---

*SRE — trade count source confirmed; implementation uses canonical keys from exit_attribution.*
