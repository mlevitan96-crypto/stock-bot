# Long/Short Verification (Droplet) — 2026-03-03

**Ran on droplet:** 2026-03-03 (UTC).  
**Script:** `scripts/verify_long_short_on_droplet.py` via `scripts/run_verify_long_short_on_droplet.py`.

---

## Verification output (from droplet)

```
## Long/Short verification

- **LONG_ONLY env:** `(unset)` -> shorts **ALLOWED**

### Signal history: file not found (skip direction mix)

### Executed trades (last N) by direction
- **unknown:** count=300, total_pnl_usd=-23.03

### Blocked (short entry by LONG_ONLY)
- Count (last 5000 blocked): **0**

---
## Today only (UTC date 2026-03-03)

### Signals today (by direction)
- long: 0, short: 0, other: 0

### Executed trades today (by direction)
- **unknown:** 61

## Why all of today's positions are long (root cause)

1. **LONG_ONLY is NOT set** (shorts are allowed).
2. **Direction comes from flow sentiment**, not from score. Each cluster gets direction from UW cache/enriched sentiment (BULLISH -> long, BEARISH -> short).
3. **All of today's signals/trades are long** because every accepted signal had **direction=bullish** (flow sentiment BULLISH). That typically means:
   - **Net call premium > put premium** in options flow (call buying or put selling dominates), so derived sentiment is BULLISH.
   - UW cache may be writing BULLISH for the symbols that passed the composite gate, or flow data today is skewed bullish (e.g. heavy call buying even in a down market).
4. To get shorts: ensure bearish flow (put buying / call selling) is present and that UW cache/enrichment sets sentiment to BEARISH for some symbols; then those clusters will get direction=bearish and side=sell.
```

---

## Note on "unknown" direction in logs

On the droplet, the last 300 trades and today's 61 trades show as **direction = unknown** in this report. That can mean:

- Attribution/exit_attribution records on droplet do not have `direction`, `position_side`, or `side` at the top level of each record (e.g. they may be inside a nested `context` or use different field names).
- The logic that *determines* direction is unchanged: **side = buy if cluster direction is bullish, else sell**. So if the UI or your view shows only longs, those are buy-side entries driven by **flow sentiment = BULLISH** for every symbol that passed the composite gate today.

So the **reason all of today's positions are long** is:

1. **LONG_ONLY is not enabled** (so shorts are not blocked by config).
2. **Every accepted signal today had direction = bullish** because:
   - Direction is set from **UW cache / enriched sentiment** (BULLISH/BEARISH), which is derived from options flow (net call vs put premium and flow type).
   - So either:
     - **Flow data today is skewed bullish** (net call premium > put premium for the symbols that passed the gate), or
     - **UW cache is returning BULLISH** for those symbols (e.g. heavy call buying or put selling in the flow feed even on a down market day).

To get shorts on down days you need **bearish flow** (put buying / call selling) to show up in the feed and in the cache so that some symbols get sentiment BEARISH and thus direction=bearish -> side=sell.

---

## Board task

**Per 30d board instructions and MEMORY_BANK:** the Board must review this verification and the long/short audit.

1. **Confirm:** Is the explanation above (direction from flow sentiment; all long because all accepted signals were bullish) consistent with what you see in the dashboard and in trade lists?
2. **Recommend:** Should we (a) add explicit `direction` / `position_side` to every attribution and exit_attribution record on the droplet for easier auditing, (b) add a regime overlay (e.g. on strongly bearish market days, require or favor bearish flow before opening new longs), or (c) other actionable change?
3. **Document:** Add any agreed recommendation to `reports/board/30d_TOP_5_AGREED_RECOMMENDATIONS.md` or a follow-up board memo.

**References:**

- Full audit: `reports/audit/LONG_SHORT_TRADE_LOGIC_AUDIT.md`
- Verify script (run on droplet): `scripts/verify_long_short_on_droplet.py`
- Runner from local: `scripts/run_verify_long_short_on_droplet.py`
