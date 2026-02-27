#!/usr/bin/env python3
"""Run CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh on droplet via DropletClient."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Script + analysis deps so droplet has everything
FILES = [
    "scripts/CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh",
    "scripts/analysis/discover_exit_data_sources.py",
    "scripts/analysis/harvest_historical_exit_truth.py",
    "scripts/analysis/normalize_exit_truth_with_provenance.py",
    "scripts/analysis/replay_exits_with_candidate_signals.py",
    "scripts/analysis/compute_exit_edge_metrics.py",
    "scripts/analysis/exit_edge_by_regime.py",
    "scripts/analysis/exit_edge_board_review.py",
    "scripts/analysis/synthesize_exit_edge_decision.py",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"

    with DropletClient() as c:
        for rel in FILES:
            local = REPO / rel
            if not local.is_file():
                print(f"Skip (missing): {rel}", file=sys.stderr)
                continue
            remote = f"{pd}/{rel}".replace("\\", "/")
            remote_dir = str(Path(remote).parent).replace("\\", "/")
            c._execute(f"mkdir -p '{remote_dir}'", timeout=5)
            try:
                c.put_file(local, remote)
                print(f"Uploaded: {rel}")
            except Exception as e:
                print(f"Upload failed {rel}: {e}", file=sys.stderr)
                try:
                    c.put_file(local, remote)
                    print(f"Uploaded (retry): {rel}")
                except Exception as e2:
                    print(f"Upload retry failed {rel}: {e2}", file=sys.stderr)
        for sh in ["CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh"]:
            c._execute(f"sed -i 's/\\r$//' {pd}/scripts/{sh} 2>/dev/null; chmod +x {pd}/scripts/{sh} 2>/dev/null", timeout=5)
        cmd = (
            f"cd {c.project_dir} && REPO={c.project_dir} "
            f"bash scripts/CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh"
        )
        out, err, rc = c._execute(cmd, timeout=600)

        # Fetch summary for Cursor review (local reports/exit_review/)
        if rc == 0 and "RUN_DIR:" in out:
            try:
                run_dir = None
                for line in out.splitlines():
                    if line.strip().startswith("RUN_DIR:"):
                        run_dir = line.split("RUN_DIR:", 1)[-1].strip()
                        break
                if run_dir and run_dir.startswith("/"):
                    summary_out, _, _ = c._execute(f"cat '{run_dir}/CURSOR_FINAL_SUMMARY.txt' 2>/dev/null || true", timeout=5)
                    board_out, _, _ = c._execute(f"cat '{run_dir}/BOARD_DECISION.json' 2>/dev/null || true", timeout=5)
                    local_dir = REPO / "reports" / "exit_review"
                    local_dir.mkdir(parents=True, exist_ok=True)
                    summary_md = local_dir / "LATEST_HISTORICAL_RUN_SUMMARY.md"
                    summary_md.write_text(
                        f"# Latest Historical Exit Review (from droplet)\n\n"
                        f"**Run dir (droplet):** `{run_dir}`\n\n## Summary\n\n```\n{summary_out}\n```\n\n"
                        f"## BOARD_DECISION.json\n\n```json\n{board_out}\n```\n",
                        encoding="utf-8",
                    )
                    print(f"Summary written for Cursor: {summary_md}")
            except Exception as e:
                print(f"Could not fetch summary for Cursor: {e}", file=sys.stderr)
    # Windows console may not support Unicode (e.g. → in log output)
    def safe_print(s, file=sys.stdout):
        try:
            print(s, file=file)
        except UnicodeEncodeError:
            print("".join(c if ord(c) < 128 else "?" for c in s), file=file)
    safe_print(out)
    if err:
        safe_print(err, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
