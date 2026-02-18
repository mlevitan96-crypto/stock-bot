# Snapshot fix — proof (droplet)

**PASS criteria:**

- [ ] `logs/score_snapshot.jsonl` exists
- [ ] snapshot_count > 0 (e.g. `wc -l logs/score_snapshot.jsonl`)
- [ ] Records have `composite_score` present and numeric
- [ ] With `SCORE_SNAPSHOT_DEBUG=1`: hook entered + write success logs observed

**Steps:**

1. Deploy current code to droplet (include commit with "Fix: ensure score snapshot emission").
2. Restart paper with debug:
   ```bash
   cd /root/stock-bot-current 2>/dev/null || cd /root/stock-bot
   tmux kill-session -t stock_bot_paper_run 2>/dev/null || true
   tmux new-session -d -s stock_bot_paper_run 'cd /root/stock-bot-current 2>/dev/null || cd /root/stock-bot; SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py'
   ```
3. Wait 5–10 minutes (or 5 cycles). Then:
   - `tmux capture-pane -t stock_bot_paper_run -p` — check for `SCORE_SNAPSHOT_DEBUG: hook entered` and `append_score_snapshot success` or `write done`.
   - `wc -l logs/score_snapshot.jsonl` — snapshot_count.
   - `head -1 logs/score_snapshot.jsonl | python3 -c "import sys,json; d=json.load(sys.stdin); print('composite_score' in d, d.get('composite_score'))"`

**Result (fill after run):**

- snapshot_count: _____
- composite_score in first record: _____
- Hook + write success logs seen: YES / NO
- **PASS / FAIL**
