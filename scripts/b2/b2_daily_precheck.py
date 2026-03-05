#!/usr/bin/env python3
"""
Phase 0: B2 daily precheck. Run on droplet (DROPLET_RUN=1).
Verifies: deployed_commit == origin/main, TRADING_MODE=PAPER, ALPACA_BASE_URL paper,
FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true, health endpoints 200.
On failure: reports/audit/B2_DAILY_PRECHECK_BLOCKERS.md and exit 1.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_dotenv(base: Path) -> None:
    """Load .env into os.environ so checks see droplet config."""
    env_path = base / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def main() -> int:
    base = REPO
    if os.getenv("B2_BASE_DIR"):
        base = Path(os.getenv("B2_BASE_DIR"))
    _load_dotenv(base)

    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []

    # 1) Deployed commit matches origin/main
    try:
        head_out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=base,
            capture_output=True,
            text=True,
            timeout=5,
        )
        origin_out = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=base,
            capture_output=True,
            text=True,
            timeout=5,
        )
        head = (head_out.stdout or "").strip() if head_out.returncode == 0 else ""
        origin = (origin_out.stdout or "").strip() if origin_out.returncode == 0 else ""
        if not head or not origin or head != origin:
            blockers.append(f"Deployed commit (HEAD) does not match origin/main: HEAD={head[:12] if head else '?'} origin/main={origin[:12] if origin else '?'}.")
    except Exception as e:
        blockers.append(f"Git rev-parse check failed: {e}")

    # 2) TRADING_MODE=PAPER and ALPACA_BASE_URL is paper
    mode = os.getenv("TRADING_MODE", "").strip().upper()
    url = (os.getenv("ALPACA_BASE_URL") or os.getenv("APCA_API_BASE_URL") or "").strip()
    if mode != "PAPER":
        blockers.append(f"TRADING_MODE must be PAPER (got {mode!r}).")
    if url and "paper" not in url.lower():
        blockers.append(f"ALPACA_BASE_URL must indicate paper (got {url[:50]!r}).")

    # 3) FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true
    b2_val = os.getenv("FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT", "").strip().lower()
    if b2_val != "true":
        blockers.append(f"FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT must be true (got {b2_val!r}).")

    # 4) Health endpoints 200 (required when DROPLET_RUN=1 or when running daily eval)
    for path in ["/api/telemetry_health", "/api/learning_readiness"]:
        try:
            r = subprocess.run(
                ["curl", "-s", "-o", os.devnull, "-w", "%{http_code}", f"http://127.0.0.1:5000{path}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            code = (r.stdout or "").strip()
            if code != "200":
                blockers.append(f"Health endpoint {path} did not return 200 (got {code}).")
        except Exception as e:
            blockers.append(f"Health check {path} failed: {e}")

    if blockers:
        lines = [
            "# B2 daily precheck — blockers",
            "",
            f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
            "",
            "Precheck failed. Resolve before running B2 daily evaluation:",
            "",
        ] + [f"- {b}" for b in blockers] + [""]
        (audit_dir / "B2_DAILY_PRECHECK_BLOCKERS.md").write_text("\n".join(lines), encoding="utf-8")
        print("B2_DAILY_PRECHECK_BLOCKERS:", "; ".join(blockers), file=sys.stderr)
        return 1
    print("B2 daily precheck: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
