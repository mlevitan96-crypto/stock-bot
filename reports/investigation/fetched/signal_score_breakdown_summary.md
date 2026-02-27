# Signal score breakdown summary

No logs/signal_score_breakdown.jsonl found. Run with SIGNAL_SCORE_BREAKDOWN_LOG=1 until >= 100 candidates.

## DROPLET COMMANDS

```bash
cd /root/stock-bot
export SIGNAL_SCORE_BREAKDOWN_LOG=1
# run paper/live until 100+ candidates
wc -l logs/signal_score_breakdown.jsonl
python3 scripts/signal_score_breakdown_summary_on_droplet.py
```