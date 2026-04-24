#!/usr/bin/env python3
"""Run baseline check, all scenario reviews, and comparative synthesis on droplet. Fetch artifacts."""
from __future__ import annotations
import os
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["DROPLET_RUN"] = "1"

def main() -> int:
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    with DropletClient() as c:
        c._execute(f"mkdir -p {proj}/reports/board/scenarios {proj}/scripts")
        # Deploy scripts
        for name in ["scenario_baseline_check.py", "run_scenario_review.py", "scenario_comparative_synthesis.py"]:
            local = REPO / "scripts" / name
            if local.exists():
                c.put_file(local, f"{proj}/scripts/{name}")
        # Phase 1: baseline check
        out, err, rc = c._execute(f"cd {proj} && python3 scripts/scenario_baseline_check.py .", timeout=15)
        print("=== Phase 1: Baseline ===")
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Baseline check failed.", file=sys.stderr)
            return 1
        # Phase 2-3: run each scenario
        for sid in ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2"]:
            out, err, rc = c._execute(f"cd {proj} && python3 scripts/run_scenario_review.py --base-dir . --scenario-id {sid}", timeout=60)
            print(f"=== Scenario {sid} ===")
            print(out or "")
            if err:
                print(err, file=sys.stderr)
            if rc != 0:
                print(f"Scenario {sid} exited {rc}", file=sys.stderr)
        # Phase 4: comparative synthesis
        out, err, rc = c._execute(f"cd {proj} && python3 scripts/scenario_comparative_synthesis.py .", timeout=30)
        print("=== Synthesis ===")
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            return rc
        # Fetch artifacts
        for name in [
            "SCENARIO_COMPARISON_LAST387.json", "SCENARIO_COMPARISON_LAST387.md",
            "scenarios/A1_review.json", "scenarios/A1_review.md",
            "scenarios/A2_review.json", "scenarios/A2_review.md",
            "scenarios/A3_review.json", "scenarios/A3_review.md",
            "scenarios/B1_review.json", "scenarios/B1_review.md",
            "scenarios/B2_review.json", "scenarios/B2_review.md",
            "scenarios/B3_review.json", "scenarios/B3_review.md",
            "scenarios/C1_review.json", "scenarios/C1_review.md",
            "scenarios/C2_review.json", "scenarios/C2_review.md",
        ]:
            src = f"{proj}/reports/board/{name}"
            content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
            if content and content.strip():
                dest = REPO / "reports" / "board" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"Fetched {name}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
