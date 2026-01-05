# Order Log Path Correction

## Issue
Audit script was using incorrect path: `logs/order.jsonl` (singular)
This resulted in incorrect order counts (showing only 38 orders when there are many more).

## Correct Paths (Per Memory Bank & config/registry.py)

### Order Events
- **CORRECT**: `logs/orders.jsonl` (plural) - per `config/registry.py` `LogFiles.ORDERS`
- **INCORRECT**: `logs/order.jsonl` (singular) - DO NOT USE

### Total Trades/Orders Count
- **AUTHORITATIVE SOURCE**: `logs/attribution.jsonl` - Contains all executed trades
- Count all records with `type == "attribution"` to get total trades

## Files Corrected
1. `check_workflow_audit.py` - Updated to use `logs/orders.jsonl` and count total from `logs/attribution.jsonl`
2. `check_signals_and_orders.py` - Updated to use `logs/orders.jsonl`

## Date
2026-01-05

## Reference
- Memory Bank: Line 985-987 (logs/orders.jsonl is correct)
- config/registry.py: LogFiles.ORDERS = Directories.LOGS / "orders.jsonl"
- Mapping audit completed over weekend confirmed correct paths
