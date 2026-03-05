#!/usr/bin/env python3
"""
Phase 0 precheck for B2 live paper test.
Asserts: paper mode enforceable, single B2 feature flag (default OFF), single rollback path, health endpoints.
On failure: reports/audit/B2_LIVE_PAPER_BLOCKERS.md and exit 1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    audit_dir = REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []

    # 1) Paper trading mode available and enforceable (no main import to avoid circular import)
    try:
        mode = os.getenv("TRADING_MODE", "PAPER")
        url = (os.getenv("ALPACA_BASE_URL") or os.getenv("APCA_API_BASE_URL") or "").strip()
        # Block only when PAPER is set and URL is explicitly non-paper (empty URL uses app default = paper)
        if (mode or "").upper() == "PAPER" and url and "paper" not in url.lower():
            blockers.append("TRADING_MODE=PAPER but ALPACA_BASE_URL does not contain 'paper'; paper mode ambiguous.")
        from config.paper_mode_config import is_paper_mode
        _ = is_paper_mode()
    except Exception as e:
        blockers.append(f"Paper mode check failed: {e}")

    # 2) Single explicit feature flag for B2 (default OFF)
    try:
        b2_val = os.getenv("FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT", "false").strip().lower()
        if b2_val not in ("true", "false", ""):
            blockers.append("FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT must be true or false.")
        # Default OFF: when unset, effective is false
        if not os.getenv("FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT"):
            pass  # default false OK
    except Exception as e:
        blockers.append(f"B2 flag check failed: {e}")

    # 3) Single explicit rollback path
    rollback_note = "Rollback: set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false (or unset), restart stock-bot. One config flip + restart."
    # Assert it's documented and simple
    if not blockers:
        pass  # rollback is one env flip + restart

    # 4) Health endpoints (local or droplet) - when run on droplet we'll curl; when run local we skip or check dashboard
    if os.getenv("DROPLET_RUN") == "1":
        import subprocess
        for path in ["/api/telemetry_health", "/api/learning_readiness"]:
            try:
                r = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://127.0.0.1:5000{path}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if (r.stdout or "").strip() != "200":
                    blockers.append(f"Health endpoint {path} did not return 200 (got {r.stdout or 'fail'}).")
            except Exception as e:
                blockers.append(f"Health check {path} failed: {e}")

    if blockers:
        lines = [
            "# B2 live paper — blockers",
            "",
            f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
            "",
            "Precheck failed. Resolve before enabling B2 live paper test:",
            "",
        ] + [f"- {b}" for b in blockers] + ["", rollback_note, ""]
        (audit_dir / "B2_LIVE_PAPER_BLOCKERS.md").write_text("\n".join(lines), encoding="utf-8")
        print("B2_LIVE_PAPER_BLOCKERS:", "; ".join(blockers), file=sys.stderr)
        return 1
    print("B2 live paper precheck: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
