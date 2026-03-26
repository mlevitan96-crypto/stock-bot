# Alpaca Loss Causality — Decomposition (Phase 2, QSA)

**Mission:** Per-trade and aggregate loss causality (direction, MAE/MFE, entry vs exit, gap, regime).  
**Authority:** QSA. READ-ONLY.  
**Date:** 2026-03-18.

Per-trade dimensions: direction correctness (long/short vs price move), regime_mismatch (entry_regime ≠ exit_regime). Aggregates: by cause (wrong direction, regime mismatch on losers), by regime, symbol, time-of-day. Data: TRADES_FROZEN.csv (+ optional TRADE_TELEMETRY). Full framework: see Phase 2 mission in ALPACA_EXPANSION_SCOPE.md.

**Data source (this run):** reports/alpaca_edge_2000_20260317_1721/TRADES_FROZEN.csv (36 trades).

---

## 2. Aggregates (Computed)

### 2.1 Loss by Cause (Summary)

| Cause | Count | Sum PnL |
|-------|-------|---------|
| Wrong direction | 22 | 0.0 |
| Regime mismatch (on losers) | 0 | 0.0 |

### 2.2 Loss by Regime

| entry_regime | Trades | Total PnL | Win rate | Mean PnL |
|--------------|--------|-----------|----------|----------|
| NEUTRAL | 36 | 63000.0 | 38.9% | 1750.0 |

### 2.3 Loss by Symbol

| Symbol | Trades | Total PnL | Win rate | Mean PnL |
|--------|--------|-----------|----------|----------|
| AAPL | 36 | 63000.0 | 38.9% | 1750.0 |

### 2.4 Loss by Time-of-Day (entry hour UTC)

| Hour bucket | Trades | Total PnL | Win rate |
|--------------|--------|-----------|----------|
| 2026-01-01T00 | 22 | 0.0 | 0.0% |
| 2026-01-21T22 | 3 | 13500.0 | 100.0% |
| 2026-01-22T21 | 2 | 9000.0 | 100.0% |
| 2026-01-22T22 | 2 | 9000.0 | 100.0% |
| 2026-01-22T23 | 2 | 9000.0 | 100.0% |
| 2026-01-23T00 | 2 | 9000.0 | 100.0% |
| 2026-01-23T01 | 2 | 9000.0 | 100.0% |
| 2026-01-23T15 | 1 | 4500.0 | 100.0% |