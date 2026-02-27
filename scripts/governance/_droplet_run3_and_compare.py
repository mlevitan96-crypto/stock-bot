#!/usr/bin/env python3
"""Create score overlay on droplet, run Run 3, then fetch aggregate metrics for all three runs."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

overlay = {"version": "2026-02-18_exit_score_plus_0.03", "exit_weights": {"score_deterioration": 0.28}}
b64 = __import__("base64").b64encode(json.dumps(overlay).encode()).decode()
create_cmd = (
    "cd /root/stock-bot && mkdir -p config/tuning/overlays && python3 -c "
    "'import base64,json; d=json.loads(base64.b64decode(\"%s\").decode()); "
    "open(\"config/tuning/overlays/exit_score_weight_tune.json\",\"w\").write(json.dumps(d,indent=2))'"
) % b64

run3_cmd = (
    "cd /root/stock-bot && OUT_DIR_PREFIX=30d_tune_score028 "
    "GOVERNED_TUNING_CONFIG=config/tuning/overlays/exit_score_weight_tune.json "
    "BACKTEST_DAYS=7 bash board/eod/run_30d_backtest_on_droplet.sh"
)

from droplet_client import DropletClient

with DropletClient() as c:
    out1, _, code1 = c._execute_with_cd(create_cmd, timeout=15000)
    print("Create overlay:", code1, out1[:500] if out1 else "")
    if code1 != 0:
        sys.exit(1)
    out2, err2, code2 = c._execute_with_cd(run3_cmd, timeout=600000)
    print("Run 3 exit code:", code2)
    print("Run 3 stdout (last 1800 chars):", (out2 or "")[-1800:])
    if err2:
        print("Run 3 stderr (last 600 chars):", err2[-600:])
