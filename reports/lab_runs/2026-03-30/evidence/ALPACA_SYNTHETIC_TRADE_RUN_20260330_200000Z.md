# Alpaca synthetic trade run (no market, no orders)

**TS:** `20260330_200000Z`  
**Lab root:** `reports/lab_runs/2026-03-30/evidence/synthetic_lab_root/`  
**Generator:** `reports/lab_runs/2026-03-30/evidence/generate_synthetic_lab_fixture.py`

---

## Constraints honored

- **No** Alpaca order API calls.  
- **No** `main.py` trading loop execution — only **synthetic JSONL** under an isolated `synthetic_lab_root` with a **stub** `main.py` (comment only; does not trigger strict **structural** anti-pattern).  
- **No** config or strategy edits in repo **outside** lab tree under `reports/lab_runs/`.

---

## Synthetic scenarios

| # | Symbol | Side | Entry (UTC) | Exit (UTC) | PnL | Score (signal_context) |
|---|--------|------|-------------|------------|-----|-------------------------|
| 1 | LABL | LONG | 2026-03-30T13:45:00+00:00 | 2026-03-30T18:30:00+00:00 | +12.34 | 3.1 |
| 2 | LABS | SHORT | 2026-03-30T14:00:00+00:00 | 2026-03-30T18:45:00+00:00 | -4.20 | 2.8 |

**Calendar:** 2026-03-30 is a **Monday** (pre-market readiness target).

---

## Walkthrough (logical)

1. **Entry decision** — `trade_intent` with `decision_outcome=entered`, `canonical_trade_id`, `decision_event_id`.  
2. **Signal context** — `signal_context.jsonl` rows for **enter** and **exit** with `final_score`, `signals.position_side`, `signals.direction` (long=bullish, short=bearish).  
3. **Lifecycle ordering** — `entry_timestamp` < `timestamp` (exit) for each row; monotonic per trade.  
4. **Unified events** — `alpaca_entry_attribution` + `alpaca_exit_attribution` (`terminal_close: true`).  
5. **Orders** — typed `order` lines with `canonical_trade_id` (synthetic only; **not** submitted).  
6. **Exit intent** — `exit_intent` on `run.jsonl` keyed by `canonical_trade_id`.  
7. **Exit attribution** — `pnl`, `exit_price` > 0, `snapshot.pnl` for PnL interpretability.  
8. **Strict completeness** — evaluated in Phase 3 (must PASS).

---

## Requirements checklist

| Requirement | PASS |
|-------------|------|
| entry decision emitted (as `trade_intent` entered) | **YES** |
| signal context attached | **YES** (`signal_context.jsonl`) |
| lifecycle ordering monotonic | **YES** |
| exit attribution emitted | **YES** |
| strict completeness | **YES** — see `strict_gate_result.json` and Phase 3 doc |

---

*Synthetic only; not production trades.*
