#!/usr/bin/env python3
"""
Owner artifact validator (read-only)
===================================

Purpose:
Validate that a given synthetic trade (or rejection) is visible across:
- logs/master_trade_log.jsonl
- logs/live_trades.jsonl (legacy compatibility)
- logs/exit_attribution.jsonl
- telemetry/<date>/telemetry_manifest.json (realized trades list)
- analysis_packs/<date>/SHADOW_VS_LIVE_DEEP_DIVE.md

Contract:
- Read-only (no writes).
- Never raises; exits 0 on success, 2 on failure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _iter_jsonl(p: Path) -> Iterable[Dict[str, Any]]:
    for ln in _read_text(p).splitlines():
        ln = (ln or "").strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except Exception:
            continue
        if isinstance(obj, dict):
            yield obj


def _exists_pred(p: Path, pred) -> bool:
    try:
        if not p.exists():
            return False
        for o in _iter_jsonl(p):
            if pred(o):
                return True
        return False
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--symbol", required=True, help="Symbol")
    ap.add_argument("--trade-id", default="", help="Trade id (for master/live logs)")
    ap.add_argument("--entry-timestamp", default="", help="Entry timestamp (for exit attribution)")
    ap.add_argument("--expect", choices=["present", "absent"], default="present")
    args = ap.parse_args()

    day = str(args.date).strip()
    sym = str(args.symbol).upper().strip()
    trade_id = str(args.trade_id or "").strip()
    entry_ts = str(args.entry_timestamp or "").strip()
    want_present = args.expect == "present"

    checks = []

    master = Path("logs/master_trade_log.jsonl")
    live = Path("logs/live_trades.jsonl")
    exit_attr = Path("logs/exit_attribution.jsonl")
    manifest = Path(f"telemetry/{day}/telemetry_manifest.json")
    deep = Path(f"analysis_packs/{day}/SHADOW_VS_LIVE_DEEP_DIVE.md")

    if trade_id:
        checks.append(("master_trade_log.trade_id", master, lambda o: o.get("trade_id") == trade_id))
        checks.append(("live_trades.trade_id", live, lambda o: o.get("trade_id") == trade_id))
    if entry_ts:
        checks.append(("exit_attribution.entry_timestamp", exit_attr, lambda o: o.get("symbol") == sym and o.get("entry_timestamp") == entry_ts))

    ok_all = True

    for name, p, pred in checks:
        present = _exists_pred(p, pred)
        ok = present if want_present else (not present)
        print(f"{name}: {'OK' if ok else 'FAIL'} (present={present})")
        ok_all = ok_all and ok

    # Telemetry manifest realized trades list
    try:
        m_present = False
        if manifest.exists():
            d = json.loads(_read_text(manifest) or "{}")
            rt = (((d.get("computed") or {}).get("shadow") or {}).get("realized_trades") or [])
            m_present = any(isinstance(r, dict) and str(r.get("symbol", "")).upper() == sym for r in rt)
        ok = m_present if want_present else (not m_present)
        print(f"telemetry_manifest.realized_trades: {'OK' if ok else 'FAIL'} (present={m_present})")
        ok_all = ok_all and ok
    except Exception as e:
        print(f"telemetry_manifest.realized_trades: FAIL (error={e})")
        ok_all = False

    # Deep dive mentions symbol
    try:
        d_present = False
        if deep.exists():
            d_present = sym in _read_text(deep)
        ok = d_present if want_present else (not d_present)
        print(f"deep_dive.contains_symbol: {'OK' if ok else 'FAIL'} (present={d_present})")
        ok_all = ok_all and ok
    except Exception as e:
        print(f"deep_dive.contains_symbol: FAIL (error={e})")
        ok_all = False

    return 0 if ok_all else 2


if __name__ == "__main__":
    raise SystemExit(main())

