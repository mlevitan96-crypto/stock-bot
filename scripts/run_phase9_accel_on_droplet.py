#!/usr/bin/env python3
"""
Run Phase 9 profitability acceleration ON THE DROPLET via DropletClient.

Steps:
  1) Droplet sync + state capture
  2) Authoritative baseline blame from logs
  3) Paper window + rolling effectiveness
  4) 30-trade early REVERT gate (if joined_count >= 30)
  5) 50-trade LOCK/REVERT gate (when joined_count >= 50)
  6) Next cycle stub (do not execute)

Uses logs-based effectiveness only (no backtest compare for exit levers).
Writes memos to reports/phase9_accel_decisions/ locally.
Requires: droplet_config.json (or DROPLET_* env), DropletClient.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE_TAG = datetime.now(timezone.utc).strftime("%Y%m%d")
DECISIONS_DIR = REPO / "reports" / "phase9_accel_decisions"
BASELINE_DIR = "reports/effectiveness_baseline_blame"
PAPER_CURRENT_DIR = "reports/effectiveness_paper_score028_current"
PAPER_GATE50_DIR = "reports/effectiveness_paper_score028_gate50"
PAPER_START_DEFAULT = "2026-02-18"


def _remote_cat(client, remote_path: str, timeout: int = 15) -> str:
    """Cat a file on droplet; return content or empty string."""
    out, _, _ = client._execute_with_cd(f"cat {remote_path} 2>/dev/null || true", timeout=timeout)
    return out or ""


def _parse_blame_from_summary(content: str) -> dict:
    """Extract joined_count, losers, weak_entry_pct, exit_timing_pct from EFFECTIVENESS_SUMMARY.md or similar."""
    r = {"joined_count": 0, "total_losing_trades": 0, "weak_entry_pct": 0, "exit_timing_pct": 0}
    for line in content.splitlines():
        if "Closed trades (joined):" in line:
            m = re.search(r"(\d+)", line)
            if m:
                r["joined_count"] = int(m.group(1))
        if "Total losing trades:" in line:
            m = re.search(r"(\d+)", line)
            if m:
                r["total_losing_trades"] = int(m.group(1))
        if "weak entry" in line and "%" in line:
            m = re.search(r"([\d.]+)", line)
            if m:
                r["weak_entry_pct"] = float(m.group(1))
        if "exit timing" in line and "%" in line:
            m = re.search(r"([\d.]+)", line)
            if m:
                r["exit_timing_pct"] = float(m.group(1))
    return r


def _parse_win_rate_giveback(content: str) -> tuple:
    """From exit_effectiveness or summary, get aggregate win_rate and avg giveback if possible."""
    # EFFECTIVENESS_SUMMARY doesn't have global win_rate; we need joined count and wins. Use blame + exit JSON.
    return None, None


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: {e}. Need droplet_config.json and DropletClient.", file=sys.stderr)
        return 1

    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        # ----- STEP 1: Droplet sync + state -----
        print("=== STEP 1: Droplet sync + state ===")
        out_status, err, _ = c._execute_with_cd("git status --short 2>/dev/null; git rev-parse HEAD 2>/dev/null", timeout=15)
        out_pull, err2, rc_pull = c._execute_with_cd(
            "git stash push -m 'pre-accel' 2>/dev/null || true; git pull origin main 2>&1", timeout=60
        )
        out_hash, _, _ = c._execute_with_cd("git rev-parse HEAD 2>/dev/null", timeout=5)
        commit_hash = (out_hash or "").strip() or "unknown"
        state_md = f"""# Phase 9 acceleration — Droplet state
**Date:** {DATE_TAG}
**Run:** Authoritative (on droplet via DropletClient)

## Git
- **Commit hash:** {commit_hash}
- **Pull exit code:** {rc_pull}
- **Status (pre-pull):** {out_status[:500] if out_status else 'N/A'}

