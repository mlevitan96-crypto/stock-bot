#!/usr/bin/env python3
"""
Post-REVERT: (1) Restart paper without overlay on droplet, (2) verify state, (3) run baseline effectiveness v2.
Output: state verification + baseline v2 dir. Caller appends verification to paper run doc and writes memos.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE_TAG = datetime.now(timezone.utc).strftime("%Y%m%d")


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    with DropletClient() as c:
        # Step 1 — Restart paper WITHOUT overlay
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cmd_restart = f"python3 board/eod/start_live_paper_run.py --date {today}"
        out_r, err_r, rc_r = c._execute_with_cd(cmd_restart, timeout=120)
        print("Restart (no overlay):", "OK" if rc_r == 0 else "FAIL", rc_r)
        print(out_r[-1500:] if len(out_r) > 1500 else out_r)

        # Verify state: no overlay (governed_tuning_config absent or empty)
        out_cat, _, _ = c._execute_with_cd("cat state/live_paper_run_state.json 2>/dev/null || true", timeout=10)
        state_json = out_cat or ""
        try:
            state_obj = json.loads(state_json)
            overlay_val = (state_obj.get("details") or {}).get("governed_tuning_config") or ""
            state_has_overlay = bool(overlay_val.strip())
        except Exception:
            state_has_overlay = "governed_tuning_config" in state_json and "overlay" in state_json.lower()
        print("State has overlay path:", state_has_overlay, "(expect False after REVERT)")

        # Verify tmux session running expected command
        out_tmux, _, _ = c._execute_with_cd("tmux list-sessions 2>/dev/null; tmux list-windows -t stock_bot_paper_run 2>/dev/null || true", timeout=10)
        tmux_ok = "stock_bot_paper_run" in (out_tmux or "")
        print("Tmux stock_bot_paper_run present:", tmux_ok)

        # Step 2 — Run baseline v2 effectiveness
        out_end, _, _ = c._execute_with_cd("date +%Y-%m-%d 2>/dev/null || true", timeout=5)
        end_date = (out_end or "").strip() or today
        cmd_eff = (
            f"python3 scripts/analysis/run_effectiveness_reports.py "
            f"--start 2026-02-01 --end {end_date} --out-dir reports/effectiveness_baseline_blame_v2"
        )
        out_eff, err_eff, rc_eff = c._execute_with_cd(cmd_eff, timeout=300)
        print("Baseline v2 effectiveness:", "OK" if rc_eff == 0 else "FAIL", rc_eff)
        print(out_eff[-1000:] if len(out_eff) > 1000 else out_eff)

        # Fetch aggregates and blame for memo
        agg_raw = ""
        blame_raw = ""
        summary_raw = ""
        for path in [
            "reports/effectiveness_baseline_blame_v2/effectiveness_aggregates.json",
            "reports/effectiveness_baseline_blame_v2/entry_vs_exit_blame.json",
            "reports/effectiveness_baseline_blame_v2/EFFECTIVENESS_SUMMARY.md",
        ]:
            o, _, _ = c._execute_with_cd(f"cat {path} 2>/dev/null || true", timeout=15)
            if "effectiveness_aggregates" in path:
                agg_raw = o or ""
            elif "entry_vs_exit_blame" in path:
                blame_raw = o or ""
            else:
                summary_raw = o or ""

    # Parse and return for memo writing
    result = {
        "restart_rc": rc_r,
        "state_has_overlay": state_has_overlay,
        "tmux_ok": tmux_ok,
        "baseline_v2_rc": rc_eff,
        "aggregates": {},
        "blame": {},
        "summary_snippet": summary_raw[:800] if summary_raw else "",
    }
    try:
        result["aggregates"] = json.loads(agg_raw) if agg_raw.strip() else {}
    except Exception:
        pass
    try:
        result["blame"] = json.loads(blame_raw) if blame_raw.strip() else {}
    except Exception:
        pass
    # Write to a temp file for caller to read, or just print JSON
    out_path = REPO / "reports" / "phase9_accel_decisions" / f"_post_revert_result_{DATE_TAG}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Result written to", out_path)
    return 0 if rc_r == 0 and rc_eff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
