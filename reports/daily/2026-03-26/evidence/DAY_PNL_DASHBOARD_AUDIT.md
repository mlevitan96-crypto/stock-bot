# Day P&L Dashboard — Calculation Review & Audit

**Date:** 2026-03-05  
**Scope:** Confirm how dashboard "Day P&L" is calculated and whether it reflects actual exit P&L or total equity change. Verification run on droplet (state + attribution); reconciliation endpoint and code reviewed.

---

## 1. How Day P&L is calculated (code)

**Source:** `dashboard.py` → `/api/positions` → `_api_positions_impl()` (lines 4126–4149).

| Step | Logic |
|------|--------|
| **Default** | `day_pnl = account.equity - account.last_equity` (Alpaca broker “day” P&L). |
| **Override** | If `state/daily_start_equity.json` exists and its `date` equals **today (UTC)**, then `day_pnl = account.equity - daily_start_equity`. |

So the dashboard **Day P&L** is:

- **Session baseline (when file exists for today):**  
  `equity_now - daily_start_equity`  
  i.e. **total equity change since the session baseline was written** (first risk check of the day in `main.py` / `risk_management.set_daily_start_equity`).
- **Otherwise:**  
  `equity_now - last_equity`  
  i.e. Alpaca’s broker “day” P&L.

**Conclusion:** Day P&L is **not** “sum of exit position P&L for the day.” It is **total equity change** for the day (realized + unrealized): closed trade P&L plus mark-to-market on open positions since the baseline time.

---

## 2. Why “losing over 100 every day” can be correct

- **Session baseline** is set once per day (e.g. 14:30 UTC when the bot first runs). So “Day P&L” = change in account equity since that moment.
- That includes:
  - Realized P&L from any positions **closed** today.
  - **Unrealized P&L** on positions still open (mark-to-market since baseline).
- If you have several open shorts and the market rallies, the **unrealized** loss can be large (e.g. -$100+). So a daily -$100+ on the dashboard can be accurate even if you had no (or small) **realized** losses from exits.

So:

- **Dashboard Day P&L** = total equity change (realized + unrealized). **Calculation is consistent with this definition.**
- **“Actual exit P&L for the day”** = sum of `pnl_usd` in `logs/attribution.jsonl` for **close/scale** events with `ts` today. That is a different number.

---

## 3. How to see “actual exit P&L” and reconcile

- **Reconciliation endpoint:**  
  `GET /api/pnl/reconcile?date=YYYY-MM-DD`  
  Returns:
  - `broker_day_pnl` = equity_now - last_equity  
  - `window_pnl` = equity_now - daily_start_equity (when file exists for that date)  
  - `attribution_closed_pnl_sum_logged` = sum of `pnl_usd` in `logs/attribution.jsonl` for records with `ts` on that date (all attribution lines for the day; close/scale events carry the realized P&L).  
  So you can compare:
  - **Dashboard Day P&L** ≈ `window_pnl` (or broker_day_pnl if no session file).
  - **“Exits only”** ≈ `attribution_closed_pnl_sum_logged` (and the dashboard’s number can differ by the day’s unrealized P&L).

- **Docs:** `reports/audit/DASHBOARD_PNL_AND_SYMBOL_UNIVERSE.md` and `docs/TRADING_DASHBOARD.md` describe the same: Day P&L is session/broker equity change; reconciliation is the way to compare with attribution.

---

## 4. Droplet verification (2026-03-05)

- **state/daily_start_equity.json** on droplet:
  - `date`: `"2026-03-05"`
  - `equity`: `48490.28`
  - `timestamp`: `"2026-03-05T14:30:33.205297+00:00"`
- **logs/attribution.jsonl:** Tail shows 2026-03-05 records; recent lines are **opens** (`trade_id` `open_*`) with `pnl_usd: 0.0`. Closes would have non-zero `pnl_usd`.

So on the droplet:

- Dashboard Day P&L = **current_equity - 48490.28** (session baseline).
- If current equity is e.g. ~48350, Day P&L ≈ **-$140** (realized + unrealized). That is consistent with the code and the definition above.

---

## 5. Accuracy verdict

| Question | Answer |
|----------|--------|
| Is Day P&L **calculated correctly** for what it represents? | **Yes.** It is equity_now minus session baseline (or broker last_equity) as implemented. |
| Does it represent **actual exit positions P&L only**? | **No.** By design it is **total equity change** (realized + unrealized). |
| Can “losing over 100 every day” be accurate? | **Yes.** Unrealized mark-to-market on open positions can easily be -$100+ per day. |
| How to confirm “exits only” P&L? | Use **`/api/pnl/reconcile?date=YYYY-MM-DD`** and compare `attribution_closed_pnl_sum_logged` to `window_pnl`; the difference is unrealized + timing. |

---

## 6. Recommendation

- **No change needed** if the intent is “equity change since session start (or broker day).” The implementation and droplet state are consistent with that.
- If you want a **separate “Realized P&L (exits today)”** on the dashboard, that would require a new metric (e.g. sum of `pnl_usd` from attribution for today’s close/scale events) and a small dashboard/API change. The current “Day P&L” label matches **total** day P&L (realized + unrealized) per MEMORY_BANK and existing docs.

---

*Audit complete. Day P&L calculation is correct for its definition; use reconciliation to compare with actual exit P&L.*
