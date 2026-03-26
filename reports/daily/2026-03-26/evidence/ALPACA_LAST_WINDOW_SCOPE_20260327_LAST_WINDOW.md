# Alpaca last-window scope

**TS:** `20260327_LAST_WINDOW`

## Venue / clock

- **Exchange calendar:** US equities regular session, **NYSE close 16:00 America/New_York** (Alpaca cash equities).
- **Window end (`close_ts`):** `2026-03-26T16:00:00-04:00` (UTC epoch `1774555200.0`)
- **Session date (ET):** `2026-03-26`

## Window

- `last_window_hours` = **2**
- `window_start` = close − 2h → UTC epoch `1774548000.0` (`2026-03-26T18:00:00+00:00`)
- Strict gate: exits with `open_ts_epoch ≤ exit_ts ≤ EXIT_TS_UTC_EPOCH_MAX` (see runner `--window-end-epoch`).