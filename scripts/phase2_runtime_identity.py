#!/usr/bin/env python3
"""
Phase-2 runtime identity: systemd unit(s), WorkingDirectory, git rev, python path.
Run on droplet. Writes reports/PHASE2_RUNTIME_IDENTITY.md.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"


def _run(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 10) -> Tuple[str, str, int]:
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd or REPO,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode
    except Exception as e:
        return "", str(e), -1


def main() -> int:
    lines: List[str] = []
    lines.append("# Phase-2 Runtime Identity")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1.1 systemd units
    lines.append("## 1. Systemd service(s)")
    lines.append("")
    out, err, rc = _run(["systemctl", "list-units", "--type=service", "--all", "--no-pager", "-o", "json"])
    unit_names: List[str] = []
    if rc == 0 and out:
        try:
            import json
            data = json.loads(out)
            for u in data.get("units") or []:
                n = (u.get("unit") or "")
                if "stock" in n.lower() or "trading" in n.lower() or "uw-flow" in n.lower() or "bot" in n.lower():
                    unit_names.append(n)
        except Exception:
            pass
    if not unit_names:
        out2, _, _ = _run(["systemctl", "list-unit-files", "--type=service", "--no-pager"])
        for line in (out2 or "").splitlines():
            if "stock" in line.lower() or "trading" in line.lower() or "uw-flow" in line.lower():
                parts = line.split()
                if parts:
                    unit_names.append(parts[0])
    for uname in unit_names[:10]:
        lines.append(f"### Unit: `{uname}`")
        lines.append("")
        o, e, _ = _run(["systemctl", "show", uname, "--property=WorkingDirectory", "--property=ExecStart", "--property=User", "--property=EnvironmentFile", "--no-pager"])
        for x in (o or "").splitlines():
            lines.append(f"- {x}")
        lines.append("")
    if not unit_names:
        lines.append("No stock-bot–related systemd units found.")
        lines.append("")

    # 1.2 git + python
    lines.append("## 2. Repo and executable")
    lines.append("")
    workdir = os.getcwd()
    lines.append(f"- **CWD (WorkingDirectory):** `{workdir}`")
    rev, _, rrev = _run(["git", "rev-parse", "HEAD"], cwd=REPO)
    lines.append(f"- **Git commit (repo root):** `{rev or 'n/a'}` (exit {rrev})")
    py_exe = sys.executable
    lines.append(f"- **Python executable:** `{py_exe}`")
    sp: List[str] = []
    try:
        sp = list(getattr(sys, "path", []))
    except Exception:
        pass
    site = ""
    for p in sp:
        if "site-packages" in str(p):
            site = str(p)
            break
    lines.append(f"- **site-packages (example):** `{site or 'n/a'}`")
    lines.append("")

    # stdout/stderr
    lines.append("## 3. Stdout/stderr")
    lines.append("")
    lines.append("Services typically use journald (StandardOutput=journal, StandardError=journal) unless overridden.")
    lines.append("")

    out_path = REPORTS / "PHASE2_RUNTIME_IDENTITY.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
