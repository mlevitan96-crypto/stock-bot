#!/usr/bin/env python3
"""
Run monolithic pre-Monday diagnostic orchestration on droplet via SSH, then fetch artifacts.
Usage: python scripts/run_monday_prep_via_droplet.py [--detach]
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
ORCHESTRATION_TIMEOUT = 2400  # 40 min for full Monday prep

DEPLOY_FILES = [
    "scripts/run_monday_prep_orchestration_on_droplet.sh",
    "scripts/run_simulation_backtest_on_droplet.py",
    "scripts/prep_alpaca_bars_snapshot.py",
    "scripts/run_event_studies_on_droplet.py",
    "scripts/run_backtest_on_droplet.py",
    "scripts/param_sweep_orchestrator.py",
    "scripts/run_adversarial_tests_on_droplet.py",
    "scripts/multi_model_runner.py",
    "scripts/run_exit_optimization_on_droplet.py",
    "scripts/generate_backtest_summary.py",
    "scripts/run_governance_full.py",
    "scripts/compute_per_signal_attribution.py",
    "scripts/run_signal_ablation_suite.py",
    "scripts/run_exec_sensitivity.py",
    "scripts/run_blocked_trade_analysis.py",
    "scripts/analysis/run_effectiveness_reports.py",
    "scripts/analysis/attribution_loader.py",
    "scripts/customer_advocate_report.py",
    "scripts/score_vs_profitability.py",
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
    local_base.mkdir(parents=True, exist_ok=True)
    gov_base.mkdir(parents=True, exist_ok=True)
    ssh = c._connect()
    sftp = ssh.open_sftp()

    def get(remote_path: str, local_path: Path) -> bool:
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            sftp.get(remote_path, str(local_path))
            print("Fetched:", local_path.relative_to(REPO))
            return True
        except Exception as e:
            print("Skip (missing/error):", remote_path, str(e)[:80])
            return False

    pairs = [
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
        (f"{remote_base}/param_sweep/best_config.json", local_base / "param_sweep" / "best_config.json"),
        (f"{remote_base}/blocked_analysis/blocked_opportunity_summary.json", local_base / "blocked_analysis" / "blocked_opportunity_summary.json"),
        (f"{remote_base}/blocked_analysis/blocked_opportunity_cost.md", local_base / "blocked_analysis" / "blocked_opportunity_cost.md"),
        (f"{remote_base}/score_analysis/score_bands.json", local_base / "score_analysis" / "score_bands.json"),
        (f"{remote_base}/score_analysis/score_vs_profitability.md", local_base / "score_analysis" / "score_vs_profitability.md"),
        (f"{remote_base}/customer_advocate.md", local_base / "customer_advocate.md"),
        (f"{remote_gov}/backtest_governance_report.json", gov_base / "backtest_governance_report.json"),
        (f"{remote_base}/multi_model/board_verdict.md", local_base / "multi_model" / "board_verdict.md"),
        (f"{remote_base}/multi_model/board_verdict.json", local_base / "multi_model" / "board_verdict.json"),
        (f"{remote_base}/multi_model/plugins.txt", local_base / "multi_model" / "plugins.txt"),
        (f"{remote_base}/multi_model/evidence_manifest.txt", local_base / "multi_model" / "evidence_manifest.txt"),
        (f"{remote_base}/FINAL_VERDICT.txt", local_base / "FINAL_VERDICT.txt"),
        (f"{remote_base}/provenance.json", local_base / "provenance.json"),
        (f"{remote_base}/preflight.txt", local_base / "preflight.txt"),
        (f"{remote_base}/config.json", local_base / "config.json"),
        (f"{remote_base}/NEXT_STEPS.md", local_base / "NEXT_STEPS.md"),
    ]
    for rem, loc in pairs:
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
                print("Skip (missing):", rel)
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
                print("Deploy failed:", rel, e)
        try:
            sftp.close()
        except Exception:
            pass

        print("\n--- RUN MONDAY PREP ORCHESTRATION ---")
        if args.detach:
            cmd = "nohup bash -c 'bash scripts/run_monday_prep_orchestration_on_droplet.sh 2>&1 | tee /tmp/monday_prep.log' > /tmp/monday_prep_nohup.log 2>&1 & echo started"
            out, err, rc = _run(c, cmd, timeout=60)
            combined = (out or "") + (err or "")
            if "started" not in combined:
                print("Failed to start detached", err or out, file=sys.stderr)
                return 1
            import time
            for _ in range(80):  # 80 * 30s = 40 min
                time.sleep(30)
                try:
                    with DropletClient() as c2:
                        out2, _, _ = _run(c2, "ls -1t /root/stock-bot/reports/backtests 2>/dev/null | head -5", timeout=15)
                        for line in (out2 or "").strip().splitlines():
                            line = line.strip()
                            if line.startswith("alpaca_monday_prep_"):
                                run_id = line
                                out3, _, _ = _run(c2, f"test -f /root/stock-bot/reports/backtests/{run_id}/FINAL_VERDICT.txt && cat /root/stock-bot/reports/backtests/{run_id}/FINAL_VERDICT.txt", timeout=10)
                                if out3 and "BACKTEST_RUN_OK" in (out3 or ""):
                                    _fetch_artifacts(c2, run_id)
                                    print("\n--- MONDAY PREP COMPLETE ---", run_id)
                                    return 0
                                if out3 and "BACKTEST_RUN_FAILED" in (out3 or ""):
                                    _fetch_artifacts(c2, run_id)
                                    print("\n--- RUN FAILED (artifacts fetched) ---", run_id, file=sys.stderr)
                                    return 1
                except Exception:
                    pass
            print("Detach poll timeout (40 min)", file=sys.stderr)
            return 1
        else:
            out, err, rc = _run(c, "bash scripts/run_monday_prep_orchestration_on_droplet.sh", timeout=ORCHESTRATION_TIMEOUT)
            if out:
                print(out)
            if err:
                print(err, file=sys.stderr)
            m = re.search(r"RUN_ID=(alpaca_monday_prep_[^\s]+)", out or "")
            run_id = m.group(1).strip() if m else None
            if not run_id and out:
                for line in (out or "").splitlines():
                    if "alpaca_monday_prep_" in line:
                        m2 = re.search(r"(alpaca_monday_prep_[^\s]+)", line)
                        if m2:
                            run_id = m2.group(1)
                            break
            if not run_id:
                out2, _, _ = _run(c, "ls -1t reports/backtests 2>/dev/null | head -5", timeout=10)
                for line in (out2 or "").strip().splitlines():
                    if line.strip().startswith("alpaca_monday_prep_"):
                        run_id = line.strip()
                        break
            if run_id:
                _fetch_artifacts(c, run_id)
                print("\n--- ARTIFACTS FETCHED ---", run_id)
            return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
