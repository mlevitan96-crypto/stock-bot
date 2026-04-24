#!/usr/bin/env python3
"""
Phase 1 precheck for C1/A3 mission. Run ON DROPLET (DROPLET_RUN=1).
Exits 0 only if all checks pass; otherwise writes reports/audit/NEXT_STEP_PRECHECK_BLOCKERS.md and exits 1.
Checks: deployed_commit, repo clean, exit_attribution.jsonl present and growing, direction_readiness.json present and fresh,
        dashboard /api/learning_readiness and /api/telemetry_health respond locally.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 15) -> tuple[str, str, int]:
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (r.stdout or "", r.stderr or "", r.returncode)
    except Exception as e:
        return ("", str(e), -1)

def main() -> int:
    base = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    if len(sys.argv) > 1:
        base = Path(sys.argv[1]).resolve()
    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    details: list[str] = []

    # 1) deployed_commit and repo clean
    out, err, rc = _run(["git", "rev-parse", "HEAD"], cwd=base)
    deployed_commit = (out or "").strip()[:12] if rc == 0 else ""
    if not deployed_commit:
        blockers.append("git rev-parse HEAD failed or not a git repo")
    else:
        details.append(f"deployed_commit: {deployed_commit}")

    out, err, rc = _run(["git", "status", "--porcelain"], cwd=base)
    if rc != 0:
        blockers.append("git status failed")
    elif (out or "").strip():
        blockers.append("repo not clean (uncommitted or untracked changes)")
    else:
        details.append("repo clean: yes")

    # 2) exit_attribution.jsonl present and growing
    exit_attr = base / "logs" / "exit_attribution.jsonl"
    if not exit_attr.exists():
        blockers.append("logs/exit_attribution.jsonl missing")
    else:
        try:
            size = exit_attr.stat().st_size
            mtime = exit_attr.stat().st_mtime
            age_sec = (datetime.now(timezone.utc).timestamp() - mtime) if mtime else 999999
            details.append(f"exit_attribution.jsonl: size={size}, last_write_ago_sec={round(age_sec)}")
            if age_sec > 86400 * 2:
                blockers.append("exit_attribution.jsonl not recently written (older than 2 days)")
        except Exception as e:
            blockers.append(f"exit_attribution.jsonl stat failed: {e}")

    # 3) direction_readiness.json present and fresh
    dr_path = base / "state" / "direction_readiness.json"
    if not dr_path.exists():
        blockers.append("state/direction_readiness.json missing")
    else:
        try:
            data = json.loads(dr_path.read_text(encoding="utf-8"))
            details.append(f"direction_readiness: telemetry_trades={data.get('telemetry_trades', 'N/A')}, ready={data.get('ready', 'N/A')}")
            mtime = dr_path.stat().st_mtime
            age_sec = datetime.now(timezone.utc).timestamp() - mtime
            if age_sec > 86400 * 3:
                blockers.append("direction_readiness.json older than 3 days (stale)")
        except Exception as e:
            blockers.append(f"direction_readiness.json read failed: {e}")

    # 4) Dashboard endpoints (local)
    for api_path in ["/api/learning_readiness", "/api/telemetry_health"]:
        out, err, rc = _run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://127.0.0.1:5000{api_path}"],
            timeout=10,
        )
        code = (out or "").strip()
        if code != "200":
            blockers.append(f"dashboard {api_path} returned HTTP {code or 'fail'}")
        else:
            details.append(f"dashboard {api_path}: 200")

    if blockers:
        lines = [
            "# Next-step precheck — BLOCKERS",
            "",
            f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Blockers (must resolve before C1/A3)",
            "",
        ]
        for b in blockers:
            lines.append(f"- {b}")
        lines.extend(["", "## Details", ""] + details + ["", "## Resolve", "", "Fix the items above, then re-run this precheck."])
        out_path = audit_dir / "NEXT_STEP_PRECHECK_BLOCKERS.md"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print("PRECHECK FAILED:", "; ".join(blockers), file=sys.stderr)
        print(f"Wrote {out_path}", file=sys.stderr)
        return 1
    print("PRECHECK OK:", " ".join(details))
    return 0

if __name__ == "__main__":
    sys.exit(main())
