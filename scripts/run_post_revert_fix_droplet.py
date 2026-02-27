#!/usr/bin/env python3
"""
Post-REVERT: Fix paper restart + canonical state on droplet.
Steps 1-6: capture truth, kill tmux, clear state, restart, deploy+baseline v2, upstream plan.
Writes: reports/phase9_accel_decisions/20260218_post_revert_restart_proof.md,
        20260218_baseline_blame_v2_verification.md, 20260218_upstream_logging_fix_plan.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE = "20260218"
DECISIONS = REPO / "reports" / "phase9_accel_decisions"
DECISIONS.mkdir(parents=True, exist_ok=True)


def run(cmd: str, timeout: int = 120):
    from droplet_client import DropletClient
    with DropletClient() as c:
        out, err, rc = c._execute_with_cd(cmd, timeout=timeout)
    return (out or ""), (err or ""), rc


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    proof_lines = [
        "# Post-REVERT restart — proof (2026-02-18)",
        "",
        "## Multi-model review (restart plan)",
        "",
        "| Lens | Note |",
        "|------|------|",
        "| **Adversarial** | Killing tmux is destructive; capture state first. Clearing state file is safe if we then restart; otherwise paper is stopped with no process. |",
        "| **Quant** | Canonical source is state file; tmux command must match (no GOVERNED_TUNING_CONFIG). Re-run effectiveness after deploy to get unclassified_pct. |",
        "| **Product** | Restart without overlay restores baseline behavior; verification docs are the audit trail. |",
        "",
        "---",
        "",
    ]

    with DropletClient() as c:
        # ----- STEP 1: Capture current truth -----
        out_git, _, _ = c._execute_with_cd("git rev-parse HEAD 2>/dev/null; echo '---'; git status 2>/dev/null", timeout=15)
        out_state, _, _ = c._execute_with_cd("cat state/live_paper_run_state.json 2>/dev/null || echo 'FILE_MISSING'", timeout=10)
        out_tmux_ls, _, _ = c._execute_with_cd("tmux ls 2>/dev/null || echo 'NO_SESSIONS'", timeout=10)
        out_tmux_cmd, _, _ = c._execute_with_cd(
            "tmux list-windows -t stock_bot_paper_run -F '#{pane_start_command}' 2>/dev/null || "
            "tmux capture-pane -pt stock_bot_paper_run -S -5 -E 5 2>/dev/null || echo 'NO_PANE'",
            timeout=10,
        )
        out_grep, _, _ = c._execute_with_cd(
            "grep -n governed_tuning state/live_paper_run_state.json 2>/dev/null || true; "
            "grep -n exit_score_weight_tune state/live_paper_run_state.json 2>/dev/null || true",
            timeout=5,
        )

        proof_lines.extend([
            "## Step 1 — Current truth (before changes)",
            "",
            "### git",
            "```",
            (out_git or "").strip(),
            "```",
            "",
            "### state/live_paper_run_state.json",
            "```json",
            (out_state or "N/A").strip(),
            "```",
            "",
            "### tmux ls",
            "```",
            (out_tmux_ls or "").strip(),
            "```",
            "",
            "### tmux command / pane (stock_bot_paper_run)",
            "```",
            (out_tmux_cmd or "").strip(),
            "```",
            "",
            "### GOVERNED_TUNING_CONFIG in state?",
            "```",
            (out_grep or "").strip(),
            "```",
            "",
        ])

        # ----- STEP 2: Hard stop -----
        c._execute_with_cd("tmux kill-session -t stock_bot_paper_run 2>/dev/null || true", timeout=10)
        out_ls2, _, _ = c._execute_with_cd("tmux ls 2>/dev/null || echo 'NO_SESSIONS'", timeout=10)
        proof_lines.extend([
            "## Step 2 — Hard stop",
            "",
            "Killed session `stock_bot_paper_run`. After: `tmux ls`:",
            "```",
            (out_ls2 or "").strip(),
            "```",
            "",
        ])

        # ----- STEP 3: Clear overlay from state -----
        clear_state_py = (
            "python3 -c \""
            "import json, os; "
            "p = 'state/live_paper_run_state.json'; "
            "d = {}; "
            "if os.path.exists(p): "
            "  d = json.load(open(p)); "
            "details = (d.get('details') or {}).copy(); "
            "details['governed_tuning_config'] = ''; "
            "d['details'] = details; "
            "open(p, 'w').write(json.dumps(d, indent=2)); "
            "print('CLEARED')\""
        )
        c._execute_with_cd(clear_state_py, timeout=15)
        out_state2, _, _ = c._execute_with_cd("cat state/live_paper_run_state.json 2>/dev/null", timeout=10)
        proof_lines.extend([
            "## Step 3 — State cleared (no overlay)",
            "",
            "```json",
            (out_state2 or "").strip(),
            "```",
            "",
        ])

        # ----- STEP 4: Restart paper without overlay -----
        # Run the same flow as start_live_paper_run.py with overlay_path=None (no GOVERNED_TUNING_CONFIG)
        out_date, _, _ = c._execute_with_cd("date +%Y-%m-%d 2>/dev/null", timeout=5)
        today = (out_date or "").strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state_py = (
            "python3 -c \"import json,os,time; d=os.path.join('state','live_paper_run_state.json'); "
            "os.makedirs(os.path.dirname(d),exist_ok=True); "
            "details={'trading_mode':'paper','process':'python3 main.py','session':'stock_bot_paper_run','governed_tuning_config':''}; "
            "json.dump({'status':'live_paper_run_started','timestamp':int(time.time()),'details':details}, open(d,'w'), indent=2); "
            "print('live_paper_run_state.json written')\""
        )
        cmd_restart = (
            "echo '1) Git' && git status && git rev-parse --abbrev-ref HEAD && git pull --rebase origin main && "
            "echo '2) EOD sanity' && python3 board/eod/eod_confirmation.py --date " + today + " --allow-missing-missed-money && "
            "echo '3) Kill old tmux' && tmux kill-session -t stock_bot_paper_run 2>/dev/null || true && "
            "echo '4) Start tmux (no overlay)' && tmux new-session -d -s stock_bot_paper_run 'LOG_LEVEL=INFO python3 main.py' && "
            "sleep 5 && echo '5) Verify' && tmux ls && "
            "echo '6) State' && " + state_py + " && echo 'DONE'"
        )
        out_restart, err_restart, rc_restart = c._execute_with_cd(cmd_restart, timeout=300)
        proof_lines.extend([
            "## Step 4 — Restart paper (no overlay)",
            "",
            "Command: git pull, EOD sanity, kill tmux, start tmux with `LOG_LEVEL=INFO python3 main.py` (no GOVERNED_TUNING_CONFIG), write state with governed_tuning_config=''.",
            f"Exit code: {rc_restart}",
            "",
            "### stdout",
            "```",
            (out_restart or "").strip()[-4000:],
            "```",
            "",
        ])
        if err_restart:
            proof_lines.extend(["### stderr", "```", err_restart.strip()[-2000:], "```", ""])

        if rc_restart != 0:
            proof_lines.extend([
                "**Restart failed.** Identify failure (git pull, EOD, tmux, permissions) and fix before re-running.",
                "",
            ])
        else:
            out_state3, _, _ = c._execute_with_cd("cat state/live_paper_run_state.json 2>/dev/null", timeout=10)
            out_tmux3, _, _ = c._execute_with_cd("tmux ls 2>/dev/null", timeout=10)
            out_pane, _, _ = c._execute_with_cd(
                "tmux capture-pane -pt stock_bot_paper_run -S -50 2>/dev/null || echo 'NO_PANE'",
                timeout=10,
            )
            proof_lines.extend([
                "### After successful start: state",
                "```json",
                (out_state3 or "").strip(),
                "```",
                "",
                "### tmux ls",
                "```",
                (out_tmux3 or "").strip(),
                "```",
                "",
                "### tmux pane (last 50 lines) — confirm no GOVERNED_TUNING_CONFIG",
                "```",
                (out_pane or "").strip(),
                "```",
                "",
            ])

        # ----- STEP 5: Deploy + re-run baseline v2 -----
        out_pull, _, rc_pull = c._execute_with_cd("git pull origin main 2>&1", timeout=60)
        proof_lines.extend([
            "## Step 5 — Deploy + baseline v2",
            "",
            "### git pull",
            "```",
            (out_pull or "").strip()[-1500:],
            "```",
            "",
        ])
        out_end, _, _ = c._execute_with_cd("date +%Y-%m-%d 2>/dev/null", timeout=5)
        end_date = (out_end or "").strip() or today
        cmd_eff = (
            f"python3 scripts/analysis/run_effectiveness_reports.py "
            f"--start 2026-02-01 --end {end_date} --out-dir reports/effectiveness_baseline_blame_v2 2>&1"
        )
        out_eff, err_eff, rc_eff = c._execute_with_cd(cmd_eff, timeout=300)
        proof_lines.extend([
            f"Effectiveness exit code: {rc_eff}",
            "```",
            (out_eff or "").strip()[-1500:],
            "```",
            "",
        ])

        # Fetch outputs for verification doc
        out_agg, _, _ = c._execute_with_cd("cat reports/effectiveness_baseline_blame_v2/effectiveness_aggregates.json 2>/dev/null || echo '{}'", timeout=10)
        out_blame, _, _ = c._execute_with_cd("cat reports/effectiveness_baseline_blame_v2/entry_vs_exit_blame.json 2>/dev/null || echo '{}'", timeout=10)

    # Write proof
    (DECISIONS / f"{DATE}_post_revert_restart_proof.md").write_text("\n".join(proof_lines), encoding="utf-8")

    # Write verification (Step 5)
    agg = {}
    blame = {}
    try:
        agg = json.loads(out_agg) if out_agg and out_agg.strip() and out_agg.strip() != "{}" else {}
    except Exception:
        pass
    try:
        blame = json.loads(out_blame) if out_blame and out_blame.strip() and out_blame.strip() != "{}" else {}
    except Exception:
        pass
    verification_lines = [
        "# Baseline v2 verification (2026-02-18)",
        "",
        "## Outputs after deploy + re-run",
        "",
        "- **effectiveness_aggregates.json** present: " + ("Yes" if agg else "No"),
        "- **entry_vs_exit_blame.json** includes **unclassified_count** / **unclassified_pct**: " +
        ("Yes" if blame.get("unclassified_count") is not None or blame.get("unclassified_pct") is not None else "No (deploy may not have unclassified yet)"),
        "",
        "### effectiveness_aggregates.json (excerpt)",
        "```json",
        json.dumps(agg, indent=2)[:1200],
        "```",
        "",
        "### entry_vs_exit_blame.json (excerpt)",
        "```json",
        json.dumps({k: blame[k] for k in ["total_losing_trades", "weak_entry_pct", "exit_timing_pct", "unclassified_count", "unclassified_pct"] if k in blame}, indent=2),
        "```",
        "",
    ]
    (DECISIONS / f"{DATE}_baseline_blame_v2_verification.md").write_text("\n".join(verification_lines), encoding="utf-8")

    # ----- STEP 6: Upstream fix plan (no code changes) -----
    upstream_plan = REPO / "reports" / "phase9_accel_decisions" / f"{DATE}_upstream_logging_fix_plan.md"
    upstream_plan.write_text(
        """# Upstream logging fix plan — giveback + classifiable blame (2026-02-18)

