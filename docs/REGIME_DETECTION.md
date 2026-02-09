# Regime Detection

## Overview

Regime detection provides market context (bull, bear, chop, crash and equivalents) for scoring and sizing. **Regime is a modifier only**: it may influence position sizing, signal weighting, or filter strength. It must **never** be used as a hard gate that blocks all trading.

## Contract

- **Modifier only:** Regime can adjust sizing, filters, or preferences. It must **not** set trade volume to zero, disable entire strategies, or block all entries.
- **When regime is UNKNOWN:** Use a safe default (e.g. neutral sizing, conservative filters). Do **not** block trades.
- **Configuration:** `ENABLE_REGIME_GATING` defaults to `false`. When `true`, the engine may block entries based on regime; operators should leave it `false` to satisfy the "regime never gates" contract.
- **Wheel strategy:** Wheel execution is **not** gated by regime. Regime is not passed to the wheel; wheel runs independently. Regime must never fully gate trading (equity or wheel).

## Pipeline

1. **Structural** — `structural_intelligence/regime_detector.py`: SPY returns (HMM or fallback) → `state/regime_detector_state.json` (RISK_ON, NEUTRAL, RISK_OFF, PANIC).
2. **Posture** — `structural_intelligence/regime_posture_v2.py`: Structural regime + `market_context_v2` → bull/bear/chop/crash → `state/regime_posture_state.json`.
3. **Intel** — `src/intel/regime_detector.py`: Reads posture + market_context → `state/regime_state.json` (RISK_ON, RISK_OFF, NEUTRAL, BEAR, MIXED).
4. **Universe** — `scripts/build_daily_universe.py`: Uses `read_regime_state()` and writes `_meta.regime_label` in `state/daily_universe_v2.json`.
5. **Board / multi-day** — `scripts/run_stockbot_daily_reports.py` builds the daily pack from `daily_universe_v2` (reading regime from `_meta.regime_label`); multi-day analysis reads regime from the stockbot pack.

## Where regime_label is set

- **At runtime:** `update_regime_posture_v2()` (called from main loop) writes `regime_posture_state.json` with `regime_label` (bull/bear/chop/crash).
- **For universe:** `build_daily_universe.py` reads `regime_state.json` and writes `daily_universe_v2.json` with `_meta.regime_label` (RISK_ON/RISK_OFF/NEUTRAL/etc.).
- **For reports:** Stockbot daily reports read regime from `daily_universe_v2._meta.regime_label` with fallback `NEUTRAL` (never `UNKNOWN` for downstream).

## Safe default

When regime cannot be determined, the system uses **NEUTRAL** (or equivalent) so that multi-day analysis and the Board see a real label. Trading is never blocked solely because regime is unknown.

## Diagnostics

- `scripts/regime_detection_diagnostic.py`: For the last N days, prints per-day regime_label, confidence, and key inputs; flags UNKNOWN and explains why (e.g. missing _meta).
