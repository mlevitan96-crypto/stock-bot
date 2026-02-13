# Wheel Spot Resolution Verification Report
**Generated:** 2026-02-10T16:40:20.258284+00:00Z
**Repo:** /root/stock-bot
**Lookback:** 7 days (since 2026-02-03)

## 1. Spot resolution counts
- **wheel_spot_resolved:** 575
- **wheel_spot_unavailable:** 0

## 2. Spot source distribution (resolved only)
- **bar_close:** 575

## 3. Option chain and orders
- **First wheel_run_started in window:** 2026-02-10T15:24:42.132460+00:00
- **First no_contracts_in_range (option chains reached):** N/A
- **First wheel_order_submitted:** 2026-02-10T16:39:04.890904+00:00
- **wheel_order_submitted count:** 1
- **wheel_order_filled count:** 1

## 4. Skip reasons (wheel_csp_skipped)
- **no_spot:** 672
- **per_position_limit:** 200
- **capital_limit:** 10
- **max_positions_reached:** 2

## 5. Verdict
**PASS.** Spot resolved and wheel_order_submitted > 0. Wheel is capable of submitting CSP orders.