## Problem

- **Giveback N/A:** Logs often lack `exit_quality_metrics` (or MFE/high_water), so `profit_giveback` is null.
- **Blame 100% unclassified:** Blame classifier needs `entry_score`, `exit_quality_metrics.profit_giveback` (or MFE), and optionally MFE on joined rows. Many joined rows lack these (entry attribution or exit attribution).

## 1. Who should emit exit_quality_metrics (MFE/MAE/giveback inputs)

- **Log writer:** Exit attribution is written in `main.py` inside `log_exit_attribution()` (around 2145–2226). It calls `compute_exit_quality_metrics()` from `src/exit/exit_quality_metrics.py` and passes the result to `build_exit_attribution_record(..., exit_quality_metrics=...)`, which is appended via `append_exit_attribution(rec)` to **logs/exit_attribution.jsonl**.
- **Inputs for giveback:** `compute_exit_quality_metrics()` needs `high_water_price` (or bars for MFE/MAE). In `main.py`, `high_water = (info.get("high_water") or entry_price)`. So **info** passed to `log_exit_attribution(symbol, info, ...)` must include **high_water** when the position was tracked (e.g. from `self.high_water[symbol]` or equivalent). If `info["high_water"]` is missing, the code falls back to `entry_price`, so MFE becomes 0 and giveback is not computed.

