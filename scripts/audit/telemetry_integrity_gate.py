#!/usr/bin/env python3
"""
Telemetry integrity gate: run all telemetry audits and exit non-zero on blocking failures.
Used by CI/local: make telemetry_gate or python scripts/audit/telemetry_integrity_gate.py.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run(cmd: list, cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Telemetry integrity gate")
    ap.add_argument("--allow-legacy", action="store_true", help="Run contract audit without --strict-canonical (pass when legacy records lack direction/side/position_side)")
    args = ap.parse_args()
    failures = []
    base = REPO

    # 1) ensure_telemetry_paths.py
    ensure_path = base / "scripts" / "ensure_telemetry_paths.py"
    if ensure_path.exists():
        code, out = run([sys.executable, str(ensure_path)], base)
        if code != 0:
            failures.append(("ensure_telemetry_paths", code, out[:500]))
    else:
        failures.append(("ensure_telemetry_paths", -1, "script not found"))

    # 2) telemetry_contract_audit.py (--strict-canonical unless --allow-legacy)
    audit_script = base / "scripts" / "audit" / "telemetry_contract_audit.py"
    if audit_script.exists():
        cmd = [sys.executable, str(audit_script), "--base-dir", str(base), "--n", "50"]
        if not getattr(args, "allow_legacy", False):
            cmd.append("--strict-canonical")
        code, out = run(cmd, base)
        if code != 0:
            failures.append(("telemetry_contract_audit (strict-canonical)", code, out[:800]))
    else:
        failures.append(("telemetry_contract_audit", -1, "script not found"))

    # 3) audit_direction_intel_wiring.py (optional: only if script exists)
    wiring_script = base / "scripts" / "audit_direction_intel_wiring.py"
    if wiring_script.exists():
        code, out = run([sys.executable, str(wiring_script), "--base-dir", str(base)], base)
        if code != 0:
            failures.append(("audit_direction_intel_wiring", code, out[:500]))

    if failures:
        print("Telemetry integrity gate FAILED:", file=sys.stderr)
        for name, code, msg in failures:
            print(f"  - {name}: exit {code}", file=sys.stderr)
            print(msg[:400], file=sys.stderr)
        return 1
    print("Telemetry integrity gate PASSED", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
