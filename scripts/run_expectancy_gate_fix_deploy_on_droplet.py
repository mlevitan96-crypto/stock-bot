#!/usr/bin/env python3
"""
Expectancy gate fix: deploy (git pull) + restart paper on droplet with NO overlay.
Writes reports/expectancy_gate_fix/restart_proof.md locally.
Requires: droplet_config.json, DropletClient.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "reports" / "expectancy_gate_fix"
DATE_TAG = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _run(c, command: str, timeout: int = 90):
    return c._execute_with_cd(command, timeout=timeout)


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: {e}. Need droplet_config.json and DropletClient.", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        # 1) Git pull
        print("=== Git pull ===")
        out_pull, err_pull, rc_pull = _run(c, "git pull origin main 2>&1", timeout=60)
        out_rev, _, _ = _run(c, "git rev-parse HEAD 2>/dev/null", timeout=5)
        commit_hash = (out_rev or "").strip() or "unknown"

        # 1b) Verify fix is present (composite_exec_score used for score_floor_breach)
        out_grep, _, _ = _run(c, "grep -n 'composite_exec_score' main.py 2>/dev/null | head -8", timeout=5)
        out_floor, _, _ = _run(c, "grep -n 'score_floor_breach = (composite_exec_score' main.py 2>/dev/null", timeout=5)
        fix_present = "composite_exec_score" in (out_grep or "") and "composite_exec_score" in (out_floor or "")

        # 2) Kill tmux, start paper NO overlay; EXPECTANCY_DEBUG=1 for proof window
        print("=== Restart paper (no overlay, EXPECTANCY_DEBUG=1) ===")
        kill_cmd = "tmux kill-session -t stock_bot_paper_run 2>/dev/null || true"
        start_cmd = 'tmux new-session -d -s stock_bot_paper_run "cd $(pwd) && EXPECTANCY_DEBUG=1 LOG_LEVEL=INFO python3 main.py"'
        state_py = (
            "python3 -c \"import json,os,time; d=os.path.join('state','live_paper_run_state.json'); "
            "os.makedirs(os.path.dirname(d),exist_ok=True); "
            "json.dump({'status':'live_paper_run_started','timestamp':int(time.time()),'details':"
            "{'trading_mode':'paper','process':'python3 main.py','session':'stock_bot_paper_run','governed_tuning_config':''}}, "
            "open(d,'w'), indent=2); print('state written')\""
        )
        full_restart = f"{kill_cmd} && {start_cmd} && sleep 3 && {state_py}"
        out_restart, err_restart, rc_restart = _run(c, full_restart, timeout=60)

        # 3) Proof
        out_tmux, _, _ = _run(c, "tmux ls 2>/dev/null || echo 'none'", timeout=5)
        out_pane, _, _ = _run(c, "tmux capture-pane -pt stock_bot_paper_run -S -60 2>/dev/null || echo 'no-pane'", timeout=5)
        out_state, _, _ = _run(c, "cat state/live_paper_run_state.json 2>/dev/null || echo '{}'", timeout=5)

        gov_ok = True
        try:
            state_obj = json.loads((out_state or "").strip()) if (out_state or "").strip() else {}
            gov = (state_obj.get("details") or {}).get("governed_tuning_config") or state_obj.get("governed_tuning_config")
            if gov:
                gov_ok = False
        except Exception:
            pass

        lines = [
            "# Expectancy gate fix — Restart proof",
            "",
            f"**Date:** {DATE_TAG}",
            "",
            "## Git pull",
            f"- Exit code: {rc_pull}",
            f"- HEAD: {commit_hash[:12]}",
            f"- Fix present (composite_exec_score + score_floor_breach): **{fix_present}**",
            "```",
            (out_pull or "")[:2000],
            "```",
            "",
            "## Restart (no overlay, EXPECTANCY_DEBUG=1)",
            f"- Restart exit code: {rc_restart}",
            f"- No GOVERNED_TUNING_CONFIG in state: **{gov_ok}**",
            "",
            "## tmux ls",
            "```",
            (out_tmux or "").strip(),
            "```",
            "",
            "## tmux capture-pane (stock_bot_paper_run)",
            "```",
            (out_pane or "").strip(),
            "```",
            "",
            "## state/live_paper_run_state.json",
            "```",
            (out_state or "").strip(),
            "```",
        ]
        (OUT_DIR / "restart_proof.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {OUT_DIR / 'restart_proof.md'}")

    return 0 if (rc_pull == 0 and rc_restart == 0 and gov_ok and fix_present) else 1


if __name__ == "__main__":
    sys.exit(main())
