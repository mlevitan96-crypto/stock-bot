#!/usr/bin/env python3
"""
Run discover_alpaca_and_run_bars_on_droplet.sh on the droplet via SSH.
Prints full output. Exit code = script exit code from droplet.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ROOT = "/root/stock-bot"
BARS_DEPLOY_FILES = [
    "scripts/run_bars_pipeline.py",
    "scripts/check_alpaca_env.py",
    "scripts/bars_universe_and_range.py",
    "scripts/fetch_alpaca_bars.py",
    "scripts/write_bars_cache_status.py",
    "scripts/audit_bars.py",
    "scripts/blocked_expectancy_analysis.py",
    "data/bars_loader.py",
    "scripts/run_droplet_truth_run.py",
]


def safe_print(text: str, file=None) -> None:
    if not text:
        return
    safe = text.replace("\u2192", "->").replace("\u2014", "-").encode("ascii", errors="replace").decode("ascii")
    f = file or sys.stdout
    f.write(safe)
    if not safe.endswith("\n"):
        f.write("\n")
    f.flush()


def main() -> int:
    from droplet_client import DropletClient

    script_name = "discover_alpaca_and_run_bars_on_droplet.sh"
    local_script = REPO / "scripts" / script_name
    cmd_run = f"cd {ROOT} && chmod +x scripts/{script_name} 2>/dev/null; bash scripts/{script_name}"

    with DropletClient() as c:
        c._execute("true", timeout=5)
        sftp = c.ssh_client.open_sftp()
        try:
            # Upload discover script with Unix line endings (droplet bash fails on \r\n)
            discover_content = (REPO / "scripts" / script_name).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            from io import BytesIO
            bio = BytesIO(discover_content)
            sftp.putfo(bio, f"{ROOT}/scripts/{script_name}")
            for rel in BARS_DEPLOY_FILES:
                local = REPO / rel
                if local.exists():
                    remote = f"{ROOT}/{rel}"
                    try:
                        sftp.stat(str(Path(remote).parent))
                    except FileNotFoundError:
                        for i, _ in enumerate(Path(remote).parent.parts):
                            d = str(Path(*Path(remote).parent.parts[: i + 1]))
                            if d and d != "/":
                                try:
                                    sftp.mkdir(d)
                                except OSError:
                                    pass
                    sftp.put(str(local), remote)
            safe_print("Deployed bars pipeline + discover script.\n")
        finally:
            sftp.close()
        out, err, rc = c._execute(cmd_run, timeout=900)
        safe_print(out or "")
        if err:
            safe_print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
