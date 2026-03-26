# Alpaca dashboard — screenshot index

**Timestamp:** 20260326_1815Z  
**Capture:** Puppeteer (headless Chrome) on droplet; Basic auth via `page.authenticate`.

## Files

| File | Intent |
|------|--------|
| `reports/screenshots/alpaca_dashboard_20260326_1815Z/01_home_disclaimer.png` | Home / header: operational activity panel + **CSA disclaimer** (“Trades are executing on Alpaca. Data is NOT certified for learning or attribution.”) |
| `02_telemetry.png` | Telemetry tab — **PARTIAL** strip / amber partial telemetry banner (no red error styling for accepted gaps) |
| `03_system_health.png` | System Health tab — integrity / learning cohort cards (informational styling) |
| `04_fast_lane.png` | Fast Lane tab — shadow ledger (PARTIAL strip default + content) |

## Script

`scripts/droplet_dashboard_screenshots.js` (run from `/tmp/dashproof` with `npm install puppeteer` on droplet; system libs installed for Chrome).

**Note:** Fast Lane “catch path” was not forced as an error; tab shows normal **PARTIAL** banner and loaded ledger (acceptable proof).
