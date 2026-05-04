# MEMORY_BANK.md — Board index & V3 Alpaca entrypoint

**Authoritative operational law (full text, golden workflow, compliance):** **`MEMORY_BANK_ALPACA.md`**.  
Cursor MUST still load and update **`MEMORY_BANK_ALPACA.md`** for any material Alpaca / droplet / governance change. This file is the **short Board-facing index** so `MEMORY_BANK.md` exists as the path the Commander referenced.

---

## V3 structural reality (2026-05-04)

| Topic | Where / what |
|--------|----------------|
| **Equity vs wheel** | Legacy US-equity harvester path remains in repo but is **optional** when `strategies.equity.enabled: false` and wheel is live. Capital focus shifted to **cash-collateralized options wheel** (CSP → assignment → CC). Liquidation / flatten scripts are **governance tools**, not the primary daily strategy when wheel-only. |
| **Fail-closed broker reads** | `strategies/wheel_strategy.run`: `list_positions` / `list_orders` exceptions **abort the wheel cycle** (no silent empty lists). |
| **Options quotes** | `fetch_alpaca_latest_quote` → `normalize_alpaca_quote` (SDK-safe). `uw_composite_v2` uses the same bridge; **`alpaca_client.get_quote`** does not assume `get_quote` exists on REST. |
| **Guarded executor** | `main.run_all_strategies`: `AlpacaExecutor(defer_reconcile=True, external_api=api_v2)`; CSP/CC/velocity use **`submit_wheel_broker_order` → `_submit_order_guarded`**. |
| **Critical Telegram pager** | `src/critical_alert.py` — dedupe + cooldown; **`alpaca_wheel_critical`** allowlisted for integrity-only mode. Wired for wheel fail-closed aborts and orchestrator exceptions. |
| **Wheel state self-heal** | `strategies/wheel_strategy._load_wheel_state` — JSON decode / shape repair, **`state/wheel_state.corrupt.<ts>.json`** backups, `wheel_state_self_healed` system_events. |

---

## Board personas (advisory readout contract)

- **Vane — SRE:** Fail-closed API reads, supervisor-adjacent signals via Telegram on **hard** wheel failures, dedupe-backed pager, state backups before destructive repair.
- **Marcus — Adversary:** Cooldown on identical dedupe keys; integrity-only gate documented; corrupt state never silently becomes “flat wrong” notional without dropping bad nodes first.
- **Sterling — Quant:** Healer **prunes** bad structures instead of inferring positions; broker reconciliation remains source of truth for assignments; allocator reads healed `open_csps` keys only as dicts of dict-rows.

---

## Changelog pointer

Detail and file-level references: **`MEMORY_BANK_ALPACA.md` §2.2.1** and **§2.2.1a** (updated 2026-05-04).
