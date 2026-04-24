"""Pull latest ALPACA_CONNECTIVITY_AUDIT_*.md from droplet into ./reports/."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from droplet_client import DropletClient

ROOT = "/root/stock-bot"


def main() -> int:
    with DropletClient() as c:
        o, _, _ = c._execute(
            f"ls -t {ROOT}/reports/ALPACA_CONNECTIVITY_AUDIT_*.md 2>/dev/null | head -1",
            timeout=30,
        )
        remote = o.strip()
        if not remote:
            print("no connectivity audit on droplet", file=sys.stderr)
            return 1
        local = REPO / "reports" / Path(remote).name
        c.get_file(remote, str(local))
        print(local)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
