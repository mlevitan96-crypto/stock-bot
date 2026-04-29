#!/usr/bin/env python3
"""
Local entrypoint: SSH to droplet (droplet_config.json / DROPLET_* env), sync main, run ws_smoke_test with .env.

Usage (from repo root): ``python scripts/debug/run_ws_smoke_on_droplet.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from droplet_client import DropletClient  # noqa: E402


def main() -> int:
    cfg = ROOT / "droplet_config.json"
    if not cfg.is_file():
        print("Missing droplet_config.json (or use DROPLET_HOST / DROPLET_KEY_FILE).", file=sys.stderr)
        return 2
    client = DropletClient(str(cfg))
    cmd = (
        "git fetch -q origin && git reset --hard -q origin/main && "
        "set -a && [ -f .env ] && . ./.env; set +a && "
        "./venv/bin/python scripts/debug/ws_smoke_test.py"
    )
    r = client.execute_command(cmd, timeout=120)
    print(r.get("stdout") or "", end="")
    err = r.get("stderr") or ""
    if err.strip():
        print(err, file=sys.stderr, end="")
    ec = int(r.get("exit_code") or 1)
    print(f"\n[droplet exit_code={ec}]", flush=True)
    return ec


if __name__ == "__main__":
    raise SystemExit(main())
