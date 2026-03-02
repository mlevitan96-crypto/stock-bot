#!/usr/bin/env python3
"""
Run real-trades board diagnostic ON THE DROPLET via SSH, then fetch REAL_TRADES_BOARD_VERDICT.md to local.
Run from repo root: python scripts/run_real_trades_board_diagnostic_via_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found; ensure droplet_config.json and paramiko available", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    root_out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    root = None
    with DropletClient() as c:
        root = get_root(c)
        cd = f"cd {root}"
        # Upload diagnostic script
        sftp = c._connect().open_sftp()
        try:
            local_script = REPO / "scripts" / "run_real_trades_board_diagnostic.py"
            if local_script.exists():
                sftp.put(str(local_script), f"{root}/scripts/run_real_trades_board_diagnostic.py")
                print("Uploaded run_real_trades_board_diagnostic.py")
        finally:
            sftp.close()
        # Run (env is the droplet's .env when run via systemd; for ad-hoc we pass recommended env)
        cmd = f"{cd} && UW_MISSING_INPUT_MODE=passthrough python3 scripts/run_real_trades_board_diagnostic.py 2>&1"
        out, err, rc = c._execute(cmd, timeout=60)
        print("\n--- Diagnostic output (on droplet) ---")
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        # Fetch verdict
        remote_md = f"{root}/reports/audit/REAL_TRADES_BOARD_VERDICT.md"
        out_dir = REPO / "reports" / "audit"
        out_dir.mkdir(parents=True, exist_ok=True)
        local_md = out_dir / "REAL_TRADES_BOARD_VERDICT.md"
        try:
            sftp = c._connect().open_sftp()
            sftp.get(remote_md, str(local_md))
            sftp.close()
            print(f"\nFetched verdict to {local_md}")
        except Exception as e:
            print(f"Could not fetch verdict file: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
