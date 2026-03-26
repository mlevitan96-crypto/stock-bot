# ALPACA post-era trade activity (read-only)

**Generated (UTC):** 2026-03-25T18:00:35.392557+00:00
**Host:** Alpaca droplet (`/root/stock-bot` logs)

## Era pin

- **strict_epoch_start (epoch):** `1774458080.0`
- **strict_epoch_start_iso:** `2026-03-25T17:01:20Z`
- **Proof summary file:** `/root/stock-bot/reports/ALPACA_STRICT_ERA_ENTRY_FILTER_FIX_PROOF_SUMMARY_20260325_1741Z.md`

## Opens count

**count_post_era_opens:** 62

(Open = `trade_id` matching `open_<SYM>_<ISO8601>` with parsed open time ≥ era pin; scanned attribution, run.jsonl entered intents, unified entry, exit_attribution trade_ids.)

## Closes count

**count_post_era_closes:** 29

(Terminal closes: unified `alpaca_exit_attribution` with `terminal_close` and close ts ≥ era; plus `exit_attribution.jsonl` deduped.)

## Status (A / B / C)

STATUS_B - Opens and closes exist (learning should arm on next strict run)

## Execution vs learning

Read-only log scan. **LEARNING_STATUS / strict completeness gate does not disable stock-bot order placement**; post-era **opens** in logs indicate execution is producing entries.

## Raw diagnostic output

```
=== PHASE 0 ===
proof_summary_file /root/stock-bot/reports/ALPACA_STRICT_ERA_ENTRY_FILTER_FIX_PROOF_SUMMARY_20260325_1741Z.md
strict_epoch_start 1774458080.0
strict_epoch_start_iso 2026-03-25T17:01:20Z
=== PHASE 1 ===
count_post_era_opens 62
sample_open 1 GM open_GM_2026-03-25T17:35:44.888932+00:00 2026-03-25T17:35:44.888932+00:00 attribution.jsonl
sample_open 2 SLB open_SLB_2026-03-25T17:35:58.865649+00:00 2026-03-25T17:35:58.865649+00:00 attribution.jsonl
sample_open 3 TSLA open_TSLA_2026-03-25T17:36:01.461206+00:00 2026-03-25T17:36:01.461206+00:00 attribution.jsonl
sample_open 4 MRNA open_MRNA_2026-03-25T17:36:20.278172+00:00 2026-03-25T17:36:20.278172+00:00 attribution.jsonl
sample_open 5 COIN open_COIN_2026-03-25T17:36:36.847948+00:00 2026-03-25T17:36:36.847948+00:00 attribution.jsonl
=== PHASE 2 ===
count_post_era_closes 29
sample_close 1 AMD open_AMD_2026-03-25T17:00:34.675846+00:00 2026-03-25T17:31:19.010694+00:00 alpaca_unified_events.jsonl
sample_close 2 AMZN open_AMZN_2026-03-25T16:55:39.648677+00:00 2026-03-25T17:31:22.289151+00:00 alpaca_unified_events.jsonl
sample_close 3 BA open_BA_2026-03-25T17:00:03.584932+00:00 2026-03-25T17:31:25.531246+00:00 alpaca_unified_events.jsonl
sample_close 4 BAC open_BAC_2026-03-25T16:52:51.211013+00:00 2026-03-25T17:31:29.055576+00:00 alpaca_unified_events.jsonl
sample_close 5 COIN open_COIN_2026-03-25T16:58:41.514540+00:00 2026-03-25T17:31:30.761966+00:00 alpaca_unified_events.jsonl
=== PHASE 3 ===
STATUS_B - Opens and closes exist (learning should arm on next strict run)
=== EXECUTION NOTE ===
LEARNING_STATUS does not disable stock-bot execution; this check is log-only.
```