**Files to change:**

- **main.py** (call sites of `log_exit_attribution`): Before calling `log_exit_attribution(symbol, info, ...)`, ensure `info` includes `high_water` when available. For example: if the executor holds `self.high_water` (or equivalent), set `info["high_water"] = self.high_water.get(symbol, info.get("high_water", entry_price))` (or the executed exit price as fallback) so that `compute_exit_quality_metrics` receives a non-trivial high_water when the position had upside. Exact location: wherever `info` is built/updated before the two call sites (~5545 displacement exit, ~7227 time/trail exit).

**Fields already written:** `exit_quality_metrics` is written by `build_exit_attribution_record` when `exit_quality_metrics` is not None; it includes `mfe`, `mae`, `time_in_trade_sec`, `profit_giveback`, `exit_efficiency`. So the only missing piece is ensuring **high_water** (or bars) is available so that `compute_exit_quality_metrics` can set MFE and thus profit_giveback.

## 2. Fields blame classifier requires

- **build_entry_vs_exit_blame** (in `scripts/analysis/run_effectiveness_reports.py`) uses joined rows (attribution + exit_attribution join). It needs:
  - **entry_score** (from entry attribution or joined row): for weak_entry (score &lt; 3).
  - **exit_quality_metrics.profit_giveback** and **exit_quality_metrics.mfe**: for exit_timing (giveback ≥ 0.3 or MFE &gt; 0 with loss).
