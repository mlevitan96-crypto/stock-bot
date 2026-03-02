#!/usr/bin/env python3
"""
Run on droplet: (1) ensure INJECT_SIGNAL_TEST=1 in .env and restart bot,
(2) wait for one run_once cycle, (3) run all-gates check and show what blocked.
Use from repo root: python scripts/run_inject_signal_test_on_droplet.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    root_out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    root = None
    with DropletClient() as c:
        root = get_root(c)
        cd = f"cd {root}"

        # 1) Git pull
        out, _, _ = c._execute(f"{cd} && git fetch origin && git pull origin main 2>&1", timeout=60)
        print("--- git pull ---")
        print((out or "")[:500])

        # 2) Upload gate check script
        sftp = c._connect().open_sftp()
        try:
            local = REPO / "scripts" / "run_all_gates_check_on_droplet.py"
            if local.exists():
                sftp.put(str(local), f"{root}/scripts/run_all_gates_check_on_droplet.py")
                print("Uploaded run_all_gates_check_on_droplet.py")
        finally:
            sftp.close()

        # 3) Ensure INJECT_SIGNAL_TEST=1 in .env (append if missing)
        out, _, _ = c._execute(
            f"{cd} && (grep -q 'INJECT_SIGNAL_TEST' .env 2>/dev/null || echo 'INJECT_SIGNAL_TEST=1' >> .env) && grep INJECT_SIGNAL .env || true",
            timeout=10,
        )
        print("--- .env INJECT_SIGNAL_TEST ---")
        print(out or "(none)")

        # 4) Restart so bot picks up env
        out, err, rc = c._execute("sudo systemctl restart stock-bot 2>&1", timeout=30)
        print("--- restart stock-bot ---")
        print(out or err or "ok")

    # 5) Wait for one run_once cycle (~60–90s)
    print("\n--- waiting 95s for one run_once cycle ---")
    time.sleep(95)

    # 6) Run all-gates check on droplet (reads state + logs)
    with DropletClient() as c:
        if root is None:
            root = get_root(c)
        cd = f"cd {root}"
        out, err, _ = c._execute(
            f"{cd} && INJECT_SIGNAL_TEST=1 python3 scripts/run_all_gates_check_on_droplet.py 2>&1",
            timeout=30,
        )
        print("\n--- ALL GATES CHECK (on droplet) ---")
        print(out or "")
        if err:
            print(err, file=sys.stderr)

        # 7) Last run + last 20 gate lines
        run_last, _, _ = c._execute(f"{cd} && tail -1 logs/run.jsonl 2>/dev/null || true", timeout=5)
        gate_tail, _, _ = c._execute(f"{cd} && tail -20 logs/gate.jsonl 2>/dev/null || true", timeout=5)
        submit_tail, _, _ = c._execute(f"{cd} && tail -5 logs/submit_entry.jsonl 2>/dev/null || true", timeout=5)
        worker_tail, _, _ = c._execute(f"{cd} && tail -8 logs/worker_debug.log 2>/dev/null || true", timeout=5)

        print("\n--- Last run.jsonl ---")
        print(run_last or "(empty)")
        print("\n--- Last 20 gate.jsonl ---")
        print(gate_tail or "(empty)")
        print("\n--- Last 5 submit_entry.jsonl ---")
        print(submit_tail or "(empty)")
        print("\n--- Last 8 worker_debug.log ---")
        print(worker_tail or "(empty)")

    print("\nDone. If orders=0 with clusters=1, check gate.jsonl above for the blocking gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
