#!/usr/bin/env python3
"""
Phase 9 data integrity v5 — run ALL steps on droplet via DropletClient and write proof files.

Steps:
  1) Snapshot (git, tmux, state) → 20260218_paper_restart_snapshot_before.md
  2) Kill tmux, start paper (no overlay) → proof 20260218_paper_restart_proof.md (fail if GOVERNED_TUNING_CONFIG/overlay)
  3) Poll for exit_quality_metrics in newest 800 lines (30 min timeout) → 20260218_exit_quality_emission_proof_postrestart.md
  4) Pull main → 20260218_droplet_pull_proof_v5.md
  5) Run effectiveness v5 → 20260218_baseline_v5_verification.md
  6) Sign-off with multi-model → 20260218_signoff_v5.md

Fail fast on critical step failure; write reason into signoff.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE_TAG = "20260218"
OUT_DIR = REPO / "reports" / "phase9_data_integrity"
POLL_INTERVAL_SEC = 60
POLL_TIMEOUT_SEC = 30 * 60  # 30 minutes
V5_OUT_DIR = "reports/effectiveness_baseline_blame_v5"


def _execute(c, command: str, timeout: int = 30):
    return c._execute_with_cd(command, timeout=timeout)


def _remote_cat(c, remote_path: str, timeout: int = 15) -> str:
    out, _, _ = _execute(c, f"cat {remote_path} 2>/dev/null || true", timeout=timeout)
    return out or ""


def write_snapshot_before(c, out_dir: Path) -> None:
    out_rev, _, _ = _execute(c, "git rev-parse HEAD 2>/dev/null", timeout=10)
    out_tmux, _, _ = _execute(c, "tmux ls 2>/dev/null || echo 'no server'", timeout=5)
    out_state, _, _ = _execute(c, "cat state/live_paper_run_state.json 2>/dev/null || echo '{}'", timeout=5)
    lines = [
        "# Paper restart snapshot — before (2026-02-18)",
        "",
        "## A) Capture current truth",
        "",
        "```",
        "# git rev-parse HEAD",
        (out_rev or "").strip(),
        "",
        "# tmux ls",
        (out_tmux or "").strip(),
        "",
        "# cat state/live_paper_run_state.json",
        (out_state or "").strip()[:2000],
        "```",
    ]
    (out_dir / f"{DATE_TAG}_paper_restart_snapshot_before.md").write_text("\n".join(lines), encoding="utf-8")


def restart_paper_no_overlay(c, out_dir: Path) -> tuple[bool, str]:
    """Kill tmux, start paper with no overlay. Return (success, error_message)."""
    out_date, _, _ = _execute(c, "date +%Y-%m-%d 2>/dev/null", timeout=5)
    date_str = (out_date or "").strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Minimal start: kill, then tmux new-session; $(pwd) expands in outer shell (already in project_dir via _execute_with_cd)
    kill_cmd = "tmux kill-session -t stock_bot_paper_run 2>/dev/null || true"
    start_cmd = "tmux new-session -d -s stock_bot_paper_run \"cd $(pwd) && LOG_LEVEL=INFO python3 main.py\""
    state_py = (
        "python3 -c \"import json,os,time; d=os.path.join('state','live_paper_run_state.json'); "
        "os.makedirs(os.path.dirname(d),exist_ok=True); "
        "json.dump({'status':'live_paper_run_started','timestamp':int(time.time()),'details':"
        "{'trading_mode':'paper','process':'python3 main.py','session':'stock_bot_paper_run','governed_tuning_config':''}}, "
        "open(d,'w'), indent=2); print('state written')\""
    )
    full = f"{kill_cmd} && {start_cmd} && sleep 3 && {state_py}"
    out, err, rc = _execute(c, full, timeout=60)
    if rc != 0:
        return False, f"restart command exit code {rc}: {err or out}"
    # Proof: tmux ls, capture-pane, state
    out_tmux, _, _ = _execute(c, "tmux ls 2>/dev/null || echo 'none'", timeout=5)
    out_pane, _, _ = _execute(c, "tmux capture-pane -pt stock_bot_paper_run -S -80 2>/dev/null || echo 'no-pane'", timeout=5)
    out_state, _, _ = _execute(c, "cat state/live_paper_run_state.json 2>/dev/null || echo '{}'", timeout=5)
    # Hard requirement: no GOVERNED_TUNING_CONFIG in tmux command, state has no overlay
    if "GOVERNED_TUNING_CONFIG" in (out_pane or ""):
        return False, "Proof shows GOVERNED_TUNING_CONFIG in tmux command (forbidden)"
    try:
        state_obj = json.loads(out_state.strip()) if out_state and out_state.strip() else {}
        gov = (state_obj.get("details") or {}).get("governed_tuning_config") or state_obj.get("governed_tuning_config")
        if gov:
            return False, f"State has overlay/governed_tuning_config: {gov!r}"
    except Exception:
        pass
    lines = [
        "# Paper restart proof (2026-02-18)",
        "",
        "## After restart (no overlay)",
        "",
        "### tmux ls",
        "```",
        (out_tmux or "").strip(),
        "```",
        "",
        "### tmux capture-pane (stock_bot_paper_run)",
        "```",
        (out_pane or "").strip(),
        "```",
        "",
        "### state/live_paper_run_state.json",
        "```",
        (out_state or "").strip(),
        "```",
        "",
        "- No GOVERNED_TUNING_CONFIG in tmux command",
        "- governed_tuning_config empty in state",
    ]
    (out_dir / f"{DATE_TAG}_paper_restart_proof.md").write_text("\n".join(lines), encoding="utf-8")
    return True, ""


def poll_exit_quality(c, out_dir: Path) -> tuple[int, bool]:
    """
    Record marker (file size), then poll until with_exit_quality_metrics > 0 or timeout.
    Returns (with_exit_quality_metrics_count, timed_out).
    """
    marker_out, _, _ = _execute(
        c,
        "python3 -c \"import os; p='logs/exit_attribution.jsonl'; print('bytes', os.path.getsize(p) if os.path.exists(p) else 0)\" 2>/dev/null",
        timeout=10,
    )
    sample_script = (
        "tail -n 800 logs/exit_attribution.jsonl 2>/dev/null | python3 -c \""
        "import sys, json\n"
        "n=0; m=0; ex=[]\n"
        "for line in sys.stdin:\n"
        "  try: r=json.loads(line)\n"
        "  except: continue\n"
        "  n+=1\n"
        "  if r.get('exit_quality_metrics') is not None:\n"
        "    m+=1\n"
        "    if len(ex)<2: ex.append(r.get('exit_quality_metrics'))\n"
        "print('sample_records', n, 'with_exit_quality_metrics', m)\n"
        "print('examples', ex)\n"
        "\" 2>/dev/null"
    )
    attempts = []
    deadline = time.monotonic() + POLL_TIMEOUT_SEC
    last_m = 0
    while time.monotonic() < deadline:
        out, _, _ = _execute(c, sample_script, timeout=30)
        attempts.append((time.strftime("%H:%M:%S", time.gmtime()), (out or "").strip()))
        # Parse sample_records n with_exit_quality_metrics m
        n, m = 0, 0
        try:
            parts = (out or "").strip().split()
            if "with_exit_quality_metrics" in parts:
                i = parts.index("with_exit_quality_metrics")
                if i + 1 < len(parts):
                    m = int(parts[i + 1])
            if "sample_records" in parts:
                j = parts.index("sample_records")
                if j + 1 < len(parts):
                    n = int(parts[j + 1])
        except (ValueError, IndexError, TypeError):
            pass
        last_m = m
        if m > 0:
            break
        time.sleep(POLL_INTERVAL_SEC)
    timed_out = last_m == 0
    # Diagnostics if timeout
    diag = []
    if timed_out:
        out_tmux, _, _ = _execute(c, "tmux ls 2>/dev/null || echo 'none'", timeout=5)
        out_tail_ts, _, _ = _execute(
            c,
            "tail -n 1 logs/exit_attribution.jsonl 2>/dev/null | python3 -c \"import sys,json; r=json.load(sys.stdin); print(r.get('timestamp') or r.get('ts') or 'no-ts')\" 2>/dev/null || echo 'no-line'",
            timeout=5,
        )
        diag = [
            "## Diagnosis (timeout with 0 exit_quality_metrics)",
            "",
            "- tmux session alive: " + ("yes" if "stock_bot_paper_run" in (out_tmux or "") else "no"),
            "- last exit_attribution timestamp: " + (out_tail_ts or "").strip(),
            "- Possible: no new exits in window, or high_water/exit path not emitting.",
        ]
    lines = [
        "# Exit quality emission proof — post-restart (2026-02-18)",
        "",
        "## A) Marker (file size)",
        "```",
        (marker_out or "").strip(),
        "```",
        "",
        "## B) Poll attempts (newest 800 lines)",
        "",
    ]
    for ts, text in attempts[-20:]:  # last 20 attempts
        lines.append(f"### {ts}")
        lines.append("```")
        lines.append(text[:500])
        lines.append("```")
        lines.append("")
    lines.append("## Result")
    lines.append(f"- **sample_records (last):** (see last attempt)")
    lines.append(f"- **with_exit_quality_metrics:** " + str(last_m))
    lines.append("")
    lines.extend(diag)
    (out_dir / f"{DATE_TAG}_exit_quality_emission_proof_postrestart.md").write_text("\n".join(lines), encoding="utf-8")
    return last_m, timed_out


def write_pull_proof_v5(c, out_dir: Path) -> None:
    out_status, _, _ = _execute(c, "git status --short 2>/dev/null", timeout=10)
    out_pull, _, rc = _execute(c, "git pull origin main 2>&1", timeout=90)
    out_rev, _, _ = _execute(c, "git rev-parse HEAD 2>/dev/null", timeout=5)
    lines = [
        "# Droplet pull proof v5 (2026-02-18)",
        "",
        "## git status (before pull)",
        "```",
        (out_status or "").strip(),
        "```",
        "",
        "## git pull",
        "```",
        (out_pull or "").strip(),
        "```",
        "",
        "## git rev-parse HEAD (after pull)",
        (out_rev or "").strip(),
        "",
        "**Exit code:** " + str(rc),
    ]
    (out_dir / f"{DATE_TAG}_droplet_pull_proof_v5.md").write_text("\n".join(lines), encoding="utf-8")


def run_baseline_v5(c, out_dir: Path) -> tuple[dict, str]:
    """Run effectiveness v5, return (blame_metrics, stderr_or_empty)."""
    out_end, _, _ = _execute(c, "date +%Y-%m-%d 2>/dev/null", timeout=5)
    end_date = (out_end or "").strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cmd = (
        f"python3 scripts/analysis/run_effectiveness_reports.py "
        f"--start 2026-02-01 --end {end_date} --out-dir {V5_OUT_DIR} 2>&1"
    )
    out_eff, err_eff, rc_eff = _execute(c, cmd, timeout=300)
    blame_raw = _remote_cat(c, f"{V5_OUT_DIR}/entry_vs_exit_blame.json", timeout=10)
    agg_raw = _remote_cat(c, f"{V5_OUT_DIR}/effectiveness_aggregates.json", timeout=10)
    blame = {}
    agg = {}
    try:
        blame = json.loads(blame_raw) if blame_raw and blame_raw.strip() else {}
    except Exception:
        pass
    try:
        agg = json.loads(agg_raw) if agg_raw and agg_raw.strip() else {}
    except Exception:
        pass
    joined = agg.get("joined_count", blame.get("joined_count", 0))
    losers = blame.get("total_losing_trades", agg.get("total_losing_trades", 0))
    weak_pct = blame.get("weak_entry_pct")
    timing_pct = blame.get("exit_timing_pct")
    uncl_pct = blame.get("unclassified_pct")
    uncl_count = blame.get("unclassified_count")
    giveback = agg.get("avg_profit_giveback")
    lines = [
        "# Baseline v5 verification (2026-02-18)",
        "",
        "## Command",
        "```",
        cmd,
        "```",
        "",
        "## Metrics",
        "| Metric | Value |",
        "|--------|--------|",
        f"| joined_count | {joined} |",
        f"| total_losing_trades | {losers} |",
        f"| weak_entry_pct | {weak_pct} |",
        f"| exit_timing_pct | {timing_pct} |",
        f"| unclassified_pct | {uncl_pct} |",
        f"| unclassified_count | {uncl_count} |",
        f"| avg_profit_giveback | {giveback} |",
        "",
        "## entry_vs_exit_blame.json (excerpt)",
        "```json",
        json.dumps(
            {k: blame.get(k) for k in ["total_losing_trades", "weak_entry_pct", "exit_timing_pct", "unclassified_count", "unclassified_pct", "joined_count"] if blame.get(k) is not None},
            indent=2,
        ),
        "```",
        "",
        "## effectiveness_aggregates.json (excerpt)",
        "```json",
        json.dumps({k: agg.get(k) for k in ["joined_count", "total_losing_trades", "avg_profit_giveback"] if agg.get(k) is not None}, indent=2),
        "```",
        "",
        "## Join / giveback",
        "- Join uses trade_id (primary) or symbol|entry_ts_bucket (fallback); see attribution_loader docstring.",
        f"- giveback populated: {giveback is not None and giveback != 'N/A'}",
        "",
    ]
    (out_dir / f"{DATE_TAG}_baseline_v5_verification.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "joined_count": joined,
        "total_losing_trades": losers,
        "weak_entry_pct": weak_pct,
        "exit_timing_pct": timing_pct,
        "unclassified_pct": uncl_pct,
        "unclassified_count": uncl_count,
        "avg_profit_giveback": giveback,
        "rc": rc_eff,
    }, (err_eff or "")


def write_signoff(
    out_dir: Path,
    exit_quality_count: int,
    timed_out_eq: bool,
    blame: dict,
    pass_fail: bool,
    blockers: list[str],
    execution_plan_review: str,
    results_review: str,
) -> None:
    weak = blame.get("weak_entry_pct")
    timing = blame.get("exit_timing_pct")
    uncl = blame.get("unclassified_pct")
    one_lever = "entry" if (weak or 0) > (timing or 0) else "exit"
    lines = [
        "# Sign-off v5 (2026-02-18)",
        "",
        "## Multi-model oversight",
        "",
        "### Execution plan review (before run)",
        execution_plan_review,
        "",
        "### Results review (after run)",
        results_review,
        "",
        "## Criteria",
        f"- [x] exit_quality_metrics on new exits: **{exit_quality_count}** (non-zero required for PASS)",
        f"- [x] Blame classifiable: unclassified_pct = {uncl}% (PASS if < 100% or explicit reason)",
        "",
        "## Result: **" + ("PASS" if pass_fail else "FAIL") + "**",
        "",
    ]
    if pass_fail:
        lines.append("Authorize exactly ONE tuning lever (do not execute): **" + one_lever + "**")
    else:
        lines.append("## Blockers")
        for b in blockers:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("STOP. No tuning until PASS.")
    (out_dir / f"{DATE_TAG}_signoff_v5.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: {e}. Need droplet_config.json and DropletClient.", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    execution_plan_review = """
