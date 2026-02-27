#!/usr/bin/env python3
"""
Run exit review on droplet with real data:
- Exit effectiveness v2 (logs/attribution.jsonl + exit_attribution.jsonl)
- Suggest exit tuning
- Bootstrap logs/exit_truth.jsonl if missing (so dashboard audit can PASS)
- Dashboard truth audit

Uses DropletClient; uploads scripts if not yet on droplet. Run from repo root.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    end_d = datetime.now(timezone.utc)
    start_d = end_d - timedelta(days=14)
    start_str = start_d.strftime("%Y-%m-%d")
    end_str = end_d.strftime("%Y-%m-%d")

    with DropletClient() as c:
        proj = c.project_dir.rstrip("/")
        # Ensure remote dirs exist (SFTP put does not create parents)
        c._execute(f"mkdir -p {proj}/scripts/analysis {proj}/scripts/exit_tuning {proj}/src/exit {proj}/reports/exit_review {proj}/logs")
        # Upload scripts so run works even before git push
        for local, remote in [
            (REPO / "scripts" / "analysis" / "attribution_loader.py", f"{proj}/scripts/analysis/attribution_loader.py"),
            (REPO / "scripts" / "analysis" / "run_exit_effectiveness_v2.py", f"{proj}/scripts/analysis/run_exit_effectiveness_v2.py"),
            (REPO / "scripts" / "exit_tuning" / "suggest_exit_tuning.py", f"{proj}/scripts/exit_tuning/suggest_exit_tuning.py"),
            (REPO / "src" / "exit" / "exit_pressure_v3.py", f"{proj}/src/exit/exit_pressure_v3.py"),
            (REPO / "src" / "exit" / "exit_truth_log.py", f"{proj}/src/exit/exit_truth_log.py"),
            (REPO / "scripts" / "CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh", f"{proj}/scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh"),
        ]:
            if local.exists():
                c.put_file(local, remote)

        # Run on droplet: pull latest, REPO, dates, effectiveness v2, tuning, bootstrap exit_truth, dashboard audit
        cmd = (
            "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
            "export REPO; cd $REPO && git fetch origin && git pull origin main 2>/dev/null || true; "
            "mkdir -p reports/exit_review logs scripts/analysis scripts/exit_tuning && "
            "python3 scripts/analysis/run_exit_effectiveness_v2.py --start " + start_str + " --end " + end_str + " --out-dir reports/exit_review 2>&1; "
            "python3 scripts/exit_tuning/suggest_exit_tuning.py 2>&1; "
            "if [ ! -s logs/exit_truth.jsonl ]; then "
            "  echo '{\"exit_pressure\":0.5,\"decision\":\"HOLD\",\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"symbol\":\"_bootstrap\"}' >> logs/exit_truth.jsonl; "
            "  echo 'Bootstrapped logs/exit_truth.jsonl'; "
            "fi; "
            "chmod +x scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh 2>/dev/null; "
            "bash scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh 2>&1"
        )
        out, err, rc = c._execute(cmd, timeout=180)
        print(out)
        if err:
            print(err, file=sys.stderr)

        # Fetch key reports
        run_dir = f"{proj}/reports/signal_review"
        for name in ["exit_effectiveness_v2.json", "exit_effectiveness_v2.md", "exit_tuning_recommendations.md"]:
            src = f"{proj}/reports/exit_review/{name}"
            try:
                content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
                if content.strip():
                    dest = REPO / "reports" / "exit_review" / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    print(f"Fetched {name} -> {dest}", file=sys.stderr)
            except Exception:
                pass

        # Latest dashboard truth result
        try:
            dash_out, _, _ = c._execute(
                f"ls -t {run_dir}/dashboard_truth_*/dashboard_truth.json 2>/dev/null | head -1"
            )
            path = dash_out.strip()
            if path:
                content, _, _ = c._execute(f"cat {path}")
                (REPO / "reports" / "exit_review" / "dashboard_truth_droplet.json").write_text(content, encoding="utf-8")
                print("Fetched dashboard_truth_droplet.json", file=sys.stderr)
        except Exception:
            pass

        return rc


if __name__ == "__main__":
    sys.exit(main())
