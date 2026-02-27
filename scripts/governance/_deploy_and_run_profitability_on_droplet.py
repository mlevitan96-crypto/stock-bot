#!/usr/bin/env python3
"""
Deploy scripts needed for profitability pipeline to droplet, then run pipeline on a backtest dir.
Uses base64 to write scripts/analysis/* and scripts/governance/* so droplet can run run_profitability.
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

# Files to deploy (relative to REPO)
FILES = [
    "scripts/analysis/attribution_loader.py",
    "scripts/analysis/run_effectiveness_reports.py",
    "scripts/governance/regression_guards.py",
    "scripts/governance/profitability_baseline_and_recommend.py",
    "scripts/governance/generate_recommendation.py",
]

def main():
    backtest_dir = "backtests/30d_tune_baseline_20260218_040651"
    for rel in FILES:
        path = REPO / rel
        if not path.exists():
            print(f"Skip (missing): {rel}", file=sys.stderr)
            continue
        content = path.read_bytes()
        b64 = base64.b64encode(content).decode("ascii")
        # Write on droplet: mkdir -p dirname; python3 -c "import base64,os; p='...'; os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'wb').write(base64.b64decode('...'))"
        escaped_path = rel.replace("'", "'\"'\"'")
        cmd = (
            f"cd /root/stock-bot && python3 -c \""
            f"import base64,os; "
            f"p='{rel}'; "
            f"os.makedirs(os.path.dirname(p),exist_ok=True); "
            f"open(p,'wb').write(base64.b64decode('{b64}')); "
            f"print('wrote',p)\""
        )
        from droplet_client import DropletClient
        with DropletClient() as c:
            out, err, code = c._execute_with_cd(cmd, timeout=30000)
            if code != 0:
                print(f"Failed {rel}: {err or out}", file=sys.stderr)
                return 1
            print(f"Deployed {rel}")
    # Run pipeline
    from droplet_client import DropletClient
    pipeline = (
        f"cd /root/stock-bot && "
        f"python3 scripts/analysis/run_effectiveness_reports.py --backtest-dir {backtest_dir} --out-dir {backtest_dir}/effectiveness && "
        f"python3 scripts/governance/regression_guards.py && "
        f"python3 scripts/governance/profitability_baseline_and_recommend.py --effectiveness-dir {backtest_dir}/effectiveness --out {backtest_dir} && "
        f"python3 scripts/governance/generate_recommendation.py --backtest-dir {backtest_dir}"
    )
    with DropletClient() as c:
        out, err, code = c._execute_with_cd(pipeline, timeout=120000)
        print("Pipeline exit code:", code)
        print(out or "")
        if err:
            print("STDERR:", err, file=sys.stderr)
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
