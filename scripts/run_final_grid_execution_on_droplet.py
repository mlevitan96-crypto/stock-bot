#!/usr/bin/env python3
"""Run CURSOR_FINAL_GRID_EXECUTION_AND_VERIFICATION.sh on droplet via DropletClient."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_FINAL_GRID_EXECUTION_AND_VERIFICATION.sh",
    "scripts/CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh",
    "scripts/analysis/find_exits_missing_bars.py",
    "scripts/analysis/fetch_missing_bars_from_alpaca.py",
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
        for sh in ["CURSOR_FINAL_GRID_EXECUTION_AND_VERIFICATION.sh", "CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh"]:
            c._execute(f"sed -i 's/\\r$//' {pd}/scripts/{sh} 2>/dev/null; chmod +x {pd}/scripts/{sh} 2>/dev/null", timeout=5)

        import time
        ts_log = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        remote_log = f"/tmp/cursor_final_grid_run_{ts_log}.log"
        cmd = (
            f"cd {c.project_dir} && [ -f .env ] && set -a && source .env && set +a; "
            f"REPO={c.project_dir} bash scripts/CURSOR_FINAL_GRID_EXECUTION_AND_VERIFICATION.sh 2>&1 | tee {remote_log}; "
            f"rc=$?; echo EXIT_CODE:$rc >> {remote_log}; exit $rc"
        )
        out, err, rc = c._execute(cmd, timeout=1800)
        # Prefer log file if stdout is empty (SSH channel sometimes drops long output)
        if (not out or out.strip() == "") and remote_log:
            out2, _, _ = c._execute(f"cat {remote_log} 2>/dev/null || true", timeout=10)
            if out2.strip():
                out = out2
                # Recover exit code from log if present
                for line in reversed(out2.strip().splitlines()):
                    if line.strip().startswith("EXIT_CODE:"):
                        try:
                            rc = int(line.strip().split(":", 1)[1].strip())
                        except ValueError:
                            pass
                        break

        # Always write full remote output for inspection
        local_dir = REPO / "reports" / "exit_review"
        local_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        raw_path = local_dir / f"final_grid_droplet_raw_{ts}.txt"
        raw_path.write_text(f"=== stdout ===\n{out}\n\n=== stderr ===\n{err}\n\n=== exit_code ===\n{rc}\n", encoding="utf-8")
        print(f"Full remote output written to: {raw_path}")

        if rc == 0 and "RUN_DIR:" in out:
            try:
                run_dir = None
                for line in reversed(out.splitlines()):
                    if line.strip().startswith("RUN_DIR:") and "final_grid_exec_" in line:
                        run_dir = line.split("RUN_DIR:", 1)[-1].strip()
                        break
                if not run_dir:
                    for line in out.splitlines():
                        if line.strip().startswith("RUN_DIR:"):
                            run_dir = line.split("RUN_DIR:", 1)[-1].strip()
                            break
                if run_dir and run_dir.startswith("/"):
                    summary_out, _, _ = c._execute(f"cat '{run_dir}/CURSOR_FINAL_SUMMARY.txt' 2>/dev/null || true", timeout=5)
                    local_dir = REPO / "reports" / "exit_review"
                    local_dir.mkdir(parents=True, exist_ok=True)
                    summary_md = local_dir / "LATEST_FINAL_GRID_EXECUTION_SUMMARY.md"
                    summary_md.write_text(
                        f"# Latest Final Grid Execution (from droplet)\n\n"
                        f"**Run dir (droplet):** `{run_dir}`\n\n## Summary\n\n```\n{summary_out}\n```\n",
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
