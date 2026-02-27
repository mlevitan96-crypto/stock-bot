#!/usr/bin/env python3
"""
Run zero-trades preflight + full signal review ON THE DROPLET via SSH, then fetch results to local.
Uses DropletClient. Run from repo root (local): python scripts/run_zero_trades_signal_review_via_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "signal_review"

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
    rc = 0

    # Connection 1: git pull
    with DropletClient() as c:
        root = get_root(c)
        cd = f"cd {root}"
        pull_out, pull_err, _ = c._execute(
            f"{cd} && git fetch origin && git reset --hard origin/main 2>&1",
            timeout=90,
        )
        print("--- git pull on droplet ---")
        print(pull_out or pull_err or "ok")

    # Connection 2: upload scripts (fresh connection to avoid drop after pull)
    with DropletClient() as c:
        if root is None:
            root = get_root(c)
        sftp = c._connect().open_sftp()
        try:
            for local_rel, remote_rel in [
                ("scripts/zero_trades_preflight_on_droplet.py", "scripts/zero_trades_preflight_on_droplet.py"),
                ("scripts/full_signal_review_on_droplet.py", "scripts/full_signal_review_on_droplet.py"),
                ("scripts/run_zero_trades_preflight_and_signal_review_on_droplet.py", "scripts/run_zero_trades_preflight_and_signal_review_on_droplet.py"),
            ]:
                local_path = REPO / local_rel
                if local_path.exists():
                    sftp.put(str(local_path), f"{root}/{remote_rel}")
                    print(f"Uploaded {remote_rel}")
        finally:
            sftp.close()

    # Connection 3: run and fetch
    with DropletClient() as c:
        if root is None:
            root = get_root(c)
        cd = f"cd {root}"
        c._execute(f"{cd} && mkdir -p reports/signal_review", timeout=5)
        cmd = f"{cd} && python3 scripts/run_zero_trades_preflight_and_signal_review_on_droplet.py 2>&1"
        out, err, rc = c._execute(cmd, timeout=300)
        print("\n--- run_zero_trades_preflight_and_signal_review_on_droplet.py (on droplet) ---")
        print(out or "")
        if err:
            print(err, file=sys.stderr)

        for name in [
            "zero_trades_preflight.md",
            "signal_funnel.md",
            "signal_funnel.json",
            "top_50_end_to_end_traces.md",
            "multi_model_adversarial_review.md",
        ]:
            remote = f"{root}/reports/signal_review/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=15)
            if content and content.strip():
                (OUT_DIR / name).write_text(content, encoding="utf-8")
                print(f"Fetched reports/signal_review/{name}")
            else:
                print(f"No content for {name}")

    return rc if rc is not None else 0


if __name__ == "__main__":
    sys.exit(main())
