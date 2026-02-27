#!/usr/bin/env python3
"""
Run Order Submission Truth Contract ON THE DROPLET via SSH, then fetch reports to local.
Requires: instrumentation in main.py (SUBMIT_ORDER_CALLED log) deployed and bot restarted
so that logs/submit_order_called.jsonl exists after a short run. Then this script counts
and produces proof/reconciliation/verdict. Run from repo root: python scripts/run_order_submission_truth_contract_via_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "order_review"

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found; install paramiko and ensure droplet_config.json exists", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    root_out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    root = None

    # Upload script and submit_call_map (so droplet has current artifacts)
    with DropletClient() as c:
        root = get_root(c)
        c._execute(f"cd {root} && mkdir -p reports/order_review", timeout=5)
        sftp = c._connect().open_sftp()
        try:
            for local_rel, remote_rel in [
                ("scripts/order_submission_truth_contract_on_droplet.py", "scripts/order_submission_truth_contract_on_droplet.py"),
                ("reports/order_review/submit_call_map.md", "reports/order_review/submit_call_map.md"),
            ]:
                local_path = REPO / local_rel
                if local_path.exists():
                    sftp.put(str(local_path), f"{root}/{remote_rel}")
                    print(f"Uploaded {remote_rel}")
        finally:
            sftp.close()

    # Run truth contract on droplet
    with DropletClient() as c:
        if root is None:
            root = get_root(c)
        c._execute(f"cd {root} && mkdir -p reports/order_review", timeout=5)
        cmd = f"cd {root} && python3 scripts/order_submission_truth_contract_on_droplet.py 2>&1"
        out, err, rc = c._execute(cmd, timeout=60)
        print("\n--- order_submission_truth_contract_on_droplet.py (on droplet) ---")
        print(out or "")
        if err:
            print(err, file=sys.stderr)

        for name in ["submit_call_proof.md", "ledger_vs_order_reconciliation.md", "board_verdict.md"]:
            remote = f"{root}/reports/order_review/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=15)
            if content and content.strip():
                (OUT_DIR / name).write_text(content, encoding="utf-8")
                print(f"Fetched reports/order_review/{name}")
            else:
                print(f"No content for {name}")

    return rc if rc is not None else 0


if __name__ == "__main__":
    sys.exit(main())
