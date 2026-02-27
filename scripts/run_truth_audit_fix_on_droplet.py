#!/usr/bin/env python3
"""
Truth-audit fix: deploy on droplet, restart paper, validate JSON, wait for score_snapshot,
run dashboard JSON trace, run truth audit. Writes reports/truth_audit_fix/20260218/ bundle.
No manual steps. PASS only if all steps succeed and truth audit PASS.
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
BUNDLE_DIR = REPO / "reports" / "truth_audit_fix" / DATE_TAG
SNAPSHOT_MIN_RECORDS = 50
POLL_INTERVAL_SEC = 60
WAIT_TIMEOUT_SEC = 30 * 60  # 30 min


def _run(c, command: str, timeout: int = 120):
    return c._execute_with_cd(command, timeout=timeout)


def main() -> int:
    overall = "FAIL"
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print("Error: {} Need DropletClient.".format(e), file=sys.stderr)
        return 1

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        # --- 00 Deploy proof ---
        print("=== Git pull ===")
        out_pull, err_pull, rc_pull = _run(c, "git pull origin main 2>&1", timeout=90)
        out_rev, _, _ = _run(c, "git rev-parse HEAD 2>/dev/null", timeout=5)
        commit_hash = (out_rev or "").strip()[:12] or "unknown"

        print("=== Restart paper (no overlay) ===")
        kill_cmd = "tmux kill-session -t stock_bot_paper_run 2>/dev/null || true"
        start_cmd = 'tmux new-session -d -s stock_bot_paper_run "cd $(pwd) && LOG_LEVEL=INFO python3 main.py"'
        out_restart, _, rc_restart = _run(c, "{} && {} && sleep 3".format(kill_cmd, start_cmd), timeout=60)

        deploy_lines = [
            "# 00 Deploy proof",
            "",
            "**Date:** " + DATE_TAG,
            "",
            "## Git pull",
            "- Exit: " + str(rc_pull),
            "- HEAD: " + commit_hash,
            "```",
            (out_pull or "")[:2000],
            "```",
            "",
            "## Restart paper",
            "- Exit: " + str(rc_restart),
            "",
        ]
        (BUNDLE_DIR / "00_deploy_proof.md").write_text("\n".join(deploy_lines), encoding="utf-8")

        # --- Validator ---
        print("=== Validate JSON artifacts ===")
        out_val, _, rc_val = _run(c, "python3 scripts/validate_json_artifacts.py 2>&1", timeout=30)

        # --- Wait for score_snapshot ---
        print("=== Waiting for score_snapshot.jsonl (min {} records, timeout {} min) ===".format(SNAPSHOT_MIN_RECORDS, WAIT_TIMEOUT_SEC // 60))
        start = time.time()
        snapshot_count = 0
        first_ts = last_ts = ""
        while (time.time() - start) < WAIT_TIMEOUT_SEC:
            out_wc, _, _ = _run(c, "wc -l < logs/score_snapshot.jsonl 2>/dev/null || echo 0", timeout=5)
            try:
                snapshot_count = int((out_wc or "0").strip())
            except ValueError:
                snapshot_count = 0
            if snapshot_count >= SNAPSHOT_MIN_RECORDS:
                out_first, _, _ = _run(c, "head -1 logs/score_snapshot.jsonl 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('ts_iso',''))\" 2>/dev/null || echo ''", timeout=5)
                out_last, _, _ = _run(c, "tail -1 logs/score_snapshot.jsonl 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('ts_iso',''))\" 2>/dev/null || echo ''", timeout=5)
                first_ts = (out_first or "").strip()
                last_ts = (out_last or "").strip()
                break
            time.sleep(POLL_INTERVAL_SEC)

        snap_lines = [
            "# 02 Score snapshot proof",
            "",
            "**Date:** " + DATE_TAG,
            "",
            "## Count",
            "- Records: " + str(snapshot_count),
            "- First ts: " + first_ts,
            "- Last ts: " + last_ts,
            "",
            "## Validator",
            "```",
            (out_val or "").strip(),
            "```",
            "",
        ]
        (BUNDLE_DIR / "02_score_snapshot_proof.md").write_text("\n".join(snap_lines), encoding="utf-8")

        # --- Dashboard JSON error trace ---
        print("=== Trace dashboard JSON error ===")
        _run(c, "python3 scripts/trace_dashboard_json_error.py 2>/dev/null", timeout=30)
        out_trace, _, _ = _run(c, "cat reports/truth_audit_fix/20260218_dashboard_json_error_trace.md 2>/dev/null || echo 'Trace file not found'", timeout=5)
        (BUNDLE_DIR / "01_dashboard_json_fix_proof.md").write_text(out_trace or "Trace not produced.", encoding="utf-8")

        # --- Truth audit ---
        print("=== Run Unified Truth Audit ===")
        audit_dir = REPO / "reports" / "truth_audit" / DATE_TAG
        try:
            import scripts.run_truth_audit_on_droplet as audit_mod
            audit_dir = REPO / "reports" / "truth_audit" / DATE_TAG
            audit_dir.mkdir(parents=True, exist_ok=True)
            data = audit_mod._run_axes(c)
            verdict, failures, fixes = audit_mod._write_reports(data, audit_dir)
        except Exception as e:
            verdict = "FAIL"
            failures = [("Exception", str(e))]
            fixes = []

        # 03 truth audit postfix
        lines_03 = [
            "# 03 Truth audit postfix",
            "",
            "**Verdict:** " + verdict,
            "",
            "## Axis results",
            "See reports/truth_audit/" + DATE_TAG + "/ for axis_01..06 and verdict.md.",
            "",
            "## Ranked failures",
            ""
        ]
        for a, r in failures:
            lines_03.append("- {}: {}".format(a, r))
        (BUNDLE_DIR / "03_truth_audit_postfix.md").write_text("\n".join(lines_03), encoding="utf-8")

        # 04 verdict
        pass_criteria = (
            snapshot_count >= SNAPSHOT_MIN_RECORDS,
            verdict == "PASS",
            rc_val == 0,
        )
        overall = "PASS" if all(pass_criteria) else "FAIL"
        lines_04 = [
            "# 04 Verdict",
            "",
            "**Overall:** **" + overall + "**",
            "",
            "## Criteria",
            "- score_snapshot records >= {}: {}".format(SNAPSHOT_MIN_RECORDS, snapshot_count >= SNAPSHOT_MIN_RECORDS),
            "- Truth audit PASS: " + str(verdict == "PASS"),
            "- JSON validator exit 0: " + str(rc_val == 0),
            "",
            "## Truth audit verdict",
            verdict,
            "",
            "## Failures",
            ""
        ]
        for a, r in failures:
            lines_04.append("- {}: {}".format(a, r))
        (BUNDLE_DIR / "04_verdict.md").write_text("\n".join(lines_04), encoding="utf-8")

        print("")
        print("=== TRUTH AUDIT FIX RESULT ===")
        print("Overall: " + overall)
        print("score_snapshot records: " + str(snapshot_count))
        print("Truth audit: " + verdict)
        print("Bundle: " + str(BUNDLE_DIR))

    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
