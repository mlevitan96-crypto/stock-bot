#!/usr/bin/env python3
"""Run blocked_expectancy_analysis.py on droplet, then fetch extracted_candidates.jsonl, replay_results.jsonl, bucket_analysis.md."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "blocked_expectancy"

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with DropletClient() as c:
        root = (
            c._execute("([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot")[0]
            or "/root/stock-bot"
        ).strip()
        cmd = f"cd {root} && python3 scripts/blocked_expectancy_analysis.py 2>&1"
        out, err, rc = c._execute(cmd, timeout=300)
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        # Fetch outputs
        for name in ["extracted_candidates.jsonl", "replay_results.jsonl", "bucket_analysis.md"]:
            remote = f"{root}/reports/blocked_expectancy/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=10)
            if content:
                (OUT_DIR / name).write_text(content, encoding="utf-8")
                print(f"Fetched {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
