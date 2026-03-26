#!/usr/bin/env python3
"""
Last-window learning safety: NYSE regular close (America/New_York 16:00) as window end, 2h slice, forward truth + SRE runner, CSA verdict.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore


def nyse_regular_close_last_completed() -> tuple[float, str, str]:
    """UTC epoch of most recent completed NYSE regular session close (Mon–Fri 16:00 ET), ISO labels."""
    if ZoneInfo is None:
        raise RuntimeError("zoneinfo required")
    et = ZoneInfo("America/New_York")
    now_et = datetime.now(timezone.utc).astimezone(et)
    d = now_et.date()
    close_today = datetime(d.year, d.month, d.day, 16, 0, 0, tzinfo=et)
    if now_et >= close_today:
        close_dt = close_today
    else:
        d = d - timedelta(days=1)
        while d.weekday() >= 5:
            d = d - timedelta(days=1)
        close_dt = datetime(d.year, d.month, d.day, 16, 0, 0, tzinfo=et)
    return close_dt.timestamp(), close_dt.isoformat(), d.isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--ts", type=str, default="20260327_LAST_WINDOW")
    ap.add_argument("--window-hours", type=int, default=2)
    ap.add_argument("--repair-max-rounds", type=int, default=6)
    ap.add_argument("--repair-sleep-seconds", type=int, default=10)
    ap.add_argument("--close-epoch-override", type=float, default=None, help="Debug: fixed window end UTC epoch")
    args = ap.parse_args()

    root = args.root.resolve()
    ts = args.ts
    if args.close_epoch_override is not None:
        close_ts = float(args.close_epoch_override)
        close_iso = datetime.fromtimestamp(close_ts, tz=timezone.utc).isoformat()
        session_date = "override"
    else:
        close_ts, close_iso, session_date = nyse_regular_close_last_completed()

    window_h = int(args.window_hours)
    window_start_ts = close_ts - window_h * 3600
    window_start_iso = datetime.fromtimestamp(window_start_ts, tz=timezone.utc).isoformat()

    scope_path = root / "reports" / "audit" / f"ALPACA_LAST_WINDOW_SCOPE_{ts}.md"
    scope_path.parent.mkdir(parents=True, exist_ok=True)
    scope_path.write_text(
        f"# Alpaca last-window scope\n\n"
        f"**TS:** `{ts}`\n\n"
        f"## Venue / clock\n\n"
        f"- **Exchange calendar:** US equities regular session, **NYSE close 16:00 America/New_York** (Alpaca cash equities).\n"
        f"- **Window end (`close_ts`):** `{close_iso}` (UTC epoch `{close_ts}`)\n"
        f"- **Session date (ET):** `{session_date}`\n\n"
        f"## Window\n\n"
        f"- `last_window_hours` = **{window_h}**\n"
        f"- `window_start` = close − {window_h}h → UTC epoch `{window_start_ts}` (`{window_start_iso}`)\n"
        f"- Strict gate: exits with `open_ts_epoch ≤ exit_ts ≤ EXIT_TS_UTC_EPOCH_MAX` (see runner `--window-end-epoch`).\n",
        encoding="utf-8",
    )

    json_out = root / "reports" / f"ALPACA_LAST_WINDOW_TRUTH_{ts}.json"
    md_out = root / "reports" / "audit" / f"ALPACA_LAST_WINDOW_TRUTH_{ts}.md"
    inc_json = root / "reports" / f"ALPACA_LAST_WINDOW_INCIDENT_{ts}.json"
    inc_md = root / "reports" / f"ALPACA_LAST_WINDOW_INCIDENT_{ts}.md"

    runner = REPO / "scripts" / "audit" / "alpaca_forward_truth_contract_runner.py"
    env = {**os.environ, "PYTHONPATH": str(REPO)}
    cmd = [
        sys.executable,
        "-u",
        str(runner),
        "--root",
        str(root),
        "--window-hours",
        str(window_h),
        "--window-end-epoch",
        str(close_ts),
        "--repair-max-rounds",
        str(args.repair_max_rounds),
        "--repair-sleep-seconds",
        str(args.repair_sleep_seconds),
        "--json-out",
        str(json_out),
        "--md-out",
        str(md_out),
        "--incident-json",
        str(inc_json),
        "--incident-md",
        str(inc_md),
    ]
    pr = subprocess.run(cmd, cwd=str(root), env=env, timeout=900)
    exit_code = pr.returncode

    interpretation = ""
    safe = False
    fg: dict = {}
    if json_out.is_file():
        try:
            data = json.loads(json_out.read_text(encoding="utf-8"))
            fg = data.get("final_gate") or {}
            seen = int(fg.get("trades_seen") or 0)
            inc = int(fg.get("trades_incomplete") or 0)
            sre_actions = len(data.get("sre_repair_actions_applied") or [])
            sre_rounds = (data.get("sre_engine_meta") or {}).get("rounds_executed", 0)
            if exit_code == 0 and inc == 0:
                safe = True
                interpretation = (
                    f"Case A: exit 0, trades_incomplete==0 (trades_seen={seen}). "
                    f"SRE repair batches applied: {sre_actions}, rounds_executed: {sre_rounds}."
                )
            elif exit_code == 0 and seen == 0:
                safe = True
                interpretation = "Case C: exit 0, vacuous cohort (no exits in window). SRE may be no-op."
            elif exit_code == 2:
                interpretation = f"Case B: exit 2 INCIDENT after bounded repair (trades_incomplete={inc})."
            else:
                interpretation = f"Operational/structural failure exit_code={exit_code}."
        except json.JSONDecodeError:
            interpretation = "Could not parse truth JSON."

    verdict = "LAST_WINDOW_LEARNING_SAFE" if safe else "LAST_WINDOW_LEARNING_NOT_SAFE"
    verdict_path = root / "reports" / "audit" / f"ALPACA_LAST_WINDOW_LEARNING_VERDICT_{ts}.md"
    verdict_path.write_text(
        f"# CSA — last-window learning verdict\n\n"
        f"**TS:** `{ts}`\n\n"
        f"## Interpretation\n\n{interpretation}\n\n"
        f"## Metrics (final_gate)\n\n"
        f"```json\n"
        f"{json.dumps({k: fg.get(k) for k in ('trades_seen', 'trades_complete', 'trades_incomplete', 'EXIT_TS_UTC_EPOCH_MAX', 'OPEN_TS_UTC_EPOCH')}, indent=2)}\n"
        f"```\n\n"
        f"## Runner exit code\n\n`{exit_code}`\n\n"
        f"## CSA verdict line\n\n**CSA_VERDICT: {verdict}**\n",
        encoding="utf-8",
    )

    print(json.dumps({"scope": str(scope_path), "truth": str(json_out), "verdict": str(verdict_path), "exit_code": exit_code, "csa_verdict": verdict}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
