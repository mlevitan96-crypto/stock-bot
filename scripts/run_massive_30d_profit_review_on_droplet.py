#!/usr/bin/env python3
"""Run CURSOR_MASSIVE_30D_PROFIT_REVIEW_AND_ITERATE.sh on droplet via DropletClient."""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_MASSIVE_30D_PROFIT_REVIEW_AND_ITERATE.sh",
    "scripts/fill_alpaca_bars_30d.py",
    "scripts/analysis/build_30d_truth_dataset.py",
    "scripts/analysis/run_massive_profit_review.py",
    "scripts/analysis/find_exits_missing_bars.py",
    "scripts/analysis/fetch_missing_bars_from_alpaca.py",
    "scripts/learning/run_profitability_campaign.py",
    "scripts/learning/run_profit_iteration.py",
    "scripts/learning/aggregate_profitability_campaign.py",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    rc = 1

    with DropletClient() as c:
        for rel in FILES:
            local = REPO / rel
            if not local.is_file():
                print(f"Skip (missing): {rel}", file=sys.stderr)
                continue
            remote = f"{pd}/{rel}".replace("\\", "/")
            remote_dir = "/".join(remote.split("/")[:-1])
            c._execute(f"mkdir -p '{remote_dir}'", timeout=5)
            try:
                content = local.read_text(encoding="utf-8")
                if rel.endswith(".sh"):
                    content = content.replace("\r\n", "\n").replace("\r", "\n")
                    c._connect()
                    sftp = c.ssh_client.open_sftp()
                    sftp.putfo(io.BytesIO(content.encode("utf-8")), remote)
                    sftp.close()
                else:
                    c.put_file(local, remote)
                print(f"Uploaded: {rel}")
            except Exception as e:
                print(f"Upload failed {rel}: {e}", file=sys.stderr)

        c._execute(f"chmod +x {pd}/scripts/CURSOR_MASSIVE_30D_PROFIT_REVIEW_AND_ITERATE.sh 2>/dev/null", timeout=5)

        # Run with smaller iter count for first run; source .env for Alpaca
        cmd = (
            f"cd {c.project_dir} && "
            "[ -f .env ] && set -a && source .env && set +a; "
            "ITERATIONS=4 PARALLELISM=2 bash scripts/CURSOR_MASSIVE_30D_PROFIT_REVIEW_AND_ITERATE.sh"
        )
        print("\n--- Running MASSIVE 30D PROFIT REVIEW on droplet ---\n")
        out, err, rc = c._execute(cmd, timeout=900)

        print(out[-6000:] if out and len(out) > 6000 else (out or "(no stdout)"))
        if err:
            print("stderr:", err[:1500] if len(err) > 1500 else err)
        print("exit code:", rc)

        # Fetch latest massive_profit_reviews run
        list_out, _, _ = c._execute(
            "ls -td reports/massive_profit_reviews/massive_30d_profit_review_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_tag = (list_out or "").strip()
        if run_tag:
            out_dir = REPO / "reports" / "massive_profit_reviews" / Path(run_tag).name
            out_dir.mkdir(parents=True, exist_ok=True)
            for name in ["CURSOR_FINAL_SUMMARY.txt", "aggregate_result.json", "truth_30d.json"]:
                content, _, _ = c._execute(f"cd {c.project_dir} && cat {run_tag}/{name} 2>/dev/null || true", timeout=10)
                if content and len(content) > 20:
                    (out_dir / name).write_text(content, encoding="utf-8")
                    print(f"Fetched: {name}")
            print("Run dir:", run_tag)

    return rc


if __name__ == "__main__":
    sys.exit(main())
