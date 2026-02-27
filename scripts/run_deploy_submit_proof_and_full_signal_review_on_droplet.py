#!/usr/bin/env python3
"""
Run on droplet (via SSH from local):
  Phase 1: Deploy main.py (SUBMIT_ORDER_CALLED), restart bot, run order submission truth contract, fetch proof.
  Phase 2: Run full_signal_review_on_droplet.py (--capture optional), fetch signal_review artifacts.
Usage: python scripts/run_deploy_submit_proof_and_full_signal_review_on_droplet.py [--skip-deploy] [--proof-only]
  --skip-deploy: skip Phase 1 (deploy + restart); run Phase 1 contract and Phase 2 only.
  --proof-only: run only Phase 1 contract (no deploy, no Phase 2).
"""
from __future__ import annotations

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
    root_out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-deploy", action="store_true", help="Skip deploy/restart; run contract + Phase 2")
    ap.add_argument("--proof-only", action="store_true", help="Run only order submission truth contract")
    args = ap.parse_args()

    if not args.proof_only and not args.skip_deploy:
        # Phase 1: deploy + restart
        import subprocess
        rc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "deploy_submit_proof_and_run_contract_on_droplet.py")],
            cwd=str(REPO), timeout=120,
        ).returncode
        if rc != 0:
            return rc
        print("\nWait >= 30 min then re-run with --proof-only to refresh proof, or run Phase 2 now.\n")

    if args.proof_only:
        import subprocess
        return subprocess.run(
            [sys.executable, str(REPO / "scripts" / "run_order_submission_truth_contract_via_droplet.py")],
            cwd=str(REPO), timeout=90,
        ).returncode

    # Run Phase 1 contract (fetch proof)
    import subprocess
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_order_submission_truth_contract_via_droplet.py")],
        cwd=str(REPO), timeout=90,
    )

    # Phase 2: upload full_signal_review script and run on droplet, fetch artifacts
    OUT_SIGNAL = REPO / "reports" / "signal_review"
    OUT_SIGNAL.mkdir(parents=True, exist_ok=True)
    with DropletClient() as c:
        root = get_root(c)
        sftp = c._connect().open_sftp()
        try:
            local = REPO / "scripts" / "full_signal_review_on_droplet.py"
            if local.exists():
                sftp.put(str(local), f"{root}/scripts/full_signal_review_on_droplet.py")
                print("Uploaded full_signal_review_on_droplet.py")
        finally:
            sftp.close()
        c._execute(f"cd {root} && mkdir -p reports/signal_review", timeout=5)
        out, err, rc = c._execute(
            f"cd {root} && python3 scripts/full_signal_review_on_droplet.py --days 7 --capture 2>&1",
            timeout=300,
        )
        print("\n--- full_signal_review_on_droplet.py (Phase 2) ---")
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        for name in ["signal_funnel.md", "signal_funnel.json", "top_50_end_to_end_traces.md", "multi_model_adversarial_review.md"]:
            remote = f"{root}/reports/signal_review/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=15)
            if content and content.strip():
                (OUT_SIGNAL / name).write_text(content, encoding="utf-8")
                print(f"Fetched reports/signal_review/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
