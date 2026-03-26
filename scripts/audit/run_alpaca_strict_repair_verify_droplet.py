#!/usr/bin/env python3
"""Upload strict-repair scripts, apply additive backfill on droplet, run strict gate + cert bundle."""
from __future__ import annotations

import json
import sys
from json import JSONDecoder
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402

PROJ = "/root/stock-bot"
# Same era as prior replay auto-era certification (no era policy change).
OPEN_TS = 1774535335.472568

UPLOAD = [
    "telemetry/alpaca_strict_completeness_gate.py",
    "scripts/audit/alpaca_strict_six_trade_additive_repair.py",
    "scripts/audit/alpaca_strict_repair_forensics.py",
    "scripts/audit/alpaca_strict_cohort_cert_bundle.py",
    "src/telemetry/strict_chain_guard.py",
    "src/exit/exit_attribution.py",
]


def main() -> int:
    c = DropletClient()
    out: dict = {"steps": {}}

    r0 = c.execute_command(
        f"cd {PROJ} && git fetch origin main && git reset --hard origin/main && git rev-parse HEAD",
        timeout=120,
    )
    out["steps"]["git"] = {"stdout": (r0.get("stdout") or "").strip(), "exit_code": r0.get("exit_code")}

    # Remove prior strict backfill sidecars only (never primary logs).
    c.execute_command(f"rm -f {PROJ}/logs/strict_backfill_run.jsonl {PROJ}/logs/strict_backfill_orders.jsonl {PROJ}/logs/strict_backfill_alpaca_unified_events.jsonl 2>/dev/null; true", 15)

    for rel in UPLOAD:
        rel = rel.replace("\\", "/")
        lp = REPO / rel
        if not lp.is_file():
            continue
        parent = rel.rsplit("/", 1)[0]
        c.execute_command(f"mkdir -p {PROJ}/{parent}", 15)
        c.put_file(lp, f"{PROJ}/{rel}")

    r1 = c.execute_command(
        f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python "
        f"{PROJ}/scripts/audit/alpaca_strict_six_trade_additive_repair.py --root {PROJ} --apply "
        f"--repair-all-incomplete-in-era --open-ts-epoch {OPEN_TS} 2>&1",
        timeout=300,
    )
    out["steps"]["repair_apply"] = {"stdout": (r1.get("stdout") or "").strip(), "exit_code": r1.get("exit_code")}

    r2 = c.execute_command(
        f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python "
        f"{PROJ}/scripts/audit/alpaca_strict_repair_forensics.py --root {PROJ} 2>&1",
        timeout=120,
    )
    fo = (r2.get("stdout") or "").strip()
    out["steps"]["forensics"] = {"stdout_tail": fo[-25000:], "exit_code": r2.get("exit_code")}
    i = fo.find("{")
    if i >= 0:
        try:
            out["forensics_json"] = JSONDecoder().raw_decode(fo, i)[0]
        except json.JSONDecodeError:
            out["forensics_parse_error"] = True

    r3 = c.execute_command(
        f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python "
        f"{PROJ}/telemetry/alpaca_strict_completeness_gate.py --root {PROJ} --audit --open-ts-epoch {OPEN_TS} 2>&1",
        timeout=180,
    )
    gout = (r3.get("stdout") or "").strip()
    out["steps"]["strict_gate"] = {"exit_code": r3.get("exit_code"), "stdout_tail": gout[-20000:]}
    gi = gout.find("{")
    if gi >= 0:
        try:
            out["strict_gate_json"] = JSONDecoder().raw_decode(gout, gi)[0]
        except json.JSONDecodeError:
            out["strict_gate_parse_error"] = True

    r4 = c.execute_command(
        f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python "
        f"{PROJ}/scripts/audit/alpaca_strict_cohort_cert_bundle.py --root {PROJ} "
        f"--open-ts-epoch {OPEN_TS} --trace-sample 15 2>&1",
        timeout=180,
    )
    bout = (r4.get("stdout") or "").strip()
    out["steps"]["cert_bundle"] = {"exit_code": r4.get("exit_code"), "stdout_tail": bout[-12000:]}
    bi = bout.find("{")
    if bi >= 0:
        try:
            out["cert_bundle_json"] = JSONDecoder().raw_decode(bout, bi)[0]
        except json.JSONDecodeError:
            out["cert_bundle_parse_error"] = True

    out["open_ts_epoch_used"] = OPEN_TS
    dest = REPO / "reports" / "ALPACA_STRICT_REPAIR_VERIFY_DROPLET.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(dest), "incomplete": (out.get("strict_gate_json") or {}).get("trades_incomplete")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
