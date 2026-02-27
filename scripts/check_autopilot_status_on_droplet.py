#!/usr/bin/env python3
"""Check path-to-profitability autopilot status on droplet: log tail + overlay closed count."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    def safe_print(s: str) -> None:
        if not s:
            return
        try:
            print(s)
        except UnicodeEncodeError:
            print(s.encode("ascii", errors="replace").decode("ascii"))

    log_path = "/tmp/path_to_profitability_autopilot.log"
    with DropletClient() as c:
        out, _, _ = c._execute(
            f"cd /root/stock-bot && echo '=== Log (last 55 lines) ===' && tail -55 {log_path} 2>/dev/null || echo '(no log)'",
            timeout=15,
        )
        safe_print(out or "")

        out2, _, _ = c._execute(
            "cd /root/stock-bot && ls -td reports/path_to_profitability/path_to_profitability_* 2>/dev/null | head -3",
            timeout=10,
        )
        print("\n=== Latest path_to_profitability runs ===")
        print((out2 or "").strip() or "(none)")

        out3, _, _ = c._execute(
            "cd /root/stock-bot && LATEST=$(ls -td reports/effectiveness_overlay_check/path_to_profitability_* 2>/dev/null | head -1) && "
            "if [ -n \"$LATEST\" ] && [ -f \"$LATEST/effectiveness_aggregates.json\" ]; then "
            "echo \"Overlay dir: $LATEST\" && cat \"$LATEST/effectiveness_aggregates.json\"; "
            "else echo 'No overlay effectiveness dir yet'; fi",
            timeout=10,
        )
        print("\n=== Overlay effectiveness (closed-trade count) ===")
        safe_print((out3 or "").strip() or "(none)")

        out4, _, _ = c._execute(
            "cd /root/stock-bot && find reports/path_to_profitability -name 'lock_or_revert_decision.json' 2>/dev/null | head -5",
            timeout=10,
        )
        if out4 and out4.strip():
            first = out4.strip().split("\n")[0].strip()
            out5, _, _ = c._execute(f"cd /root/stock-bot && cat '{first}'", timeout=5)
            print("\n=== LOCK/REVERT decision (autopilot completed) ===")
            safe_print((out5 or "").strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
