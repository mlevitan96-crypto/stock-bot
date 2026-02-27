#!/usr/bin/env python3
"""Run CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh on droplet via DropletClient."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh",
    "scripts/analysis/exit_param_grid_search.py",
    "scripts/analysis/exit_grid_board_review.py",
]

def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"

    def safe_print(s, file=sys.stdout):
        try:
            print(s, file=file)
        except UnicodeEncodeError:
            print("".join(c if ord(c) < 128 else "?" for c in s), file=file)

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
        c._execute(f"sed -i 's/\\r$//' {pd}/scripts/CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh 2>/dev/null; chmod +x {pd}/scripts/CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh 2>/dev/null", timeout=5)

        cmd = f"cd {c.project_dir} && REPO={c.project_dir} bash scripts/CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh"
        out, err, rc = c._execute(cmd, timeout=900)

        if rc == 0 and "RUN_DIR:" in out:
            try:
                run_dir = None
                for line in out.splitlines():
                    if line.strip().startswith("RUN_DIR:"):
                        run_dir = line.split("RUN_DIR:", 1)[-1].strip()
                        break
                if run_dir and run_dir.startswith("/"):
                    summary_out, _, _ = c._execute(f"cat '{run_dir}/CURSOR_FINAL_SUMMARY.txt' 2>/dev/null || true", timeout=5)
                    rec_out, _, _ = c._execute(f"cat '{run_dir}/grid_board_review/GRID_RECOMMENDATION.json' 2>/dev/null || true", timeout=5)
                    local_dir = REPO / "reports" / "exit_review"
                    local_dir.mkdir(parents=True, exist_ok=True)
                    summary_md = local_dir / "LATEST_GRID_SEARCH_SUMMARY.md"
                    summary_md.write_text(
                        f"# Latest Exit Grid Search (from droplet)\n\n"
                        f"**Run dir (droplet):** `{run_dir}`\n\n## Summary\n\n```\n{summary_out}\n```\n\n"
                        f"## GRID_RECOMMENDATION.json\n\n```json\n{rec_out}\n```\n",
                        encoding="utf-8",
                    )
                    print(f"Summary written for Cursor: {summary_md}")
            except Exception as e:
                print(f"Could not fetch summary for Cursor: {e}", file=sys.stderr)

    safe_print(out)
    if err:
        safe_print(err, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
