#!/usr/bin/env python3
"""Deploy forward truth contract to droplet: git sync, upload files, install systemd, manual proof run."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402

PROJ = "/root/stock-bot"
TS_TAG = "20260327_FORWARD_TRUTH_FINAL"


def main() -> int:
    c = DropletClient()
    bundle: dict = {"ts": TS_TAG, "steps": {}}

    rg = c.execute_command(
        f"cd {PROJ} && git fetch origin main && git reset --hard origin/main && git rev-parse HEAD",
        timeout=120,
    )
    bundle["steps"]["git"] = {"stdout": (rg.get("stdout") or "").strip(), "exit_code": rg.get("exit_code")}

    upload = [
        "telemetry/alpaca_strict_completeness_gate.py",
        "scripts/audit/alpaca_strict_six_trade_additive_repair.py",
        "scripts/audit/alpaca_forward_truth_contract_runner.py",
        "deploy/systemd/alpaca-forward-truth-contract-run.sh",
        "deploy/systemd/alpaca-forward-truth-contract.service",
        "deploy/systemd/alpaca-forward-truth-contract.timer",
    ]
    for rel in upload:
        rel = rel.replace("\\", "/")
        lp = REPO / rel
        if not lp.is_file():
            bundle.setdefault("upload_skipped", []).append(rel)
            continue
        parent = rel.rsplit("/", 1)[0]
        c.execute_command(f"mkdir -p {PROJ}/{parent}", 15)
        c.put_file(lp, f"{PROJ}/{rel}")

    c.execute_command(
        f"sed -i 's/\\r$//' {PROJ}/deploy/systemd/alpaca-forward-truth-contract-run.sh 2>/dev/null; "
        f"chmod +x {PROJ}/deploy/systemd/alpaca-forward-truth-contract-run.sh",
        15,
    )

    # Install units to systemd (droplet runs as root).
    c.execute_command(
        f"cp {PROJ}/deploy/systemd/alpaca-forward-truth-contract.service /etc/systemd/system/ && "
        f"cp {PROJ}/deploy/systemd/alpaca-forward-truth-contract.timer /etc/systemd/system/ && "
        f"systemctl daemon-reload",
        timeout=60,
    )
    en = c.execute_command(
        "systemctl enable --now alpaca-forward-truth-contract.timer 2>&1",
        timeout=60,
    )
    bundle["steps"]["enable_timer"] = {"stdout": (en.get("stdout") or "").strip(), "exit_code": en.get("exit_code")}

    cat_s = c.execute_command("systemctl cat alpaca-forward-truth-contract.service 2>&1", 30)
    cat_t = c.execute_command("systemctl cat alpaca-forward-truth-contract.timer 2>&1", 30)
    st = c.execute_command("systemctl status alpaca-forward-truth-contract.timer --no-pager -l 2>&1", 30)
    bundle["steps"]["systemctl_cat_service"] = (cat_s.get("stdout") or "").strip()
    bundle["steps"]["systemctl_cat_timer"] = (cat_t.get("stdout") or "").strip()
    bundle["steps"]["systemctl_status_timer"] = (st.get("stdout") or "").strip()[:12000]

    manual = c.execute_command(
        "bash deploy/systemd/alpaca-forward-truth-contract-run.sh >/tmp/alpaca_ftc_last.log 2>&1; echo $? > /tmp/alpaca_ftc_ec.txt",
        timeout=600,
    )
    ec_f = c.execute_command("cat /tmp/alpaca_ftc_ec.txt 2>/dev/null || echo missing", 15)
    log_tail = c.execute_command("tail -c 12000 /tmp/alpaca_ftc_last.log 2>/dev/null || true", 15)
    mo = (log_tail.get("stdout") or "").strip()
    bundle["steps"]["manual_run"] = {
        "runner_ssh_meta": {"exit_code": manual.get("exit_code"), "stderr": (manual.get("stderr") or "").strip()[:2000]},
        "stdout_tail": mo[-25000:],
        "ec_file_raw": (ec_f.get("stdout") or "").strip()[:80],
    }
    try:
        raw_ec = (ec_f.get("stdout") or "").strip()
        if raw_ec and raw_ec != "missing":
            bundle["manual_exit_code"] = int(raw_ec.split()[0])
    except (ValueError, IndexError):
        bundle["manual_exit_parse_error"] = True

    lj = c.execute_command(
        "journalctl -u alpaca-forward-truth-contract.service --no-pager -n 120 2>&1",
        45,
    )
    bundle["steps"]["journalctl_service"] = (lj.get("stdout") or "").strip()[-80000:]

    ls_art = c.execute_command(
        f"ls -t {PROJ}/reports/ALPACA_FORWARD_TRUTH_RUN*.json 2>/dev/null | head -5 || true",
        20,
    )
    bundle["steps"]["recent_run_artifacts"] = (ls_art.get("stdout") or "").strip()
    latest = c.execute_command(
        f"L=$(ls -t {PROJ}/reports/ALPACA_FORWARD_TRUTH_RUN*.json 2>/dev/null | head -1); "
        f"test -n \"$L\" && head -c 2500 \"$L\" || echo {{}}",
        20,
    )
    bundle["steps"]["latest_run_json_head"] = (latest.get("stdout") or "").strip()

    dest = REPO / "reports" / "audit" / f"ALPACA_FORWARD_TRUTH_CONTRACT_DROPLET_BUNDLE_{TS_TAG}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(dest), "manual_exit": bundle.get("manual_exit_code")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
