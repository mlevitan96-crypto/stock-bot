# Exit quality end-to-end trace (2026-02-18)

## 1) Where exit quality is computed

- **main.py** → `log_exit_attribution()` (around 2170–2226) calls `compute_exit_quality_metrics()` from `src/exit/exit_quality_metrics.py`.
- **Input:** `high_water = (info.get("high_water") or entry_price)`. So **info["high_water"]** must be set by the caller; otherwise we default to entry_price → MFE = 0 → profit_giveback = None.

## 2) Inspection of logs/exit_attribution.jsonl (droplet)

- **Total lines in file:** 2000
- **Sample (last 200 lines):** 200 lines parsed.
- **Records with exit_quality_metrics present:** 0
- **Records with profit_giveback non-null:** 0
- **Records with mfe non-null:** 0

### Sample records WITH profit_giveback
```json
[]
```

### Sample records with exit_quality_metrics but WITHOUT profit_giveback
```json
[]
```

## 3) Why giveback is N/A

- **high_water** is not stored in exit_attribution.jsonl; it is only used inside `log_exit_attribution` to compute MFE. If the **caller** does not set **info["high_water"]**, we use `entry_price` → MFE = 0 for long → no giveback.
- **Root cause:** The two call sites (displacement exit ~5545, time/trail exit ~7227) pass **info** from `self.opens.get(symbol, {})` or similar; **info** does not include **high_water** unless the executor has been updating it in opens/metadata. The executor tracks **self.high_water[symbol]** separately but never injects it into **info** before calling `log_exit_attribution`.
- **Fix:** Before each `log_exit_attribution(..., info=info, ...)`, set `info["high_water"] = self.high_water.get(symbol, info.get("high_water") or entry_price)` so that giveback can be computed when the position had upside.
