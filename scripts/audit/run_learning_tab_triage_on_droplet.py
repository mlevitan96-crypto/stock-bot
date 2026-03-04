#!/usr/bin/env python3
"""Phase 1: Run on droplet (or via SSH) to triage Learning tab endpoints. Writes LEARNING_TAB_TRIAGE.md."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def run_local_triage() -> str:
    """Run triage locally (e.g. on droplet with DROPLET_RUN=1)."""
    import urllib.request
    import json
    base = "http://127.0.0.1:5000"
    out = []
    out.append("# Learning Tab Triage\n")
    out.append(f"**Triage time (UTC):** {datetime.now(timezone.utc).isoformat()}\n\n")
    for path in ["/api/learning_readiness", "/api/telemetry_health", "/api/situation"]:
        out.append(f"## {path}\n\n")
        try:
            req = urllib.request.Request(base + path, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.getcode()
                body = resp.read().decode("utf-8")
                out.append(f"- **HTTP:** {code}\n")
                if code == 200:
                    try:
                        j = json.loads(body)
                        keys = list(j.keys())[:20]
                        out.append(f"- **Keys (sample):** {keys}\n")
                        if path == "/api/learning_readiness":
                            out.append(f"- telemetry_trades: {j.get('telemetry_trades')}\n")
                            out.append(f"- visibility_matrix length: {len(j.get('visibility_matrix') or [])}\n")
                    except Exception as e:
                        out.append(f"- **JSON parse error:** {e}\n")
                out.append(f"- **Body (first 500 chars):**\n```\n{body[:500]}\n```\n\n")
        except urllib.error.HTTPError as e:
            out.append(f"- **HTTP error:** {e.code} {e.reason}\n\n")
        except Exception as e:
            out.append(f"- **Error:** {type(e).__name__}: {e}\n\n")
    return "".join(out)


def main() -> int:
    if os.environ.get("DROPLET_RUN"):
        report = run_local_triage()
        dest = REPO / "reports" / "audit" / "LEARNING_TAB_TRIAGE.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(report, encoding="utf-8")
        print(report)
        return 0
    # Run via SSH: execute script on droplet with DROPLET_RUN=1 then fetch report
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    with DropletClient() as c:
        c._execute(f"cd {proj} && git fetch origin && git reset --hard origin/main 2>/dev/null || true", timeout=30)
        c._execute(f"cd {proj} && DROPLET_RUN=1 python3 scripts/audit/run_learning_tab_triage_on_droplet.py", timeout=30)
        out, _, _ = c._execute(f"cat {proj}/reports/audit/LEARNING_TAB_TRIAGE.md 2>/dev/null")
    if out:
        (REPO / "reports" / "audit" / "LEARNING_TAB_TRIAGE.md").write_text(out, encoding="utf-8")
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
