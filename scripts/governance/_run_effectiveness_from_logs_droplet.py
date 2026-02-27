#!/usr/bin/env python3
"""Run effectiveness from logs on droplet (--start --end) then generate recommendation."""
import base64
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

# Date range: last 14 days from today (UTC) so we have some data
from datetime import datetime, timedelta, timezone
end = datetime.now(timezone.utc).date()
start = end - timedelta(days=14)
start_str = start.strftime("%Y-%m-%d")
end_str = end.strftime("%Y-%m-%d")

# Deploy scripts if not already (we need run_effectiveness_reports, attribution_loader, generate_recommendation)
# Then run: effectiveness from logs, then generate_recommendation to a temp out dir
# We'll use reports/effectiveness_from_logs_<date> as out dir and then run generate_recommendation with --effectiveness-dir
out_dir = f"reports/effectiveness_from_logs_{end_str}"

pipeline = (
    f"cd /root/stock-bot && "
    f"python3 scripts/analysis/run_effectiveness_reports.py --start {start_str} --end {end_str} --out-dir {out_dir} && "
    f"python3 scripts/governance/generate_recommendation.py --effectiveness-dir {out_dir} --out {out_dir}"
)

from droplet_client import DropletClient
with DropletClient() as c:
    out, err, code = c._execute_with_cd(pipeline, timeout=120000)
    print("Exit code:", code)
    print(out or "")
    if err:
        print("STDERR:", err, file=sys.stderr)
    # Fetch the recommendation content
    if code == 0:
        out2, _, _ = c._execute_with_cd(f"cd /root/stock-bot && cat {out_dir}/profitability_recommendation.md 2>/dev/null || cat {out_dir}/*.md 2>/dev/null || true", timeout=5000)
        print("--- Recommendation ---")
        print(out2 or "(no md)")
sys.exit(0 if code == 0 else 1)
