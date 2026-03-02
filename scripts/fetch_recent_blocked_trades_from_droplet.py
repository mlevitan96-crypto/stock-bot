#!/usr/bin/env python3
"""
Fetch recent blocked trades from the droplet and print why they were blocked.
Run from repo root. Requires droplet_config.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    n = 20
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except ValueError:
            pass
    with DropletClient() as c:
        root = get_root(c)
        out, err, rc = c._execute(
            f"tail -n {n} {root}/state/blocked_trades.jsonl 2>/dev/null || echo ''",
            timeout=10,
        )
        if err:
            print(err, file=sys.stderr)
        lines = [s.strip() for s in (out or "").strip().splitlines() if s.strip()]
        if not lines:
            print("No blocked_trades.jsonl lines found.")
            return 0
        print(f"Last {len(lines)} blocked trades (symbol, reason, score, composite_pre_norm, composite_post_norm):")
        print("-" * 100)
        for line in lines:
            try:
                rec = json.loads(line)
                symbol = rec.get("symbol", "?")
                reason = rec.get("reason", rec.get("block_reason", "?"))
                score = rec.get("score")
                att = rec.get("attribution_snapshot") or {}
                pre = att.get("composite_pre_norm")
                post = att.get("composite_post_norm")
                print(f"  {symbol:6}  reason={reason}  score={score}  pre_norm={pre}  post_norm={post}")
            except Exception as e:
                print(f"  (parse error: {e})  {line[:80]}...")
        # UW daemon status
        out2, _, _ = c._execute("systemctl is-active uw-flow-daemon.service 2>/dev/null || echo 'inactive'", timeout=5)
        daemon_status = (out2 or "").strip()
        print("-" * 100)
        print(f"UW daemon (uw-flow-daemon.service): {daemon_status}")
        if daemon_status != "active":
            out3, _, _ = c._execute("systemctl status uw-flow-daemon.service --no-pager 2>&1 | head -15", timeout=5)
            print(out3 or "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
