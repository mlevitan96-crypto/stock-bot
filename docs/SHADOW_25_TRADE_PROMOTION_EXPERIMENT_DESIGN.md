# Shadow 25-Trade Promotion Experiment — Full Design

**Goal:** A self-contained shadow experiment that, every 25 trades (go-forward only), evaluates “every angle” and promotes the most profitable one. After 500 trades we have 20 promotion steps and a record of what would have been best at each step — with **zero** interaction with live trading or other areas. CSA and SRE help design and review.

**Experiment name:** Alpaca Fast-Lane (kept as the only experiment with this concept).

---

## Decisions (2026-03-14)

| Question | Decision |
|----------|----------|
| **Angles** | As many as we review in regular analysis — thorough review and promotion strategy (see Section 4). |
| **Epoch / start** | Start “now” = **Monday when market opens** (2026-03-17). Historical run **cancelled**: only trades with exit timestamp ≥ epoch are considered. |
| **Experiment root path** | **CSA and SRE to choose** the best path: `state/shadow_promotion_experiment/` vs `experiments/shadow_25t_promotion/` (or equivalent). |
| **Name** | Keep **Alpaca Fast-Lane** in Telegram and dashboard. |

---

## 1. Opinion: How to Implement This in the Best Way

**Recommendation:**

- **Keep it fully isolated:** One directory tree, one ledger, one config. No reads from main experiment ledger or live config; no writes to them. The “promotion” is **inside the experiment only** (we record “promoted = X” and optionally Telegram it); we do **not** change what the live bot runs.
- **Go-forward from an epoch:** Only count trades whose **exit timestamp** is on or after an **epoch start**. That gives a clean “next 25 trades as they happen” without re-processing history.
- **Angles = dimensions we can attribute from logs:** Use only fields already present in `exit_attribution.jsonl` (and optionally other logs we agree to read). For each 25-trade window, aggregate PnL by each dimension (e.g. by strategy, by exit_reason, by regime), then pick the **single best-performing angle** for that window and call that the “promoted” one for the cycle.
- **One promotion per cycle:** At the end of each 25-trade window we output: “Promoted: &lt;angle&gt; (e.g. strategy:equity or exit_reason:profit_target) for cycle N.” Telegram and the experiment ledger both say **what was promoted**, plus window PnL and optional runner-ups.
- **CSA/SRE in the design:** CSA signs off on angle definitions and profit logic; SRE signs off on isolation, disk, and failure modes. Both are review-only; no execution gating.

---

## 2. Scope and Isolation

| Rule | Meaning |
|------|--------|
| **Own area** | All experiment state and config live under a single root (e.g. `state/shadow_promotion_experiment/` or `experiments/shadow_25t_promotion/`). |
| **Read-only from the rest of the world** | Only read from `logs/exit_attribution.jsonl` (and any other agreed log paths). No read from `state/governance_experiment_1_hypothesis_ledger_alpaca.json`, live config, or strategy config. |
| **Write-only to experiment area** | Writes only to the experiment directory (ledger, state, cycle artifacts, experiment config). No writes to main config, main ledger, or any path the live bot uses for execution. |
| **No live interaction** | “Promotion” is an internal label for the experiment (and for Telegram). It does **not** change live config, overlays, or strategy selection. |

---

## 3. Epoch and Go-Forward Windowing

- **Epoch start:** Set to **Monday 2026-03-17 market open** (e.g. `2026-03-17T13:30:00Z` for 9:30 AM ET). Only trades with `timestamp` (or `exit_timestamp`) **≥** that value are considered. **Historical run is cancelled:** no cycles are run on pre-epoch data.
- **Windows:** Among post-epoch trades only, we take them in chronological order. Window 1 = trades 1–25 after epoch, window 2 = 26–50, …, window 20 = 476–500.
- **Config:** `epoch_start_iso` in the experiment config; optional override so CSA/SRE can align with a specific open if needed.

---

## 4. Angles (What We Look At) — Robust Slice of Views (Implemented)

“Every angle” = every dimension we can **attribute from the logs** and aggregate PnL over. Each closed trade has exactly one value per dimension. **Implemented set (CSA/SRE can extend):**

