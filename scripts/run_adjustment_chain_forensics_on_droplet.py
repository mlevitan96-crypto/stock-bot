#!/usr/bin/env python3
"""
Run adjustment chain forensics on droplet (adjustment_chain_forensics.py), then fetch reports to local.
Uses DropletClient. Run from repo root (local).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "score_autopsy"

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with DropletClient() as c:
        root_cmd = "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot"
        root_out, _, _ = c._execute(root_cmd, timeout=10)
        root = (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()
        cd = f"cd {root}"

        sftp = c._connect().open_sftp()
        try:
            local_script = REPO / "scripts" / "adjustment_chain_forensics.py"
            if local_script.exists():
                sftp.put(str(local_script), f"{root}/scripts/adjustment_chain_forensics.py")
                print("Uploaded scripts/adjustment_chain_forensics.py")
        finally:
            sftp.close()

        c._execute(f"{cd} && mkdir -p reports/score_autopsy", timeout=5)
        cmd = f"{cd} && python3 scripts/adjustment_chain_forensics.py 2>&1"
        out, err, rc = c._execute(cmd, timeout=180)
        print(out or "")
        if err:
            print(err, file=sys.stderr)

        for name in [
            "adjustment_delta_attribution.md",
            "top_50_killed_by_adjustments.md",
            "adjustment_vs_executed_comparison.md",
            "bars_alignment_20_sample.md",
        ]:
            remote = f"{root}/reports/score_autopsy/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=10)
            if content:
                (OUT_DIR / name).write_text(content, encoding="utf-8")
                print(f"Fetched {name}")
    return rc or 0


if __name__ == "__main__":
    sys.exit(main())
