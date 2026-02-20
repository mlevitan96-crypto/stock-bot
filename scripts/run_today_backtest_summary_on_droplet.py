#!/usr/bin/env python3
"""
Run today's signal backtest summary on the droplet and fetch SUMMARY.md + summary.json.

Usage (local):
  python scripts/run_today_backtest_summary_on_droplet.py [--date YYYY-MM-DD]

Requires: DropletClient (DROPLET_HOST / droplet_config.json).
Writes: reports/investigation/fetched/today_backtest_SUMMARY_<date>.md and today_backtest_summary_<date>.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FETCHED = REPO / "reports" / "investigation" / "fetched"


def _run(c, cmd: str, timeout: int = 120):
    pd = c.project_dir
    return c._execute(f"cd {pd} && {cmd}", timeout=timeout)


def _cat(c, remote_path: str, timeout: int = 15) -> str:
    out, err, rc = _run(c, f"cat {remote_path} 2>/dev/null || echo '__MISSING__'", timeout=timeout)
    return (out or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    try:
        from droplet_client import DropletClient
    except Exception as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1

    date_arg = f" --date {args.date}" if args.date else ""
    # Output dir on droplet: reports/investigation/today_backtest_YYYYMMDD
    if args.date:
        suffix = args.date.replace("-", "")
    else:
        from datetime import datetime, timezone
        suffix = datetime.now(timezone.utc).strftime("%Y%m%d")
    remote_dir = f"reports/investigation/today_backtest_{suffix}"

    FETCHED.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        print("Running today_signal_backtest_summary_on_droplet.py on droplet...")
        out, err, rc = _run(c, f"python3 scripts/today_signal_backtest_summary_on_droplet.py{date_arg}", timeout=90)
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Script exited non-zero; may still have written output.", file=sys.stderr)

        summary_md = _cat(c, f"{remote_dir}/SUMMARY.md")
        summary_json = _cat(c, f"{remote_dir}/summary.json")

        if summary_md and "__MISSING__" not in summary_md:
            local_md = FETCHED / f"today_backtest_SUMMARY_{suffix}.md"
            local_md.write_text(summary_md, encoding="utf-8")
            print(f"Fetched SUMMARY -> {local_md}")
        else:
            print("SUMMARY.md not found or empty on droplet.", file=sys.stderr)

        if summary_json and "__MISSING__" not in summary_json:
            local_json = FETCHED / f"today_backtest_summary_{suffix}.json"
            local_json.write_text(summary_json, encoding="utf-8")
            print(f"Fetched summary.json -> {local_json}")
        else:
            print("summary.json not found or empty on droplet.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
