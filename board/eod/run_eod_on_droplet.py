#!/usr/bin/env python3
"""Run EOD script on droplet: deploy board/eod + contract via SFTP, cd /root/stock-bot, export CLAWDBOT_SESSION_ID, run EOD."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REMOTE_ROOT = "/root/stock-bot"
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    c = DropletClient()
    try:
        ssh = c._connect()
        sftp = ssh.open_sftp()

        def ensure_remote_dir(path: str) -> None:
            try:
                sftp.stat(path)
            except FileNotFoundError:
                try:
                    sftp.mkdir(path)
                except Exception:
                    pass

        ensure_remote_dir(f"{REMOTE_ROOT}/board")
        ensure_remote_dir(f"{REMOTE_ROOT}/board/eod")
        ensure_remote_dir(f"{REMOTE_ROOT}/board/eod/out")

        local_eod = REPO / "board" / "eod" / "run_stock_quant_officer_eod.py"
        local_contract = REPO / "board" / "stock_quant_officer_contract.md"
        sftp.put(str(local_eod), f"{REMOTE_ROOT}/board/eod/run_stock_quant_officer_eod.py")
        sftp.put(str(local_contract), f"{REMOTE_ROOT}/board/stock_quant_officer_contract.md")
        sftp.close()

        cmd = "export CLAWDBOT_SESSION_ID=\"stock_quant_eod_$(date -u +%Y-%m-%d)\" && python3 board/eod/run_stock_quant_officer_eod.py"
        out, err, rc = c._execute_with_cd(cmd, timeout=300)
        print("=== stdout ===")
        print(out)
        if err:
            print("=== stderr ===")
            print(err)
        print("=== exit code ===", rc)
        return rc
    finally:
        c.close()


if __name__ == "__main__":
    sys.exit(main())
