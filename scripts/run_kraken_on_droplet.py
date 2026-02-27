#!/usr/bin/env python3
"""
Upload Kraken massive-review script + downloader to droplet, run it, fetch reports.
Uses DropletClient (SSH). Ensures Kraken 30d pipeline runs on real droplet data.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def run(c, cmd: str, timeout: int = 120):
    return c._execute(f"cd {c.project_dir} && {cmd}", timeout=timeout)


def upload_with_lf(c, local: Path, remote: str, content: str) -> None:
    """Upload content with LF line endings (for .sh)."""
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    c._connect()
    sftp = c.ssh_client.open_sftp()
    try:
        sftp.putfo(io.BytesIO(normalized.encode("utf-8")), remote)
    finally:
        sftp.close()


def main() -> int:
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    to_upload = [
        "scripts/CURSOR_KRAKEN_30D_MASSIVE_REVIEW_AND_ITERATE.sh",
        "scripts/data/kraken_download_30d_resumable.py",
        "scripts/learning/run_profit_iteration.py",
        "scripts/learning/aggregate_profitability_campaign.py",
    ]

    with DropletClient() as c:
        out, _, _ = run(c, "pwd", timeout=5)
        if out and out.strip():
            pd = out.strip().split()[-1] if "stock-bot" in (out or "") else out.strip()
        if "/root/stock-bot" not in (out or ""):
            out2, _, _ = run(c, "cd /root/stock-bot && pwd", timeout=5)
            if out2 and out2.strip():
                pd = out2.strip()
        print("Droplet project_dir:", pd)

        run(c, "mkdir -p scripts/learning scripts/data data/raw/kraken data/cache/kraken data/checkpoints/kraken", timeout=10)

        for rel in to_upload:
            local = REPO / rel
            if not local.exists():
                print("Skip (missing):", rel)
                continue
            remote = f"{pd}/{rel}"
            try:
                content = local.read_text(encoding="utf-8")
                if rel.endswith(".sh"):
                    upload_with_lf(c, local, remote, content)
                else:
                    c.put_file(local, remote)
                print("Uploaded:", rel)
            except Exception as e:
                print("Upload failed", rel, e)

        # Run Kraken massive review: 2 days + 4 iters for a quick validation (full 30d/48 iters on demand)
        print("\n--- KRAKEN 30D MASSIVE REVIEW (DAYS=2, ITERATIONS=4) ---")
        cmd = "DAYS=2 ITERATIONS=4 PARALLELISM=2 bash scripts/CURSOR_KRAKEN_30D_MASSIVE_REVIEW_AND_ITERATE.sh"
        out, err, rc = run(c, cmd, timeout=600)
        print(out[-4000:] if out and len(out) > 4000 else (out or "(no output)"))
        if err:
            print("stderr:", err[:800])
        print("exit:", rc)

        # Fetch latest massive_reviews run (most recent RUN_TAG dir)
        list_out, _, _ = run(c, "ls -t reports/massive_reviews 2>/dev/null | head -1", timeout=10)
        run_tag = (list_out or "").strip()
        if run_tag:
            out_dir = REPO / "reports" / "massive_reviews" / run_tag
            out_dir.mkdir(parents=True, exist_ok=True)
            for name in [
                "kraken/KRAKEN_30D_COVERAGE.json",
                "kraken/KRAKEN_30D_DOWNLOAD_STATUS.json",
                "review/MASSIVE_REVIEW_SEED.json",
                "CURSOR_FINAL_SUMMARY.txt",
            ]:
                remote_path = f"reports/massive_reviews/{run_tag}/{name}"
                content, _, _ = run(c, f"cat {remote_path} 2>/dev/null || echo __MISSING__", timeout=10)
                if content and "__MISSING__" not in content and len(content) > 20:
                    dest = out_dir / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    print("Fetched:", name)
            print("Run tag:", run_tag)
        else:
            print("No massive_reviews dir found on droplet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
