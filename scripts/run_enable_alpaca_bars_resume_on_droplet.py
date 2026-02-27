#!/usr/bin/env python3
"""
Run enable_alpaca_bars_resume.sh on the droplet (resume mode).
No re-discovery; precondition: .env.research exists. Retry SSH and continue Phases 2-5.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ROOT = "/root/stock-bot"
SCRIPT_NAME = "enable_alpaca_bars_resume.sh"
BARS_DEPLOY = [
    "scripts/bars_universe_and_range.py",
    "scripts/fetch_alpaca_bars.py",
    "scripts/write_bars_cache_status.py",
    "scripts/audit_bars.py",
    "scripts/blocked_expectancy_analysis.py",
    "scripts/blocked_signal_expectancy_pipeline.py",
    "data/bars_loader.py",
]


def safe_print(text: str, file=None) -> None:
    if not text:
        return
    safe = text.replace("\u2192", "->").replace("\u2014", "-").encode("ascii", errors="replace").decode("ascii")
    (file or sys.stdout).write(safe)
    if not safe.endswith("\n"):
        (file or sys.stdout).write("\n")
    (file or sys.stdout).flush()


def main() -> int:
    from droplet_client import DropletClient

    with DropletClient() as c:
        c._execute("true", timeout=5)
        sftp = c.ssh_client.open_sftp()
        try:
            for rel in BARS_DEPLOY:
                local = REPO / rel
                if local.exists():
                    remote = f"{ROOT}/{rel}"
                    try:
                        sftp.stat(str(Path(remote).parent))
                    except FileNotFoundError:
                        for i in range(1, len(Path(remote).parent.parts) + 1):
                            d = str(Path(*Path(remote).parent.parts[:i]))
                            if d and d != "/":
                                try:
                                    sftp.mkdir(d)
                                except OSError:
                                    pass
                    sftp.put(str(local), remote)
            content = (REPO / "scripts" / SCRIPT_NAME).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            from io import BytesIO
            sftp.putfo(BytesIO(content), f"{ROOT}/scripts/{SCRIPT_NAME}")
            safe_print("Deployed resume script + deps (no Phase 0/1).\n")
        finally:
            sftp.close()
        c._execute(f"cd {ROOT} && python3 -c 'import pyarrow' 2>/dev/null || pip3 install -q pyarrow || pip3 install --user -q pyarrow", timeout=120)
        out, err, rc = c._execute(f"cd {ROOT} && bash scripts/{SCRIPT_NAME}", timeout=900)
        safe_print(out or "")
        if err:
            safe_print(err, file=sys.stderr)
        verdict, _, _ = c._execute(f"cat {ROOT}/reports/bars/final_verdict.txt 2>/dev/null; true", timeout=10)
        safe_print("")
        safe_print("========== FINAL VERDICT (from droplet) ==========")
        if (verdict or "").strip():
            safe_print(verdict.strip())
        else:
            safe_print("(verdict file missing or empty)")
        safe_print("==================================================")
        return rc


if __name__ == "__main__":
    sys.exit(main())