- **Entry attribution** (logs/attribution.jsonl): Must expose **entry_score** (or equivalent) on the record that joins to exit_attribution so that the loader puts it on the joined row. If entry_score is computed at entry but not stored in attribution.jsonl, add it to the attribution record written at entry (or to the exit record if that’s where the join key lives).

**Files to check/change:**

- **Attribution writer (entry):** Identify where logs/attribution.jsonl is appended (entry fill or decision). Ensure the written record includes **entry_score** (or the field name the join/loader uses) so that `load_joined_closed_trades` produces rows with `entry_score`. If the loader expects a specific key (e.g. `entry_score`), add that key to the attribution record.
- **Exit side:** Already covered above (exit_quality_metrics via high_water).

## 3. Smallest upstream change summary

| File(s) | Change |
|--------|--------|
| main.py | Before each `log_exit_attribution(..., info=info, ...)`, set `info["high_water"] = self.high_water.get(symbol, info.get("high_water") or entry_price)` (or equivalent) so high_water is present when the executor tracked it. |
| Entry attribution writer | Ensure the attribution record written at entry (or the record that joins to exit) includes **entry_score** so joined rows have it. |

## 4. How to verify after change

1. **Giveback:** After deploying and running paper (or backtest) for some trades: `grep -o '"exit_quality_metrics":[^}]*' logs/exit_attribution.jsonl | head -20` — should see `profit_giveback` non-null when MFE was positive. Run effectiveness; **effectiveness_aggregates.json** or SUMMARY should show **avg_profit_giveback** non-null when data exists.
2. **Blame:** Re-run effectiveness; **entry_vs_exit_blame.json** should have **unclassified_pct** &lt; 100 (and weak_entry_pct / exit_timing_pct non-zero when data allows), and joined rows should have entry_score and exit_quality_metrics where we added the fields.
""",
        encoding="utf-8",
    )

    print("Wrote:", DECISIONS / f"{DATE}_post_revert_restart_proof.md")
    print("Wrote:", DECISIONS / f"{DATE}_baseline_blame_v2_verification.md")
    print("Wrote:", upstream_plan)
    return 0 if rc_restart == 0 and rc_eff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
