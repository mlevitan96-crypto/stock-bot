#!/usr/bin/env python3
"""Upload campaign/enforce scripts to droplet, run enforce + trading review + 2-iter campaign, fetch results."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def run(c, cmd: str, timeout: int = 120):
    return c._execute(f"cd {c.project_dir} && {cmd}", timeout=timeout)


def main() -> int:
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    to_upload = [
        "scripts/CURSOR_ENFORCE_DROPLET_AND_NO_SUPPRESSION.sh",
        "scripts/CURSOR_AUTONOMOUS_PROFITABILITY_CAMPAIGN.sh",
        "scripts/learning/run_profit_iteration.py",
        "scripts/learning/aggregate_profitability_campaign.py",
        "scripts/learning/__init__.py",
        "scripts/data/build_canonical_dataset.py",
        "scripts/data/build_features.py",
        "scripts/data/build_labels.py",
        "scripts/data/__init__.py",
    ]

    with DropletClient() as c:
        out, _, _ = run(c, "pwd", timeout=5)
        if out and out.strip():
            pd = out.strip()
        print("Droplet project_dir:", pd)

        run(c, "mkdir -p scripts/learning scripts/data", timeout=10)

        for rel in to_upload:
            local = REPO / rel
            if not local.exists():
                continue
            remote = f"{pd}/{rel}"
            try:
                content = local.read_text(encoding="utf-8")
                if rel.endswith(".sh"):
                    content = content.replace("\r\n", "\n").replace("\r", "\n")
                    import io
                    c._connect()
                    sftp = c.ssh_client.open_sftp()
                    try:
                        try:
                            sftp.stat(remote)
                        except FileNotFoundError:
                            pass
                        sftp.putfo(io.BytesIO(content.encode("utf-8")), remote)
                    finally:
                        sftp.close()
                else:
                    c.put_file(local, remote)
                print("Uploaded:", rel)
            except Exception as e:
                print("Upload failed", rel, e)

        print("\n--- ENFORCE (droplet-only + no suppression) ---")
        out, err, rc = run(c, "bash scripts/CURSOR_ENFORCE_DROPLET_AND_NO_SUPPRESSION.sh", timeout=60)
        print(out or "(no output)")
        if err:
            print("stderr:", err[:600])
        print("exit:", rc)

        print("\n--- TRADING ENVIRONMENT REVIEW (real 150 trades) ---")
        out, err, rc = run(c, "python3 scripts/trading_environment_review_on_droplet.py --last-n 150", timeout=90)
        print(out or "(no output)")
        if err:
            print("stderr:", err[:400])
        print("exit:", rc)

        print("\n--- PROFITABILITY CAMPAIGN (2 iters, real data) ---")
        # Re-upload fixed iteration/aggregate (REPO path fix)
        for rel in ["scripts/learning/run_profit_iteration.py", "scripts/learning/aggregate_profitability_campaign.py"]:
            local = REPO / rel
            if local.exists():
                c.put_file(local, f"{pd}/{rel}")
                print("Re-uploaded (REPO fix):", rel)
        out, err, rc = run(c, "ITERATIONS=2 PARALLELISM=1 bash scripts/CURSOR_AUTONOMOUS_PROFITABILITY_CAMPAIGN.sh", timeout=400)
        print(out[-3000:] if out and len(out) > 3000 else (out or "(no output)"))
        if err:
            print("stderr:", err[:600])
        print("exit:", rc)

        # Fetch latest trading review and campaign summary
        from datetime import datetime, timezone
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_dir = REPO / "reports" / "trading_environment_review"
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in [f"TRADING_ENVIRONMENT_REVIEW_{date_str}.md", f"TRADING_ENVIRONMENT_REVIEW_{date_str}.json"]:
            content, _, _ = run(c, f"cat {pd}/reports/trading_environment_review/{name} 2>/dev/null || echo", timeout=10)
            if content and "__MISSING__" not in content and len(content) > 100:
                (out_dir / name).write_text(content, encoding="utf-8")
                print("Fetched:", name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
