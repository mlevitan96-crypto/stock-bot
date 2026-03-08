#!/usr/bin/env python3
"""Capture CSA paper-only proof on droplet (run locally, SSHs to droplet). Writes reports/audit/csa_paper_only_proof.txt."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from droplet_client import DropletClient

def main():
    c = DropletClient()
    proof = Path(__file__).resolve().parents[2] / "reports" / "audit"
    proof.mkdir(parents=True, exist_ok=True)
    cmd = (
        "grep -E '^TRADING_MODE=|^ALPACA_BASE_URL=|^APCA_API_BASE_URL=' .env 2>/dev/null || true; "
        "echo '---'; "
        "env 2>/dev/null | grep -E 'TRADING_MODE|ALPACA_BASE|ALPACA_LIVE|APCA_API' || true"
    )
    out, err, _ = c._execute_with_cd(cmd, timeout=10)
    text = (out or "") + (err or "")
    text_redact = re.sub(r"(KEY|SECRET|PASSWORD)=[^\s]+", r"\1=***REDACTED***", text)
    (proof / "csa_paper_only_proof.txt").write_text(text_redact, encoding="utf-8")
    print("CSA paper-only proof saved (values redacted)")
    if "ALPACA_LIVE" in text:
        print("WARNING: ALPACA_LIVE found in env", file=sys.stderr)
        return 1
    if "TRADING_MODE=LIVE" in text:
        print("WARNING: LIVE mode or ambiguous", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
