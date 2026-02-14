# Backtests

## 30-day backtest (droplet only)

Full 30-day historical replay from logs. **Run on the droplet only** (has access to `logs/` and `state/`).

### Quick run

```bash
cd /root/stock-bot-current  # or /root/stock-bot
bash board/eod/run_30d_backtest_on_droplet.sh
```

### Steps (what the script does)

1. **Sync repo** – `git fetch && git checkout main && git pull --rebase`
2. **Config** – Writes `backtests/config/30d_backtest_config.json` (last 30 days, all flags on).
3. **Run backtest** – `python3 scripts/run_30d_backtest_droplet.py`  
   Replays from:
   - `logs/attribution.jsonl` → executed trades
   - `logs/exit_attribution.jsonl` → exits (regime, reason)
   - `state/blocked_trades.jsonl` → blocked candidates
4. **Outputs** (under `backtests/30d/`):
   - `backtest_trades.jsonl` – trades in window
   - `backtest_exits.jsonl` – exits with regime/reason
   - `backtest_blocks.jsonl` – blocked trades in window
   - `backtest_summary.json` – counts, P&L, win rate, reason counts
   - `backtest_review_for_mark.md` – short summary for review
5. **Optional push** – Set `PUSH_BACKTEST_RESULTS=1` to commit and push artifacts to GitHub.

### Config flags (in `30d_backtest_config.json`)

- `use_exit_regimes`, `use_uw`, `use_survivorship`, `use_constraints`, `use_correlation_sizing`, `use_wheel_strategy` – used as metadata in the replay (logs already reflect these systems).
- `log_all_candidates`, `log_all_exits`, `log_all_blocks` – ensure we write all replayed candidates, exits, and blocks.

### Manual run (without the shell script)

```bash
python3 scripts/write_30d_backtest_config.py
python3 scripts/run_30d_backtest_droplet.py
```
