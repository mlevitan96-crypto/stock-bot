# PHASE 5 — Strict Gate Re-Run (mandatory)

**Timestamp:** 2026-03-26T18:00Z  
**Epoch:** `1774458080` (unchanged)  
**Rules:** Same as prior certification (`telemetry/alpaca_strict_completeness_gate.py`).

---

## Droplet run (pre-deploy snapshot)

| Metric | Value |
|--------|------:|
| `trades_seen` | 197 |
| `trades_complete` | 81 |
| `trades_incomplete` | 116 |
| Join coverage (complete / seen) | **41.1%** |
| `LEARNING_STATUS` | **BLOCKED** |
| `learning_fail_closed_reason` | `incomplete_trade_chain` |

**Important:** The droplet executed the **prior** gate script revision **before** deploying this repair branch. Counts are **not** expected to move until:

1. `git pull` + `systemctl restart stock-bot.service` (or equivalent), and  
2. Optional: `python scripts/audit/backfill_unified_terminal_from_exit_attribution.py --root /root/stock-bot` (after dry-run review), and  
3. New post-deploy trades (and/or time) so `run.jsonl` contains post-fix `trade_intent` / `exit_intent` keys.

---

## Local synthetic trace (post-repair code)

- **Fixture:** `tests/test_strict_completeness_forward_parity.py`
- **Result:** `LEARNING_STATUS=ARMED`, `trades_complete=1`, `trades_incomplete=0`

---

## Artifacts

- `reports/ALPACA_STRICT_COMPLETENESS_GATE_20260326_1800Z.json`
