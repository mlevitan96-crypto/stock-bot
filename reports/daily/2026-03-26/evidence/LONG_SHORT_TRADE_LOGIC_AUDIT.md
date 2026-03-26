# Long vs Short Trade Logic — Audit & Verification

**Purpose:** Confirm how the bot determines long vs short entries, that both directions are calculated and allowed (unless LONG_ONLY is set), and how to verify on droplet and with the board.

**Date:** 2026-03-03

---

## 1. How direction is determined (not score-based)

**Important:** Direction (long vs short) is **not** derived from “score ≥ 3.0 = long”. It comes from **flow sentiment**.

### Pipeline

1. **Options flow → sentiment**
   - Raw flow trades are normalized in `main.py` (`_normalize_flow_trade`):
     - Call buying or put selling → **bullish**
     - Call selling or put buying → **bearish**
   - Per-trade direction is stored on each normalized trade.

2. **UW cache → enriched sentiment**
   - UW cache holds per-symbol `sentiment` (BULLISH / BEARISH / NEUTRAL) and optionally `conviction`.
   - If cache has no sentiment/conviction, `uw_enrichment_v2._derive_conviction_from_flow_trades()` derives it from **net call vs put premium**:
     - `net_premium = call_premium - put_premium`
     - `net_premium > 10_000` → **BULLISH**
     - `net_premium < -10_000` → **BEARISH**
     - Else → **NEUTRAL** (with small conviction if total premium > 0)
   - So sentiment is driven by **options flow** (call vs put premium), not by a numeric score threshold.

3. **Composite → cluster direction**
   - When building clusters from composite (e.g. `main.py` composite_v3 path), cluster `direction` is set from **enriched sentiment**:
     - `flow_sentiment = enriched.get("sentiment", "NEUTRAL")` → lowercased to `bullish` / `bearish` / `neutral`.
     - Cluster gets `"direction": flow_sentiment`.

4. **Cluster → order side**
   - In the entry loop: `direction = c.get("direction", "unknown")`.
   - Side is set as: **`side = "buy" if c["direction"] == "bullish" else "sell"`** (main.py ~9286).
   - So: **bullish → buy (long), bearish → sell (short)**.

5. **LONG_ONLY safety**
   - Config: `LONG_ONLY = get_env("LONG_ONLY", "false").lower() == "true"` (main.py ~347).
   - If `LONG_ONLY` is true, any **short entry** (`side == "sell"`) is **blocked** and logged as `long_only_blocked_short_entry`.
   - Default is **false** (shorts allowed when sentiment is bearish).

### Summary table

| Source              | What sets it                    | Resulting trade      |
|---------------------|----------------------------------|----------------------|
| Flow sentiment      | Call vs put premium / flow type | BULLISH / BEARISH    |
| Enriched sentiment  | Cache or _derive_conviction_*   | bullish / bearish   |
| Cluster direction   | From enriched sentiment         | bullish / bearish   |
| Order side          | direction == bullish → buy      | Long vs short       |
| LONG_ONLY=true      | Blocks side=="sell"            | Only longs allowed  |

So if you “see all longs” while the market is down, possible causes are:

- **LONG_ONLY=true** on droplet (shorts explicitly disabled).
- **Flow/cache skew:** Net call premium consistently > put (e.g. heavy call buying even in down market) → sentiment stays BULLISH.
- **Data/aggregation:** UW daemon or cache writing sentiment that is mostly BULLISH.

The **score ≥ 3.0** rule appears in strategy summaries and backtests for **PnL sign / classification** (e.g. “long if score ≥ 3.0 else short” in sims). It is **not** the source of entry direction in the live pipeline; entry direction is flow-sentiment → cluster direction → side.

---

## 2. Where in code to verify

