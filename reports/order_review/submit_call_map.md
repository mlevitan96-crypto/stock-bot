# Submit call map — Order Submission Truth Contract

**Purpose:** Identify the exact broker submit and all guards/conditions that must be true to reach it. All paths and line numbers refer to the repo (main.py unless noted).

---

## 1. Broker submit (single point)

| Item | Value |
|------|--------|
| **Function** | `AlpacaExecutor._submit_order_guarded` (then `self.api.submit_order`) |
| **File** | `main.py` |
| **Line numbers** | **3884–3894** (limit order), **3895–3904** (market order) |
| **API** | `self.api` = `tradeapi.REST(...)` (Alpaca SDK). See `main.py` **3762**. |

The actual network call is:
- `return self.api.submit_order(symbol=..., qty=..., side=..., type=order_type, time_in_force=..., limit_price=..., client_order_id=..., **kwargs)` (limit)
- `return self.api.submit_order(symbol=..., qty=..., side=..., type=order_type, time_in_force=..., client_order_id=..., **kwargs)` (market)

---

## 2. Call sites of `_submit_order_guarded`

| Call site | File | Line | Caller context |
|-----------|------|------|----------------|
| Entry (limit, backoff) | main.py | 4559 | `submit_entry` → backoff(submit_order)() |
| Entry (limit, final) | main.py | 4718 | `submit_entry` → direct after limit attempts |
| Entry (market) | main.py | 4865 | `submit_entry` → backoff(submit_market_order)() |
| Scale-out partial | main.py | 5827 | `_scale_out_partial` |
| market_buy | main.py | 5841 | `market_buy` |
| market_sell | main.py | 5844 | `market_sell` |

Entry path from trading loop: `decide_and_execute` → **9347** `self.executor.submit_entry(...)`.

---

## 3. Conditions that must be true to reach the submit (entry path only)

All of the following must pass for a candidate to reach `_submit_order_guarded` from `submit_entry`. Early returns below prevent the submit.

| # | Condition / guard | File:lines | If false → return / block |
|---|-------------------|------------|---------------------------|
| 1 | `entry_score` present and > 0 | main.py 4246–4249 | `missing_entry_score` |
| 2 | `market_regime` / `regime` not unknown/empty | main.py 4251–4255 | `missing_market_regime` |
| 3 | If side=sell: asset shortable | main.py 4258–4268 | `asset_not_shortable` |
| 4 | `ref_price = get_last_trade(symbol) > 0` | main.py 4269–4272 | `bad_ref_price` |
| 5 | Trade guard approves | main.py 4274–4324 | `trade_guard_blocked` |
| 6 | Spread watchdog: spread_bps ≤ MAX_SPREAD_BPS | main.py 4331–4325 | `spread_too_wide` |
| 7 | Notional ≥ MIN_NOTIONAL_USD | main.py 4426–4421 | `min_notional_blocked` |
| 8 | Price vs position cap (or fractional qty path) | main.py 4405–4420, 4410–4419 | `price_exceeds_cap` / `Price_Exceeds_Cap` |
| 9 | Risk/validate_order_size passes | main.py 4446–4454 | `risk_validation_failed` |
| 10 | Buying power: required_margin ≤ available_bp | main.py 4458–4465 | `insufficient_buying_power` |
| 11 | Not AUDIT_DRY_RUN (early check in submit_entry) | main.py 4509–4528 | mock return, no broker call |
| 12 | Inside _submit_order_guarded: no AUDIT_MODE assert | main.py 3820–3834 | RuntimeError re-raised |
| 13 | Inside _submit_order_guarded: not _should_use_dry_run() | main.py 3836–3866 | mock order return |

So for the **broker submit to be called** from the entry path:
- No early return in `submit_entry` (1–11).
- No audit assert and no dry-run in `_submit_order_guarded` (12–13).

---

## 4. Telemetry written before/at submit

- **Before submit (instrumentation):** `log_event("submit_order_called", "SUBMIT_ORDER_CALLED", symbol, ts, mode, qty, side)` → `logs/submit_order_called.jsonl`.
- **After submit:** `log_order({...})` in various branches → `logs/orders.jsonl`.  
- **submit_entry blocks:** `log_event("submit_entry", msg, ...)` → `logs/submit_entry.jsonl`.

---

## 5. Summary

- **Single broker submit:** `main.py` **3884** (limit) and **3895** (market) inside `_submit_order_guarded`.
- **Entry path:** `submit_entry` (4224) → many guards above → `_submit_order_guarded` (3800) → audit checks → `self.api.submit_order`.
- **Evidence files on droplet:** `logs/submit_order_called.jsonl` (submit reached), `logs/orders.jsonl` (order-layer events), `logs/submit_entry.jsonl` (submit_entry blocks).
