#!/usr/bin/env python3
"""
Run the full Alpaca backtest orchestration on the droplet via SSH, then fetch key artifacts.
On failure writes reports/backtests/RUN_FAILED_NEEDS_RERUN.txt (trigger) and retries up to max_attempts.
Usage: python scripts/run_alpaca_backtest_orchestration_via_droplet.py [--max-attempts N]
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
TRIGGER_FILE = REPO / "reports" / "backtests" / "RUN_FAILED_NEEDS_RERUN.txt"
ORCHESTRATION_TIMEOUT = 1200  # 20 min to reduce connection drop during long run

# Files to deploy to droplet before running (so run works without git push)
DEPLOY_FILES = [
    "scripts/run_alpaca_backtest_orchestration_on_droplet.sh",
    "scripts/check_backtest_scripts_present.py",
    "scripts/prep_alpaca_bars_snapshot.py",
    "scripts/run_simulation_backtest_on_droplet.py",
    "scripts/run_event_studies_on_droplet.py",
    "scripts/run_backtest_on_droplet.py",
    "scripts/param_sweep_orchestrator.py",
    "scripts/run_adversarial_tests_on_droplet.py",
    "scripts/multi_model_runner.py",
    "scripts/run_exit_optimization_on_droplet.py",
    "scripts/generate_backtest_summary.py",
    "scripts/run_governance_full.py",
    "scripts/backtest_governance_check.py",
    "scripts/score_vs_profitability.py",
    "scripts/customer_advocate_report.py",
    "scripts/review_score_analysis_soundness.py",
    "scripts/analysis/run_effectiveness_reports.py",
    "scripts/analysis/attribution_loader.py",
    "configs/backtest_config.json",
    "configs/param_grid.json",
]


def _run(c, cmd: str, timeout: int = 600):
    pd = getattr(c, "project_dir", REMOTE_ROOT) or REMOTE_ROOT
    full = f"cd {pd} && {cmd}"
    return c._execute(full, timeout=timeout)


def _write_trigger(run_id: str | None, reason: str, exit_code: int | None = None):
    TRIGGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    body = f"RUN_ID={run_id or 'unknown'}\nREASON={reason}\n"
    if exit_code is not None:
        body += f"EXIT_CODE={exit_code}\n"
    body += "\nFix the issue above and re-run: python scripts/run_alpaca_backtest_orchestration_via_droplet.py\n"
    TRIGGER_FILE.write_text(body, encoding="utf-8")
    print(f"Trigger written: {TRIGGER_FILE} ({reason})", file=sys.stderr)


def _verify_data(local_base: Path, run_id: str) -> tuple[bool, str]:
    """Return (success, reason)."""
    verdict = local_base / "FINAL_VERDICT.txt"
    if not verdict.exists():
        return False, "FINAL_VERDICT.txt missing"
    text = verdict.read_text(encoding="utf-8").strip()
    if "BACKTEST_RUN_OK" not in text:
        return False, f"FINAL_VERDICT not OK: {text[:200]}"
    if not (local_base / "baseline" / "metrics.json").exists() and not (local_base / "baseline" / "backtest_summary.json").exists():
        return False, "baseline metrics/summary missing"
    if not (local_base / "summary" / "summary.md").exists():
        return False, "summary/summary.md missing"
    return True, "OK"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-attempts", type=int, default=3, help="Max orchestration attempts (default 3)")
    ap.add_argument("--detach", action="store_true", help="Start orchestration with nohup on droplet, then poll and fetch (survives SSH disconnect)")
    args = ap.parse_args()
    max_attempts = max(1, args.max_attempts)
    if args.detach:
        return _run_detached(max_attempts)
    try:
        from droplet_client import DropletClient
    except Exception as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        print("Set DROPLET_HOST (and key/password) or droplet_config.json", file=sys.stderr)
        return 1

    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print(f"\n--- RETRY ATTEMPT {attempt}/{max_attempts} ---\n")
        run_id = None
        rc = -1
        try:
            with DropletClient() as c:
                run_id, rc = _run_one(c)
        except Exception as e:
            _write_trigger(run_id, f"exception: {e}", None)
            if attempt == max_attempts:
                raise
            continue
        local_base = REPO / "reports" / "backtests" / (run_id or "")
        if run_id and local_base.exists():
            ok, reason = _verify_data(local_base, run_id)
            if ok:
                if TRIGGER_FILE.exists():
                    TRIGGER_FILE.unlink()
                print("\n--- DATA VERIFIED: run complete ---")
                return 0
            _write_trigger(run_id, reason, rc)
        else:
            _write_trigger(run_id, "run_id missing or no artifacts fetched", rc)
        if attempt == max_attempts:
            print(f"All {max_attempts} attempts exhausted. See {TRIGGER_FILE}", file=sys.stderr)
            return 1
    return 1


def _run_detached(max_attempts: int) -> int:
    """Start orchestration with nohup on droplet; poll until done; fetch. Survives SSH disconnect."""
    try:
        from droplet_client import DropletClient
    except Exception as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print(f"\n--- RETRY ATTEMPT {attempt}/{max_attempts} ---\n")
        try:
            with DropletClient() as c:
                _run(c, "mkdir -p configs", timeout=5)
                ssh = c._connect()
                sftp = ssh.open_sftp()
                pd = REMOTE_ROOT
                for rel in DEPLOY_FILES:
                    local = REPO / rel
                    if not local.exists():
                        continue
                    remote = f"{pd}/{rel}"
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
                    except Exception:
                        pass
                sftp.close()
                # Start orchestration in background; RUN_ID is printed at start
                cmd = "cd /root/stock-bot && nohup bash -c 'bash scripts/run_alpaca_backtest_orchestration_on_droplet.sh 2>&1 | tee /tmp/orch_last.log' > /tmp/nohup_orch.log 2>&1 & echo started"
                out, err, rc = _run(c, cmd, timeout=30)
            # Poll: short SSH connections to check for latest run dir and FINAL_VERDICT or ERROR
            import time
            for _ in range(40):  # 40 * 30s = 20 min max
                time.sleep(30)
                try:
                    with DropletClient() as c:
                        out2, _, _ = _run(c, "ls -1t /root/stock-bot/reports/backtests 2>/dev/null | head -1", timeout=10)
                        run_id = (out2 or "").strip() if out2 else ""
                        if not run_id or not run_id.startswith("alpaca_backtest_"):
                            continue
                        out3, _, _ = _run(c, f"test -f /root/stock-bot/reports/backtests/{run_id}/FINAL_VERDICT.txt && cat /root/stock-bot/reports/backtests/{run_id}/FINAL_VERDICT.txt || test -f /root/stock-bot/reports/backtests/{run_id}/ERROR.txt && echo FAILED", timeout=10)
                        if out3 and "BACKTEST_RUN_OK" in (out3 or ""):
                            _fetch_artifacts(c, run_id)
                            local_base = REPO / "reports" / "backtests" / run_id
                            ok, _ = _verify_data(local_base, run_id)
                            if ok and TRIGGER_FILE.exists():
                                TRIGGER_FILE.unlink()
                            print("\n--- DATA VERIFIED: run complete (detach) ---")
                            return 0 if ok else 1
                        if out3 and "FAILED" in (out3 or ""):
                            break  # error file present, exit poll and retry
                except Exception:
                    pass
            _write_trigger(None, "detach poll timeout (20 min) or run failed", None)
        except Exception as e:
            _write_trigger(None, f"detach exception: {e}", None)
        if attempt == max_attempts:
            return 1
    return 1


def _fetch_artifacts(c, run_id: str) -> None:
    """Fetch key artifacts for run_id from droplet into local reports/backtests/run_id."""
    local_base = REPO / "reports" / "backtests" / run_id
    gov_base = REPO / "reports" / "governance" / run_id
    local_base.mkdir(parents=True, exist_ok=True)
    gov_base.mkdir(parents=True, exist_ok=True)
    sftp = c._connect().open_sftp()
    remote_base = f"{REMOTE_ROOT}/reports/backtests/{run_id}"
    remote_gov = f"{REMOTE_ROOT}/reports/governance/{run_id}"

    def get(remote_path: str, local_path: Path) -> bool:
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            sftp.get(remote_path, str(local_path))
            print(f"Fetched: {local_path.relative_to(REPO)}")
            return True
        except Exception:
            return False

    for rem, loc in [
        (f"{remote_base}/summary/summary.md", local_base / "summary" / "summary.md"),
        (f"{remote_base}/baseline/metrics.json", local_base / "baseline" / "metrics.json"),
        (f"{remote_base}/baseline/backtest_summary.json", local_base / "baseline" / "backtest_summary.json"),
        (f"{remote_base}/baseline/run_diagnostics.json", local_base / "baseline" / "run_diagnostics.json"),
        (f"{remote_base}/baseline/trades.csv", local_base / "baseline" / "trades.csv"),
        (f"{remote_base}/baseline/backtest_trades.jsonl", local_base / "baseline" / "backtest_trades.jsonl"),
        (f"{remote_base}/baseline/backtest_exits.jsonl", local_base / "baseline" / "backtest_exits.jsonl"),
        (f"{remote_gov}/backtest_governance_report.json", gov_base / "backtest_governance_report.json"),
        (f"{remote_base}/multi_model/prosecutor_output.md", local_base / "multi_model" / "prosecutor_output.md"),
        (f"{remote_base}/multi_model/defender_output.md", local_base / "multi_model" / "defender_output.md"),
        (f"{remote_base}/multi_model/sre_output.md", local_base / "multi_model" / "sre_output.md"),
        (f"{remote_base}/multi_model/board_verdict.md", local_base / "multi_model" / "board_verdict.md"),
        (f"{remote_base}/multi_model/board_verdict.json", local_base / "multi_model" / "board_verdict.json"),
        (f"{remote_base}/multi_model/evidence_manifest.txt", local_base / "multi_model" / "evidence_manifest.txt"),
        (f"{remote_base}/multi_model/plugins.txt", local_base / "multi_model" / "plugins.txt"),
        (f"{remote_base}/FINAL_VERDICT.txt", local_base / "FINAL_VERDICT.txt"),
        (f"{remote_base}/provenance.json", local_base / "provenance.json"),
        (f"{remote_base}/preflight.txt", local_base / "preflight.txt"),
        (f"{remote_base}/score_analysis/score_bands.json", local_base / "score_analysis" / "score_bands.json"),
        (f"{remote_base}/score_analysis/score_vs_profitability.md", local_base / "score_analysis" / "score_vs_profitability.md"),
        (f"{remote_base}/customer_advocate.md", local_base / "customer_advocate.md"),
    ]:
        get(rem, loc)
    try:
        sftp.close()
    except Exception:
        pass


def _run_one(c):
    """Execute one full deploy+run+fetch. Returns (run_id, rc)."""
    # 1) Git pull so droplet has latest
    print("--- GIT PULL ---")
    out, err, rc = _run(c, "git fetch origin && git pull origin main", timeout=60)
    if out:
        print(out[:600])
    if rc != 0:
        print("Warning: git pull non-zero", file=sys.stderr)

    # 2) Ensure remote configs dir exists, then deploy orchestration and required scripts/configs
    _run(c, "mkdir -p configs", timeout=5)
    print("\n--- DEPLOY SCRIPTS TO DROPLET ---")
    ssh = c._connect()
    sftp = ssh.open_sftp()
    pd = REMOTE_ROOT  # use absolute path for SFTP
    for rel in DEPLOY_FILES:
        local = REPO / rel
        if not local.exists():
            print(f"Skip (missing locally): {rel}")
            continue
        remote = f"{pd}/{rel}"
        try:
            parent = Path(remote).parent
            try:
                sftp.stat(str(parent))
            except FileNotFoundError:
                acc = Path(pd)
                try:
                    rel_parts = parent.relative_to(pd).parts
                except ValueError:
                    rel_parts = Path(rel).parent.parts
                for part in rel_parts:
                    acc = acc / part
                    try:
                        sftp.mkdir(str(acc))
                    except OSError:
                        pass
            if rel.endswith(".sh"):
                text = local.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
                sftp.putfo(io.BytesIO(text.encode("utf-8")), remote)
            else:
                sftp.put(str(local), remote)
            print(f"Deployed: {rel}")
        except Exception as e:
            print(f"Deploy failed {rel}: {e}")
    sftp.close()

    # 3) Run orchestration (long timeout to avoid connection drop)
    print("\n--- RUNNING BACKTEST ORCHESTRATION (this may take several minutes) ---")
    out, err, rc = _run(c, "bash scripts/run_alpaca_backtest_orchestration_on_droplet.sh", timeout=ORCHESTRATION_TIMEOUT)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)

    # 4) Discover RUN_ID from output or latest dir
    run_id = None
    if out:
        m = re.search(r"RUN_ID=(alpaca_backtest_[^\s]+)", out)
        if m:
            run_id = m.group(1).strip()
        m2 = re.search(r"Run ID:\s*(alpaca_backtest_[^\s]+)", out)
        if m2:
            run_id = run_id or m2.group(1).strip()
    if not run_id:
        out2, _, _ = _run(c, "ls -1t reports/backtests 2>/dev/null | head -5", timeout=10)
        if out2:
            for line in out2.strip().splitlines():
                line = line.strip()
                if line.startswith("alpaca_backtest_"):
                    run_id = line
                    break
    if not run_id:
        print("Could not determine RUN_ID; check droplet reports/backtests/", file=sys.stderr)
        return None, rc if rc != 0 else 1

    print(f"\n--- RUN_ID: {run_id} ---")

    # 5) Fetch key artifacts
    local_base = REPO / "reports" / "backtests" / run_id
    local_base.mkdir(parents=True, exist_ok=True)
    gov_base = REPO / "reports" / "governance" / run_id
    gov_base.mkdir(parents=True, exist_ok=True)

    sftp = c._connect().open_sftp()
    remote_base = f"{REMOTE_ROOT}/reports/backtests/{run_id}"
    remote_gov = f"{REMOTE_ROOT}/reports/governance/{run_id}"

    def get(remote_path: str, local_path: Path) -> bool:
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            sftp.get(remote_path, str(local_path))
            print(f"Fetched: {local_path.relative_to(REPO)}")
            return True
        except FileNotFoundError:
            print(f"Missing on droplet: {remote_path}")
            return False
        except Exception as e:
            print(f"Error fetching {remote_path}: {e}")
            return False

    get(f"{remote_base}/summary/summary.md", local_base / "summary" / "summary.md")
    get(f"{remote_base}/baseline/metrics.json", local_base / "baseline" / "metrics.json")
    get(f"{remote_base}/baseline/backtest_summary.json", local_base / "baseline" / "backtest_summary.json")
    get(f"{remote_base}/baseline/run_diagnostics.json", local_base / "baseline" / "run_diagnostics.json")
    get(f"{remote_base}/baseline/trades.csv", local_base / "baseline" / "trades.csv")
    get(f"{remote_base}/baseline/backtest_trades.jsonl", local_base / "baseline" / "backtest_trades.jsonl")
    get(f"{remote_base}/baseline/backtest_exits.jsonl", local_base / "baseline" / "backtest_exits.jsonl")
    get(f"{remote_gov}/backtest_governance_report.json", gov_base / "backtest_governance_report.json")
    get(f"{remote_base}/multi_model/prosecutor_output.md", local_base / "multi_model" / "prosecutor_output.md")
    get(f"{remote_base}/multi_model/defender_output.md", local_base / "multi_model" / "defender_output.md")
    get(f"{remote_base}/multi_model/sre_output.md", local_base / "multi_model" / "sre_output.md")
    get(f"{remote_base}/multi_model/board_verdict.md", local_base / "multi_model" / "board_verdict.md")
    get(f"{remote_base}/multi_model/board_verdict.json", local_base / "multi_model" / "board_verdict.json")
    get(f"{remote_base}/multi_model/evidence_manifest.txt", local_base / "multi_model" / "evidence_manifest.txt")
    get(f"{remote_base}/multi_model/plugins.txt", local_base / "multi_model" / "plugins.txt")
    get(f"{remote_base}/FINAL_VERDICT.txt", local_base / "FINAL_VERDICT.txt")
    get(f"{remote_base}/provenance.json", local_base / "provenance.json")
    get(f"{remote_base}/preflight.txt", local_base / "preflight.txt")
    get(f"{remote_base}/score_analysis/score_bands.json", local_base / "score_analysis" / "score_bands.json")
    get(f"{remote_base}/score_analysis/score_vs_profitability.md", local_base / "score_analysis" / "score_vs_profitability.md")
    get(f"{remote_base}/customer_advocate.md", local_base / "customer_advocate.md")

    try:
        sftp.close()
    except Exception:
        pass
    c.close()

    print("\n--- ARTIFACTS (local) ---")
    print(f"  reports/backtests/{run_id}/summary/summary.md")
    print(f"  reports/backtests/{run_id}/baseline/metrics.json")
    print(f"  reports/governance/{run_id}/backtest_governance_report.json")
    print(f"  reports/backtests/{run_id}/multi_model/board_verdict.md")
    print(f"  reports/backtests/{run_id}/FINAL_VERDICT.txt")

    return run_id, rc


if __name__ == "__main__":
    sys.exit(main())
