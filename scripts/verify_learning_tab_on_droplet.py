#!/usr/bin/env python3
"""Verify Learning tab and /api/learning_readiness on droplet after deploy."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    # Single SSH session: pull, restart dashboard, wait, then curl and check page
    script = f"""
cd {proj} && git fetch origin && git reset --hard origin/main 2>/dev/null || true
pkill -f dashboard.py 2>/dev/null; sleep 2
nohup venv/bin/python -u dashboard.py >> logs/dashboard.log 2>&1 & sleep 1
sleep 12
echo '---HTTP---'
curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:5000/api/learning_readiness 2>/dev/null || echo 000
echo ''
echo '---BODY---'
curl -s http://127.0.0.1:5000/api/learning_readiness 2>/dev/null | head -c 400
echo ''
echo '---PAGE---'
curl -s http://127.0.0.1:5000/ 2>/dev/null | grep -o 'learning_readiness\\|direction-banner\\|situation-strip' | sort -u
"""
    with DropletClient() as c:
        out, err, rc = c._execute(script, timeout=60000)
    text = (out or "") + (err or "")
    if "---HTTP---" in text:
        after = text.split("---HTTP---", 1)[-1]
        code_part = after.split("---BODY---")[0].strip().split()[0] if "---BODY---" in after else ""
        http_code = code_part.strip()
    else:
        http_code = ""
    if http_code != "200":
        print(f"FAIL: /api/learning_readiness returned HTTP {http_code!r}. Output: {text[:800]}")
        return 1
    if "telemetry_trades" not in text:
        print("FAIL: response missing telemetry_trades. Output:", text[:600])
        return 1
    print("OK: /api/learning_readiness returns 200 with telemetry_trades")
    if "---PAGE---" in text:
        page_part = text.split("---PAGE---", 1)[-1]
        if "direction-banner" in page_part or "situation-strip" in page_part:
            print("FAIL: page still contains old banner ids")
            return 1
        if "learning_readiness" not in page_part:
            print("FAIL: page missing learning_readiness tab")
            return 1
    print("OK: banners removed, Learning tab present")
    print("All checks passed. Learning tab is live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
