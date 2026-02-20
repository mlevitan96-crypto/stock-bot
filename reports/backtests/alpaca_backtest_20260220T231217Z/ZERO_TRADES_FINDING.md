# Why This Run Shows Zero Trades

## Short answer

**Zero trades are because no executed trades were logged in the replay window on the droplet**, not because the backtest script fails to find them.

## How the 30d backtest works

The baseline step (`run_30d_backtest_droplet.py`) **replays existing logs**; it does **not** simulate trades from signals.

- **Trades** come from `logs/attribution.jsonl` (executed paper/live trades in the date window).
- **Exits** from `logs/exit_attribution.jsonl`.
- **Blocks** from `state/blocked_trades.jsonl`.

So:

- **0 trades** = no records in `logs/attribution.jsonl` in the run window (2026-01-15 to 2026-02-14) on the droplet.
- **740 exits** = records were present in `logs/exit_attribution.jsonl` in that window (exits can exist without matching entries if attribution is partial or from a different pipeline).

## What to check on the droplet

1. **Does `logs/attribution.jsonl` exist and have lines in the window?**  
   e.g. `wc -l logs/attribution.jsonl` and `grep -E "2026-01|2026-02" logs/attribution.jsonl | head`.
2. **Is paper/live actually placing and filling trades?**  
   If the live/paper loop isn’t opening positions or isn’t logging to attribution, the replay will still show 0 trades.
3. **Date window vs droplet data:**  
   Config uses last 30 days; if the droplet has no attribution in that range, you’ll get 0 trades.

## Conclusion

- The backtest is **finding** everything that’s in the logs; it’s not missing trades.
- Zero trades here means **signals / paper pipeline are not producing executed trades that get written to `logs/attribution.jsonl`** in that window on the droplet, or that file is empty/missing for that period.

For a backtest that **generates** trades from signals (instead of replaying attribution), you’d need a different pipeline (e.g. historical replay engine or signal-driven simulator) that writes to attribution or to a backtest-specific trade file.
