# 01 Runtime health

## tmux ls
```
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
stock_bot_paper_run: 1 windows (created Wed Feb 18 19:31:50 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)
```

## tmux capture-pane (stock_bot_paper_run, last 200 lines)
```
DEBUG: Computing composite score for COIN (symbol 33/57)
DEBUG: COIN composite_score=0.921
DEBUG: Sector Tide boost applied to COIN: +0.30 (sector=Financial, count=12)
DEBUG: Persistence boost applied to COIN: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for COIN: score=1.72 < threshold=2.70
DEBUG: Logged rejected signal to history: COIN score=1.72 reason=score=1.72 < th
reshold=2.70
DEBUG: Composite signal REJECTED for COIN: score=1.72 < threshold=2.70
DEBUG: Computing composite score for TSLA (symbol 34/57)
DEBUG: TSLA composite_score=0.632
DEBUG: Sector Tide boost applied to TSLA: +0.30 (sector=Technology, count=10)
DEBUG: Persistence boost applied to TSLA: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for TSLA: score=1.43 < threshold=2.70
DEBUG: Logged rejected signal to history: TSLA score=1.43 reason=score=1.43 < th
reshold=2.70
DEBUG: Composite signal REJECTED for TSLA: score=1.43 < threshold=2.70
DEBUG: Computing composite score for SPY (symbol 35/57)
DEBUG: SPY composite_score=0.184
DEBUG: Sector Tide boost applied to SPY: +0.30 (sector=ETF, count=10)
DEBUG: Persistence boost applied to SPY: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for SPY: score=0.98 < threshold=2.70
DEBUG: Logged rejected signal to history: SPY score=0.98 reason=score=0.98 < thr
eshold=2.70
DEBUG: Composite signal REJECTED for SPY: score=0.98 < threshold=2.70
DEBUG: Computing composite score for C (symbol 36/57)
DEBUG: C composite_score=0.280
DEBUG: Sector Tide boost applied to C: +0.30 (sector=Financial, count=12)
DEBUG: Persistence boost applied to C: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for C: score=1.08 < threshold=2.70
DEBUG: Logged rejected signal to history: C score=1.08 reason=score=1.08 < thres
hold=2.70
DEBUG: Composite signal REJECTED for C: score=1.08 < threshold=2.70
DEBUG: Computing composite score for XLE (symbol 37/57)
DEBUG: XLE composite_score=0.719
DEBUG: Sector Tide boost applied to XLE: +0.30 (sector=ETF, count=10)
DEBUG: Persistence boost applied to XLE: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for XLE: score=1.52 < threshold=2.70
DEBUG: Logged rejected signal to history: XLE score=1.52 reason=score=1.52 < thr
eshold=2.70
DEBUG: Composite signal REJECTED for XLE: score=1.52 < threshold=2.70
DEBUG: Computing composite score for GS (symbol 38/57)
DEBUG: GS composite_score=0.385
DEBUG: Sector Tide boost applied to GS: +0.30 (sector=Financial, count=12)
DEBUG: Persistence boost applied to GS: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for GS: score=1.19 < threshold=2.70
DEBUG: Logged rejected signal to history: GS score=1.19 reason=score=1.19 < thre
shold=2.70
DEBUG: Composite signal REJECTED for GS: score=1.19 < threshold=2.70
DEBUG: Computing composite score for BA (symbol 39/57)
DEBUG: BA composite_score=0.697
DEBUG: Persistence boost applied to BA: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for BA: score=1.20 < threshold=2.70
DEBUG: Logged rejected signal to history: BA score=1.20 reason=score=1.20 < thre
shold=2.70
DEBUG: Composite signal REJECTED for BA: score=1.20 < threshold=2.70
DEBUG: Computing composite score for NFLX (symbol 40/57)
DEBUG: NFLX composite_score=0.397
DEBUG: Sector Tide boost applied to NFLX: +0.30 (sector=Technology, count=10)
DEBUG: Persistence boost applied to NFLX: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for NFLX: score=1.20 < threshold=2.70
DEBUG: Logged rejected signal to history: NFLX score=1.20 reason=score=1.20 < th
reshold=2.70
DEBUG: Composite signal REJECTED for NFLX: score=1.20 < threshold=2.70
DEBUG: Computing composite score for TGT (symbol 41/57)
DEBUG: TGT composite_score=0.305
DEBUG: Sector Tide boost applied to TGT: +0.30 (sector=Consumer, count=10)
DEBUG: Persistence boost applied to TGT: +0.50 (count=15, whale_motif=True)
DEBUG: Composite signal REJECTED for TGT: score=1.10 < thres
```

## state/live_paper_run_state.json
```
{
  "status": "live_paper_run_started",
  "timestamp": 1771443113,
  "details": {
    "trading_mode": "paper",
    "process": "python3 main.py",
    "session": "stock_bot_paper_run",
    "governed_tuning_config": ""
  }
}
```

## Checks
- Tmux session present: **True**
- No GOVERNED_TUNING_CONFIG / no overlay in state: **True**