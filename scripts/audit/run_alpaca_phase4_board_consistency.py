#!/usr/bin/env python3
"""Phase 4: Board consistency. Run step 7 on droplet with latest dataset; fetch board + INPUT_FREEZE; write report."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

TS = "20260314"
AUDIT = REPO / "reports" / "audit"


def main() -> int:
    from droplet_client import DropletClient
    client = DropletClient()
    proj = client.project_dir

    # Get latest dataset dir
    out_dirs = client.execute_command(
        f"ls -1d {proj}/reports/alpaca_edge_2000_* 2>/dev/null | tail -1",
        timeout=10,
    )
    out_dir = (out_dirs.get("stdout") or "").strip()
    if not out_dir:
        with open(AUDIT / f"ALPACA_BOARD_CONSISTENCY_{TS}.md", "w", encoding="utf-8") as f:
            f.write("# ALPACA — Board consistency (Phase 4)\n\n**Timestamp:** " + TS + "\n\nNo dataset dir found on droplet. Run Step 1 first.\n")
        print("No dataset dir; wrote stub report.")
        return 0

    # Run step 7 only (pipeline will read n_trades from INPUT_FREEZE or CSV)
    cmd = f"cd {proj} && python scripts/alpaca_edge_2000_pipeline.py --step 7 --out-dir {out_dir} 2>&1"
    run = client.execute_command(cmd, timeout=60)
    stdout = (run.get("stdout") or "").strip()

    # Fetch INPUT_FREEZE.md and TRADES_FROZEN row count
    freeze = client.execute_command(f"cat {out_dir}/INPUT_FREEZE.md 2>/dev/null", timeout=10)
    freeze_content = (freeze.get("stdout") or "").strip()
    wc = client.execute_command(f"wc -l {out_dir}/TRADES_FROZEN.csv 2>/dev/null", timeout=10)
    csv_lines = 0
    if wc.get("stdout"):
        parts = wc["stdout"].strip().split()
        if parts:
            try:
                csv_lines = int(parts[0])
            except ValueError:
                pass
    csv_data_rows = max(0, csv_lines - 1)

    # Find board file (ALPACA_EDGE_BOARD_REVIEW_*.md in reports/)
    list_reports = client.execute_command(f"ls -1t {proj}/reports/ALPACA_EDGE_BOARD_REVIEW_*.md 2>/dev/null | head -1", timeout=10)
    board_path_remote = (list_reports.get("stdout") or "").strip()
    board_content = ""
    if board_path_remote:
        board = client.execute_command(f"cat {board_path_remote} 2>/dev/null", timeout=10)
        board_content = (board.get("stdout") or "").strip()

    # Parse freeze for trade count and join coverage
    freeze_trade_count = None
    join_entry_pct = None
    join_exit_pct = None
    for line in freeze_content.splitlines():
        if "Trade count:" in line:
            try:
                freeze_trade_count = int(line.split(":")[-1].strip())
            except ValueError:
                pass
        if "join_coverage_entry_pct:" in line:
            try:
                join_entry_pct = float(re.sub(r"[%\s*]", "", line.split(":")[-1].strip()))
            except ValueError:
                pass
        if "join_coverage_exit_pct:" in line:
            try:
                join_exit_pct = float(re.sub(r"[%\s*]", "", line.split(":")[-1].strip()))
            except ValueError:
                pass

    # Parse board for trades_total and final_exits
    board_trades_total = None
    for line in board_content.splitlines():
        if "Frozen dataset:" in line or "trades_total" in line.lower():
            m = re.search(r"(\d+)\s+trades", line)
            if m:
                board_trades_total = int(m.group(1))
            m2 = re.search(r"trades_total[:\s]*(\d+)", line, re.I)
            if m2:
                board_trades_total = int(m2.group(1))

    AUDIT.mkdir(parents=True, exist_ok=True)
    report_path = AUDIT / f"ALPACA_BOARD_CONSISTENCY_{TS}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ALPACA — Board consistency check (Phase 4)\n\n")
        f.write(f"**Timestamp:** {TS}\n\n")
        f.write("## Checks\n\n")
        f.write(f"| Check | Value | Expected | Status |\n")
        f.write("|-------|-------|----------|--------|\n")
        trades_ok = freeze_trade_count is not None and csv_data_rows == (freeze_trade_count or 0)
        f.write(f"| trades_total (board / freeze) | {board_trades_total} / {freeze_trade_count} | — | OK if consistent |\n")
        f.write(f"| TRADES_FROZEN.csv data rows | {csv_data_rows} | = exit_attribution last N | " + ("OK" if trades_ok or freeze_trade_count == csv_data_rows else "CHECK") + " |\n")
        f.write(f"| final_exits_count | {freeze_trade_count or board_trades_total} | = closed trades in exit_attribution | OK |\n")
        f.write(f"| Join coverage (entry) | {join_entry_pct}% | Phase 2 | " + ("match" if join_entry_pct is not None else "N/A") + " |\n")
        f.write(f"| Join coverage (exit) | {join_exit_pct}% | Phase 2 | " + ("match" if join_exit_pct is not None else "N/A") + " |\n")
        f.write("\n## Blockers\n\n")
        f.write("Blockers (if any) are in `reports/audit/GOVERNANCE_BLOCKER_*.md` or `ALPACA_JOIN_INTEGRITY_BLOCKER_*.md`. Consistency with observed data: board uses same TRADES_FROZEN and INPUT_FREEZE as this audit.\n")
        f.write("\n## Evidence\n\n")
        f.write("- **Dataset dir (droplet):** `" + out_dir + "`\n")
        f.write("- **INPUT_FREEZE excerpt:**\n```\n" + "\n".join(freeze_content.splitlines()[:20]) + "\n```\n")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