## Confirmation
This run is on the droplet (commands executed via SSH).
"""
        (DECISIONS_DIR / f"{DATE_TAG}_droplet_state.md").write_text(state_md, encoding="utf-8")
        print(f"Recorded state: {commit_hash[:8]}")

        # ----- STEP 2: Authoritative baseline blame -----
        print("=== STEP 2: Baseline blame (from logs) ===")
        out_date, _, _ = c._execute_with_cd("date +%Y-%m-%d 2>/dev/null || true", timeout=5)
        end_date = (out_date or "").strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not end_date or len(end_date) < 10:
            end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cmd_baseline = (
            f"python3 scripts/analysis/run_effectiveness_reports.py "
            f"--start 2026-02-01 --end {end_date} --out-dir {BASELINE_DIR} && "
            f"python3 scripts/governance/generate_recommendation.py --effectiveness-dir {BASELINE_DIR}"
        )
        out_base, err_base, rc_base = c._execute_with_cd(cmd_baseline, timeout=300)
        print(out_base[-2000:] if len(out_base) > 2000 else out_base)
        if rc_base != 0:
            print("Baseline effectiveness failed; continuing to capture what exists.", file=sys.stderr)

        summary_base = _remote_cat(c, f"{BASELINE_DIR}/EFFECTIVENESS_SUMMARY.md")
        blame_json = _remote_cat(c, f"{BASELINE_DIR}/entry_vs_exit_blame.json")
        baseline_metrics = _parse_blame_from_summary(summary_base)
        try:
            blame_data = json.loads(blame_json) if blame_json.strip() else {}
            baseline_metrics["total_losing_trades"] = blame_data.get("total_losing_trades", 0)
            baseline_metrics["weak_entry_pct"] = blame_data.get("weak_entry_pct", 0)
            baseline_metrics["exit_timing_pct"] = blame_data.get("exit_timing_pct", 0)
        except Exception:
            pass

        conclusion = "EXIT still justified"
        if baseline_metrics.get("weak_entry_pct", 0) > baseline_metrics.get("exit_timing_pct", 0):
            conclusion = "ENTRY dominates — next cycle must be ENTRY"

        baseline_memo = f"""# Phase 9 acceleration — Baseline blame (authoritative, droplet)
**Date:** {DATE_TAG}

## Source
- **Dir:** {BASELINE_DIR}
- **Window:** 2026-02-01 to {end_date}

## Metrics
| Metric | Value |
|--------|--------|
| joined_count | {baseline_metrics.get('joined_count', 'N/A')} |
| total_losing_trades | {baseline_metrics.get('total_losing_trades', 'N/A')} |
| weak_entry_pct | {baseline_metrics.get('weak_entry_pct', 'N/A')} |
| exit_timing_pct | {baseline_metrics.get('exit_timing_pct', 'N/A')} |

## Conclusion
**{conclusion}**

## Multi-model (why this could be wrong)
- **Adversarial:** Sample may be regime-specific; blame can shift with more data.
- **Quant:** With <10 losers, percentages are noisy.
- **Product:** Re-run baseline when new logs accumulate; update this memo.
"""
        (DECISIONS_DIR / f"{DATE_TAG}_baseline_blame.md").write_text(baseline_memo, encoding="utf-8")

        # ----- STEP 3: Paper window + rolling effectiveness -----
        print("=== STEP 3: Paper-period effectiveness ===")
        state_json = _remote_cat(c, "state/live_paper_run_state.json")
        paper_start = PAPER_START_DEFAULT
        try:
            s = json.loads(state_json) if state_json.strip() else {}
            ts = s.get("details", {}).get("timestamp") or s.get("timestamp")
            if ts:
                from datetime import datetime as dt
                paper_start = dt.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            pass

        cmd_paper = (
            f"python3 scripts/analysis/run_effectiveness_reports.py "
            f"--start {paper_start} --end {end_date} --out-dir {PAPER_CURRENT_DIR}"
        )
        out_paper, _, rc_paper = c._execute_with_cd(cmd_paper, timeout=300)
        print(out_paper[-1500:] if len(out_paper) > 1500 else out_paper)

        summary_paper = _remote_cat(c, f"{PAPER_CURRENT_DIR}/EFFECTIVENESS_SUMMARY.md")
        paper_metrics = _parse_blame_from_summary(summary_paper)
        joined_count = paper_metrics.get("joined_count", 0)
        losers = paper_metrics.get("total_losing_trades", 0)

        # Update paper run doc checkpoint (append to local file)
        paper_run_path = REPO / "reports" / "PROFITABILITY_PAPER_RUN_2026-02-18.md"
        checkpoint_block = f"""
## Checkpoint update ({DATE_TAG} — droplet)
- **Paper window:** {paper_start} to {end_date}
- **joined_count:** {joined_count}
- **total_losing_trades:** {losers}
- **Baseline:** weak_entry_pct={baseline_metrics.get('weak_entry_pct')}, exit_timing_pct={baseline_metrics.get('exit_timing_pct')}
"""
        if paper_run_path.exists():
            t = paper_run_path.read_text(encoding="utf-8")
            if "Checkpoint update" not in t or DATE_TAG not in t:
                # Append before final Summary table if present
                if "## Summary" in t:
                    t = t.replace("## Summary", checkpoint_block + "\n## Summary")
                else:
                    t = t.rstrip() + "\n" + checkpoint_block + "\n"
                paper_run_path.write_text(t, encoding="utf-8")

        # ----- STEP 4: 30-trade gate -----
        if joined_count >= 30:
            print("=== STEP 4: 30-trade gate ===")
            base_wr = baseline_metrics.get("weak_entry_pct")  # we don't have baseline win_rate in summary; use blame as proxy
            # Early REVERT: win_rate < baseline - 3% OR giveback > baseline + 0.05. We need win_rate/giveback from effectiveness.
            blame_paper = _remote_cat(c, f"{PAPER_CURRENT_DIR}/entry_vs_exit_blame.json")
            paper_wr = None
            try:
                bp = json.loads(blame_paper) if blame_paper.strip() else {}
                # Compute win_rate from joined: we don't have it in blame. Use exit_effectiveness or signal for aggregate.
                pass
            except Exception:
                pass
            gate30_memo = f"""# Phase 9 acceleration — Paper gate 30 (droplet)
