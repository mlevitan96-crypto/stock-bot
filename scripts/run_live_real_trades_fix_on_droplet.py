#!/usr/bin/env python3
"""
One-shot: deploy code to droplet, set UW_MISSING_INPUT_MODE=passthrough and INJECT_SIGNAL_TEST=0, restart.
Run from repo root after pushing: python scripts/run_live_real_trades_fix_on_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found; need droplet_config.json and paramiko", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    with DropletClient() as c:
        root = get_root(c)
        cd = f"cd {root}"
        # 1) Ensure .env has UW_MISSING_INPUT_MODE=passthrough and INJECT_SIGNAL_TEST=0
        #    Use grep to check; if missing, append. Do not overwrite .env.
        for var, val in [("UW_MISSING_INPUT_MODE", "passthrough"), ("INJECT_SIGNAL_TEST", "0")]:
            check = f"grep -E '^{var}=' {root}/.env 2>/dev/null || true"
            out, _, _ = c._execute(f"{cd} && {check}", timeout=5)
            if var not in (out or ""):
                # Append (safe: no eval)
                c._execute(f"{cd} && echo '' >> .env && echo '# Real-trades fix (run_live_real_trades_fix_on_droplet)' >> .env && echo '{var}={val}' >> .env", timeout=5)
                print(f"  Appended {var}={val} to .env")
            else:
                print(f"  .env already has {var}")
        # 2) Sync code: fetch + reset so deploy is clean
        out, err, rc = c._execute(f"{cd} && git fetch origin && git reset --hard origin/main 2>&1", timeout=90)
        print("\n--- git fetch + reset ---")
        print(out or err or "ok")
        if rc != 0:
            print("Warning: git reset had non-zero exit", file=sys.stderr)
        # 3) Kill stale dashboard then restart
        c._execute(f"{cd} && pkill -f 'dashboard\\.py' 2>/dev/null; sleep 1; true", timeout=10)
        out2, err2, rc2 = c._execute(f"{cd} && sudo systemctl restart stock-bot 2>&1", timeout=60)
        print("\n--- systemctl restart stock-bot ---")
        print(out2 or err2 or "ok")
        if rc2 != 0:
            print("Restart failed", file=sys.stderr)
            return 1
        print("\nLive fix applied. Wait ~90s then: tail -1 logs/run.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