| Check | Location |
|-------|----------|
| LONG_ONLY config | `main.py` ~347: `Config.LONG_ONLY` |
| Short entry block | `main.py` ~9494–9535: `if Config.LONG_ONLY and side == "sell"` |
| Side from direction | `main.py` ~9286: `side = "buy" if c["direction"] == "bullish" else "sell"` |
| Cluster direction (composite) | `main.py` ~11344–11346: `"direction": flow_sentiment` from enriched |
| Sentiment derivation | `uw_enrichment_v2.py` ~19–47: `_derive_conviction_from_flow_trades` (net call/put premium) |
| Direction from sentiment (v2) | `uw_composite_v2.py` ~1464–1466: `direction = "bullish" if sent == "BULLISH" else ...` |

---

## 3. Droplet verification

### 3.1 Environment

- On droplet, check: **`LONG_ONLY`**
  - If `LONG_ONLY=true` → shorts are disabled by design.
  - If unset or `false` → both longs and shorts are allowed; direction comes from flow sentiment.

### 3.2 Signal / direction mix

- **Signal history** (e.g. `logs/signal_history.jsonl` if present): count `direction` / `direction_normalized` by `bullish` vs `bearish` over the last 24–48 hours.
- **Blocked trades** (`state/blocked_trades.jsonl`): grep for `long_only_blocked_short_entry`. If you see many, LONG_ONLY is on or was on when those were logged.
- **Recent trades**: From `logs/attribution.jsonl` or `logs/exit_attribution.jsonl`, count by `direction` or `position_side` (long vs short) to see actual executed mix.

### 3.3 Script

- **On droplet:** `cd /root/stock-bot && python3 scripts/verify_long_short_on_droplet.py --base-dir . --last 200`
- **From local (run on droplet via SSH):** `python scripts/run_verify_long_short_on_droplet.py --last 200`

The script reports:
- Whether LONG_ONLY is enabled (from env),
- Recent signal direction mix (from signal history if available),
- Last N trades’ direction and PnL from attribution/exit_attribution,
- Count of blocked short entries (long_only_blocked_short_entry).

---

## 4. Board / 30-day review

- **30-day comprehensive review** (`scripts/build_30d_comprehensive_review.py`) can be extended to include:
  - Count and PnL by **direction** (long vs short) from attribution and exit_attribution.
  - So the board can see if we’re mostly long, mostly short, or balanced, and how each side is performing.
- **Board personas** should consider:
  - When market is “severely down,” should we expect more bearish flow and thus more short candidates?
  - If all executed trades are long, is LONG_ONLY on, or is flow/cache sentiment skewed bullish?
  - Recommendations: e.g. “Verify LONG_ONLY on droplet,” “Audit UW/cache sentiment distribution,” “Add direction mix to 30d board bundle.”

---

## 5. Adjustments to consider

1. **Confirm LONG_ONLY on droplet**  
   If you want both longs and shorts, ensure `LONG_ONLY` is not set to `true` in the droplet environment.

2. **Inspect flow/cache sentiment**  
   If LONG_ONLY is false but you still see only longs, check:
   - UW cache: distribution of `sentiment` (BULLISH vs BEARISH) per symbol.
   - Raw flow: ratio of call vs put premium and sweep direction; confirm bearish flow is present and making it into cache/enriched.

3. **Regime / market context**  
   The composite uses regime and alignment (e.g. `uw_composite_v2` alignment dampening). It does not force direction from “market down → shorts only”; direction remains from flow sentiment. If desired, you could add a **review or overlay** (e.g. “in strongly bearish regime, require bearish flow before allowing long” or “highlight when all signals are long in a down day”) without changing the core rule that direction = flow sentiment.

4. **Board 30d bundle**  
   Add long/short breakdown (counts and PnL) to the 30d review so the board can explicitly review direction mix and performance.

---

## 6. References

- Entry loop and side: `main.py` ~9286, ~9494–9535.
- Cluster direction from composite: `main.py` ~11288–11346.
- Sentiment derivation: `uw_enrichment_v2.py` ~19–47, ~464–477.
- Direction in composite v2: `uw_composite_v2.py` ~1464–1466.
- Flow normalization (per-trade direction): `main.py` ~2772–2781.
