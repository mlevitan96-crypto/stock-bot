#!/usr/bin/env python3
"""
Run WHY WE DIDN'T WIN forensic + shadow exit surgical ON DROPLET, then fetch all artifacts locally.
1) Forensic: trace/attribution join, lag, board packet, CSA verdict.
2) Surgical: lag distribution, first-firing condition, shadow exit-on-first-eligibility PnL.
Execute from repo root. Requires: droplet_client.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"
EXPERIMENTS = REPO / "reports" / "experiments"


def main() -> int:
    ap = argparse.ArgumentParser(description="Run why-we-didnt-win forensic on droplet and fetch 6 artifacts")
    ap.add_argument("--date", default="2026-03-09", help="YYYY-MM-DD")
    ap.add_argument("--skip-surgical", action="store_true", help="Skip shadow exit surgical (only run forensic)")
    ap.add_argument("--run-exit-lag-experiment", action="store_true", help="Run exit-lag compression shadow replay and fetch experiment artifacts")
    ap.add_argument("--run-exit-lag-multi-day", action="store_true", help="Run exit-lag multi-day validation and fetch multi-day artifacts (uses existing EXIT_LAG_SHADOW_RESULTS_*.json)")
    ap.add_argument("--exit-lag-days", type=int, default=10, help="Max days for multi-day validation (default 10)")
    ap.add_argument("--backfill-exit-lag-days", type=int, default=0, help="Backfill shadow results for last N trading days (SRE/CSA); then run multi-day. 0 = off")
    ap.add_argument("--anchor-date", default=None, help="Anchor date YYYY-MM-DD for backfill (default: --date)")
    ap.add_argument("--fetch-logs", action="store_true", help="Also fetch raw logs from droplet (exit_attribution, exit_decision_trace, blocked_trades) to droplet_data/ for local scenario use")
    args = ap.parse_args()
    date_str = args.date

    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1

    client = DropletClient()

    out_pull, err_pull, rc_pull = client._execute_with_cd("git pull origin main", timeout=30)
    print("git pull:", out_pull or err_pull or "ok")

    if args.backfill_exit_lag_days and args.backfill_exit_lag_days > 0:
        # Ensure exit-lag scripts exist on droplet (in case not yet on main)
        pd = client.project_dir.rstrip("/")
        scripts_to_upload = [
            ("scripts/experiments/run_exit_lag_backfill_days.py", "scripts/experiments/run_exit_lag_backfill_days.py"),
            ("scripts/experiments/run_exit_lag_multi_day_validation.py", "scripts/experiments/run_exit_lag_multi_day_validation.py"),
            ("scripts/experiments/run_exit_lag_adversarial_review.py", "scripts/experiments/run_exit_lag_adversarial_review.py"),
            ("scripts/experiments/run_exit_lag_customer_advocate_note.py", "scripts/experiments/run_exit_lag_customer_advocate_note.py"),
        ]
        for local_rel, remote_rel in scripts_to_upload:
            local_path = REPO / local_rel
            if local_path.exists():
                remote_path = f"{pd}/{remote_rel}"
                try:
                    client.put_file(local_path, remote_path)
                    print("Uploaded", remote_rel)
                except Exception as e:
                    print("Upload failed for", remote_rel, e, file=sys.stderr)

        anchor = args.anchor_date or date_str
        cmd_backfill = f"python3 scripts/experiments/run_exit_lag_backfill_days.py --days {args.backfill_exit_lag_days} --anchor-date {anchor}"
        out_bf, err_bf, rc_bf = client._execute_with_cd(cmd_backfill, timeout=600)
        print("--- Exit-lag backfill (SRE) ---")
        print(out_bf or "")
        if err_bf:
            print(err_bf, file=sys.stderr)
        if rc_bf != 0:
            print("Backfill had failures (check manifest).", file=sys.stderr)
        # After backfill, run multi-day validation (includes adversarial + customer advocate)
        cmd_multi = f"python3 scripts/experiments/run_exit_lag_multi_day_validation.py --days {args.exit_lag_days}"
        out_multi, err_multi, rc_multi = client._execute_with_cd(cmd_multi, timeout=90)
        print("--- Exit-lag multi-day validation (CSA + adversarial + customer advocate) ---")
        print(out_multi or "")
        if err_multi:
            print(err_multi, file=sys.stderr)
    else:
        cmd = f"python3 scripts/audit/run_why_we_didnt_win_forensic.py --date {date_str} --fail-if-no-trace-above 0.20"
        out, err, rc = client._execute_with_cd(cmd, timeout=300)
        print("--- Why we didn't win forensic ---")
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Forensic script exited", rc, file=sys.stderr)
            blocker_path = AUDIT / f"INTRADAY_FORENSIC_BLOCKERS_{date_str}.md"
            if blocker_path.exists():
                print("Blockers file written; check", blocker_path, file=sys.stderr)
            return rc

        if not args.skip_surgical:
            cmd_surg = f"python3 scripts/audit/run_intraday_shadow_exit_surgical.py --date {date_str}"
            out_surg, err_surg, rc_surg = client._execute_with_cd(cmd_surg, timeout=60)
            print("--- Shadow exit surgical ---")
            print(out_surg or "")
            if err_surg:
                print(err_surg, file=sys.stderr)
            if rc_surg != 0:
                print("Surgical script exited", rc_surg, file=sys.stderr)

        if args.run_exit_lag_experiment:
            cmd_replay = f"python3 scripts/experiments/run_exit_lag_shadow_replay.py --date {date_str}"
            out_replay, err_replay, rc_replay = client._execute_with_cd(cmd_replay, timeout=120)
            print("--- Exit-lag shadow replay ---")
            print(out_replay or "")
            if err_replay:
                print(err_replay, file=sys.stderr)
            if rc_replay != 0:
                print("Exit-lag replay exited", rc_replay, file=sys.stderr)

        if args.run_exit_lag_multi_day:
            cmd_multi = f"python3 scripts/experiments/run_exit_lag_multi_day_validation.py --days {args.exit_lag_days}"
            out_multi, err_multi, rc_multi = client._execute_with_cd(cmd_multi, timeout=90)
            print("--- Exit-lag multi-day validation (CSA + adversarial + customer advocate) ---")
            print(out_multi or "")
            if err_multi:
                print(err_multi, file=sys.stderr)
            if rc_multi != 0:
                print("Multi-day validation exited", rc_multi, file=sys.stderr)

    artifacts = [
        (AUDIT, f"INTRADAY_PORTFOLIO_UNREALIZED_CURVE_{date_str}.json"),
        (AUDIT, f"INTRADAY_EXIT_LAG_AND_GIVEBACK_{date_str}.json"),
        (AUDIT, f"INTRADAY_BLOCKED_COUNTERFACTUALS_{date_str}.json"),
        (AUDIT, f"INTRADAY_JOIN_DIAGNOSTICS_{date_str}.json"),
        (AUDIT, f"INTRADAY_FORENSIC_FULL_{date_str}.md"),
        (BOARD, f"INTRADAY_BOARD_PACKET_{date_str}.md"),
        (AUDIT, f"CSA_INTRADAY_VERDICT_{date_str}.json"),
        (AUDIT, f"INTRADAY_ELIGIBILITY_EXIT_LAG_DISTRIBUTION_{date_str}.json"),
        (AUDIT, f"INTRADAY_EXIT_CONDITION_FIRST_FIRE_{date_str}.json"),
        (AUDIT, f"INTRADAY_SHADOW_EXIT_ON_FIRST_ELIGIBILITY_{date_str}.json"),
        (AUDIT, f"INTRADAY_SHADOW_EXIT_SURGICAL_SUMMARY_{date_str}.md"),
    ]
    if args.run_exit_lag_experiment:
        artifacts.extend([
            (EXPERIMENTS, f"EXIT_LAG_SHADOW_RESULTS_{date_str}.json"),
            (EXPERIMENTS, f"EXIT_LAG_RISK_IMPACT_{date_str}.md"),
            (BOARD, f"EXIT_LAG_BOARD_PACKET_{date_str}.md"),
            (AUDIT, f"CSA_EXIT_LAG_VERDICT_{date_str}.json"),
        ])
    if args.run_exit_lag_multi_day or (args.backfill_exit_lag_days and args.backfill_exit_lag_days > 0):
        artifacts.extend([
            (EXPERIMENTS, "EXIT_LAG_MULTI_DAY_RESULTS.json"),
            (EXPERIMENTS, "EXIT_LAG_ROBUSTNESS_SCORECARD.md"),
            (EXPERIMENTS, "EXIT_LAG_REGIME_BREAKDOWN.md"),
            (EXPERIMENTS, "EXIT_LAG_ADVERSARIAL_REVIEW.md"),
            (EXPERIMENTS, "EXIT_LAG_CUSTOMER_ADVOCATE_NOTE.md"),
            (BOARD, "EXIT_LAG_MULTI_DAY_BOARD_PACKET.md"),
            (AUDIT, "CSA_EXIT_LAG_MULTI_DAY_VERDICT.json"),
        ])
    if args.backfill_exit_lag_days and args.backfill_exit_lag_days > 0:
        artifacts.append((EXPERIMENTS, "EXIT_LAG_BACKFILL_MANIFEST.json"))
    remote_audit = "reports/audit"
    remote_board = "reports/board"
    remote_experiments = "reports/experiments"
    for dir_path, name in artifacts:
        if dir_path == EXPERIMENTS:
            remote = f"{remote_experiments}/{name}"
        else:
            remote = f"{remote_audit}/{name}" if dir_path == AUDIT else f"{remote_board}/{name}"
        cat_out, _, _ = client._execute_with_cd(f"cat {remote} 2>/dev/null || true", timeout=15)
        if not (cat_out or "").strip():
            print("Missing on droplet:", remote, file=sys.stderr)
            continue
        dir_path.mkdir(parents=True, exist_ok=True)
        out_path = dir_path / name
        if name.endswith(".json"):
            try:
                json.loads(cat_out)
            except json.JSONDecodeError:
                cat_out = cat_out.strip()
            out_path.write_text(cat_out, encoding="utf-8")
        else:
            out_path.write_text(cat_out, encoding="utf-8")
        print("Fetched", out_path)

    if args.fetch_logs:
        data_dir = REPO / "droplet_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        pd = client.project_dir.rstrip("/")
        logs_to_fetch = [
            ("logs/exit_attribution.jsonl", data_dir / "logs" / "exit_attribution.jsonl"),
            ("reports/state/exit_decision_trace.jsonl", data_dir / "reports" / "state" / "exit_decision_trace.jsonl"),
            ("state/blocked_trades.jsonl", data_dir / "state" / "blocked_trades.jsonl"),
            ("logs/attribution.jsonl", data_dir / "logs" / "attribution.jsonl"),
        ]
        for remote_rel, local_path in logs_to_fetch:
            try:
                client.get_file(remote_rel, local_path)
                print("Fetched log", local_path)
            except Exception as e:
                print("Fetch log failed", remote_rel, e, file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
