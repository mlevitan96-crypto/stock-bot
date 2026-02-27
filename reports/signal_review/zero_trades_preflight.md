# Zero-trades preflight (Phase 0)

Generated: 2026-02-20 18:38 UTC
**ZERO TYPE: C**

## 1) Main loop running

- **reports/decision_ledger/decision_ledger.jsonl** — newest event ts: 1771602603 (2026-02-20T15:50:03+00:00)
- **logs/score_snapshot.jsonl** — newest ts: 1771612710 (2026-02-20T18:38:30+00:00)
- **state/blocked_trades.jsonl** — newest ts: 1771612713 (2026-02-20T18:38:33+00:00)
- **logs/run.jsonl** — newest ts: 1771612700 (2026-02-20T18:38:20+00:00)

## 2) Candidate existence

- Ledger events last 24h: **3037** (path: reports/decision_ledger/decision_ledger.jsonl)
- Ledger events last 2h: **0**

## 3) First-fail gate distribution (last 24h)

| Gate:Reason | Count |
|-------------|-------|
| expectancy_gate:score_floor_breach | 3037 |

## 4) UW defer lifecycle

- **reports/uw_health/uw_defer_retry_events.jsonl** — events last 24h: 0, resolved: 0, expired_then_penalized: 0
- **reports/uw_health/uw_deferred_candidates.jsonl** — current deferred candidates (line count): 0

## 5) Capacity/risk

- First-fail gate counts (capacity/max_positions/theme_exposure) last 24h: **0**
- Gate:reason keys: (none)

## 6) Order layer

- **logs/orders.jsonl** — order-related lines last 24h: 396 (attempts), 0 (fills), 0 (rejects); action counts: {'': 396}
- **logs/submit_entry.jsonl** — submit_entry lines last 24h: 0, reject/block/error: 0; top msg: []

---

## Board verdict (fix-ready)

- **Classification: C — Orders attempted but rejected/never filled.**
- **Evidence:** Order/submit_entry attempts last 24h: 396; fills: 0; rejects: 0.
- **Fix:** Inspect logs/orders.jsonl and logs/submit_entry.jsonl for rejection reasons (Alpaca 422, buying power, trade guard, spread, etc.). No strategy tuning; fix broker/guard/validation layer.
- **Next:** Address specific rejection codes; re-run preflight to confirm ZERO TYPE moves to B or trades fill.
