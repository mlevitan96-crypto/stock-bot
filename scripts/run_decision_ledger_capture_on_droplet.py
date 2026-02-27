#!/usr/bin/env python3
"""
Run decision ledger capture + summarizer on droplet, then fetch reports to local.
Uses DropletClient. Run from repo root (local).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "decision_ledger"

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

        # Pull latest
        pull_out, pull_err, pull_rc = c._execute(
            f"{cd} && git fetch origin && git reset --hard origin/main 2>&1",
            timeout=90,
        )
        print("--- git pull ---")
        print(pull_out or pull_err or "ok")

        # Upload decision_ledger scripts if missing (so we can run without pushing)
        sftp = c._connect().open_sftp()
        try:
            def put(local_rel: str, remote_rel: str) -> None:
                local_path = REPO / local_rel
                if not local_path.exists():
                    return
                remote_path = f"{root}/{remote_rel}"
                sftp.put(str(local_path), remote_path)
                print(f"Uploaded {remote_rel}")

            put("scripts/decision_ledger_writer.py", "scripts/decision_ledger_writer.py")
            put("scripts/run_decision_ledger_capture.py", "scripts/run_decision_ledger_capture.py")
            put("scripts/summarize_decision_ledger.py", "scripts/summarize_decision_ledger.py")
            put("reports/decision_ledger/schema.md", "reports/decision_ledger/schema.md")
            put("reports/decision_ledger/adversarial_reviews.md", "reports/decision_ledger/adversarial_reviews.md")
        finally:
            sftp.close()

        c._execute(f"{cd} && mkdir -p reports/decision_ledger", timeout=5)

        # Run capture
        cmd_capture = f"{cd} && python3 scripts/run_decision_ledger_capture.py 2>&1"
        out_cap, err_cap, rc_cap = c._execute(cmd_capture, timeout=120)
        print("\n--- run_decision_ledger_capture.py ---")
        print(out_cap or "")
        if err_cap:
            print(err_cap, file=sys.stderr)
        if rc_cap != 0:
            print(f"Capture exit code: {rc_cap}", file=sys.stderr)

        # Run summarizer
        cmd_sum = f"{cd} && python3 scripts/summarize_decision_ledger.py 2>&1"
        out_sum, err_sum, rc_sum = c._execute(cmd_sum, timeout=60)
        print("\n--- summarize_decision_ledger.py ---")
        print(out_sum or "")
        if err_sum:
            print(err_sum, file=sys.stderr)

        # Fetch all decision_ledger artifacts
        for name in [
            "decision_ledger.jsonl",
            "blocked_attribution_summary.md",
            "score_distribution.md",
            "top_50_blocked_examples.md",
            "reproduction.md",
            "adversarial_reviews.md",
            "schema.md",
        ]:
            remote = f"{root}/reports/decision_ledger/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=15)
            if content:
                (OUT_DIR / name).write_text(content, encoding="utf-8")
                print(f"Fetched {name}")
            else:
                print(f"No content for {name}")

    return 0 if rc_cap == 0 and rc_sum == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
