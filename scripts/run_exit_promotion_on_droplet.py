#!/usr/bin/env python3
"""Run CURSOR_RUN_EXIT_PROMOTION_NOW.sh on droplet via DropletClient."""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_RUN_EXIT_PROMOTION_NOW.sh",
    "scripts/CURSOR_EXECUTE_EXIT_PROMOTION_ON_DROPLET.sh",
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
                return 1
        for sh in ["CURSOR_RUN_EXIT_PROMOTION_NOW.sh", "CURSOR_EXECUTE_EXIT_PROMOTION_ON_DROPLET.sh"]:
            c._execute(f"sed -i 's/\\r$//' {pd}/scripts/{sh} 2>/dev/null; chmod +x {pd}/scripts/{sh} 2>/dev/null", timeout=5)

        ts_log = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        remote_log = f"/tmp/cursor_exit_promotion_{ts_log}.log"
        cmd = (
            f"cd {c.project_dir} && REPO={c.project_dir} bash scripts/CURSOR_RUN_EXIT_PROMOTION_NOW.sh "
            f"2>&1 | tee {remote_log}; rc=$?; echo EXIT_CODE:$rc >> {remote_log}; exit $rc"
        )
        out, err, rc = c._execute(cmd, timeout=300)
        if (not out or out.strip() == "") and remote_log:
            out2, _, _ = c._execute(f"cat {remote_log} 2>/dev/null || true", timeout=10)
            if out2.strip():
                out = out2
                for line in reversed(out2.strip().splitlines()):
                    if line.strip().startswith("EXIT_CODE:"):
                        try:
                            rc = int(line.strip().split(":", 1)[1].strip())
                        except ValueError:
                            pass
                        break

        local_dir = REPO / "reports" / "exit_review"
        local_dir.mkdir(parents=True, exist_ok=True)
        raw_path = local_dir / f"exit_promotion_droplet_{ts_log}.txt"
        raw_path.write_text(
            f"=== stdout ===\n{out}\n\n=== stderr ===\n{err}\n\n=== exit_code ===\n{rc}\n",
            encoding="utf-8",
        )
        print(f"Output written to: {raw_path}")

    safe_print(out)
    if err:
        safe_print(err, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
