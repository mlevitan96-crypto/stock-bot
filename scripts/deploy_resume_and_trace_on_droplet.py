#!/usr/bin/env python3
"""Deploy enable_alpaca_bars_resume.sh to droplet then run bash -x trace (no detached start)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
ROOT = "/root/stock-bot"

def main() -> int:
    from droplet_client import DropletClient
    with DropletClient() as c:
        c._execute("true", timeout=5)
        sftp = c.ssh_client.open_sftp()
        content = (REPO / "scripts" / "enable_alpaca_bars_resume.sh").read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        from io import BytesIO
        sftp.putfo(BytesIO(content), f"{ROOT}/scripts/enable_alpaca_bars_resume.sh")
        sftp.close()
        cmd = f"cd {ROOT} && bash -x scripts/enable_alpaca_bars_resume.sh > reports/bars/interactive_trace_after_fix.log 2>&1; echo TRACE_EXIT=$?"
        c._execute(cmd, timeout=300)
        out, _, _ = c._execute(f"wc -l {ROOT}/reports/bars/fetch_debug.log 2>/dev/null; tail -20 {ROOT}/reports/bars/fetch_debug.log 2>/dev/null", timeout=10)
    print("--- fetch_debug.log line count + tail ---")
    print(out or "(empty)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
