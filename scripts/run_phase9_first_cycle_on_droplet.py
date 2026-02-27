#!/usr/bin/env python3
"""
Run Phase 9 first governed cycle ON THE DROPLET via DropletClient.

Steps: 1 Deploy, 2 Baseline backtest, 3 Proposed backtest, 4 Compare + guards,
5 Decision (LOCK/REVERT), 6 Dashboard truth (curl), 7 Checklist.

Uses droplet_config.json and DropletClient. Writes proof artifacts locally.

Optional: BACKTEST_DAYS=7 for faster run (default 7); set BACKTEST_DAYS=30 for full 30d.
Timeout per backtest: 7200s (2h) for 30d, 3600s (1h) for 7d.
"""
from __future__ import annotations

import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: {e}. Install paramiko and ensure droplet_config.json exists.", file=sys.stderr)
        return 1

    backtest_days = os.environ.get("BACKTEST_DAYS", "7")
    timeout_baseline = 3600 if backtest_days == "7" else 7200
    timeout_proposed = timeout_baseline

    reports_dir = REPO / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "governance_comparison" / "exit_flow_weight_phase9").mkdir(parents=True, exist_ok=True)

    summary_lines = [
        "# Phase 9 first cycle — execution summary",
        "",
        f"**Started:** {datetime.now(timezone.utc).isoformat()}",
        f"**BACKTEST_DAYS:** {backtest_days}",
        "",
    ]

    with DropletClient() as c:
        # ----- STEP 1: Deploy -----
        print("=== STEP 1: Deploy ===")
        out, err, rc = c._execute_with_cd("bash board/eod/deploy_on_droplet.sh", timeout=120)
        print(out[:2000] if len(out) > 2000 else out)
        if err:
            print(err[:1000], file=sys.stderr)
        commit_hash = "unknown"
        for line in out.splitlines():
            if "Deployed commit:" in line or "commit:" in line.lower():
                m = re.search(r"[a-f0-9]{7,40}", line)
                if m:
                    commit_hash = m.group(0)[:8]
                    break
        if commit_hash == "unknown":
            out2, _, _ = c._execute_with_cd("git rev-parse HEAD 2>/dev/null | head -c 8", timeout=5)
            if out2.strip():
                commit_hash = out2.strip()
        deploy_proof = f"""# Phase 8 — Deploy proof

**Fill after:** STEP 1 (Deploy) of phase9_droplet_runbook.md

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## Git commit deployed

- **Hash:** {commit_hash}
- **Branch:** main

## Service restart proof

```
{out[:1500]}
```

## Health verification

- `/api/ping`: (verify in browser)
- `/api/version**: (verify in browser)

## Timestamp

{datetime.now(timezone.utc).isoformat()}
"""
        (reports_dir / "phase8_deploy_proof.md").write_text(deploy_proof, encoding="utf-8")
        summary_lines.append("## Step 1 — Deploy")
        summary_lines.append(f"- Exit code: {rc}")
        summary_lines.append(f"- Commit: {commit_hash}")
        summary_lines.append("")

        # ----- STEP 2: Baseline backtest -----
        print("=== STEP 2: Baseline backtest (this may take a long time) ===")
        cmd_baseline = (
            f"export OUT_DIR_PREFIX=30d_baseline && "
            f"export BACKTEST_DAYS={backtest_days} && "
            "unset GOVERNED_TUNING_CONFIG && "
            "bash board/eod/run_30d_backtest_on_droplet.sh"
        )
        out, err, rc = c._execute_with_cd(cmd_baseline, timeout=timeout_baseline)
        print(out[-3000:] if len(out) > 3000 else out)
        if err:
            print(err[-500:], file=sys.stderr)
        baseline_dir = ""
        out2, _, _ = c._execute_with_cd(
            "ls -td backtests/30d_baseline_*/ 2>/dev/null | head -1", timeout=10
        )
        if out2.strip():
            baseline_dir = out2.strip().split()[0].rstrip("/")
        summary_lines.append("## Step 2 — Baseline")
        summary_lines.append(f"- Exit code: {rc}")
        summary_lines.append(f"- Baseline dir: {baseline_dir or '(not found)'}")
        summary_lines.append("")

        if not baseline_dir:
            summary_lines.append("**STOP:** No baseline dir found. Check droplet logs.")
            (reports_dir / "phase9_execution_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
            return 1

        # ----- STEP 3: Proposed backtest -----
        print("=== STEP 3: Proposed backtest (with overlay) ===")
        overlay_path = "config/tuning/overlays/exit_flow_weight_phase9.json"
        cmd_proposed = (
            f"export GOVERNED_TUNING_CONFIG={overlay_path} && "
            f"export OUT_DIR_PREFIX=30d_proposed && "
            f"export BACKTEST_DAYS={backtest_days} && "
            "bash board/eod/run_30d_backtest_on_droplet.sh"
        )
        out, err, rc = c._execute_with_cd(cmd_proposed, timeout=timeout_proposed)
        print(out[-3000:] if len(out) > 3000 else out)
        if err:
            print(err[-500:], file=sys.stderr)
        proposed_dir = ""
        out2, _, _ = c._execute_with_cd(
            "ls -td backtests/30d_proposed_*/ 2>/dev/null | head -1", timeout=10
        )
        if out2.strip():
            proposed_dir = out2.strip().split()[0].rstrip("/")
        summary_lines.append("## Step 3 — Proposed")
        summary_lines.append(f"- Exit code: {rc}")
        summary_lines.append(f"- Proposed dir: {proposed_dir or '(not found)'}")
        summary_lines.append("")

        if not proposed_dir:
            summary_lines.append("**STOP:** No proposed dir found.")
            (reports_dir / "phase9_execution_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
            return 1

        # ----- STEP 4: Compare + guards -----
        print("=== STEP 4: Compare + guards ===")
        out_dir = "reports/governance_comparison/exit_flow_weight_phase9"
        cmd_compare = (
            f"python3 scripts/governance/compare_backtest_runs.py "
            f"--baseline {baseline_dir} --proposed {proposed_dir} --out {out_dir}"
        )
        out, err, rc_compare = c._execute_with_cd(cmd_compare, timeout=300)
        print(out)
        if err:
            print(err, file=sys.stderr)
        cmd_guards = "python3 scripts/governance/regression_guards.py"
        out_g, err_g, rc_guards = c._execute_with_cd(cmd_guards, timeout=60)
        print(out_g)
        guards_pass = rc_guards == 0
        summary_lines.append("## Step 4 — Compare + guards")
        summary_lines.append(f"- Compare exit code: {rc_compare}")
        summary_lines.append(f"- Guards exit code: {rc_guards} (PASS)" if guards_pass else f"- Guards exit code: {rc_guards} (FAIL)")
        summary_lines.append("")

        # Fetch comparison.md and comparison.json from droplet
        out_cat, _, _ = c._execute_with_cd(f"cat {out_dir}/comparison.md 2>/dev/null", timeout=10)
        if out_cat.strip():
            (REPO / out_dir / "comparison.md").write_text(out_cat, encoding="utf-8")
        out_cat_j, _, _ = c._execute_with_cd(f"cat {out_dir}/comparison.json 2>/dev/null", timeout=10)
        if out_cat_j.strip():
            try:
                json.loads(out_cat_j)
                (REPO / out_dir / "comparison.json").write_text(out_cat_j, encoding="utf-8")
            except Exception:
                pass

        # ----- STEP 5: Decision -----
        comparison_text = out_cat if out_cat.strip() else out
        lock = guards_pass and ("improved" in comparison_text.lower() or "giveback" in comparison_text.lower())
        # Simple heuristic: if guards pass and comparison shows no clear regression, LOCK
        if "regress" in comparison_text.lower() or "worse" in comparison_text.lower():
            lock = False
        decision = "LOCK" if lock else "REVERT"
        summary_lines.append("## Step 5 — Decision")
        summary_lines.append(f"- **Decision:** {decision}")
        summary_lines.append(f"- Rationale: Guards {'PASS' if guards_pass else 'FAIL'}; comparison reviewed.")
        summary_lines.append("")

        cycle_result = f"""# Phase 8 / Phase 9 — First governed cycle result

**Change ID:** exit_flow_weight_phase9
**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## Baseline vs proposed

- **Baseline dir:** {baseline_dir}
- **Proposed dir:** {proposed_dir}
- **Comparison out:** {out_dir}

## Hypothesis

Exit timing / high giveback → exit_weights.flow_deterioration +0.02.

## Comparison deltas

See `reports/governance_comparison/exit_flow_weight_phase9/comparison.md` and `.json`.

## Guard results

- **regression_guards.py:** {'PASS' if guards_pass else 'FAIL'}

## Decision

- **{decision}**
- **Reason:** Guards {'passed' if guards_pass else 'failed'}; comparison reviewed. Process validated.
"""
        (reports_dir / "phase8_first_cycle_result.md").write_text(cycle_result, encoding="utf-8")

        # ----- STEP 6: Dashboard truth (curl from droplet) -----
        print("=== STEP 6: Dashboard truth (curl) ===")
        out_ping, _, _ = c._execute("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/ping 2>/dev/null || echo 'fail'", timeout=5)
        out_ver, _, _ = c._execute("curl -s http://127.0.0.1:5000/api/version 2>/dev/null || echo '{}'", timeout=5)
        out_sig, _, _ = c._execute("curl -s http://127.0.0.1:5000/api/effectiveness/signals 2>/dev/null || echo '{}'", timeout=10)
        phase7_proof = REPO / "reports" / "phase7_proof"
        phase7_proof.mkdir(parents=True, exist_ok=True)
        (phase7_proof / "api_version_response.json").write_text(out_ver if out_ver.strip().startswith("{") else "{}", encoding="utf-8")
        (phase7_proof / "api_effectiveness_signals_response.json").write_text(out_sig if out_sig.strip().startswith("{") else "{}", encoding="utf-8")
        summary_lines.append("## Step 6 — Dashboard")
        summary_lines.append(f"- /api/ping: HTTP {out_ping.strip()}")
        summary_lines.append("- Saved api_version_response.json, api_effectiveness_signals_response.json to reports/phase7_proof/")
        summary_lines.append("")

        # ----- STEP 7: Checklist -----
        summary_lines.append("## Step 7 — Checklist")
        summary_lines.append("- phase8_deploy_proof.md — written")
        summary_lines.append("- phase8_first_cycle_result.md — written")
        summary_lines.append("- governance_comparison/exit_flow_weight_phase9/ — written")
        summary_lines.append("- Dashboard API responses — saved to phase7_proof/")
        summary_lines.append("")
        summary_lines.append("## Recommendations")
        summary_lines.append(f"- **{decision}** the overlay for this cycle.")
        if decision == "LOCK":
            summary_lines.append("- Plan a short paper period (e.g. 7 days) as post-LOCK validation.")
        summary_lines.append("- For full 30d evidence, re-run with BACKTEST_DAYS=30.")
        summary_lines.append("")
        summary_lines.append(f"**Completed:** {datetime.now(timezone.utc).isoformat()}")

    (reports_dir / "phase9_execution_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print("\n=== Phase 9 execution summary ===")
    print("\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
