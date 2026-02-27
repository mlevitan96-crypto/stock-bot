#!/usr/bin/env python3
"""Fetch truth run reports from droplet and print A/B/C summary. Run locally after run_truth_run_on_droplet.py."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient
    root = "/root/stock-bot"
    files = [
        "reports/research_dataset/final_verdict.md",
        "reports/research_dataset/build_log.md",
        "reports/research_dataset/integrity_audit.md",
        "reports/signal_strength/conditional_expectancy.md",
        "reports/blocked_signal_expectancy/bucket_analysis.md",
        "reports/blocked_signal_expectancy/signal_group_expectancy.md",
        "reports/research_dataset/baseline_results.md",
    ]
    with DropletClient() as c:
        for rel in files:
            out, err, rc = c._execute(f"cat {root}/{rel} 2>/dev/null || echo '(file not found)'", timeout=10)
            text = (out or "").strip()
            if not text or "(file not found)" in text:
                continue
            safe = text.replace("\u2192", "->").encode("ascii", errors="replace").decode("ascii")
            print(f"--- {rel} ---")
            print(safe[:4000] + ("..." if len(safe) > 4000 else ""))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
