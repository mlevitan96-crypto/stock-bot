#!/usr/bin/env python3
"""
Run CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh ON THE DROPLET and fetch results.
Per MEMORY_BANK: use droplet for accurate data. Run from local: SSH, pull, run script, fetch RUN_DIR.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_LOCAL = REPO / "reports" / "cursor_final_remediation"


def get_root(c) -> str:
    out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (out or "/root/stock-bot").strip().splitlines()[-1].strip() if out else "/root/stock-bot"


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; install paramiko and ensure droplet_config.json exists", file=sys.stderr)
        return 1

    OUT_LOCAL.mkdir(parents=True, exist_ok=True)
    root = None

    with DropletClient() as c:
        root = get_root(c)
        cd = f"cd {root}"
        # Pull latest
        pull_out, pull_err, _ = c._execute(
            f"{cd} && git fetch origin && git reset --hard origin/main 2>&1",
            timeout=90,
        )
        print("--- git pull on droplet ---")
        print(pull_out or pull_err or "ok")

    with DropletClient() as c:
        root = get_root(c)
        cd = f"cd {root}"
        # Pull latest (avoid reset --hard so we don't overwrite in-use files like uw_flow_cache)
        pull_out, pull_err, _ = c._execute(
            f"{cd} && git fetch origin && git pull --rebase origin main 2>&1 || git pull origin main 2>&1",
            timeout=90,
        )
        print("--- git pull on droplet ---")
        print(pull_out or pull_err or "ok")

    # Upload script via base64 to avoid SFTP size issues
    local_script = REPO / "scripts" / "CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh"
    if local_script.exists():
        import base64
        content = local_script.read_bytes()
        b64 = base64.b64encode(content).decode("ascii")
        with DropletClient() as c:
            root = root or get_root(c)
            c._execute(f"cd {root} && mkdir -p scripts", timeout=5)
            # Write b64 in one go via Python on droplet to avoid quoting/chunk issues
            c._execute(
                f"cd {root} && python3 -c \"import base64; open('scripts/CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh','wb').write(base64.b64decode('''{b64}''')); print('ok')\"",
                timeout=15,
            )
            print("Uploaded CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh via base64")

    # Run remediation script (may exit 1 if no candidates above MIN_EXEC_SCORE)
    with DropletClient() as c:
        root = root or get_root(c)
        cd = f"cd {root}"
        cmd = f"{cd} && chmod +x scripts/CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh && bash scripts/CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh 2>&1"
        out, err, rc = c._execute(cmd, timeout=600)
        print("\n--- CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh (on droplet) ---")
        print(out or "")
        if err:
            print(err, file=sys.stderr)

    # Find RUN_DIR from log (last RUN_DIR: line)
    run_dir_remote = None
    for line in (out or "").splitlines():
        if line.strip().startswith("RUN_DIR:"):
            run_dir_remote = line.split("RUN_DIR:", 1)[-1].strip()
    if not run_dir_remote:
        run_dir_remote = f"{root}/reports/backtests/promotion_candidate_final_unknown"

    # Fetch artifacts from RUN_DIR and excerpts
    with DropletClient() as c:
        root = root or get_root(c)
        for name in [
            "cursor_final_summary.txt",
            "cursor_report.md",
            "SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md",
        ]:
            remote = f"{run_dir_remote}/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=15)
            if content and content.strip():
                (OUT_LOCAL / name).write_text(content, encoding="utf-8")
                print(f"Fetched {name}")

        # Also fetch from signal_review (audit may write there)
        for name in ["signal_funnel.json", "signal_audit_diagnostic_droplet.json"]:
            remote = f"{root}/reports/signal_review/{name}"
            content, _, _ = c._execute(f"cat {remote} 2>/dev/null || true", timeout=15)
            if content and content.strip():
                (OUT_LOCAL / name).write_text(content, encoding="utf-8")
                print(f"Fetched {name}")

    # Fetch log
    with DropletClient() as c:
        log_content, _, _ = c._execute("cat /tmp/cursor_final_autonomous_remediation.log 2>/dev/null || true", timeout=15)
        if log_content:
            (OUT_LOCAL / "remediation.log").write_text(log_content, encoding="utf-8")
            print("Fetched remediation.log")

    print("\n--- LOCAL ARTIFACTS ---")
    print(f"Report dir: {OUT_LOCAL}")
    if (OUT_LOCAL / "cursor_final_summary.txt").exists():
        print((OUT_LOCAL / "cursor_final_summary.txt").read_text(encoding="utf-8"))
    return rc if rc is not None else 0


if __name__ == "__main__":
    sys.exit(main())
