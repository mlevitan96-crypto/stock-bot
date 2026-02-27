#!/usr/bin/env python3
"""
Run CURSOR_DROPLET_UW_DISCOVER_AND_SELF_HEAL.sh on the droplet.
Uploads script, runs, fetches all audit artifacts. Real data only; droplet only.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_DROPLET_UW_DISCOVER_AND_SELF_HEAL.sh",
]

FETCH_FILES = [
    "uw_env_snapshot.json",
    "uw_repo_scan.json",
    "uw_data_inventory.json",
    "uw_client_candidates.json",
    "UW_DATA_AUDIT.md",
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
            content = local.read_text(encoding="utf-8")
            content = content.replace("\r\n", "\n").replace("\r", "\n")
            c._connect()
            sftp = c.ssh_client.open_sftp()
            sftp.putfo(io.BytesIO(content.encode("utf-8")), remote)
            sftp.close()
            print(f"Uploaded: {rel}")

        c._execute(f"chmod +x {pd}/scripts/CURSOR_DROPLET_UW_DISCOVER_AND_SELF_HEAL.sh 2>/dev/null", timeout=5)

        cmd = f"cd {c.project_dir} && bash scripts/CURSOR_DROPLET_UW_DISCOVER_AND_SELF_HEAL.sh"
        print("\n--- Running UW DISCOVER + SELF-HEAL on droplet ---\n")
        out, err, rc = c._execute(cmd, timeout=300)

        print(out[-12000:] if out and len(out) > 12000 else (out or "(no stdout)"))
        if err:
            print("stderr:", err[:3000] if len(err) > 3000 else err)
        print("exit code:", rc)

        list_out, _, _ = c._execute(
            f"cd {c.project_dir} && ls -1dt reports/uw_discover_self_heal/uw_discover_self_heal_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_tag = (list_out or "").strip()
        if run_tag:
            name = Path(run_tag).name
            out_dir = REPO / "reports" / "uw_discover_self_heal" / name
            out_dir.mkdir(parents=True, exist_ok=True)
            for fname in FETCH_FILES:
                content, _, _ = c._execute(
                    f"cd {c.project_dir} && cat {run_tag}/{fname} 2>/dev/null || true",
                    timeout=30,
                )
                if content and len(content) > 5:
                    (out_dir / fname).write_text(content, encoding="utf-8")
                    print(f"Fetched: {fname}")
            # Fetch log if present (log path is /tmp/RUN_TAG.log; we have run_tag so name is the tag)
            log_name = name + ".log"
            log_content, _, _ = c._execute(f"cat /tmp/{log_name} 2>/dev/null || true", timeout=10)
            if log_content and len(log_content) > 5:
                (out_dir / "run.log").write_text(log_content, encoding="utf-8")
                print("Fetched: run.log")
            print("Run dir:", run_tag)
            print("Local copy:", out_dir)
        else:
            print("No uw_discover_self_heal run dir found.", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
