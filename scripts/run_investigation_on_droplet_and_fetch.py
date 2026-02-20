#!/usr/bin/env python3
"""
Run investigation on droplet (baseline, full signal review, closed loops, optional signal breakdown)
and fetch report contents back. Prints data and writes fetched reports to reports/investigation/fetched/.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
FETCHED_DIR = REPO / "reports" / "investigation" / "fetched"


def _run(c, cmd: str, timeout: int = 120):
    """Execute on droplet with project_dir as cwd."""
    pd = c.project_dir
    full = f"cd {pd} && {cmd}"
    return c._execute(full, timeout=timeout)


def _cat(c, remote_path: str) -> str:
    """Read remote file content."""
    out, err, rc = _run(c, f"cat {remote_path} 2>/dev/null || echo '__MISSING__'", timeout=15)
    return out.strip() if out else ""


def main() -> int:
    try:
        from droplet_client import DropletClient
    except Exception as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        print("Set DROPLET_HOST (and key/password) or droplet_config.json", file=sys.stderr)
        return 1

    FETCHED_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    with DropletClient() as c:
        # 1) Git pull
        out, err, rc = _run(c, "git fetch origin && git pull origin main", timeout=60)
        results.append(("git_pull", rc, out[:500] + ("..." if len(out) > 500 else "")))
        print("--- GIT PULL ---")
        print(out[:800] if out else "(no output)")
        if rc != 0:
            print("Warning: git pull non-zero", file=sys.stderr)

        # 1b) Verify script presence (Phase 1)
        out0, err0, rc0 = _run(c, "python3 scripts/verify_droplet_script_presence.py", timeout=30)
        if out0:
            print("\n--- SCRIPT PRESENCE ---")
            print(out0[:400])
        # 2) Baseline snapshot
        out, err, rc = _run(c, "python3 scripts/investigation_baseline_snapshot_on_droplet.py", timeout=60)
        results.append(("baseline_snapshot", rc, out))
        print("\n--- BASELINE SNAPSHOT ---")
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)

        # 3) Full signal review (no --capture to avoid long run; use existing ledger)
        out, err, rc = _run(c, "python3 scripts/full_signal_review_on_droplet.py --days 7", timeout=120)
        results.append(("full_signal_review", rc, out))
        print("\n--- FULL SIGNAL REVIEW ---")
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)

        # 4a) Order reconciliation (Phase 4)
        out4a, err4a, rc4a = _run(c, "python3 scripts/order_reconciliation_on_droplet.py", timeout=30)
        if out4a:
            print("\n--- ORDER RECONCILIATION ---")
            print(out4a)
        # 4b) Closed loops checklist
        out, err, rc = _run(c, "python3 scripts/run_closed_loops_checklist_on_droplet.py", timeout=30)
        results.append(("closed_loops_checklist", rc, out))
        print("\n--- CLOSED LOOPS CHECKLIST ---")
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)

        # 5) Signal breakdown summary (if log has >= 100 lines)
        out, err, rc = _run(c, "wc -l logs/signal_score_breakdown.jsonl 2>/dev/null || echo '0'", timeout=10)
        n_breakdown = 0
        if out:
            try:
                n_breakdown = int(out.strip().split()[0])
            except Exception:
                pass
        if n_breakdown >= 100:
            out2, err2, rc2 = _run(c, "python3 scripts/signal_score_breakdown_summary_on_droplet.py", timeout=60)
            results.append(("signal_breakdown_summary", rc2, out2))
            print("\n--- SIGNAL BREAKDOWN SUMMARY ---")
            print(out2 or "(no output)")
        else:
            print(f"\n--- SIGNAL BREAKDOWN: skipped (lines={n_breakdown}, need 100) ---")

        # Fetch report files
        pd = c.project_dir
        to_fetch = [
            ("reports/investigation/BASELINE_SNAPSHOT.md", "BASELINE_SNAPSHOT.md"),
            ("reports/investigation/CLOSED_LOOPS_CHECKLIST.md", "CLOSED_LOOPS_CHECKLIST.md"),
            ("reports/investigation/DROPLET_SCRIPT_PRESENCE.md", "DROPLET_SCRIPT_PRESENCE.md"),
            ("reports/investigation/ORDER_RECONCILIATION.md", "ORDER_RECONCILIATION.md"),
            ("reports/signal_review/signal_funnel.md", "signal_funnel.md"),
            ("reports/signal_review/signal_funnel.json", "signal_funnel.json"),
            ("reports/signal_review/paper_trade_metric_reconciliation.md", "paper_trade_metric_reconciliation.md"),
            ("reports/signal_review/multi_model_adversarial_review.md", "multi_model_adversarial_review.md"),
            ("reports/signal_review/signal_score_breakdown_summary.md", "signal_score_breakdown_summary.md"),
            ("reports/signal_review/expectancy_gate_truth_200.md", "expectancy_gate_truth_200.md"),
        ]
        for remote, local_name in to_fetch:
            content = _cat(c, f"{pd}/{remote}")
            if content and "__MISSING__" not in content:
                local_path = FETCHED_DIR / local_name
                local_path.write_text(content, encoding="utf-8")
                print(f"\nFetched: {remote} -> {local_path}")
                results.append((f"fetched_{local_name}", 0, f"{len(content)} chars"))
            else:
                results.append((f"fetched_{local_name}", 1, "missing or empty"))
    # Summary
    print("\n" + "=" * 60)
    print("INVESTIGATION RUN SUMMARY")
    print("=" * 60)
    for name, code, note in results:
        print(f"  {name}: exit={code}  {note[:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
