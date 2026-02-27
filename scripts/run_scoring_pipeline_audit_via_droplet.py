#!/usr/bin/env python3
"""
Run the full scoring pipeline trade-blocker audit ON THE DROPLET and fetch results.
Use this from local: SSH to droplet, git pull, run run_scoring_pipeline_audit_on_droplet.py, fetch report.
Requires: droplet_config.json or DROPLET_* env; repo pushed to GitHub so droplet can pull.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "signal_review"


def get_root(c) -> str:
    out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (out or "/root/stock-bot").strip().splitlines()[-1].strip() if out else "/root/stock-bot"


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; install paramiko and ensure droplet_config.json exists", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    root = None

    # Upload audit script (so we don't require a push for new script)
    with DropletClient() as c:
        root = get_root(c)
        sftp = c._connect().open_sftp()
        try:
            local_path = REPO / "scripts" / "run_scoring_pipeline_audit_on_droplet.py"
            if local_path.exists():
                sftp.put(str(local_path), f"{root}/scripts/run_scoring_pipeline_audit_on_droplet.py")
                print("Uploaded scripts/run_scoring_pipeline_audit_on_droplet.py")
        finally:
            sftp.close()

    with DropletClient() as c:
        root = get_root(c)
        cd = f"cd {root}"
        # Pull latest (per MEMORY_BANK: deploy then run on droplet)
        pull_out, pull_err, _ = c._execute(
            f"{cd} && git fetch origin && git reset --hard origin/main 2>&1",
            timeout=90,
        )
        print("--- git pull on droplet ---")
        print(pull_out or pull_err or "ok")

    with DropletClient() as c:
        if root is None:
            root = get_root(c)
        cd = f"cd {root}"
        c._execute(f"{cd} && mkdir -p reports/signal_review", timeout=5)
        cmd = f"{cd} && python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days 7 2>&1"
        out, err, rc = c._execute(cmd, timeout=400)
        print("\n--- run_scoring_pipeline_audit_on_droplet.py (on droplet) ---")
        print(out or "")
        if err:
            print(err, file=sys.stderr)

        # Fetch audit report and related artifacts
        for name in [
            "SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md",
            "signal_funnel.json",
            "signal_funnel.md",
            "signal_audit_diagnostic_droplet.json",
            "top_50_end_to_end_traces.md",
            "multi_model_adversarial_review.md",
            "paper_trade_metric_reconciliation.md",
            "signal_score_breakdown_summary.md",
        ]:
            remote = f"{root}/reports/signal_review/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=15)
            if content and content.strip() and "No such file" not in content:
                (OUT_DIR / name).write_text(content, encoding="utf-8")
                print(f"Fetched reports/signal_review/{name}")
            else:
                if name == "SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md":
                    print(f"Warning: {name} not found or empty on droplet")

    print("\n--- LOCAL ARTIFACTS ---")
    print(f"Primary report: {OUT_DIR / 'SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md'}")
    if (OUT_DIR / "SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md").exists():
        print("\n--- EXECUTIVE EXCERPT ---")
        text = (OUT_DIR / "SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md").read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("**Verdict:**") or line.startswith("**No.**") or line.startswith("**Yes.**") or line.startswith("**Root cause"):
                print(line)
            if "Dominant choke" in line or "Can we make trades" in line:
                print(line)
    return rc if rc is not None else 0


if __name__ == "__main__":
    sys.exit(main())
