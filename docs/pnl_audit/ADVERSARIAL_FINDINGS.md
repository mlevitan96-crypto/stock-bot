# Adversarial review — PnL lineage (standing findings)

Template for red-team review. **Canonical contract:** `LINEAGE_MATRIX.json`. Evidence runs copy here to `reports/daily/<ET>/evidence/ALPACA_PNL_LINEAGE_ADVERSARIAL_FINDINGS.md`.

## 1) Ambiguity — dual sources

| Topic | Canonical choice |
|-------|------------------|
| `order_id` | **Broker REST** `order.id` is authoritative. Local `logs/orders.jsonl` may omit on some fill-shaped rows — audits must not assume local always has id. |
| `entry_reason` (informal) | **`final_decision_primary_reason`** (+ `blocked_reason` / `gate_summary`). No literal `entry_reason` key. |
| Entry price | **`filled_avg_price`** at fill; not NBBO quote at intent. |

## 2) Join fragility

| Risk | Mitigation |
|------|------------|
| ts-only joins | Use only as fallback; prefer `order_id` + `canonical_trade_id`. |
| Local fill rows without `order_id` | Join via broker `list_orders` / activities for the session window. |
| Clock skew | Compare broker `filled_at` vs local `ts` with tolerance (e.g. minutes). |

## 3) Fee trap

| Mode | Contract |
|------|----------|
| Alpaca paper | **Deterministic zero** commission on REST when fields absent; document gross≈net unless enriched. |
| Live / future | Require **FILL activities** or explicit `commission` on order object; see `scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py`. |

## 4) “Looks present but unusable”

| Trap | Signal |
|------|--------|
| In-memory only | Field in debugger but never `jsonl_write` / `append_exit_attribution`. |
| Persisted but not joinable | Row lacks `symbol` or `order_id` when audit expects join. |
| Wrong timezone | Mixed naive UTC vs ET display — normalize to UTC in stored rows. |

## Top 5 ways this could still fail tomorrow

1. **`stock-bot` inactive** — no new rows; matrix is correct but empty. *Mitigation:* `systemctl start stock-bot` before session; verify `logs/run.jsonl` mtime.
2. **Phase 2 telemetry disabled** — `PHASE2_TELEMETRY_ENABLED=false` kills `trade_intent`. *Mitigation:* env check in readiness script.
3. **Dashboard down** — `/api/pnl/reconcile` 503; reconciliation artifact missing. *Mitigation:* broker-only audit path; restart supervisor.
4. **Intelligence trace absent** — `final_decision_primary_reason` empty; CRITICAL system_event noise. *Mitigation:* accept `gate_summary` / thesis_tags for audit narrative.
5. **Broker rate limit / clock failure** — REST gaps. *Mitigation:* retry with backoff; cache last-good clock in evidence.
