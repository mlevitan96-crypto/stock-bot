#!/usr/bin/env python3
"""
One-shot live red-team review on the host (intended for Alpaca droplet).

Runs ``off_leash_alpaca_hunt`` and writes:
  - reports/off_leash_hunt_findings.json
  - reports/RED_TEAM_REPORT.md

Usage:
  cd /root/stock-bot && PYTHONPATH=/root/stock-bot python3 scripts/audit/full_live_review_once.py
  python3 scripts/audit/full_live_review_once.py --root . --no-journal
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--journal-lines", type=int, default=5000)
    ap.add_argument("--jsonl-tail", type=int, default=120_000)
    ap.add_argument("--no-journal", action="store_true", help="Skip journalctl (non-Linux / CI)")
    args = ap.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root))
    hunt_path = root / "scripts" / "audit" / "off_leash_alpaca_hunt.py"
    spec = importlib.util.spec_from_file_location("off_leash_alpaca_hunt", hunt_path)
    if spec is None or spec.loader is None:
        print(json.dumps({"ok": False, "error": f"cannot load {hunt_path}"}))
        return 2
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    run_hunt = mod.run_hunt
    findings_to_markdown = mod._findings_to_markdown

    findings = run_hunt(
        root,
        journal_lines=args.journal_lines,
        jsonl_tail=args.jsonl_tail,
        skip_journal=args.no_journal,
    )
    out_json = root / "reports" / "off_leash_hunt_findings.json"
    out_md = root / "reports" / "RED_TEAM_REPORT.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    out_md.write_text(findings_to_markdown(findings), encoding="utf-8")
    print(
        json.dumps(
            {"ok": True, "findings_json": str(out_json), "RED_TEAM_REPORT": str(out_md)},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
