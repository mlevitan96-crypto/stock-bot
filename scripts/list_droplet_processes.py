#!/usr/bin/env python3
"""List everything running on the droplet: processes, services, cron. Run from local with droplet_config."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("Need droplet_client and droplet_config.json", file=sys.stderr)
        return 1

    def run(cmd: str, timeout: int = 20) -> str:
        out, err, rc = c._execute(cmd, timeout=timeout)
        return (out or "").strip() + ("\n" + (err or "").strip() if err else "")

    with DropletClient() as c:
        print("=== 0. Load average and top 25 processes by CPU (system-wide) ===")
        print(run("uptime"))
        print(run("ps -eo pid,pcpu,pmem,time,comm,args --no-headers --sort=-pcpu 2>/dev/null | head -26"))

        print("\n=== 1. CPU usage: stock-bot related processes (%%CPU = current, TIME = cumulative CPU) ===")
        print(run("ps -eo pid,pcpu,pmem,time,args --no-headers | grep -E 'main.py|dashboard|heartbeat|deploy_supervisor|uw_flow|cache_enrichment|systemd_start' | grep -v grep"))

        print("\n=== 3. Python / stock-bot related processes (full ps aux) ===")
        print(run("ps aux | grep -E 'python|stock-bot|uw_flow|deploy_supervisor|main.py|dashboard|heartbeat' | grep -v grep"))

        print("\n=== 4. All running systemd services ===")
        print(run("systemctl list-units --type=service --state=running --no-pager 2>/dev/null | head -80"))

        print("\n=== 5. Root crontab ===")
        print(run("crontab -l 2>/dev/null || echo '(no crontab)'"))

        print("\n=== 6. /etc/cron.d and cron.daily ===")
        print(run("ls -la /etc/cron.d/ 2>/dev/null; echo '---'; ls /etc/cron.daily/ 2>/dev/null"))

        print("\n=== 7. Top 30 processes by memory ===")
        print(run("ps aux --sort=-%mem 2>/dev/null | head -31"))

        print("\n=== 8. Process count by command name ===")
        print(run("ps -eo comm= | sort | uniq -c | sort -rn | head -30"))

        print("\n=== 9. Disk usage (df -h) ===")
        print(run("df -h"))

        print("\n=== 10. Any stock-bot systemd units (enabled or running) ===")
        print(run("systemctl list-unit-files '*stock*' '*uw*' '*trading*' 2>/dev/null; systemctl list-units --all '*stock*' '*uw*' 2>/dev/null"))

    return 0


if __name__ == "__main__":
    import io
    if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
