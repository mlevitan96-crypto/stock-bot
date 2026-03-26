# STOP-GATE 1 — Adversarial review (mandatory)

**Artifact:** `ALPACA_DATA_ADVERSARIAL_REVIEW_20260326_2015Z`

---

## Stance: assume data is broken

I treat every “green” signal as **wrong until proven** on the **production droplet** with journals and full log joins.

---

## Disproof attempts (what I believe fails)

1. **Phase 1 missing** — No `systemctl` / `journalctl` artifacts → **cannot** know if writers or trading loop are running.
2. **`orders.jsonl` is empty** — Disproves **A** (submit/fill) and **B** (execution sidecar) for this workspace.
3. **`exit_attribution` without `trade_id`** — Disproves **C** for strict cross-log joins unless a separate mapping artifact exists (not used in certification).
4. **unified `terminal_close` count ≈ 2.8% of exit_attribution rows** — Disproves **B** if unified must reflect every terminal close.
5. **Duplicate unified events** for same `trade_id` — Risks **duplicate joins** or inflated counts if consumers are naive.
6. **Fixture / test rows** (`parity_*`, `inv`, empty `trade_id`) — Contaminate “live trade” certification unless filtered by epoch / schema guard.
7. **Stale `run.jsonl`** vs fresh `alpaca_*` — Suggests **multiple writers** or **non-production** use of workspace; **D** fails for monotonic coherency across surfaces.
8. **Grep found no errors** — Proves almost nothing; real failures are in **journals** and **binary crash** paths.

---

## Untested paths

- Broker API reconciliation vs `orders.jsonl` (no replay in this run).
- Partial fills, cancels, replaces, and **client_order_id** ↔ `trade_id` mapping.
- Clock skew between host and Alpaca.
- Log rotation / truncation / `logrotate` dropping evidence.
- Any **Alpaca-only** systemd unit names not present in repo.

---

## What could still be wrong after a “GO” on droplet

- Joins could pass on a **short window** but fail on **30d** due to schema migration.
- **Silent** drops in asyncio tasks without log lines.
- **Rate limits** only visible in network layer, not JSONL.

**Bottom line:** This certification run, on **this workspace evidence**, does **not** support continuing live trading under the **PERFECT** contract.
