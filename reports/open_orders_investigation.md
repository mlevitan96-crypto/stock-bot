# Open Orders Investigation — Why Orders Aren't Occurring

**Purpose:** Identify why no (open) orders are being placed or visible. Two interpretations:

1. **Orders not being placed** — bot never submits entry orders.
2. **Open orders not visible** — pending (unfilled) orders exist at Alpaca but UI/API doesn’t show them.

This doc focuses on (1). For (2), see “Open orders visibility” below.

---

## 1. Control flow: when are entry orders skipped?

Entry orders are only submitted when **all** of the following are true:

| Check | Location | If false → orders = [] |
|-------|----------|------------------------|
| Market open | Worker loop | `run_once()` not called; no clusters, no orders. |
| Not degraded | run_once | `reduce_only_broker_degraded` → skip entries. |
| Armed | run_once | `not_armed_skip_entries` → ALPACA_BASE_URL must be paper endpoint. |
| Reconciled | run_once | `not_reconciled_skip_entries` → executor.ensure_reconciled() failed. |
| Risk OK | run_once | Early return with `risk_freeze` → no decide_and_execute. |
| Clusters > 0 | decide_and_execute | `reason="no_clusters"` in cycle_summary. |
| At least one candidate passes all gates | decide_and_execute | cycle_summary with considered > 0, orders=0, gate_counts show blocks. |

**Armed** = `trading_is_armed()`: `ALPACA_BASE_URL` must contain `paper-api.alpaca.markets` and must **not** be live (`api.alpaca.markets` without "paper"). If URL is wrong or unset, bot is unarmed and skips entries.

**Reconciled** = executor’s positions synced with Alpaca (and metadata). If `ensure_reconciled()` fails (e.g. API error, bad metadata), entries are skipped.

---

## 2. Where to look for evidence

- **Run once / skip entries**
  - `logs/run.jsonl` — `"msg": "complete"` with `clusters`, `orders`, `risk_freeze`, `market_open`.
  - `logs/worker_debug.log` — "Market is OPEN" vs "Market is CLOSED", "About to call run_once()", "decide_and_execute returned N orders".
- **Armed / reconciled / degraded**
  - `logs/run.jsonl` or event log — `not_armed_skip_entries`, `not_reconciled_skip_entries`, `reduce_only_broker_degraded`.
  - Run script below to grep these.
- **Clusters and gates**
  - `logs/gate.jsonl` — `cycle_summary`: `considered`, `orders`, `gate_counts`, `reason` (e.g. `no_clusters`).
  - `gate_counts`: e.g. `expectancy_blocked:...`, `max_new_positions_per_cycle_reached`, `max_one_position_per_symbol`.
- **Last order**
  - Dashboard “last order” uses Alpaca `list_orders(status='all', limit=1)` and/or `logs/orders.jsonl`, `data/live_orders.jsonl`.

---

## 3. Checklist (run when market is open)

1. **Market** — `logs/worker_debug.log`: "Market is OPEN" and "About to call run_once()" each cycle.
2. **ALPACA_BASE_URL** — On droplet: `grep ALPACA .env` or check process env. Must be `https://paper-api.alpaca.markets` for paper.
3. **Armed** — No `not_armed_skip_entries` in recent run/gate logs.
4. **Reconciled** — No `not_reconciled_skip_entries`; if present, check Alpaca API and `state/position_metadata.json`.
5. **Degraded** — No `reduce_only_broker_degraded`; if present, broker/API was unreachable.
6. **Risk** — No `risk_freeze` in `logs/run.jsonl`.
7. **Clusters** — `logs/gate.jsonl` cycle_summary: `considered` > 0. If 0, upstream (UW cache, signals) produced no candidates.
8. **Gates** — If considered > 0 but orders = 0, inspect `gate_counts` (e.g. all expectancy_blocked, or max_new_positions_per_cycle_reached).

---

## 4. Open orders visibility (pending orders at Alpaca)

- **Bot** does not currently expose an API that returns `list_orders(status='open')` for the dashboard.
- **Dashboard** “last order” uses `list_orders(status='all', limit=1)` for age; it does not list all open orders.
- If you need to **see pending orders** in the UI: add an endpoint (e.g. `/api/orders/open`) that calls Alpaca `list_orders(status='open')` and return them; then add a small “Open orders” section that calls it.

---

## 5. Quick diagnostic script

Run (locally or on droplet):

```bash
python scripts/investigate_open_orders.py
```

With droplet SSH (from repo root on droplet):

```bash
cd /root/stock-bot && python3 scripts/investigate_open_orders.py
```

Or from local via DropletClient (script can support `--remote` to tail logs on droplet).

The script prints: recent run completion (clusters, orders, risk_freeze), skip_entries events, gate cycle_summary, and worker_debug lines for market/run_once/decide_and_execute.

---

## 6. Droplet run (2026-02-19, market open) — confirmed findings

- **Market:** Open. Worker: `Market check: market_open=True`, `run_once()` called, completing with clusters=14, 26.
- **Armed / reconciled / degraded:** No skip-entry events. ALPACA_BASE_URL set in .env.
- **Run completion:** `clusters=14,26`, `orders=0`, no risk_freeze.
- **Root cause:** All candidates blocked by gates.
  - **gate_counts:** `score_below_min` (37, 14, 26) and `expectancy_blocked:score_floor_breach` (1, 14).
- **Conclusion:** Orders are not placed because every candidate either (1) fails the minimum score filter (`score_below_min`) or (2) reaches the expectancy gate and fails on score floor breach (`expectancy_blocked:score_floor_breach`). No issue with market, armed, or reconciliation.


---

## Post-threshold-change (MIN_EXEC_SCORE=2.5)

- **Commit on droplet:** `4e45064 Config: adjust thresholds based on blocked-trade expectancy analysis` (deployed via git reset --hard origin/main; paper restarted).
- **Recent cycle_summary:** considered=1, orders=0, gate_counts={'expectancy_blocked:score_floor_breach': 1}; considered=14, orders=0, gate_counts={'score_below_min': 14}; considered=13, orders=0, gate_counts={'expectancy_blocked:score_floor_breach': 13}.
- **Verdict:** STILL BLOCKED by expectancy_blocked:score_floor_breach (and score_below_min in some cycles).
