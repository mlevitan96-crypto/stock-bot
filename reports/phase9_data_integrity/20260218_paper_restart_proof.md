# Paper restart proof (2026-02-18)

**After running Step 1B (kill tmux, start_live_paper_run.py --date $(date +%Y-%m-%d)), run below and paste.**

## Commands

```bash
cd /root/stock-bot
tmux ls
tmux capture-pane -pt stock_bot_paper_run -S -80
cat state/live_paper_run_state.json
```

## Proof (paste here)

- [ ] No GOVERNED_TUNING_CONFIG in tmux command
- [ ] state has no overlay path / governed_tuning_config empty

```
# tmux ls
# tmux capture-pane ...
# cat state/...
```
