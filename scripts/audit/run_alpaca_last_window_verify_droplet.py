#!/usr/bin/env python3
"""Git sync droplet, upload last-window gate/runner/engine/SRE, run verify, pull key artifacts locally."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402

PROJ = "/root/stock-bot"
TS = "20260327_LAST_WINDOW"


def main() -> int:
    c = DropletClient()
    bundle: dict = {"ts": TS, "steps": {}}

    rg = c.execute_command(
        f"cd {PROJ} && git fetch origin main && git reset --hard origin/main && git rev-parse HEAD",
        timeout=120,
    )
    bundle["steps"]["git"] = {"stdout": (rg.get("stdout") or "").strip(), "exit_code": rg.get("exit_code")}

    for rel in (
        "telemetry/alpaca_strict_completeness_gate.py",
        "scripts/audit/alpaca_forward_truth_contract_runner.py",
        "scripts/audit/alpaca_sre_auto_repair_engine.py",
        "scripts/audit/alpaca_sre_repair_playbooks.py",
        "scripts/audit/alpaca_strict_six_trade_additive_repair.py",
        "scripts/audit/alpaca_last_window_learning_verify.py",
    ):
        rel = rel.replace("\\", "/")
        lp = REPO / rel
        parent = rel.rsplit("/", 1)[0]
        c.execute_command(f"mkdir -p {PROJ}/{parent}", 15)
        c.put_file(lp, f"{PROJ}/{rel}")

    vr = c.execute_command(
        f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python -u {PROJ}/scripts/audit/alpaca_last_window_learning_verify.py "
        f"--root {PROJ} --ts {TS} 2>&1",
        timeout=900,
    )
    bundle["steps"]["verify"] = {"stdout": (vr.get("stdout") or "").strip()[-8000:], "exit_code": vr.get("exit_code")}

    paths = [
        f"{PROJ}/reports/audit/ALPACA_LAST_WINDOW_SCOPE_{TS}.md",
        f"{PROJ}/reports/ALPACA_LAST_WINDOW_TRUTH_{TS}.json",
        f"{PROJ}/reports/audit/ALPACA_LAST_WINDOW_TRUTH_{TS}.md",
        f"{PROJ}/reports/audit/ALPACA_LAST_WINDOW_LEARNING_VERDICT_{TS}.md",
    ]
    fetched = {}
    for p in paths:
        cat = c.execute_command(f"cat {p} 2>/dev/null || echo MISSING", 60)
        fetched[p] = (cat.get("stdout") or "").strip()
    bundle["fetched"] = fetched

    out = REPO / "reports" / f"ALPACA_LAST_WINDOW_DROPLET_BUNDLE_{TS}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    # Mirror verdict + scope + truth json locally when present
    scope_local = REPO / "reports" / "audit" / f"ALPACA_LAST_WINDOW_SCOPE_{TS}.md"
    truth_local = REPO / "reports" / f"ALPACA_LAST_WINDOW_TRUTH_{TS}.json"
    verdict_local = REPO / "reports" / "audit" / f"ALPACA_LAST_WINDOW_LEARNING_VERDICT_{TS}.md"
    sk = f"{PROJ}/reports/audit/ALPACA_LAST_WINDOW_SCOPE_{TS}.md"
    if sk in fetched and not fetched[sk].startswith("MISSING"):
        scope_local.write_text(fetched[sk], encoding="utf-8")
    tk = f"{PROJ}/reports/ALPACA_LAST_WINDOW_TRUTH_{TS}.json"
    if tk in fetched and not fetched[tk].startswith("MISSING"):
        truth_local.write_text(fetched[tk], encoding="utf-8")
    vk = f"{PROJ}/reports/audit/ALPACA_LAST_WINDOW_LEARNING_VERDICT_{TS}.md"
    if vk in fetched and not fetched[vk].startswith("MISSING"):
        verdict_local.write_text(fetched[vk], encoding="utf-8")

    print(json.dumps({"written": str(out), "local_verdict": str(verdict_local)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
