# Paper restart snapshot — before (2026-02-18)

## A) Capture current truth

```
# git rev-parse HEAD
d4f694cc97a97ade2d0a53589f664d782912c0de

# tmux ls
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
stock_bot_paper_run: 1 windows (created Wed Feb 18 17:25:11 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)

# cat state/live_paper_run_state.json
{
  "status": "live_paper_run_started",
  "timestamp": 1771435516,
  "details": {
    "trading_mode": "paper",
    "process": "python3 main.py",
    "session": "stock_bot_paper_run",
    "governed_tuning_config": ""
  }
}
```