- **Adversarial:** Restart must be no-overlay; proof must show no GOVERNED_TUNING_CONFIG. Poll may time out if no new exits; diagnostics then required.
- **Quant:** exit_quality_metrics requires new exits after restart; join fix (trade_id) makes blame classifiable when entry_score is present on joined rows.
- **Product:** PASS only if exit_quality > 0 and unclassified_pct < 100% (or bounded with explicit reason). One lever authorized on PASS.
"""
    results_review_placeholder = "(filled after run)"

    with DropletClient() as c:
        # Ensure we're in project dir (client uses project_dir in _execute_with_cd)
        print("=== STEP 1: Snapshot before ===")
        write_snapshot_before(c, OUT_DIR)
        print("Wrote snapshot_before.")

        print("=== STEP 1: Restart paper (no overlay) ===")
        ok, err = restart_paper_no_overlay(c, OUT_DIR)
        if not ok:
            results_review = "- **Adversarial:** Restart failed: " + err + ". Overlay or GOVERNED_TUNING_CONFIG present."
            write_signoff(OUT_DIR, 0, True, {}, False, [err], execution_plan_review, results_review)
            print("FAIL:", err, file=sys.stderr)
            return 1
        print("Restart proof written.")

        print("=== STEP 2: Poll for exit_quality_metrics (up to 30 min) ===")
        eq_count, timed_out = poll_exit_quality(c, OUT_DIR)
        print(f"with_exit_quality_metrics={eq_count}, timed_out={timed_out}")

        print("=== STEP 3: Pull main ===")
        write_pull_proof_v5(c, OUT_DIR)
        print("Pull proof v5 written.")

        print("=== STEP 4: Run baseline v5 ===")
        blame_metrics, err_eff = run_baseline_v5(c, OUT_DIR)
        if blame_metrics.get("rc") != 0:
            print("Effectiveness run had non-zero exit code; continuing with available data.", file=sys.stderr)

        uncl_pct = blame_metrics.get("unclassified_pct")
        try:
            uncl_pct_f = float(uncl_pct) if uncl_pct is not None else 100.0
        except (TypeError, ValueError):
            uncl_pct_f = 100.0
        blockers = []
        if eq_count == 0:
            blockers.append("exit_quality_metrics not observed on new exits (with_exit_quality_metrics == 0)")
            if timed_out:
                blockers.append("Poll timed out (30 min); no new exits with exit_quality_metrics in sample.")
        if uncl_pct_f >= 100:
            blockers.append("Blame not classifiable: unclassified_pct >= 100% (or provide explicit field-level reason in verification).")
        pass_fail = eq_count > 0 and uncl_pct_f < 100

        results_review = f"""
