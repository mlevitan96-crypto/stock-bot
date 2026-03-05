#!/usr/bin/env python3
"""
Run B2 daily evaluation on droplet via alpaca: precheck, evaluator, tripwire enforcer, then board review.
Fetches B2_DAILY_STATUS.md/.json and B2_TRIPWIRE_CLEAR.md or B2_AUTO_ROLLBACK_PROOF.md to local.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"
    with DropletClient() as c:
        # Phase 0: precheck (load .env on droplet via B2_BASE_DIR)
        out, err, rc = c._execute_with_cd(
            f"export B2_BASE_DIR={proj} && DROPLET_RUN=1 python3 scripts/b2/b2_daily_precheck.py",
            timeout=15,
        )
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("B2 daily precheck failed; not running evaluator.", file=sys.stderr)
            # Fetch blockers if present
            content, _, _ = c._execute(f"cat {proj}/reports/audit/B2_DAILY_PRECHECK_BLOCKERS.md 2>/dev/null || true", timeout=5)
            if content and content.strip():
                (REPO / "reports" / "audit" / "B2_DAILY_PRECHECK_BLOCKERS.md").write_text(content, encoding="utf-8")
            return 1

        # Source .env so evaluator/enforcer see vars when run
        env_cmd = f"set -a && [ -f {proj}/.env ] && . {proj}/.env && set +a"
        # Evaluator
        out2, err2, rc2 = c._execute_with_cd(
            f"{env_cmd} && python3 scripts/b2/b2_daily_evaluator.py --base-dir . --since-hours 24",
            timeout=60,
        )
        print(out2 or "")
        if err2:
            print(err2, file=sys.stderr)
        if rc2 != 0:
            print("B2 daily evaluator failed", file=sys.stderr)
            return 1

        # Tripwire enforcer
        out3, err3, rc3 = c._execute_with_cd(
            f"{env_cmd} && python3 scripts/b2/b2_tripwire_enforcer.py",
            timeout=90,
        )
        print(out3 or "")
        if err3:
            print(err3, file=sys.stderr)
        # Enforcer exits 0 even after rollback (proof written)
        if rc3 != 0:
            print("B2 tripwire enforcer failed or rollback failed", file=sys.stderr)

        # Fetch artifacts
        for name in ["B2_DAILY_STATUS.md", "B2_DAILY_STATUS.json"]:
            src = f"{proj}/reports/board/{name}"
            content, _, _ = c._execute(f"cat {src} 2>/dev/null || true", timeout=5)
            if content and content.strip():
                dest = REPO / "reports" / "board" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"Fetched {name}", file=sys.stderr)
        for name in ["B2_TRIPWIRE_CLEAR.md", "B2_AUTO_ROLLBACK_PROOF.md"]:
            src = f"{proj}/reports/audit/{name}"
            content, _, _ = c._execute(f"cat {src} 2>/dev/null || true", timeout=5)
            if content and content.strip():
                dest = REPO / "reports" / "audit" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"Fetched {name}", file=sys.stderr)

    # Board review (separate script, fetches last387)
    print("Running board review (last 387)...", file=sys.stderr)
    import subprocess
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_30d_board_review_on_droplet.py"), "--last-n-exits", "387"],
        cwd=REPO,
        timeout=180,
    )
    if r.returncode != 0:
        print("Board review failed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
