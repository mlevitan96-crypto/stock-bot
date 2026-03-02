# Dashboard: Day P&L, Current Score, and Symbol Universe

## Day P&L

**Source (fixed):** The dashboard `/api/positions` now uses **session-based Day P&L** when available for accurate data.

- **Primary:** `equity_now - daily_start_equity` from `state/daily_start_equity.json` when the file exists and the stored date matches today (UTC). This is the same baseline used by `risk_management.calculate_daily_pnl()` and is written when the bot starts or on first check each day.
- **Fallback:** `account.equity - account.last_equity` (broker “day” P&L) when the session file is missing or for a different date.

**Why broker Day P&L can look wrong:** Alpaca’s `last_equity` is from the broker’s day boundary (e.g. previous close or session start). If you expect “P&L since I started the bot today,” that is the session baseline, not the broker number. The dashboard now prefers the session baseline so the displayed Day P&L matches that definition.

**Reconciliation:** Use `/api/pnl/reconcile?date=YYYY-MM-DD` to compare broker day P&L, session window P&L, and attribution closed P&L for a given date.

---

## Current / Exit Score on Open Positions

**How it’s computed:** For each open position, the dashboard gets the **current composite score** from:

1. **Preferred:** `state/signal_strength_cache` (written by the main engine’s open-position refresh).
2. **Fallback:** Live computation: load `data/uw_flow_cache.json`, enrich the symbol with `uw_enrichment_v2.enrich_signal()`, then `uw_composite_v2.compute_composite_score_v3()` (alias of `compute_composite_score_v2`).

**Why “Current” can be much lower than “Entry” (e.g. 0.15 vs 4.80):**

- **Entry score** is stored in position metadata at fill time (or recovered from attribution).
- **Current score** is the **live** composite from today’s UW cache and enrichment. If there is little or no recent flow for that symbol, or the symbol was opened from an **injected test** (e.g. `INJECT_SIGNAL_TEST=1`), the live composite can be low (e.g. 0.15) while the entry score was high (e.g. 4.0+).

**Dashboard behavior:**

- When **entry_score ≥ 3** and **current_score < 0.5**, the dashboard marks the current score as **likely stale** and shows “(stale?)” with a tooltip: “Current score may be stale (low flow data for this symbol).” This avoids misreading a low live composite as “exit scoring is wrong” when the cause is missing/stale flow or an injected test position.

---

## Symbol Universe and “Only SPY” Orders

**Where the universe comes from:**

- **Composite scoring** in `main.py` runs over symbols present in **`data/uw_flow_cache.json`** (keys that do not start with `_`). The UW ingestion / daemon populates this cache; symbols that never get UW flow never enter the composite loop.
- **Entry gates** (e.g. `should_enter_v2`, expectancy, UW defer) then filter which of those symbols are allowed to trade.

**Why you may have seen only SPY so far:**

1. **Inject test was enabled:** With `INJECT_SIGNAL_TEST=1`, when the composite loop produces **zero** clusters (no symbol passes the gates), the engine injects a **synthetic** cluster for **SPY** with score 4.0 so the execution path can be tested. The two SPY orders you saw were very likely from this injected test, not from natural composite signals.
2. **Natural signals were 0:** Before the freshness/conviction fixes, no symbol was reaching the entry threshold (e.g. 2.7), so `clusters=0` every cycle. With the inject on, the only “candidate” was the injected SPY cluster.

**What to do:**

- **Turn off the inject test** on the droplet: set `INJECT_SIGNAL_TEST=0` (or unset) and restart so only real composite signals can produce orders.
- **Other symbols** will only trade when:
  - They appear in `data/uw_flow_cache.json`,
  - Their composite score (after enrichment and v2 adjustments) is ≥ threshold (e.g. 2.7),
  - They pass UW defer, expectancy, and other gates.

**Verification:**

- Check droplet env: `INJECT_SIGNAL_TEST` should be 0 or unset for normal operation.
- Check cache: number of symbols in `uw_flow_cache.json` (excluding `_*` keys) is the scoring universe.
- See `reports/audit/TRADE_LOGIC_SIGNAL_TO_EXECUTION_TRACE.md` and `reports/audit/ALL_GATES_CHECKLIST.md` for the full path and gate list.
