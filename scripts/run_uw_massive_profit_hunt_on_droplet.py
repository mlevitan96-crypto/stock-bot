#!/usr/bin/env python3
"""
Run CURSOR_DROPLET_UW_MASSIVE_PROFIT_HUNT_FOREVER.sh on the droplet.
Uploads script, runs (real data only). Optionally set MAX_HOURS for shorter run.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_DROPLET_UW_MASSIVE_PROFIT_HUNT_FOREVER.sh",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    rc = 1

    max_hours = os.environ.get("MAX_HOURS", "2")
    full_truth = os.environ.get("FULL_TRUTH", "")
    parallelism = os.environ.get("PARALLELISM", "16")
    iterations_per_round = os.environ.get("ITERATIONS_PER_ROUND", "4000")

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

        c._execute(f"chmod +x {pd}/scripts/CURSOR_DROPLET_UW_MASSIVE_PROFIT_HUNT_FOREVER.sh 2>/dev/null", timeout=5)

        env_parts = [
            f"MAX_HOURS={max_hours}",
            f"PARALLELISM={parallelism}",
            f"ITERATIONS_PER_ROUND={iterations_per_round}",
        ]
        if full_truth:
            env_parts.append(f"FULL_TRUTH={full_truth}")
        env_str = " ".join(env_parts)

        cmd = f"cd {c.project_dir} && {env_str} bash scripts/CURSOR_DROPLET_UW_MASSIVE_PROFIT_HUNT_FOREVER.sh"
        print("\n--- Running UW MASSIVE PROFIT HUNT on droplet ---")
        print(f"   MAX_HOURS={max_hours} PARALLELISM={parallelism} ITERATIONS_PER_ROUND={iterations_per_round}")
        if full_truth:
            print(f"   FULL_TRUTH={full_truth}")
        print()

        # Allow up to MAX_HOURS + 1 hour
        timeout_sec = int(max_hours) * 3600 + 3600
        out, err, rc = c._execute(cmd, timeout=timeout_sec)

        print(out[-15000:] if out and len(out) > 15000 else (out or "(no stdout)"))
        if err:
            print("stderr:", err[:3000] if len(err) > 3000 else err)
        print("exit code:", rc)

        list_out, _, _ = c._execute(
            f"cd {c.project_dir} && ls -1dt reports/uw_massive_profit_hunt/uw_massive_profit_hunt_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_tag = (list_out or "").strip()
        if run_tag:
            name = Path(run_tag).name
            out_dir = REPO / "reports" / "uw_massive_profit_hunt" / name
            out_dir.mkdir(parents=True, exist_ok=True)
            for fname in [
                "CURSOR_FINAL_SUMMARY.txt",
                "uw_cache_inventory.json",
                "uw_events_manifest.json",
                "uw_forward_returns_manifest.json",
            ]:
                content, _, _ = c._execute(
                    f"cd {c.project_dir} && cat {run_tag}/{fname} 2>/dev/null || true",
                    timeout=30,
                )
                if content and len(content) > 5:
                    (out_dir / fname).write_text(content, encoding="utf-8")
                    print(f"Fetched: {fname}")
            print("Run dir:", run_tag)
            print("Local copy:", out_dir)
        else:
            print("No uw_massive_profit_hunt run dir found.", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
