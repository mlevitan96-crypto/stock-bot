# Directional Intelligence — Replay & Backtest Readiness

**Purpose:** Ensure the replay engine can load intel snapshots and direction events, condition direction on any subset of intelligence, and run long-only / short-only / mixed and regime-conditioned backtests.

**Status:** Telemetry capture implemented; replay conditioning is specification-only (no live behavior changes).

---

## 1. Artifacts Captured (Telemetry Only)

| Artifact | Path | When |
|----------|------|------|
| Intel snapshot (entry) | `logs/intel_snapshot_entry.jsonl` | On position open (after mark_open) |
| Intel snapshot (exit) | `logs/intel_snapshot_exit.jsonl` | On exit (before append_exit_attribution) |
| Direction event | `logs/direction_event.jsonl` | At entry and exit |
| Entry snapshot state | `state/position_intel_snapshots.json` | Keyed by `SYMBOL:entry_ts` for exit deltas |
| Embed in attribution | `logs/attribution.jsonl` | Not at write time; entry attribution does not currently embed (optional future) |
| Embed in exit_attribution | `logs/exit_attribution.jsonl` | `direction_intel_embed` on each record |
| Embed in exit_event | `logs/exit_event.jsonl` | `direction_intel_embed` on each record |

---

## 2. Replay Engine Contract

The replay engine **SHOULD** be able to:

1. **Load intel_snapshot_entry.jsonl / intel_snapshot_exit.jsonl**
   - Match by symbol and timestamp (or entry_ts for exit).
   - Each line is JSON: `timestamp`, `event` (entry/exit), `premarket_intel`, `postmarket_intel`, `overnight_intel`, `futures_intel`, `volatility_intel`, `breadth_intel`, `sector_intel`, `etf_flow_intel`, `macro_intel`, `uw_intel`, `regime_posture`.

2. **Load direction_event.jsonl**
   - Each line: `timestamp`, `event_type` (entry/exit), `symbol`, `direction_components` (canonical list), `metadata` (includes `intel_deltas` at exit).

3. **Condition direction on any subset of intelligence**
   - Use `CANONICAL_DIRECTION_INTEL_COMPONENTS`: premarket_direction, postmarket_direction, overnight_direction, futures_direction, volatility_direction, breadth_direction, sector_direction, etf_flow_direction, macro_direction, uw_direction.
   - Each component has `raw_value`, `normalized_value`, `contribution_to_direction_score`.
   - Replay can: require N of M components to align (e.g. futures_direction + breadth_direction both up), or weight by contribution_to_direction_score.

4. **Test long-only, short-only, mixed**
   - Filter or override direction in replay: e.g. force all entries to long, or short when volatility_direction == "up" and futures_direction == "down".

5. **Test regime-conditioned direction**
   - Use `vol_regime`, `regime_posture` from snapshot; e.g. in crash regime allow only shorts or suppress longs.

6. **Test futures/breadth/vol-conditioned direction**
   - Use `futures_intel.futures_trend_strength`, `breadth_intel.adv_dec_ratio`, `volatility_intel.vol_regime` from snapshots to gate or weight direction in backtest.

---

## 3. Canonical Direction Components

Defined in `src/intelligence/direction_intel.py`:

```python
CANONICAL_DIRECTION_INTEL_COMPONENTS = [
    "premarket_direction",
    "postmarket_direction",
    "overnight_direction",
    "futures_direction",
    "volatility_direction",
    "breadth_direction",
    "sector_direction",
    "etf_flow_direction",
    "macro_direction",
    "uw_direction",
]
```

Each component in `direction_components` has:
- `raw_value`
- `normalized_value` (-1, 0, or 1 for down/flat/up)
- `contribution_to_direction_score`

---

## 4. Entry→Exit Intel Deltas

Stored in `direction_event.jsonl` at exit under `metadata.intel_deltas` (and in `direction_intel_embed.intel_deltas` in exit_attribution/exit_event):

- `futures_direction_delta`
- `vol_regime_entry` / `vol_regime_exit`
- `breadth_adv_dec_delta`
- `sector_strength_delta`
- `macro_risk_entry` / `macro_risk_exit`
- `overnight_volatility_delta`

Replay can use these to study how regime/breadth/vol changed during the trade and correlate with PnL.

---

## 5. No Live Behavior Changes

This design is **telemetry and analysis only**. Entry logic, exit logic, and governance are unchanged. Direction in live trading continues to come from flow sentiment (BULLISH/BEARISH); the new intelligence is captured for replay and board review only.
