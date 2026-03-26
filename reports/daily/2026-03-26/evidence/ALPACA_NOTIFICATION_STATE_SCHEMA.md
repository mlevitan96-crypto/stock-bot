# Alpaca Trade Notification State Schema (SRE)

**File:** `state/alpaca_trade_notifications.json`

---

## Schema

```json
{
  "promotion_tag": "PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS",
  "activated_utc": "2026-03-20T00:22:37Z",
  "notified_100": false,
  "notified_500": false,
  "last_count_utc": "2026-03-20T00:22:37Z",
  "last_count": 0
}
```

---

## Fields

| Field | Type | Purpose |
|-------|------|---------|
| `promotion_tag` | string | Links to `state/alpaca_diagnostic_promotion.json` |
| `activated_utc` | ISO 8601 UTC | Filter trades ≥ this timestamp |
| `notified_100` | boolean | **true** after 100-trade message sent |
| `notified_500` | boolean | **true** after 500-trade message sent |
| `last_count_utc` | ISO 8601 UTC | Last time count was computed (for debugging) |
| `last_count` | integer | Last computed count (for debugging) |

---

## Atomic writes

**Method:** Write to temp file, then `os.replace()` (atomic on POSIX).

```python
import json
import os
from pathlib import Path

def _atomic_write_state(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
```

---

## Idempotent updates

- **Read** current state (or create default if missing).
- **Compute** current trade count.
- **Update** only `notified_*` flags when threshold crossed.
- **Write** atomically.

**Safe to run repeatedly:** If `notified_100 == true`, 100-trade message will **not** send again even if script runs multiple times.

---

## Initialization

If file missing, initialize from `state/alpaca_diagnostic_promotion.json`:
- Copy `promotion_tag` and `activated_utc`.
- Set `notified_100 = false`, `notified_500 = false`.
- Set `last_count_utc` and `last_count` to current values.

---

*SRE — state schema ensures one notification per threshold.*