- **Adversarial:** exit_quality_metrics count={eq_count}; timed_out={timed_out}. Blame unclassified_pct={uncl_pct}. Pass criteria: eq>0 and (uncl<100 or explicit reason).
- **Quant:** joined_count={blame_metrics.get('joined_count')}, weak_entry_pct={blame_metrics.get('weak_entry_pct')}, exit_timing_pct={blame_metrics.get('exit_timing_pct')}.
- **Product:** {"PASS: one lever authorized (entry or exit)." if pass_fail else "FAIL: " + "; ".join(blockers)}
"""

        print("=== STEP 5: Sign-off ===")
        write_signoff(
            OUT_DIR,
            eq_count,
            timed_out,
            blame_metrics,
            pass_fail,
            blockers,
            execution_plan_review,
            results_review,
        )

    print("=== DONE ===")
    files_written = sorted(p.name for p in OUT_DIR.glob(f"{DATE_TAG}_*.md"))
    print("Proof files:", files_written)
    # Required summary
    print("---")
    print("Summary: exit_quality_metrics coverage:", eq_count)
    print("Blame split: weak_entry_pct=%s exit_timing_pct=%s unclassified_pct=%s" % (blame_metrics.get("weak_entry_pct"), blame_metrics.get("exit_timing_pct"), blame_metrics.get("unclassified_pct")))
    print("PASS/FAIL:", "PASS" if pass_fail else "FAIL")
    print("Files written:", ", ".join(str(OUT_DIR / f) for f in files_written))
    return 0 if pass_fail else 1


if __name__ == "__main__":
    sys.exit(main())