| Angle | Source | Example values | Why it matters for profitability |
|-------|--------|----------------|-----------------------------------|
| **strategy** | `strategy_id`, `strategy`, `mode` | equity, wheel, unknown | Which strategy is making money. |
| **exit_reason** | `exit_reason`, `close_reason` | profit_target, time_exit, displacement, trailing_stop, signal_decay, session_end | Which exit type is most profitable. |
| **exit_regime** | `exit_regime` | RISK_ON, NEUTRAL, RISK_OFF, BEAR | Market regime at exit. |
| **entry_regime** | `entry_regime` | RISK_ON, NEUTRAL, RISK_OFF | Regime at entry. |
| **regime_transition** | entry vs exit regime | same, shift | Did regime change during the trade. |
| **sector** | `entry_sector_profile`, `exit_sector_profile` | TECH, BIOTECH, ENERGY, UNKNOWN | Which sectors are profitable. |
| **hold_bucket** | `time_in_trade_minutes` | short (&lt;60m), medium (60–240m), long (&gt;240m) | Optimal hold time. |
| **exit_score_band** | `v2_exit_score` | low (&lt;2), mid (2–5), high (&gt;5) | Exit quality vs PnL. |
| **time_of_day** | exit timestamp | morning, afternoon, close | Time-of-day effect. |
| **day_of_week** | exit timestamp | Mon, Tue, … | Day-of-week effect. |
| **exit_regime_decision** | `exit_regime_decision` | normal, … | Exit decision type. |
| **score_deterioration_bucket** | `score_deterioration` | low, mid, high | How much score fell before exit. |
| **replacement** | `replacement_candidate` | replaced, no_replacement | Displacement vs non-displacement. |
| **symbol** | `symbol` | AAPL, TSLA, … | Which symbols are profitable. |

For each 25-trade window we:

- For each dimension, aggregate **realized PnL** by value.
- Pick the **single (dimension, value)** with the **highest total PnL** in that window = **Promoted** (e.g. `exit_reason:profit_target`).
- Record `promoted_angle`, `promoted_dimension`, `promoted_value`, and `angle_rankings` (top 15) in the ledger; Telegram sends “Promoted: &lt;angle&gt;” and optional runner-ups.

**CSA/SRE:** Add dimensions (e.g. signal family, entry score band) when the data exists in logs; refine buckets as needed.

---

## 4b. Run-Time Flow and Notifications (Verification)

- **Cron:** Cycle script runs every 15 minutes; supervisor runs every 4 hours (see `scripts/install_fast_lane_cron_on_droplet.py`).
- **Strict 25-trade windows:** Each cycle uses exactly the next 25 post-epoch trades. The script only appends a ledger entry when `len(window) == 25`; it never creates a 24- or 26-trade cycle. Windows are consecutive: 1–25, 26–50, …, 476–500.
- **Telegram every 25 trades:** After each completed cycle the cycle script calls `notify_fast_lane_summary.py --kind cycle` with `--promoted` and `--runner-ups`. You get one Telegram per cycle (e.g. “🔬 Alpaca Fast-Lane (25-trade promotion)”, Cycle: cycle_0001, Promoted: …, Window PnL: …).
- **At 500 total trades:** The supervisor reads the ledger; when `total_trades >= 500` it sends **one** board summary via `notify_fast_lane_summary.py --kind board` (e.g. “📊 Alpaca Fast-Lane — Board Summary (500-trade supervisor)”, Total cycles: 20, Total trades: 500, Cumulative PnL, Top promoted angles). So you get a final Telegram at the 500-trade milestone. After that, no further cycles are created (no 21st window) until you optionally reset the epoch.

---

## 5. Cycle Logic (Per 25-Trade Window)

1. **Load experiment config** (epoch start, paths).
2. **Read exit log** and filter to trades with timestamp ≥ epoch start; sort by timestamp; take only up to the next 25 **not yet processed** (using `last_processed_trade_index` or equivalent).
3. If we have fewer than 25 new trades, exit (no cycle this run).
4. **Attribute each trade** to strategy, exit_reason, regime (normalize missing to `unknown`).
5. **Aggregate PnL by angle:**  
   - By strategy: sum PnL per strategy.  
   - By exit_reason: sum PnL per exit_reason.  
   - By regime: sum PnL per regime.
6. **Pick winner:** Across all (dimension, value) pairs, choose the one with highest total PnL in this window. That is **“promoted”** for this cycle.
7. **Persist:** Append one cycle record to the experiment ledger (cycle_id, trade range, window PnL, promoted angle, optional runner-ups, timestamp).
8. **Update state:** e.g. `last_processed_trade_index` (or equivalent) so the next run takes the next 25.
9. **Telegram:** Send a single message: e.g. “Shadow promotion (cycle N): Promoted **&lt;dimension&gt;:&lt;value&gt;** (window PnL $X.XX). No live impact.”
10. **Optional:** Write cycle artifacts (summary.json, trades_snapshot.json) under the experiment dir.

---

## 6. Experiment Directory Layout

**CSA and SRE to choose the best path.** Two options:

