# Alpaca strict repair — locked target set

**Timestamp:** `20260326_STRICT_ZERO_FINAL`  
**Scope:** Alpaca only. No gate relaxation, no era policy change, no waiting for new trades.

## Hard-coded repair targets (forensics / CSA lock)

Symbols (as requested): **PFE, QQQ, WMT, HOOD, LCID, CAT**

Full `trade_id` values (authoritative strings):

| Symbol | `trade_id` |
|--------|------------|
| PFE | `open_PFE_2026-03-26T14:29:25.977370+00:00` |
| QQQ | `open_QQQ_2026-03-26T15:10:28.882493+00:00` |
| WMT | `open_WMT_2026-03-26T15:10:28.883737+00:00` |
| HOOD | `open_HOOD_2026-03-26T15:51:38.174449+00:00` |
| LCID | `open_LCID_2026-03-26T15:51:38.396698+00:00` |
| CAT | `open_CAT_2026-03-26T16:34:40.245664+00:00` |

These match `TARGET_TRADE_IDS` in `scripts/audit/alpaca_strict_six_trade_additive_repair.py` and default `--trade-ids` in `scripts/audit/alpaca_strict_repair_forensics.py`.

## Note on cohort size

Iterative repair (`--repair-all-incomplete-in-era`) was applied on the droplet for **all** incomplete trades in the strict window (not only the six above), using additive sidecars only. The six symbols remain the named forensic targets for sign-off.
