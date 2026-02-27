#!/usr/bin/env python3
"""
Run discover_alpaca_and_run_bars.py on the droplet via SSH.
Deploys the discover script (and bars pipeline scripts if missing), then runs discover.
Prints full output including the required one-block summary.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
ROOT = "/root/stock-bot"

DEPLOY_FILES = [
    "scripts/discover_alpaca_and_run_bars.py",
    "scripts/run_bars_pipeline.py",
    "scripts/check_alpaca_env.py",
    "scripts/bars_universe_and_range.py",
    "scripts/fetch_alpaca_bars.py",
    "scripts/write_bars_cache_status.py",
    "scripts/audit_bars.py",
    "scripts/blocked_expectancy_analysis.py",
    "data/bars_loader.py",
    "scripts/run_droplet_truth_run.py",
]


def safe_print(text: str, file=None) -> None:
    if not text:
        return
    safe = text.replace("\u2192", "->").replace("\u2014", "-").encode("ascii", errors="replace").decode("ascii")
    f = file or sys.stdout
    f.write(safe)
    if not safe.endswith("\n"):
        f.write("\n")
    f.flush()


def deploy(client) -> None:
    sftp = client.ssh_client.open_sftp()
    try:
        for rel in DEPLOY_FILES:
            local = REPO / rel
            if not local.exists():
                continue
            remote = f"{ROOT}/{rel}"
            remote_dir = str(Path(remote).parent)
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                parts = Path(remote_dir).parts
                for i in range(1, len(parts) + 1):
                    d = "/".join(parts[:i])
                    if d == "/":
                        continue
                    try:
                        sftp.mkdir(d)
                    except OSError:
                        pass
            sftp.put(str(local), remote)
            safe_print(f"Deployed {rel}")
    finally:
        sftp.close()


def main() -> int:
    from droplet_client import DropletClient

    safe_print("=== Discover Alpaca + run bars (on droplet) ===\n")
    with DropletClient() as c:
        c._execute(f"cd {ROOT} && true", timeout=10)  # ensure connected
        safe_print("Deploying scripts...")
        deploy(c)
        safe_print("")
        cmd = f"cd {ROOT} && python3 scripts/discover_alpaca_and_run_bars.py"
        out, err, rc = c._execute(cmd, timeout=960)
        safe_print(out or "")
        if err:
            safe_print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
