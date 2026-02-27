#!/usr/bin/env python3
"""
Run CURSOR_EXIT_PROMOTION_REVIEW_ALL_PERSONAS.sh on the droplet, then fetch
BOARD_DECISION.json, CURSOR_FINAL_SUMMARY.txt, and key artifacts to local.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    script_name = "CURSOR_EXIT_PROMOTION_REVIEW_ALL_PERSONAS.sh"
    local_script = REPO / "scripts" / script_name
    if not local_script.exists():
        print(f"ERROR: {local_script} not found", file=sys.stderr)
        return 1

    with DropletClient() as c:
        proj = c.project_dir.rstrip("/")
        remote_script = f"{proj}/scripts/{script_name}"

        # Ensure remote dirs and pull latest (script creates stub contract/checklist if missing)
        c._execute(
            f"cd {proj} && git fetch origin && git pull origin main 2>/dev/null || true && "
            f"mkdir -p scripts reports/exit_review scripts/analysis scripts/exit_tuning src/exit logs",
            timeout=60,
        )
        # Upload only the promotion script to avoid connection drops from many SFTP puts
        c.put_file(local_script, remote_script)
        # Strip CRLF so bash on Linux works
        c._execute(f"sed -i 's/\\r$//' {remote_script}", timeout=5)

        # Run the full pipeline (effectiveness v2 x2, tuning, dashboard audit, board synthesis)
        cmd = f"cd {proj} && chmod +x scripts/{script_name} && REPO={proj} bash scripts/{script_name}"
        out, err, rc = c._execute(cmd, timeout=600)
        print(out)
        if err:
            print(err, file=sys.stderr)

        # Parse RUN_DIR from output (e.g. "RUN_DIR: /root/stock-bot/...") or from "START ... exit_promotion_review_<tag>"
        run_dir_match = re.search(r"RUN_DIR:\s*(\S+)", out)
        if run_dir_match:
            run_dir = run_dir_match.group(1).strip()
        else:
            tag_match = re.search(r"START EXIT PROMOTION REVIEW\s+(exit_promotion_review_\S+)", out)
            if tag_match:
                run_dir = f"{proj}/reports/exit_review/promotion_{tag_match.group(1).strip()}"
            else:
                print("RUN_DIR not found in output; cannot fetch artifacts.", file=sys.stderr)
                return rc if rc != 0 else 1

        # Fetch key artifacts
        local_run = REPO / "reports" / "exit_review" / Path(run_dir).name
        local_run.mkdir(parents=True, exist_ok=True)

        for name in [
            "BOARD_DECISION.json",
            "CURSOR_FINAL_SUMMARY.txt",
            "exit_tuning_recommendations.md",
            "exit_tuning_patch.json",
            "dashboard_truth_audit.log",
        ]:
            src = f"{run_dir}/{name}"
            try:
                content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
                if content.strip():
                    (local_run / name).write_text(content, encoding="utf-8")
                    print(f"Fetched {name} -> {local_run / name}", file=sys.stderr)
            except Exception as e:
                print(f"Skip {name}: {e}", file=sys.stderr)

        for sub in ["baseline", "shadow"]:
            for ext in ["json", "md"]:
                name = f"exit_effectiveness_v2.{ext}"
                src = f"{run_dir}/{sub}/{name}"
                try:
                    content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
                    if content.strip():
                        d = local_run / sub
                        d.mkdir(parents=True, exist_ok=True)
                        (d / name).write_text(content, encoding="utf-8")
                        print(f"Fetched {sub}/{name}", file=sys.stderr)
                except Exception:
                    pass

        # Fetch multi-model / persona outputs (prosecutor, defender, SRE, board)
        for name in [
            "prosecutor_output.md",
            "defender_output.md",
            "sre_output.md",
            "board_verdict.md",
            "board_verdict.json",
        ]:
            src = f"{run_dir}/board_review/{name}"
            try:
                content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
                if content.strip():
                    (local_run / "board_review").mkdir(parents=True, exist_ok=True)
                    (local_run / "board_review" / name).write_text(content, encoding="utf-8")
                    print(f"Fetched board_review/{name}", file=sys.stderr)
            except Exception:
                pass

        # Print board summary for user
        summary_file = local_run / "CURSOR_FINAL_SUMMARY.txt"
        if summary_file.exists():
            print("\n" + "=" * 60 + "\nBOARD SUMMARY\n" + "=" * 60)
            print(summary_file.read_text(encoding="utf-8"))
        decision_file = local_run / "BOARD_DECISION.json"
        if decision_file.exists():
            print("\n" + "=" * 60 + "\nBOARD_DECISION.json\n" + "=" * 60)
            print(decision_file.read_text(encoding="utf-8"))

    return rc


if __name__ == "__main__":
    sys.exit(main())
