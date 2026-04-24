"""One-off: upload council mission script and run on droplet."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402

ET = "2026-04-01"


def main() -> None:
    c = DropletClient()
    c.put_file(
        "scripts/audit/run_hypothesis_council_profit_mission.py",
        "/root/stock-bot/scripts/audit/run_hypothesis_council_profit_mission.py",
    )
    cmd = (
        f"sed -i 's/\\r$//' /root/stock-bot/scripts/audit/run_hypothesis_council_profit_mission.py 2>/dev/null || true; "
        f"cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_hypothesis_council_profit_mission.py "
        f"--evidence-et {ET} --root /root/stock-bot"
    )
    r = c.execute_command(cmd, 120)
    print("exit_code", r.get("exit_code"))
    print("stdout", (r.get("stdout") or "")[:4000])
    print("stderr", (r.get("stderr") or "")[:4000])
    if r.get("exit_code") != 0:
        raise SystemExit(1)
    base = f"reports/daily/{ET}/evidence"
    for name in [
        "HYPOTHESIS_COUNCIL_PHASE0_CONTEXT.json",
        "HYPOTHESIS_COUNCIL_ACTION_VERDICT.md",
    ]:
        c.get_file(f"{base}/{name}", REPO / base / name)
        print("pulled", name)


if __name__ == "__main__":
    main()
