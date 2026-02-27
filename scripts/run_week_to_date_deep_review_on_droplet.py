#!/usr/bin/env python3
"""
Run CURSOR_DROPLET_WEEK_TO_DATE_DEEP_REVIEW.sh on the droplet with real data.
Uploads script + analysis/learning deps, runs, fetches report.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_DROPLET_WEEK_TO_DATE_DEEP_REVIEW.sh",
    "scripts/analysis/slice_truth_by_time.py",
    "scripts/analysis/label_large_moves.py",
    "scripts/analysis/correlate_signals_before_moves.py",
    "scripts/analysis/correlate_signals_after_moves.py",
    "scripts/analysis/build_entry_exit_intelligence.py",
    "scripts/learning/generate_contextual_policies.py",
    "scripts/learning/run_policy_simulations.py",
    "scripts/learning/aggregate_profitability_campaign.py",
]

FETCH_FILES = [
    "BOARD_REVIEW_PACKET.md",
    "CURSOR_FINAL_SUMMARY.txt",
    "truth_wtd.json",
    "entry_exit_intelligence_wtd.json",
    "aggregate_result.json",
    "candidate_policies_wtd.json",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    rc = 1

    full_truth = os.environ.get("FULL_TRUTH", "")
    iterations = os.environ.get("ITERATIONS", "200")
    parallelism = os.environ.get("PARALLELISM", "8")
    min_trades = os.environ.get("MIN_TRADES", "50")

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
                content = content.replace("\r\n", "\n").replace("\r", "\n")
                if rel.endswith(".sh") or rel.endswith(".py"):
                    c._connect()
                    sftp = c.ssh_client.open_sftp()
                    sftp.putfo(io.BytesIO(content.encode("utf-8")), remote)
                    sftp.close()
                else:
                    c.put_file(local, remote)
                print(f"Uploaded: {rel}")
            except Exception as e:
                print(f"Upload failed {rel}: {e}", file=sys.stderr)

        c._execute(f"chmod +x {pd}/scripts/CURSOR_DROPLET_WEEK_TO_DATE_DEEP_REVIEW.sh 2>/dev/null", timeout=5)

        env_parts = [
            f"ITERATIONS={iterations}",
            f"PARALLELISM={parallelism}",
            f"MIN_TRADES={min_trades}",
        ]
        if full_truth:
            env_parts.append(f"FULL_TRUTH={full_truth}")
        env_str = " ".join(env_parts)

        cmd = f"cd {c.project_dir} && {env_str} bash scripts/CURSOR_DROPLET_WEEK_TO_DATE_DEEP_REVIEW.sh"
        print("\n--- Running WEEK-TO-DATE DEEP REVIEW on droplet ---")
        if full_truth:
            print(f"   FULL_TRUTH={full_truth}")
        print(f"   ITERATIONS={iterations} PARALLELISM={parallelism} MIN_TRADES={min_trades}\n")
        out, err, rc = c._execute(cmd, timeout=1200)

        print(out[-10000:] if out and len(out) > 10000 else (out or "(no stdout)"))
        if err:
            print("stderr:", err[:2000] if len(err) > 2000 else err)
        print("exit code:", rc)

        list_out, _, _ = c._execute(
            f"cd {c.project_dir} && ls -1dt reports/week_to_date_review/week_to_date_review_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_tag = (list_out or "").strip()
        if run_tag:
            name = Path(run_tag).name
            out_dir = REPO / "reports" / "week_to_date_review" / name
            out_dir.mkdir(parents=True, exist_ok=True)
            for fname in FETCH_FILES:
                content, _, _ = c._execute(
                    f"cd {c.project_dir} && cat {run_tag}/{fname} 2>/dev/null || true",
                    timeout=30,
                )
                if content and len(content) > 10:
                    dest = out_dir / fname
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    print(f"Fetched: {fname}")
            print("Run dir:", run_tag)
            print("Local copy:", out_dir)
        else:
            print("No week_to_date_review run dir found.", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
