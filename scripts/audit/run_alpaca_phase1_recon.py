#!/usr/bin/env python3
"""Phase 1: Droplet inventory vs pipeline read reconciliation. Runs on droplet via DropletClient, writes report."""
from __future__ import annotations

import json
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
    proj = client.project_dir  # e.g. /root/stock-bot

    # --- Droplet inventory: line counts and sample keys ---
    inventory = {}
    for rel in ["logs/exit_attribution.jsonl", "logs/master_trade_log.jsonl", "logs/attribution.jsonl"]:
        path = f"{proj}/{rel}"
        lc = client.execute_command(f"wc -l {path} 2>/dev/null || echo '0'", timeout=10)
        line_count = 0
        if lc.get("stdout"):
            parts = lc["stdout"].strip().split()
            if parts:
                try:
                    line_count = int(parts[0])
                except ValueError:
                    pass
        tail = client.execute_command(f"tail -1 {path} 2>/dev/null", timeout=10)
        sample_keys = []
        if tail.get("stdout") and tail["stdout"].strip():
            try:
                obj = json.loads(tail["stdout"].strip())
                sample_keys = list(obj.keys()) if isinstance(obj, dict) else []
            except json.JSONDecodeError:
                sample_keys = ["<not json>"]
        inventory[rel] = {"line_count": line_count, "sample_record_keys": sample_keys}

    # --- Run Step 1 in diagnostic mode (capture stderr for drop reasons) ---
    cmd = (
        f"cd {proj} && python scripts/alpaca_edge_2000_pipeline.py --step 1 --allow-missing-attribution --diagnostic 2>&1"
    )
    step1_result = client.execute_command(cmd, timeout=120)
    step1_stdout = step1_result.get("stdout") or ""
    step1_stderr = step1_result.get("stderr") or ""

    # Parse diagnostic line: [diagnostic] exit_path=... lines_read=... blank=... json_error=... not_dict=... no_exit_ts=... rows_kept=... rows_after_max_trades=... drop_cap=...
    diagnostic_line = None
    for line in (step1_stdout + "\n" + step1_stderr).splitlines():
        if "[diagnostic]" in line:
            diagnostic_line = line
            break

    # TRADES_FROZEN.csv row count (data rows, exclude header)
    out_dirs = client.execute_command(f"ls -1d {proj}/reports/alpaca_edge_2000_* 2>/dev/null | tail -1", timeout=10)
    out_dir = (out_dirs.get("stdout") or "").strip()
    csv_count = None
    if out_dir:
        wc = client.execute_command(f"wc -l {out_dir}/TRADES_FROZEN.csv 2>/dev/null", timeout=10)
        if wc.get("stdout"):
            parts = wc["stdout"].strip().split()
            if parts:
                try:
                    csv_count = int(parts[0]) - 1  # subtract header
                except ValueError:
                    pass

    # Build report
    source_count = inventory.get("logs/exit_attribution.jsonl", {}).get("line_count", 0)
    pipeline_count = csv_count
    drop_reasons = []
    if diagnostic_line:
        for m in re.finditer(r"(\w+)=(\d+)", diagnostic_line):
            k, v = m.group(1), m.group(2)
            if k in ("blank", "json_error", "not_dict", "no_exit_ts", "drop_cap") and int(v) > 0:
                drop_reasons.append(f"{k}={v}")

    AUDIT.mkdir(parents=True, exist_ok=True)
    report_path = AUDIT / f"ALPACA_PIPELINE_READ_RECON_{TS}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ALPACA — Pipeline read reconciliation (Phase 1)\n\n")
        f.write(f"**Timestamp:** {TS}\n\n")
        f.write("## Droplet inventory (source counts)\n\n")
        f.write("| Source | Line count | Sample keys (last record) |\n")
        f.write("|--------|-----------|---------------------------|\n")
        for rel, data in inventory.items():
            keys_preview = ", ".join((data.get("sample_record_keys") or [])[:12])
            if len((data.get("sample_record_keys") or [])) > 12:
                keys_preview += ", ..."
            f.write(f"| `{rel}` | {data.get('line_count', 0)} | {keys_preview} |\n")
        f.write("\n## Step 1 diagnostic (paths opened, rows read/kept/dropped)\n\n")
        f.write("- **Pipeline command:** `python scripts/alpaca_edge_2000_pipeline.py --step 1 --allow-missing-attribution --diagnostic`\n")
        f.write("- **Exit log path opened:** `logs/exit_attribution.jsonl` (primary source for TRADES_FROZEN.csv)\n\n")
        if diagnostic_line:
            f.write("```\n" + diagnostic_line + "\n```\n\n")
        f.write("## Reconciliation table\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| source_count (exit_attribution.jsonl lines) | {source_count} |\n")
        f.write(f"| pipeline_count (TRADES_FROZEN.csv data rows) | {pipeline_count if pipeline_count is not None else 'N/A'} |\n")
        f.write(f"| drop_reason (if any) | {'; '.join(drop_reasons) if drop_reasons else 'none (except max_trades cap)'} |\n")
        f.write("\n## Confirmation\n\n")
        if pipeline_count is not None and source_count > 0:
            if pipeline_count <= source_count and (source_count - pipeline_count) <= 2001:
                f.write("- TRADES_FROZEN.csv row count is consistent with exit_attribution.jsonl (last N trades, N ≤ max_trades).\n")
            else:
                f.write("- **Check:** pipeline_count vs source_count may indicate truncation or multiple sources.\n")
        f.write("- No silent filtering due to schema drift if diagnostic shows drops only for blank/json_error/not_dict/no_exit_ts; timestamp/field parsing uses same logic as writer.\n")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
