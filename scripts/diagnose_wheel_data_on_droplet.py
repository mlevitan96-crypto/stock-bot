#!/usr/bin/env python3
"""
Diagnose wheel strategy data sources on droplet.
Run: python scripts/diagnose_wheel_data_on_droplet.py
Or via SSH: ssh root@DROPLET "cd /root/stock-bot && python3 scripts/diagnose_wheel_data_on_droplet.py"
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    base = ROOT
    logs = base / "logs"
    state = base / "state"
    reports = base / "reports"

    print("=== Wheel Data Diagnostic ===\n")
    print("Paths (cwd-independent):")
    print(f"  logs:      {logs.resolve()}")
    print(f"  state:    {state.resolve()}")
    print(f"  reports:  {reports.resolve()}\n")

    # 1) attribution.jsonl
    attr_path = logs / "attribution.jsonl"
    wheel_attr = 0
    if attr_path.exists():
        for line in attr_path.read_text(encoding="utf-8", errors="replace").splitlines()[-5000:]:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("type") == "attribution" and (rec.get("strategy_id") or rec.get("context", {}).get("strategy_id")) == "wheel":
                    wheel_attr += 1
            except Exception:
                pass
        print(f"attribution.jsonl: EXISTS, wheel records (last 5k lines): {wheel_attr}")
    else:
        print(f"attribution.jsonl: MISSING")

    # 2) telemetry.jsonl
    telem_path = logs / "telemetry.jsonl"
    wheel_telem = 0
    if telem_path.exists():
        for line in telem_path.read_text(encoding="utf-8", errors="replace").splitlines()[-2000:]:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("strategy_id") == "wheel":
                    wheel_telem += 1
            except Exception:
                pass
        print(f"telemetry.jsonl: EXISTS, wheel records (last 2k lines): {wheel_telem}")
    else:
        print(f"telemetry.jsonl: MISSING")

    # 3) wheel_state.json
    ws_path = state / "wheel_state.json"
    if ws_path.exists():
        try:
            ws = json.loads(ws_path.read_text(encoding="utf-8", errors="replace"))
            csp = ws.get("csp_history") or []
            cc = ws.get("cc_history") or []
            open_csps = ws.get("open_csps") or {}
            assignments = sum(1 for h in csp if isinstance(h, dict) and h.get("assigned") is True)
            callaways = sum(1 for h in cc if isinstance(h, dict) and h.get("called_away") is True)
            print(f"wheel_state.json: EXISTS, csp_history={len(csp)}, cc_history={len(cc)}, assignments={assignments}, call_aways={callaways}, open_csps={len(open_csps)}")
        except Exception as e:
            print(f"wheel_state.json: EXISTS but parse error: {e}")
    else:
        print(f"wheel_state.json: MISSING")

    # 4) reports/*_stock-bot_wheel.json
    wheel_reports = list(reports.glob("*_stock-bot_wheel.json")) if reports.exists() else []
    wheel_reports.sort(key=lambda p: p.name, reverse=True)
    print(f"\nreports/*_stock-bot_wheel.json: {len(wheel_reports)} files")
    for p in wheel_reports[:5]:
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            pc = d.get("premium_collected", 0)
            ac = d.get("assignment_count", 0)
            ca = d.get("call_away_count", 0)
            rp = d.get("realized_pnl", 0)
            print(f"  {p.name}: premium_collected={pc}, assignment_count={ac}, call_away_count={ca}, realized_pnl={rp}")
        except Exception as e:
            print(f"  {p.name}: parse error {e}")

    # 5) Run generate_daily_strategy_reports if reports empty or stale
    today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
    today_wheel = reports / f"{today}_stock-bot_wheel.json"
    if not today_wheel.exists() or not wheel_reports:
        print(f"\n>>> Run: python3 scripts/generate_daily_strategy_reports.py --date {today}")
        print("    to ensure wheel report exists for today.")

    print("\n=== End diagnostic ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
