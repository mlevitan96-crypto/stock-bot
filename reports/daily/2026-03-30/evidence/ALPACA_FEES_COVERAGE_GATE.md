# ALPACA FEES COVERAGE GATE

## Source of truth

- **Primary:** broker-provided `commission` / `fees` on REST order objects when present.
- **Secondary:** `account/activities` type **FILL** with `net_amount` / `commission` (`scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py` pattern).
- **Tertiary:** deterministic fee schedule is **not** the paper default in-repo; audits use hybrid broker+local join.

- REST filled-like rows considered: **50**
- Rows with fee signal (commission/fees/legs/activity join): **0** (0.00%)

```json
{
  "sample_orders_rest_keys": [
    "id",
    "client_order_id",
    "created_at",
    "updated_at",
    "submitted_at",
    "filled_at",
    "expired_at",
    "canceled_at",
    "failed_at",
    "replaced_at",
    "replaced_by",
    "replaces",
    "asset_id",
    "symbol",
    "asset_class",
    "notional",
    "qty",
    "filled_qty",
    "filled_avg_price",
    "order_class",
    "order_type",
    "type",
    "side",
    "position_intent",
    "time_in_force",
    "limit_price",
    "stop_price",
    "status",
    "extended_hours",
    "legs",
    "trail_percent",
    "trail_price",
    "hwm",
    "subtag",
    "source",
    "expires_at"
  ]
}
```

- Alpaca base URL (fee context): `https://paper-api.alpaca.markets`
- Paper account (deterministic zero-commission path): **True**

## Verdict: **PASS**

- **Note:** PASS under **paper deterministic fee path** (commission fields often absent; treat as $0 for forward audit).
