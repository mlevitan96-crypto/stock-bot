#!/usr/bin/env python3
"""
Combine a backtest run dir into 3 files: run_overview.md, multi_model_review.md, baseline_data.json.
Preserves all data in sections. Usage: python scripts/combine_backtest_report_to_three_files.py --run-dir reports/backtests/alpaca_backtest_20260221T225347Z
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="e.g. reports/backtests/alpaca_backtest_20260221T225347Z")
    args = ap.parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = REPO / run_dir
    if not run_dir.is_dir():
        print("Run dir not found:", run_dir, file=sys.stderr)
        return 1

    base = run_dir / "baseline"
    multi = run_dir / "multi_model"
    summary_dir = run_dir / "summary"
    gov_dir = REPO / "reports" / "governance" / run_dir.name

    # --- 1. run_overview.md ---
    sections = []
    sections.append("# Run overview\n")
    sections.append("**Run ID:** " + run_dir.name + "\n")
    verdict = (run_dir / "FINAL_VERDICT.txt").read_text(encoding="utf-8").strip() if (run_dir / "FINAL_VERDICT.txt").exists() else ""
    sections.append("## FINAL_VERDICT\n\n```\n" + verdict + "\n```\n")
    sections.append("## Config & provenance\n")
    for name, f in [("provenance.json", run_dir / "provenance.json"), ("config.json", run_dir / "config.json")]:
        if f.exists():
            sections.append("### " + name + "\n\n```json\n" + f.read_text(encoding="utf-8").strip() + "\n```\n")
    sections.append("## Preflight\n\n```\n")
    if (run_dir / "preflight.txt").exists():
        sections.append((run_dir / "preflight.txt").read_text(encoding="utf-8"))
    sections.append("\n```\n")
    sections.append("## Summary\n\n")
    if (summary_dir / "summary.md").exists():
        sections.append((summary_dir / "summary.md").read_text(encoding="utf-8"))
    sections.append("\n## Baseline metrics\n\n```json\n")
    if (base / "metrics.json").exists():
        sections.append((base / "metrics.json").read_text(encoding="utf-8"))
    sections.append("\n```\n\n## Backtest summary\n\n```json\n")
    if (base / "backtest_summary.json").exists():
        sections.append((base / "backtest_summary.json").read_text(encoding="utf-8"))
    sections.append("\n```\n\n## Run diagnostics\n\n```json\n")
    if (base / "run_diagnostics.json").exists():
        sections.append((base / "run_diagnostics.json").read_text(encoding="utf-8"))
    sections.append("\n```\n")
    sections.append("## Governance\n\n```json\n")
    if (gov_dir / "backtest_governance_report.json").exists():
        sections.append((gov_dir / "backtest_governance_report.json").read_text(encoding="utf-8"))
    sections.append("\n```\n")

    (run_dir / "run_overview.md").write_text("".join(sections), encoding="utf-8")
    print("Wrote", run_dir / "run_overview.md")

    # --- 2. multi_model_review.md ---
    mm = []
    mm.append("# Multi-model review\n")
    for title, path in [
        ("Board verdict", multi / "board_verdict.md"),
        ("Board verdict (JSON)", multi / "board_verdict.json"),
        ("Prosecutor", multi / "prosecutor_output.md"),
        ("Defender", multi / "defender_output.md"),
        ("SRE", multi / "sre_output.md"),
    ]:
        if path.exists():
            mm.append("## " + title + "\n\n")
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".json":
                mm.append("```json\n" + text.strip() + "\n```\n")
            else:
                mm.append(text)
            mm.append("\n")
    mm.append("## Evidence manifest\n\n```\n")
    if (multi / "evidence_manifest.txt").exists():
        mm.append((multi / "evidence_manifest.txt").read_text(encoding="utf-8"))
    mm.append("\n```\n\n## Plugins\n\n```\n")
    if (multi / "plugins.txt").exists():
        mm.append((multi / "plugins.txt").read_text(encoding="utf-8"))
    mm.append("\n```\n")
    (run_dir / "multi_model_review.md").write_text("".join(mm), encoding="utf-8")
    print("Wrote", run_dir / "multi_model_review.md")

    # --- 3. baseline_data.json ---
    data = {}
    if (base / "run_diagnostics.json").exists():
        data["run_diagnostics"] = json.loads((base / "run_diagnostics.json").read_text(encoding="utf-8"))
    if (base / "metrics.json").exists():
        data["metrics"] = json.loads((base / "metrics.json").read_text(encoding="utf-8"))
    if (base / "backtest_summary.json").exists():
        data["backtest_summary"] = json.loads((base / "backtest_summary.json").read_text(encoding="utf-8"))
    if (gov_dir / "backtest_governance_report.json").exists():
        data["governance"] = json.loads((gov_dir / "backtest_governance_report.json").read_text(encoding="utf-8"))
    trades = []
    if (base / "trades.csv").exists():
        with (base / "trades.csv").open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                trades.append(row)
    data["trades_count"] = len(trades)
    data["trades"] = trades
    exits = []
    if (base / "backtest_exits.jsonl").exists():
        for line in (base / "backtest_exits.jsonl").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    exits.append(json.loads(line))
                except Exception:
                    pass
    data["exits_count"] = len(exits)
    data["exits"] = exits
    (run_dir / "baseline_data.json").write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print("Wrote", run_dir / "baseline_data.json", "(" + str(len(trades)) + " trades)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
