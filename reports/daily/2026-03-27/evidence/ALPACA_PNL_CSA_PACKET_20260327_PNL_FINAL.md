# CSA — Profit discovery packet (20260327_PNL_FINAL)

## What is true

- Last-window forward truth on **2026-03-26** reported **CERT_OK**, `forward_trades_incomplete=0`, `trades_seen=44` (artifact: `reports\ALPACA_LAST_WINDOW_TRUTH_20260327_LAST_WINDOW.json`).
- This workspace **does not** contain the per-trade log slice or `complete_trade_ids` list needed to reproduce those 44 rows.

## What is uncertain

- Exact membership of the 44 trades without enumerated IDs in the saved JSON.
- Economic PnL decomposition (fees, gross) for that cohort without droplet exports.

## Top 10 profit levers (ranked)

| Rank | Lever | Expected impact | Confidence | Risk note |
|------|-------|-----------------|------------|-----------|
| 1 | Emit `complete_trade_ids` on every CERT_OK run | high traceability | high | None — code already updated |
| 2 | Freeze replay gzip bundles in CI artifact | enables offline re-run | high | Storage cost |
| 3 | Join fees per canonical_trade_id | net PnL truth | high | Broker fee schema drift |
| 4 | Shadow ledger for blocked intents | quantify false negatives | medium | lookahead control |
| 5 | Latency path metrics in orders.jsonl | infra PnL leak detection | medium | clock skew |
| 6 | Exit winner × hold surfaces | exit policy tuning | medium | small n in window |
| 7 | Spread / slippage at entry | microstructure drag | medium | needs NBBO archive |
| 8 | Regime tags at entry | stability | medium | regime model error |
| 9 | CI deploy markers correlated to PnL | operational alpha loss | low | confounding sessions |
| 10 | Dashboard closed_trades parity check | operator trust | high | API drift |

## Top 10 ways we could fool ourselves

1. Missing trade enumeration in saved CERT_OK JSON (historical runs).
2. Empty local replay archives masquerading as ‘replay ready’.
3. Mixing last-window cohort with full-day language.
4. Shadow path PnL without same-bar constraints.
5. Multiple positions per symbol without alias join closure.
6. Overfitting interaction bins with n≈44.
7. Using dashboard aggregates without row-level reconciliation.
8. Legacy PREERA opens excluded — do not compare to forward without label.
9. Fee omission if only Alpaca ‘pnl’ field used.
10. Latency measured in wall clock without NTP health.

## Bounded next experiments

1. Re-run forward truth runner on droplet after deploying gate change → store JSON with `complete_trade_ids`.
2. Export one gzipped slice: `exit_attribution`, `run`, `orders`, `alpaca_unified_events` for the same window.
3. Run reconciliation script; require delta=0 for promotion.
