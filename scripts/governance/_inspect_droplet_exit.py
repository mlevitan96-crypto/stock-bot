import base64, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
script = """
import json
p = "backtests/30d_tune_baseline_20260218_040651/backtest_exits.jsonl"
with open(p) as f:
    r = json.loads(f.readline())
print("keys:", list(r.keys())[:25])
print("entry_timestamp:", r.get("entry_timestamp"))
print("symbol:", r.get("symbol"))
"""
b64 = base64.b64encode(script.encode()).decode()
from droplet_client import DropletClient
with DropletClient() as c:
    out, err, code = c._execute_with_cd('cd /root/stock-bot && python3 -c \'import base64; exec(base64.b64decode("%s").decode())\'' % b64, timeout=15000)
    print(out or err)