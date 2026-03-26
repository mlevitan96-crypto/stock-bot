# Phase 2 — Event flow certification (Quant + SRE)

**Artifact:** `ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z`  
**Machine JSON:** [`reports/ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z.json`](../ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z.json)

---

## Method (read-only)

```text
python scripts/audit/alpaca_event_flow_audit.py --root . --hours 8760 --sample-size 15 --seed 7 --json-out reports/ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z.json
```

**Window:** 8760h filter still includes all local rows (sparse logs).  
**Proxies (per script notes):**

- **entry_decision_made** → `trade_intent` + `decision_outcome=entered` and/or `alpaca_entry_attribution`
- **execution submit / fill** → `orders.jsonl` heuristics
- **terminal close (unified contract)** → `alpaca_exit_attribution` with **`terminal_close: true`**

---

## Counts (workspace `c:\Dev\stock-bot`, **not droplet**)

| Stream | Metric | Value |
|--------|--------|------:|
| Unified | `alpaca_entry_attribution` rows | 51 |
| Unified | `alpaca_exit_attribution` rows | 39 |
| run.jsonl | `trade_intent_entered` | 78 |
| run.jsonl | `trade_intent` | 102 |
| orders.jsonl | heuristic rows in window | **0** |
| exit_attribution.jsonl | rows in window | 36 |
| Unified | distinct `trade_id` with `terminal_close` exit | **1** |

## Ratios

| Ratio | Value | Interpretation |
|-------|-------|----------------|
| unified_terminal_close ÷ exit_attribution | **0.028** | **Fails contract B** if exit_attribution economic closes must appear as unified terminal closes |
| unified_entry ÷ trade_intent_entered | **0.654** | **Incomplete** alignment between run log and unified entry stream |

---

## Fifteen random traces (sampled)

See `random_trade_traces` in the JSON. Summary:

- Most sampled `trade_id`s: **no** matching `exit_attribution` row with same `trade_id` (local `exit_attribution.jsonl` **has no `trade_id` field** — join integrity broken for strict end-to-end).
- **open_TSLA_2026-03-14T12-00-00Z:** unified entry + unified exit with terminal_close; **0** `orders.jsonl` rows on canonical key → **execution path not evidenced** in this workspace.
- Several traces are **fixture** ids (`parity_*`, `inv`).

---

## Adversarial note

This phase **does not** certify production. It **disproves** “perfect collection” for the **local** log bundle: empty `orders.jsonl` alone violates **A** and **B** for any live execution.
