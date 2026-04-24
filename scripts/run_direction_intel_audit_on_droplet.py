#!/usr/bin/env python3
"""Run direction intel wiring audit on droplet and fetch report to reports/audit/."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

def main():
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    script_local = REPO / "scripts" / "audit_direction_intel_wiring.py"
    report_remote = f"{proj}/reports/audit/DIRECTION_INTEL_WIRING_AUDIT.md"
    with DropletClient() as c:
        c._execute(f"mkdir -p {proj}/scripts {proj}/reports/audit")
        c.put_file(script_local, f"{proj}/scripts/audit_direction_intel_wiring.py")
        out, err, rc = c._execute(
            f"cd {proj} && python3 scripts/audit_direction_intel_wiring.py --base-dir . --out reports/audit/DIRECTION_INTEL_WIRING_AUDIT.md 2>&1",
            timeout=60,
        )
        print(out)
        if err:
            print(err, file=sys.stderr)
        content, _, _ = c._execute(f"cat {report_remote} 2>/dev/null || true")
        if content and content.strip():
            dest = REPO / "reports" / "audit" / "DIRECTION_INTEL_WIRING_AUDIT.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            print(f"Fetched report -> {dest}", file=sys.stderr)
        else:
            print("No report content from droplet", file=sys.stderr)
    return 0 if rc == 0 else rc

if __name__ == "__main__":
    sys.exit(main())
