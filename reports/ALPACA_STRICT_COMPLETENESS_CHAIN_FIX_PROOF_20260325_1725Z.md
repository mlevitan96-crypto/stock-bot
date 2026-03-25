# ALPACA strict completeness — chain gaps + proof (full)

**Artifact TS:** 20260325_1725Z  
**Repo HEAD (reference):** `076bb03`

---

## Hard requirement — plan confirmation

1. **Plan (restated):** Measure strict completeness on the post-restart epoch; enumerate incomplete reasons and chain matrices; define an authoritative join key; align the strict gate and emitters so intent-time and fill-time IDs join safely; add tests; deploy; re-run gate on live windows; document outcomes without operator questions.

2. **Failure-mode review:** (a) Using latest resolved fill **per symbol** as the join key collides when multiple trades share a ticker. (b) Orders logged while runtime attribution keys point at a **new** blocked intent (e.g. LONG flip) stamp the **wrong** `canonical_trade_id` vs the open **SHORT** in metadata. (c) Unified entry rows keyed only under `trade_key` miss lookups when consumers use `canonical_trade_id`. (d) Exit rows need correct **SHORT** vs **LONG** when deriving `trade_key` from `open_*` trade_id. (e) `exit_intent` without metadata keys misses join unless live attribution store is merged.

3. **PLAN_VERDICT:** **APPROVE.**

4. **STOP on REVISE:** N/A.

---

## Phase 0 — Blockers (tooling)

Tooling: `scripts/alpaca_strict_chain_audit.py` calls `evaluate_completeness(..., audit=True)` and prints:

- `trades_seen` / `trades_complete` / `trades_incomplete`
- `reason_histogram`
- `incomplete_trade_ids_by_reason` (capped)
- `chain_matrices_sample` (up to 5 incomplete trades)

---

## Phase 1 — Authoritative join key (CSA)

Implemented in `telemetry/alpaca_strict_completeness_gate.py`:

- **Primary key per trade:** `trade_key` from unified `alpaca_exit_attribution` (terminal close), else derived from `trade_id` `open_{SYM}_{ts}` with `normalize_side` on the **exit_attribution.jsonl** row.
- **Aliases:** Fixed-point expansion over `intent_to_fill` built from `canonical_trade_id_resolved` (`canonical_trade_id_intent` → `canonical_trade_id_fill`).
- **Join surfaces:** `trade_intent` (entered), `unified_entry`, `orders`, `exit_intent` — each checked with **`any(alias in index)`** after expansion.
- **Unified entry load:** each `alpaca_entry_attribution` row is indexed under **both** `trade_key` and `canonical_trade_id` when present.

**Removed:** seeding aliases from “latest fill per symbol” (correctness bug for multiple round-trips per ticker).

---

## Phase 2 — Join plumbing (SRE)

| Change | Location | Purpose |
|--------|----------|---------|
| Metadata-first `canonical_trade_id` on orders | `main.py` `log_order` | When the event omits `canonical_trade_id`, copy from durable `POSITION_METADATA` before merging in-memory keys — avoids wrong LONG stamp on SHORT positions during blocked flips. |
| `exit_intent` key backfill | `main.py` `_emit_exit_intent` | Fill `canonical_trade_id` / `decision_event_id` / `symbol_normalized` / `time_bucket_id` from `get_symbol_attribution_keys` when metadata did not carry them. |

No strategy or execution decision changes; additive telemetry only.

---

## Phase 3 — Tests

File: `tests/test_alpaca_entry_ts_normalization.py`

- `test_strict_gate_resolves_intent_vs_fill_via_canonical_trade_id_resolved` — intent ID ≠ fill ID; resolution edge; **ARMED** with 1/1 complete.
- `test_strict_gate_orders_entry_and_exit_share_canonical` — two order rows, same canonical; **ARMED**.

---

## Phase 4–5 — Deploy and live windows

- **Droplet:** `/root/stock-bot` fast-forward to `076bb03`; `stock-bot.service` restarted when `main.py` changed.
- **STRICT_EPOCH_START:** `1774458080` (`2026-03-25T17:01:20Z`).
- **Gate `--open-ts-epoch 1774458080`:** `trades_seen: 0` → **BLOCKED** / **NO_POST_DEPLOY_PROOF_YET**.
- **Gate `--open-ts-epoch 1774456240` (same-day historical batch):** still **30 incomplete** / **30 seen** — frozen logs do not contain the join surfaces under the strict definitions (see summary histogram).

---

## Phase 6 — Artifacts

- `reports/ALPACA_STRICT_COMPLETENESS_CHAIN_FIX_PROOF_20260325_1725Z.md` (this file)
- `reports/ALPACA_STRICT_COMPLETENESS_CHAIN_FIX_PROOF_SUMMARY_20260325_1725Z.md`

Copies on droplet under `/root/stock-bot/reports/` after upload/pull.

---

## Code references

```text
telemetry/alpaca_strict_completeness_gate.py   — evaluate_completeness, _expand_canonical_aliases, AUTHORITATIVE_JOIN_KEY_RULE
main.py                                        — log_order (metadata canonical), _emit_exit_intent (key backfill)
scripts/alpaca_strict_chain_audit.py          — audit CLI
scripts/alpaca_post_deploy_terminal_close_audit.py — DEPLOY_START = 1774458080
tests/test_alpaca_entry_ts_normalization.py    — strict gate ARMED scenarios
```

---

## Next proof step (operational)

After the next **terminal close** with timestamp ≥ `1774458080`, re-run:

```bash
/root/stock-bot/venv/bin/python3 scripts/alpaca_strict_chain_audit.py --root /root/stock-bot --open-ts-epoch 1774458080
```

Target: `trades_seen >= 1`, `trades_complete >= 1`, `trades_incomplete == 0` for that cohort.
