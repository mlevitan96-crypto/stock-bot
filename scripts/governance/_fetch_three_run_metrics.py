#!/usr/bin/env python3
"""Fetch aggregate metrics for the three tune runs from droplet. Prints JSON to stdout."""
import base64
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

script = """
import json
def agg(path):
    total_pnl = 0.0
    wins = 0
    givebacks = []
    n = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line)
                pnl = float(r.get("pnl") or 0)
                total_pnl += pnl
                if pnl > 0: wins += 1
                gb = r.get("exit_quality_metrics", {}).get("profit_giveback")
                if gb is not None: givebacks.append(float(gb))
                n += 1
            except: continue
    return {"total_trades": n, "total_pnl_usd": round(total_pnl, 2), "win_rate": round(wins/n, 4) if n else 0, "avg_profit_giveback": round(sum(givebacks)/len(givebacks), 4) if givebacks else None}
dirs = [
    ("baseline", "backtests/30d_tune_baseline_20260218_040651/backtest_exits.jsonl"),
    ("flow022", "backtests/30d_tune_flow022_20260218_040706/backtest_exits.jsonl"),
    ("score028", "backtests/30d_tune_score028_20260218_040930/backtest_exits.jsonl"),
]
out = {name: agg(path) for name, path in dirs}
print(json.dumps(out, indent=2))
"""
b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
from droplet_client import DropletClient
with DropletClient() as c:
    cmd = 'cd /root/stock-bot && python3 -c \'import base64; exec(base64.b64decode("%s").decode())\'' % b64
    out, err, code = c._execute_with_cd(cmd, timeout=120000)
    if code != 0:
        print(err or out, file=sys.stderr)
        sys.exit(code)
    print(out.strip())
