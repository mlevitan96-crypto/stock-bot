# Alpaca Fast-Lane: Go-Forward 25-Trade Promotion Experiment (Design)

## Goal (High Level)

- **Go-forward only:** Use the *next* 25 trades (as they happen), not historical data.
- **25-trade promotions:** Every 25 trades, evaluate and **promote** a strategy/config (entries, exits, signals, etc.). Repeat for 20 windows → 500 trades.
- **Outcome:** After 500 trades, we have optimized for the best strategies/signals across entries, exits, and everything the bot uses to be profitable.
- **Telegram:** After each 25-trade window, fire off **what was promoted** (not just “best candidate” from ranking).

So: **sequential, go-forward optimization with a real promotion step and clear Telegram messaging.**

---

## Does This Make Sense?

**Yes.** It’s a clear experiment: 20 promotion steps of 25 trades each, go-forward only, with promotion decisions and Telegram after each step.

---

## Are We Set Up To Do This Today?

**No.** The current fast-lane is **analysis-only** and **backward-looking**. Here’s the gap.

### What We Have Now

| Aspect | Current behavior |
|--------|-------------------|
| **Data** | Reads *entire* `exit_attribution.jsonl` from the top. Processes the **next** 25 lines from where we left off → effectively **historical** (oldest unprocessed first). |
| **Promotion** | **None.** We only *rank* candidates and record “best candidate.” We do **not** write to config, strategy, or signals. |
| **Telegram** | Sends “best candidate” and PnL. Does **not** say “promoted X” or drive any change. |
| **Go-forward** | No. Windows are “next 25 in the log,” not “next 25 trades *after* an epoch start.” |

So: we are **not** doing go-forward 25-trade promotions with real promotion actions and promotion-focused Telegram.

### What We’d Need for Your Goal

1. **Go-forward windowing**
   - Define an **epoch start** (e.g. timestamp or “trade count since activation”).
   - Only count **trades that close after** that epoch start.
   - Window 1 = trades 1–25 after epoch, window 2 = 26–50, …, window 20 = 476–500.

2. **Promotion mechanism**
   - After each 25-trade window:
     - Evaluate (e.g. PnL, metrics, or a small candidate set).
     - **Promote** something: e.g. write the chosen strategy/config/signals into the place the bot reads (config file, overlay, or “active strategy” state).
   - The bot then uses that promoted config for the *next* 25 trades (or until the next promotion).

3. **Telegram = “what was promoted”**
   - After each 25-trade activity, send: e.g. “Promoted: [strategy/config/signal X] for next 25 trades” (and optionally PnL of the window that led to it).

4. **Governance / safety**
   - Clear rules for what can be promoted (e.g. only from an approved candidate list).
   - Optional: CSA/SRE review of promotion logic and write paths (still align with MEMORY_BANK “no execution gating” if promotions are explicitly authorized).

---

## Summary

- **Goal:** Go-forward, 25-trade promotions for 500 trades, with Telegram saying what was promoted after each 25-trade step. **Makes sense.**
- **Current setup:** Shadow-only, historical-style windows, no promotion, Telegram reports “best candidate” only. **Not set up for the above.**
- **To get there:** Add epoch-based go-forward windowing, a defined promotion step (with writes to config/state the bot uses), and Telegram text that reports the **promotion** after each 25-trade activity.

If you want to proceed, next step is to lock the **promotion surface** (what we’re allowed to change: e.g. exit overlay, signal weights, single strategy flag) and then implement go-forward windowing + promotion step + Telegram copy.
