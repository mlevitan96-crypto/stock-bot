#!/usr/bin/env python3
"""Run CURSOR_BIND_CTR_TO_STOCK_BOT_SERVICE.sh on droplet via DropletClient. Uploads script then runs."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "truth" / "CURSOR_BIND_CTR_TO_STOCK_BOT_SERVICE.sh"


def main() -> int:
    if not SCRIPT.is_file():
        print(f"Missing script: {SCRIPT}", file=sys.stderr)
        return 1
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    remote = f"{pd}/scripts/truth/CURSOR_BIND_CTR_TO_STOCK_BOT_SERVICE.sh"

    with DropletClient() as c:
        c._execute(f"mkdir -p {pd}/scripts/truth", timeout=5)
        c.put_file(SCRIPT, remote)
        c._execute(f"sed -i 's/\\r$//' {remote}; chmod +x {remote}", timeout=5)
        cmd = f"cd {c.project_dir} && REPO={c.project_dir} bash scripts/truth/CURSOR_BIND_CTR_TO_STOCK_BOT_SERVICE.sh"
        out, err, rc = c._execute(cmd, timeout=120)
    print(out)
    if err:
        print(err, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
