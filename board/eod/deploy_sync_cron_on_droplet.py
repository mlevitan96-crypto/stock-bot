#!/usr/bin/env python3
"""Deploy droplet_sync_to_github.sh to droplet, chmod +x, add cron 21:32 UTC weekdays. Path-agnostic."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def detect_stockbot_root(client) -> str:
    """Detect stock-bot root on droplet: prefer stock-bot-current, fallback stock-bot."""
    cmd = (
        "ROOT=/root/stock-bot; "
        "[ -d /root/stock-bot-current/scripts ] && [ -d /root/stock-bot-current/config ] "
        "&& [ -f /root/stock-bot-current/board/eod/run_stock_quant_officer_eod.py ] "
        "&& ROOT=/root/stock-bot-current; echo $ROOT"
    )
    out, _, _ = client._execute(cmd, timeout=5)
    return (out or "").strip() or "/root/stock-bot"


def main() -> int:
    from droplet_client import DropletClient

    c = DropletClient()
    remote_root = detect_stockbot_root(c)

    local_sh = REPO / "scripts" / "droplet_sync_to_github.sh"
    if not local_sh.exists():
        print(f"Missing {local_sh}", file=sys.stderr)
        return 1

    try:
        ssh = c._connect()
        sftp = ssh.open_sftp()
        text = local_sh.read_text(encoding="utf-8", errors="replace")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        import io
        sftp.putfo(io.BytesIO(text.encode("utf-8")), f"{remote_root}/scripts/droplet_sync_to_github.sh")
        sftp.close()
        print("Uploaded droplet_sync_to_github.sh")

        c._execute(f"chmod +x {remote_root}/scripts/droplet_sync_to_github.sh", timeout=5)
        print("chmod +x done")

        cron_line = f"32 21 * * 1-5 cd {remote_root} && bash scripts/droplet_sync_to_github.sh >> {remote_root}/logs/cron_sync.log 2>&1"
        c._execute(f"mkdir -p {remote_root}/logs", timeout=5)
        install = (
            "(crontab -l 2>/dev/null | grep -v 'droplet_sync_to_github.sh' || true; "
            f"printf '%s\\n' '{cron_line}') | crontab -"
        )
        out, err, rc = c._execute(install, timeout=10)
        if rc != 0:
            print("crontab install failed:", out or err, file=sys.stderr)
            return rc
        print("Cron job added (32 21 * * 1-5, path-agnostic)")

        out2, _, _ = c._execute("crontab -l", timeout=5)
        print("crontab -l:\n", out2)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
