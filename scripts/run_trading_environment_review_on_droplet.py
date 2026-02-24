#!/usr/bin/env python3
"""
Run trading environment review on droplet and fetch report to local.
- Ensures droplet has latest code (git pull)
- Runs scripts/trading_environment_review_on_droplet.py --last-n 150
- Optionally runs full_signal_review and multi-model style check
- Fetches TRADING_ENVIRONMENT_REVIEW_<date>.md and .json to reports/trading_environment_review/
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "trading_environment_review"


def _run(c, cmd: str, timeout: int = 120):
    pd = c.project_dir
    return c._execute(f"cd {pd} && {cmd}", timeout=timeout)


def _cat(c, remote_path: str) -> str:
    out, err, rc = _run(c, f"cat {remote_path} 2>/dev/null || echo '__MISSING__'", timeout=15)
    return (out or "").strip()


def main() -> int:
    try:
        from droplet_client import DropletClient
    except Exception as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        print("Set DROPLET_HOST (and key/password) or droplet_config.json", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        pd = c.project_dir
        print("--- GIT PULL ---")
        out, err, rc = _run(c, "git fetch origin && git pull origin main", timeout=60)
        print(out[:600] if out else "(no output)")
        if rc != 0:
            print("Warning: git pull non-zero", file=sys.stderr)

        print("\n--- TRADING ENVIRONMENT REVIEW (last 150 trades, signals, persona) ---")
        out, err, rc = _run(c, "python3 scripts/trading_environment_review_on_droplet.py --last-n 150", timeout=90)
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Warning: trading_environment_review_on_droplet.py returned non-zero", file=sys.stderr)

        print("\n--- FULL SIGNAL REVIEW (funnel, choke point) ---")
        out2, err2, rc2 = _run(c, "python3 scripts/full_signal_review_on_droplet.py --days 7", timeout=120)
        if out2:
            print(out2[-1200:] if len(out2) > 1200 else out2)
        if rc2 != 0:
            print("Warning: full_signal_review returned non-zero", file=sys.stderr)

        from datetime import datetime, timezone
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        to_fetch = [
            (f"{pd}/reports/trading_environment_review/TRADING_ENVIRONMENT_REVIEW_{date_str}.md", f"TRADING_ENVIRONMENT_REVIEW_{date_str}.md"),
            (f"{pd}/reports/trading_environment_review/TRADING_ENVIRONMENT_REVIEW_{date_str}.json", f"TRADING_ENVIRONMENT_REVIEW_{date_str}.json"),
        ]
        for remote, local_name in to_fetch:
            content = _cat(c, remote)
            if content and "__MISSING__" not in content:
                local_path = OUT_DIR / local_name
                local_path.write_text(content, encoding="utf-8")
                print(f"\nFetched: {remote} -> {local_path}")
            else:
                print(f"\nMissing or empty: {remote}")

        funnel_md = _cat(c, f"{pd}/reports/signal_review/signal_funnel.md")
        if funnel_md and "__MISSING__" not in funnel_md:
            (OUT_DIR / "signal_funnel.md").write_text(funnel_md, encoding="utf-8")
            print("Fetched: signal_funnel.md")

    print("\n" + "=" * 60)
    print("Trading environment review complete. Reports in:", OUT_DIR)
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
