#!/usr/bin/env python3
"""
Run droplet-native refresh of symbol risk features (vol/beta).
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from droplet_client import DropletClient


def main() -> int:
    payload_path = Path("reports") / "_daily_review_tools" / "droplet_refresh_symbol_risk_features_payload.py"
    code = payload_path.read_text(encoding="utf-8")
    b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")

    remote_cmd = (
        "cd /root/stock-bot"
        " && /root/stock-bot/venv/bin/python -c "
        "'import base64; exec(base64.b64decode(\"" + b64 + "\").decode(\"utf-8\"))'"
    )

    with DropletClient() as c:
        r = c.execute_command(remote_cmd, timeout=240)
        out = (r.get("stdout") or r.get("stderr") or "").strip()
        print(out)
        return 0 if r.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