**Date:** {DATE_TAG}
**joined_count (paper):** {joined_count}

## Early REVERT rule
- REVERT if: win_rate < baseline - 3% OR giveback > baseline + 0.05

## Multi-model
- **Adversarial:** 30 trades is small; -3% could be noise.
- **Quant:** Proceed to 50-trade gate unless delta is extreme.
- **Product:** Document either way; do not LOCK at 30.

## Decision
- **REVERT:** (fill if criteria met)
- **Continue to gate 50:** (fill if criteria not met)
"""
            (DECISIONS_DIR / f"{DATE_TAG}_paper_gate_30.md").write_text(gate30_memo, encoding="utf-8")
            # If we had baseline win_rate and giveback we would compare and optionally run restart. Skip auto-REVERT without numbers.
        else:
            print(f"=== STEP 4: 30-trade gate skipped (joined_count={joined_count} < 30) ===")

        # ----- STEP 5: 50-trade gate -----
        if joined_count >= 50:
            print("=== STEP 5: 50-trade gate ===")
            cmd_gate50 = (
                f"python3 scripts/analysis/run_effectiveness_reports.py "
                f"--start {paper_start} --end {end_date} --out-dir {PAPER_GATE50_DIR}"
            )
            c._execute_with_cd(cmd_gate50, timeout=300)
            summary50 = _remote_cat(c, f"{PAPER_GATE50_DIR}/EFFECTIVENESS_SUMMARY.md")
            blame50 = _remote_cat(c, f"{PAPER_GATE50_DIR}/entry_vs_exit_blame.json")
            m50 = _parse_blame_from_summary(summary50)
            try:
                b50 = json.loads(blame50) if blame50.strip() else {}
                m50["weak_entry_pct"] = b50.get("weak_entry_pct", 0)
                m50["exit_timing_pct"] = b50.get("exit_timing_pct", 0)
            except Exception:
                pass

            comp_md = f"""# Phase 9 acceleration — Gate 50 comparison (droplet)
**Date:** {DATE_TAG}

## Baseline
- joined_count: {baseline_metrics.get('joined_count')}
- weak_entry_pct: {baseline_metrics.get('weak_entry_pct')}
- exit_timing_pct: {baseline_metrics.get('exit_timing_pct')}

## Proposed (paper score028)
- joined_count: {m50.get('joined_count')}
- weak_entry_pct: {m50.get('weak_entry_pct')}
- exit_timing_pct: {m50.get('exit_timing_pct')}

## LOCK criteria
- win_rate delta >= -2%
- giveback delta <= +0.05
(Fill win_rate/giveback from effectiveness JSONs if available.)
"""
            (DECISIONS_DIR / f"{DATE_TAG}_paper_gate_50_comparison.md").write_text(comp_md, encoding="utf-8")
            models_md = f"""# Phase 9 acceleration — Gate 50 multi-model (droplet)
**Date:** {DATE_TAG}

## Adversarial
- Why LOCK could be wrong: regime-specific sample.
- Why REVERT could be wrong: variance in short window.

## Quant
- 50 trades gives ~14%% SE on win_rate. LOCK provisional until confirmed.

## Product
- Document final decision in PROFITABILITY_PAPER_RUN_2026-02-18.md.

## Decision
- [ ] LOCK
- [ ] REVERT
(Fill after comparison.)
"""
            (DECISIONS_DIR / f"{DATE_TAG}_paper_gate_50_models.md").write_text(models_md, encoding="utf-8")
        else:
            print(f"=== STEP 5: 50-trade gate skipped (joined_count={joined_count} < 50) ===")

        # ----- STEP 6: Next cycle stub -----
        stub_path = REPO / "reports" / "change_proposals" / f"next_cycle_entry_or_exit_{DATE_TAG}.md"
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        if not stub_path.exists():
            stub_path.write_text(f"""# Change Proposal (stub): Next cycle — ENTRY or EXIT
**Date:** {DATE_TAG}
**Conclusion from baseline:** {conclusion}
Do not start until current paper overlay (score028) is decided at 50-trade gate.
""", encoding="utf-8")

    print("=== DONE ===")
    print(f"Memos written to {DECISIONS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
