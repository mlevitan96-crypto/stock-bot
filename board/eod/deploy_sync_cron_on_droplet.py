#!/usr/bin/env python3
"""Deploy droplet_sync_to_github.sh to droplet, chmod +x, add cron 21:32 UTC weekdays."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REMOTE_ROOT = "/root/stock-bot"
CRON_LINE = "32 21 * * 1-5 /root/stock-bot/scripts/droplet_sync_to_github.sh >> /root/stock-bot/cron_sync.log 2>&1"


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    local_sh = REPO / "scripts" / "droplet_sync_to_github.sh"
    if not local_sh.exists():
        print(f"Missing {local_sh}", file=sys.stderr)
        return 1

    c = DropletClient()
    try:
        ssh = c._connect()
        sftp = ssh.open_sftp()
        text = local_sh.read_text(encoding="utf-8", errors="replace")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        import io
        sftp.putfo(io.BytesIO(text.encode("utf-8")), f"{REMOTE_ROOT}/scripts/droplet_sync_to_github.sh")
        sftp.close()
        print("Uploaded droplet_sync_to_github.sh")

        c._execute(f"chmod +x {REMOTE_ROOT}/scripts/droplet_sync_to_github.sh", timeout=5)
        print("chmod +x done")

        install = (
            "(crontab -l 2>/dev/null | grep -v 'droplet_sync_to_github.sh' || true; "
            f"printf '%s\\n' '{CRON_LINE}') | crontab -"
        )
        out, err, rc = c._execute(install, timeout=10)
        if rc != 0:
            print("crontab install failed:", out or err, file=sys.stderr)
            return rc
        print("Cron job added (32 21 * * 1-5)")

        out2, _, _ = c._execute("crontab -l", timeout=5)
        print("crontab -l:\n", out2)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
