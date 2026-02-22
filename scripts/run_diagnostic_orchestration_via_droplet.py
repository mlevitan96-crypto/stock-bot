#!/usr/bin/env python3
"""
Run full diagnostic orchestration on droplet via SSH, then fetch artifacts.
Usage: python scripts/run_diagnostic_orchestration_via_droplet.py [--detach]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
REMOTE_ROOT = "/root/stock-bot"
ORCHESTRATION_TIMEOUT = 1800  # 30 min for full diagnostic

DEPLOY_FILES = [
    "scripts/run_diagnostic_orchestration_on_droplet.sh",
    "scripts/check_diagnostic_scripts_present.py",
    "scripts/run_simulation_backtest_on_droplet.py",
    "scripts/compute_per_signal_attribution.py",
    "scripts/run_signal_ablation_suite.py",
    "scripts/run_exec_sensitivity.py",
    "scripts/run_blocked_trade_analysis.py",
    "scripts/run_event_studies_on_droplet.py",
    "scripts/run_backtest_on_droplet.py",
    "scripts/param_sweep_orchestrator.py",
    "scripts/run_adversarial_tests_on_droplet.py",
    "scripts/multi_model_runner.py",
    "scripts/run_exit_optimization_on_droplet.py",
    "scripts/generate_backtest_summary.py",
    "scripts/run_governance_full.py",
    "scripts/prep_alpaca_bars_snapshot.py",
    "configs/backtest_config.json",
]


def _run(c, cmd: str, timeout: int = 600):
    pd = getattr(c, "project_dir", REMOTE_ROOT) or REMOTE_ROOT
    full = f"cd {pd} && {cmd}"
    out, err, rc = c._execute(full, timeout=timeout)
    return out, err, rc


def _fetch_artifacts(c, run_id: str) -> None:
    remote_base = f"{REMOTE_ROOT}/reports/backtests/{run_id}"
    remote_gov = f"{REMOTE_ROOT}/reports/governance/{run_id}"
    local_base = REPO / "reports" / "backtests" / run_id
    gov_base = REPO / "reports" / "governance" / run_id
    ssh = c._connect()
    sftp = ssh.open_sftp()

    def get(remote_path: str, local_path: Path) -> bool:
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            sftp.get(remote_path, str(local_path))
            print("Fetched:", local_path.relative_to(REPO))
            return True
        except Exception as e:
            print("Missing or error", remote_path, e)
            return False

    for rem, loc in [
        (f"{remote_base}/summary/summary.md", local_base / "summary" / "summary.md"),
        (f"{remote_base}/baseline/metrics.json", local_base / "baseline" / "metrics.json"),
        (f"{remote_base}/baseline/backtest_summary.json", local_base / "baseline" / "backtest_summary.json"),
        (f"{remote_base}/baseline/backtest_trades.jsonl", local_base / "baseline" / "backtest_trades.jsonl"),
        (f"{remote_base}/baseline/backtest_exits.jsonl", local_base / "baseline" / "backtest_exits.jsonl"),
        (f"{remote_base}/attribution/per_signal_pnl.json", local_base / "attribution" / "per_signal_pnl.json"),
        (f"{remote_base}/ablation/ablation_summary.json", local_base / "ablation" / "ablation_summary.json"),
        (f"{remote_base}/exec_sensitivity/exec_sensitivity.json", local_base / "exec_sensitivity" / "exec_sensitivity.json"),
        (f"{remote_base}/exit_sweep/exit_sweep_summary.json", local_base / "exit_sweep" / "exit_sweep_summary.json"),
        (f"{remote_base}/param_sweep/pareto_frontier.json", local_base / "param_sweep" / "pareto_frontier.json"),
        (f"{remote_gov}/backtest_governance_report.json", gov_base / "backtest_governance_report.json"),
        (f"{remote_base}/multi_model/board_verdict.md", local_base / "multi_model" / "board_verdict.md"),
        (f"{remote_base}/multi_model/board_verdict.json", local_base / "multi_model" / "board_verdict.json"),
        (f"{remote_base}/multi_model/plugins.txt", local_base / "multi_model" / "plugins.txt"),
        (f"{remote_base}/FINAL_VERDICT.txt", local_base / "FINAL_VERDICT.txt"),
        (f"{remote_base}/provenance.json", local_base / "provenance.json"),
        (f"{remote_base}/preflight.txt", local_base / "preflight.txt"),
    ]:
        get(rem, loc)
    try:
        sftp.close()
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detach", action="store_true", help="Run with nohup and poll")
    args = ap.parse_args()
    try:
        from droplet_client import DropletClient
    except Exception as e:
        print("DropletClient not available:", e, file=sys.stderr)
        return 1

    with DropletClient() as c:
        _run(c, "mkdir -p configs", timeout=5)
        print("--- DEPLOY SCRIPTS ---")
        ssh = c._connect()
        sftp = ssh.open_sftp()
        for rel in DEPLOY_FILES:
            local = REPO / rel
            if not local.exists():
                continue
            remote = f"{REMOTE_ROOT}/{rel}"
            try:
                parent = str(Path(remote).parent)
                try:
                    sftp.stat(parent)
                except FileNotFoundError:
                    pass
                if rel.endswith(".sh"):
                    text = local.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
                    sftp.putfo(io.BytesIO(text.encode("utf-8")), remote)
                else:
                    sftp.put(str(local), remote)
                print("Deployed:", rel)
            except Exception as e:
                print("Deploy failed", rel, e)
        sftp.close()

        print("--- RUN DIAGNOSTIC ORCHESTRATION ---")
        out, err, rc = _run(c, "bash scripts/run_diagnostic_orchestration_on_droplet.sh", timeout=ORCHESTRATION_TIMEOUT)
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)

    run_id = None
    if out:
        m = re.search(r"RUN_ID=(alpaca_diag_[^\s]+)", out)
        if m:
            run_id = m.group(1)
    if not run_id:
        print("Could not discover RUN_ID from output", file=sys.stderr)
        return 1

    with DropletClient() as c:
        _fetch_artifacts(c, run_id)

    print("--- ARTIFACTS ---")
    print("  reports/backtests/" + run_id + "/")
    print("  reports/governance/" + run_id + "/")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
