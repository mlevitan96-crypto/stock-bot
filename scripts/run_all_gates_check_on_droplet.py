#!/usr/bin/env python3
"""
Run on droplet (or via SSH from local) to check every gate that can prevent trades.
Prints a report. When INJECT_SIGNAL_TEST=1 is set and bot restarted, run this after one cycle
to see which gate blocked the injected signal.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def _read(path: Path, default: str = "") -> str:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        pass
    return default


def _read_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def main() -> int:
    print("=" * 70)
    print("ALL GATES CHECK (signal to execution)")
    print("=" * 70)
    print(f"Time: {datetime.now(timezone.utc).isoformat()}\n")

    # A. run_once-level gates
    print("--- A. run_once-level ---")
    freeze_path = REPO / "state" / "governor_freezes.json"
    freeze_data = _read_json(freeze_path)
    freeze_active = bool(freeze_data and any(freeze_data.get(k) for k in freeze_data if isinstance(freeze_data.get(k), bool)))
    print(f"  A1 Freeze (governor_freezes.json): {'BLOCK' if freeze_active else 'PASS'}  {freeze_data or 'no file'}")

    health_safe = (REPO / "state" / "health_safe_mode.flag").exists()
    print(f"  A1b Health safe mode flag:          {'BLOCK' if health_safe else 'PASS'}")

    kill_path = REPO / "state" / "kill_switch.json"
    kill_data = _read_json(kill_path)
    kill_active = kill_data.get("enabled", False) if isinstance(kill_data, dict) else False
    print(f"  B1 Kill switch:                     {'BLOCK' if kill_active else 'PASS'}  {kill_data or 'no file'}")

    base_url = os.environ.get("ALPACA_BASE_URL", "")
    armed = "paper-api.alpaca.markets" in base_url and "live" not in base_url.lower()
    print(f"  A7 Armed (paper URL):              {'PASS' if armed else 'BLOCK'}  ALPACA_BASE_URL={base_url[:50] if base_url else 'not set'}...")

    cache_path = REPO / "data" / "uw_flow_cache.json"
    cache_exists = cache_path.exists()
    if cache_exists:
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8", errors="replace"))
            sym_count = len([k for k in cache if not k.startswith("_")])
            print(f"  A4 UW cache:                       PASS  {sym_count} symbols")
        except Exception as e:
            print(f"  A4 UW cache:                       WARN  exists but unreadable: {e}")
    else:
        print(f"  A4 UW cache:                       BLOCK  missing")

    # Recent run.jsonl
    run_path = REPO / "logs" / "run.jsonl"
    run_last = ""
    if run_path.exists():
        for line in reversed(run_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()):
            if line.strip():
                run_last = line.strip()
                break
    if run_last:
        try:
            r = json.loads(run_last)
            print(f"\n  Last run.jsonl: clusters={r.get('clusters', '?')}, orders={r.get('orders', '?')}")
            if r.get("metrics", {}).get("composite_enabled") is not None:
                print(f"    composite_enabled={r['metrics'].get('composite_enabled')}")
        except Exception:
            print(f"\n  Last run.jsonl: (parse error)")
    else:
        print("\n  No run.jsonl entries")

    # Recent gate.jsonl (last 15)
    gate_path = REPO / "logs" / "gate.jsonl"
    gate_lines = []
    if gate_path.exists():
        lines = gate_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        gate_lines = [l for l in lines if l.strip()][-15:]
    print("\n--- Last 15 gate.jsonl ---")
    if not gate_lines:
        print("  (none)")
    else:
        for line in gate_lines:
            try:
                g = json.loads(line)
                sym = g.get("symbol", "")
                ev = g.get("event", g.get("gate_type", ""))
                reason = g.get("message", g.get("reason", g.get("rejection_reason", "")))
                print(f"  {ev}  symbol={sym}  {reason[:60] if reason else ''}")
            except Exception:
                print(f"  {line[:80]}")

    # submit_entry
    sub_path = REPO / "logs" / "submit_entry.jsonl"
    sub_lines = []
    if sub_path.exists():
        lines = sub_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        sub_lines = [l for l in lines if l.strip()][-5:]
    print("\n--- Last 5 submit_entry.jsonl ---")
    if not sub_lines:
        print("  (none)")
    else:
        for line in sub_lines:
            try:
                s = json.loads(line)
                print(f"  {s.get('msg', s.get('status', ''))}  symbol={s.get('symbol', '')}")
            except Exception:
                print(f"  {line[:80]}")

    # Inject test hint
    if os.environ.get("INJECT_SIGNAL_TEST") == "1":
        print("\n  INJECT_SIGNAL_TEST=1 is set. Next run_once will inject 1 synthetic cluster if clusters==0.")
    else:
        print("\n  To test execution path: set INJECT_SIGNAL_TEST=1, restart bot, wait one cycle, re-run this script.")

    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
