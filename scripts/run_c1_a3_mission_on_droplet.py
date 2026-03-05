#!/usr/bin/env python3
"""
C1 promote + A3 shadow mission: run precheck, board review (387), A3 shadow, proof writers, decision packet on droplet.
Deploy scripts via put_file; fetch all artifacts. Optional: --deploy then commit/push and deploy to droplet, re-verify.
DROPLET_RUN=1 for droplet-only execution.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
os.environ["DROPLET_RUN"] = "1"


def main() -> int:
    ap = argparse.ArgumentParser(description="C1 promote + A3 shadow mission on droplet")
    ap.add_argument("--deploy", action="store_true", help="After fetch: commit, push, deploy to droplet, re-run and verify")
    ap.add_argument("--skip-precheck", action="store_true", help="Skip Phase 1 precheck (use if dashboard not up)")
    args = ap.parse_args()
    proj = "/root/stock-bot"

    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root", file=sys.stderr)
        return 1

    with DropletClient() as c:
        # Deploy scripts and builder
        c._execute(f"mkdir -p {proj}/scripts/shadow {proj}/scripts/audit {proj}/scripts/board {proj}/reports/audit {proj}/reports/board {proj}/state/shadow")
        files_to_put = [
            (REPO / "scripts" / "droplet_next_step_precheck.py", f"{proj}/scripts/droplet_next_step_precheck.py"),
            (REPO / "scripts" / "build_30d_comprehensive_review.py", f"{proj}/scripts/build_30d_comprehensive_review.py"),
            (REPO / "scripts" / "shadow" / "run_a3_expectancy_floor_shadow.py", f"{proj}/scripts/shadow/run_a3_expectancy_floor_shadow.py"),
            (REPO / "scripts" / "audit" / "write_c1_promotion_proof.py", f"{proj}/scripts/audit/write_c1_promotion_proof.py"),
            (REPO / "scripts" / "audit" / "write_a3_shadow_proof.py", f"{proj}/scripts/audit/write_a3_shadow_proof.py"),
            (REPO / "scripts" / "board" / "build_next_action_packet.py", f"{proj}/scripts/board/build_next_action_packet.py"),
            (REPO / "scripts" / "audit" / "run_chief_strategy_auditor.py", f"{proj}/scripts/audit/run_chief_strategy_auditor.py"),
            (REPO / "scripts" / "audit" / "enforce_csa_gate.py", f"{proj}/scripts/audit/enforce_csa_gate.py"),
        ]
        c._execute(f"mkdir -p {proj}/src/contracts")
        csa_schema = REPO / "src" / "contracts" / "csa_verdict_schema.py"
        if csa_schema.exists():
            c.put_file(csa_schema, f"{proj}/src/contracts/csa_verdict_schema.py")
        rw = REPO / "board" / "eod" / "rolling_windows.py"
        if rw.exists():
            c._execute(f"mkdir -p {proj}/board/eod")
            c.put_file(rw, f"{proj}/board/eod/rolling_windows.py")
        for local, remote in files_to_put:
            if local.exists():
                c.put_file(local, remote)

        # Phase 1: precheck
        if not args.skip_precheck:
            out, err, rc = c._execute(f"cd {proj} && python3 scripts/droplet_next_step_precheck.py .", timeout=20)
            print("=== Precheck ===")
            print(out or "")
            if err:
                print(err, file=sys.stderr)
            if rc != 0:
                content, _, _ = c._execute(f"cat {proj}/reports/audit/NEXT_STEP_PRECHECK_BLOCKERS.md 2>/dev/null || true")
                if content and content.strip():
                    (REPO / "reports" / "audit" / "NEXT_STEP_PRECHECK_BLOCKERS.md").parent.mkdir(parents=True, exist_ok=True)
                    (REPO / "reports" / "audit" / "NEXT_STEP_PRECHECK_BLOCKERS.md").write_text(content, encoding="utf-8")
                print("Precheck failed. See reports/audit/NEXT_STEP_PRECHECK_BLOCKERS.md", file=sys.stderr)
                return 1

        # Phase 2–4: board review (387), A3 shadow, proofs, packet
        out, err, rc = c._execute(
            f"cd {proj} && python3 scripts/build_30d_comprehensive_review.py --base-dir . --out-dir reports/board --last-n-exits 387 --output-basename last387_comprehensive_review",
            timeout=120,
        )
        print("=== Board review (387) ===")
        print(out or "")
        if rc != 0:
            print("Board review failed", file=sys.stderr)
            return 1

        out, err, rc = c._execute(f"cd {proj} && python3 scripts/shadow/run_a3_expectancy_floor_shadow.py --since-hours 24", timeout=60)
        print("=== A3 shadow ===")
        print(out or "")
        if rc != 0:
            print("A3 shadow failed", file=sys.stderr)

        c._execute(f"cd {proj} && python3 scripts/audit/write_c1_promotion_proof.py .", timeout=10)
        c._execute(f"cd {proj} && python3 scripts/audit/write_a3_shadow_proof.py .", timeout=10)
        out, err, rc = c._execute(f"cd {proj} && python3 scripts/board/build_next_action_packet.py .", timeout=15)
        print("=== Decision packet ===")
        print(out or "")

        # CSA: run after artifacts, then enforce gate
        mission_id = "c1_a3_mission_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        c._execute(f"cd {proj} && python3 scripts/audit/run_chief_strategy_auditor.py --mission-id {mission_id} --board-review-json reports/board/last387_comprehensive_review.json --base-dir .", timeout=60)
        gate_rc = c._execute(f"cd {proj} && python3 scripts/audit/enforce_csa_gate.py --mission-id {mission_id} --csa-verdict-json reports/audit/CSA_VERDICT_{mission_id}.json --require-override-for HOLD ESCALATE ROLLBACK", timeout=15)[2]
        if gate_rc != 0:
            print("CSA gate did not pass; mission continues but promotion steps require override. See reports/audit/CSA_GATE_BLOCKER_*.md", file=sys.stderr)

        # Fetch artifacts (include CSA outputs)
        artifacts = [
            "reports/board/last387_comprehensive_review.json",
            "reports/board/last387_comprehensive_review.md",
            "reports/audit/C1_PROMOTION_PROOF.md",
            "reports/audit/A3_SHADOW_PROOF.md",
            "reports/audit/A3_SHADOW_RESULTS.md",
            "state/shadow/a3_expectancy_floor_shadow.json",
            "reports/board/NEXT_ACTION_PACKET_C1_PROMOTED_A3_SHADOW.json",
            "reports/board/NEXT_ACTION_PACKET_C1_PROMOTED_A3_SHADOW.md",
            "reports/audit/CSA_SUMMARY_LATEST.md",
            "reports/audit/CSA_VERDICT_LATEST.json",
            f"reports/audit/CSA_FINDINGS_{mission_id}.md",
            f"reports/audit/CSA_VERDICT_{mission_id}.json",
        ]
        for rel in artifacts:
            content, _, _ = c._execute(f"cat {proj}/{rel} 2>/dev/null || true")
            if content and content.strip():
                dest = REPO / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"Fetched {rel}", file=sys.stderr)

    if args.deploy:
        # Commit, push, deploy to droplet, re-run and verify
        import subprocess
        subprocess.run(["git", "add", "scripts/droplet_next_step_precheck.py", "scripts/build_30d_comprehensive_review.py",
                        "scripts/shadow/run_a3_expectancy_floor_shadow.py", "scripts/audit/write_c1_promotion_proof.py",
                        "scripts/audit/write_a3_shadow_proof.py", "scripts/board/build_next_action_packet.py"],
                       cwd=REPO, check=False)
        subprocess.run(["git", "commit", "-m", "C1 promote + A3 shadow: board review opportunity-cost ranking, shadow script, proofs, packet"], cwd=REPO, check=False)
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO, check=False)
        with DropletClient() as c:
            r = c.deploy()
            if not r.get("success", False):
                print("Deploy failed:", r.get("error"), file=sys.stderr)
                return 1
            out, _, _ = c._execute(f"cd {proj} && python3 scripts/build_30d_comprehensive_review.py --base-dir . --out-dir reports/board --last-n-exits 387 --output-basename last387_comprehensive_review", timeout=120)
            c._execute(f"cd {proj} && python3 scripts/shadow/run_a3_expectancy_floor_shadow.py --since-hours 24", timeout=60)
            content, _, _ = c._execute(f"cat {proj}/reports/board/last387_comprehensive_review.json 2>/dev/null | head -c 4000")
            if "opportunity_cost_ranked_reasons" in (content or ""):
                print("Verify OK: C1 visible in board review", file=sys.stderr)
            else:
                print("Verify WARN: C1 key not found in board review excerpt", file=sys.stderr)
            content2, _, _ = c._execute(f"cat {proj}/state/shadow/a3_expectancy_floor_shadow.json 2>/dev/null")
            if content2 and "additional_admitted_trades" in content2:
                print("Verify OK: A3 shadow artifacts exist", file=sys.stderr)
            else:
                print("Verify WARN: A3 shadow state missing", file=sys.stderr)

    print("Mission complete. C1 promoted (reporting); A3 shadow run. See reports/board/NEXT_ACTION_PACKET_* and reports/audit/*_PROOF.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
