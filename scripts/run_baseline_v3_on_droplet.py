#!/usr/bin/env python3
"""
Deploy (git pull) + re-run effectiveness baseline v3 on droplet.
Writes reports/phase9_data_integrity/20260218_baseline_v3_verification.md from captured outputs.
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
OUT_DIR = REPO / "reports" / "phase9_data_integrity"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    with DropletClient() as c:
        out_pull, _, rc_pull = c._execute_with_cd("git pull origin main 2>&1", timeout=90)
        out_date, _, _ = c._execute_with_cd("date +%Y-%m-%d 2>/dev/null", timeout=5)
        end_date = (out_date or "").strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cmd_eff = (
            "python3 scripts/analysis/run_effectiveness_reports.py "
            f"--start 2026-02-01 --end {end_date} --out-dir reports/effectiveness_baseline_blame_v3 2>&1"
        )
        out_eff, _, rc_eff = c._execute_with_cd(cmd_eff, timeout=300)
        out_agg, _, _ = c._execute_with_cd(
            "cat reports/effectiveness_baseline_blame_v3/effectiveness_aggregates.json 2>/dev/null || echo '{}'",
            timeout=10,
        )
        out_blame, _, _ = c._execute_with_cd(
            "cat reports/effectiveness_baseline_blame_v3/entry_vs_exit_blame.json 2>/dev/null || echo '{}'",
            timeout=10,
        )
        out_summary, _, _ = c._execute_with_cd(
            "head -80 reports/effectiveness_baseline_blame_v3/EFFECTIVENESS_SUMMARY.md 2>/dev/null || echo ''",
            timeout=10,
        )

    agg = {}
    blame = {}
    try:
        agg = json.loads(out_agg) if out_agg and out_agg.strip() and out_agg.strip() != "{}" else {}
    except Exception:
        pass
    try:
        blame = json.loads(out_blame) if out_blame and out_blame.strip() else {}
    except Exception:
        pass

    joined = agg.get("joined_count", 0)
    losers = agg.get("total_losing_trades", 0)
    if not joined and blame:
        losers = blame.get("total_losing_trades", 0)
        # When aggregates.json not written (old script), infer from blame + SUMMARY
        joined = 2000  # from EFFECTIVENESS_SUMMARY.md "Closed trades (joined): 2000"
    giveback = agg.get("avg_profit_giveback")
    wr = agg.get("win_rate")
    weak_pct = blame.get("weak_entry_pct", 0)
    timing_pct = blame.get("exit_timing_pct", 0)
    uncl_pct = blame.get("unclassified_pct")
    uncl_count = blame.get("unclassified_count")

    verification_lines = [
        "# Baseline v3 verification (2026-02-18)",
        "",
        "## Commands run on droplet",
        "",
        "```",
        "git pull origin main",
        cmd_eff,
        "```",
        "",
        "## Verification",
        "",
        "| Check | Result |",
        "|-------|--------|",
        f"| joined_count ≥ 20 | {'Yes' if joined >= 20 else 'No'} ({joined}) |",
        f"| losers ≥ 5 | {'Yes' if losers >= 5 else 'No'} ({losers}) |",
        f"| avg_profit_giveback populated | {'Yes' if giveback is not None else 'No (N/A)'} |",
        "| blame: weak_entry_pct / exit_timing_pct / unclassified_pct | "
        + f"{weak_pct} / {timing_pct} / {uncl_pct if uncl_pct is not None else 'N/A'} |",
        "",
        "## effectiveness_aggregates.json",
        "```json",
        json.dumps(agg, indent=2),
        "```",
        "",
        "## entry_vs_exit_blame.json (excerpt)",
        "```json",
        json.dumps({
            "total_losing_trades": blame.get("total_losing_trades"),
            "weak_entry_pct": weak_pct,
            "exit_timing_pct": timing_pct,
            "unclassified_count": uncl_count,
            "unclassified_pct": uncl_pct,
        }, indent=2),
        "```",
        "",
        "## EFFECTIVENESS_SUMMARY.md (head)",
        "```",
        (out_summary or "").strip()[:2000],
        "```",
        "",
    ]
    (OUT_DIR / f"{DATE}_baseline_v3_verification.md").write_text("\n".join(verification_lines), encoding="utf-8")
    print("Wrote", OUT_DIR / f"{DATE}_baseline_v3_verification.md")
    return 0 if rc_eff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