- **Option A:** `state/shadow_promotion_experiment/` (or reuse existing `state/fast_lane_experiment/` for Alpaca Fast-Lane). State may be gitignored; epoch and paths in config there.
- **Option B:** `experiments/shadow_25t_promotion/` (or `experiments/alpaca_fast_lane/`) so layout is in repo and versioned.

Proposed layout (path TBD by CSA/SRE):

```
<experiment_root>/
├── config.json                     # epoch_start_iso (e.g. 2026-03-17T13:30:00Z), optional angle toggles
├── ledger.json                     # array of cycle records
├── state.json                      # last_processed_trade_index (post-epoch), total_trades_processed, last_cycle_id
├── cycles/
│   ├── cycle_0001/
│   │   ├── summary.json
│   │   └── trades_snapshot.json
│   └── ...
└── logs/
    └── shadow_promotion.log
```

- **config.json:** Epoch start; optionally which angles to enable.
- **ledger.json:** One entry per cycle: cycle_id, trade range, trade_count (25), window_pnl_usd, **promoted_angle** (e.g. `"exit_reason:profit_target"`), optional rankings, timestamp_completed.
- **state.json:** Cursor for “next 25” (among post-epoch trades only) and metadata.

No other state or config is read or written.

---

## 7. CSA Role (Design Review)

- **Angle definitions:** Confirm that strategy, exit_reason, and regime are the right “angles” for the first version, and that we normalize missing values to `unknown` in a consistent way.
- **Profit logic:** Confirm that we use realized PnL (from exit_attribution) and that “best” = highest sum PnL in the window for that angle. No double-counting, no use of unrealized or off-log data.
- **No live impact:** Confirm that promotion is only recorded and messaged; no code path writes to live config or strategy selection.
- **Optional:** Review Telegram wording so it’s clear this is shadow-only and “Promoted” means “winner of this 25-trade window in the experiment.”

CSA does **not** gate execution; review is advisory and for correctness/clarity.

---

## 8. SRE Role (Design Review)

- **Isolation:** Confirm that the only reads are from agreed log paths and the only writes are under the experiment directory. No shared state with live trading or main experiment ledger.
- **Disk and retention:** Confirm ledger and cycle artifacts have bounded size (e.g. 20 cycles × small JSON). Optional: retention or pruning policy for old cycle dirs.
- **Cron and idempotency:** If we run every 15 minutes, confirm that “fewer than 25 new trades” is a no-op and that we don’t double-process the same trade (state cursor is updated only after a full 25-trade cycle).
- **Failure modes:** If the script crashes mid-run, state is only updated after a full cycle; so we might re-process the same 25 trades on next run. Optional: make the “take next 25” and “write state” steps atomic (e.g. write state to a temp file and rename), so we never advance the cursor unless the cycle is fully written.

SRE does **not** gate execution; review is for operability and safety.

---

## 9. Telegram Contract

After each completed 25-trade cycle, send **exactly one** message, for example:

- **Title:** e.g. “Alpaca Fast-Lane (25-trade promotion, no live impact)”
- **Cycle:** cycle number (e.g. 1–20)
- **Promoted:** &lt;dimension&gt;:&lt;value&gt; (e.g. `exit_reason:profit_target`)
- **Window PnL:** $X.XX for this 25-trade window
- **Optional:** “Runner-ups: …” or “Next 25 trades: …”
- **Closer:** “Shadow only; no live config changes.”

Same TELEGRAM_* env as today; no new channels required.

---

## 10. After 500 Trades (20 Cycles)

- **Experiment summary:** We have 20 cycle records, each with a “promoted” angle and window PnL. We can compute cumulative PnL and counts per promoted angle (e.g. “exit_reason:profit_target was promoted in 8 of 20 cycles”).
- **Optional:** A small “supervisor” script (or extend the existing one) that at 500 trades emits a short summary (e.g. to Telegram or to a file under the experiment dir): top promoted angles, total trades, cumulative PnL, and a one-line CSA/SRE note that this was shadow-only.
- **No automatic change to live:** Findings inform future decisions; they do not auto-update live config.

---

## 11. Next Steps

- **Implement:** Go-forward windowing (epoch filter), full angle set (strategy, exit_reason, regime, sector, hold_bucket, exit_score_band), “promoted” winner per cycle, and Telegram “Promoted: …” using the Alpaca Fast-Lane name.
- **Stop historical run:** Epoch set to Monday 2026-03-17 market open; current cycle script will be updated to process only trades with timestamp ≥ epoch, so no further cycles run on pre-epoch data.
- **CSA/SRE:** (1) Choose experiment root path. (2) Review and optionally extend the angle list. (3) Review isolation and failure modes before/after implementation.
