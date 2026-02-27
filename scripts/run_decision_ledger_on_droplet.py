#!/usr/bin/env python3
"""
On droplet (or locally): mkdir -p reports/decision_ledger, run capture, run summarizer.
Run from repo root:
  python3 scripts/run_decision_ledger_capture.py
  python3 scripts/summarize_decision_ledger.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ledger_dir = REPO / "reports" / "decision_ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    code1 = subprocess.run([py, str(REPO / "scripts" / "run_decision_ledger_capture.py")], cwd=REPO, timeout=120).returncode
    if code1 != 0:
        print("run_decision_ledger_capture.py failed.", file=sys.stderr)
        return code1
    code2 = subprocess.run([py, str(REPO / "scripts" / "summarize_decision_ledger.py")], cwd=REPO, timeout=60).returncode
    if code2 != 0:
        print("summarize_decision_ledger.py failed.", file=sys.stderr)
        return code2
    print("Decision ledger capture + summarizer OK. See reports/decision_ledger/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
