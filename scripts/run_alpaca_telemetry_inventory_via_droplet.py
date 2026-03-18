#!/usr/bin/env python3
"""Upload inventory script and run on droplet; fetch ALPACA_TELEMETRY_INVENTORY.md."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    c = DropletClient()
    proj = c.project_dir.replace("~", "/root")
    local = REPO / "scripts" / "alpaca_telemetry_inventory_droplet.py"
    remote = f"{proj.rstrip('/')}/scripts/alpaca_telemetry_inventory_droplet.py"
    try:
        c.put_file(str(local), remote)
    except Exception as e:
        print("upload:", e)
    o, e, rc = c._execute(f"cd {proj} && python3 scripts/alpaca_telemetry_inventory_droplet.py", timeout=120)
    print(o or e or "")
    try:
        c.get_file("reports/audit/ALPACA_TELEMETRY_INVENTORY.md", REPO / "reports" / "audit" / "ALPACA_TELEMETRY_INVENTORY.md")
    except Exception as ex:
        print("fetch:", ex)
    return rc


if __name__ == "__main__":
    sys.exit(main())
