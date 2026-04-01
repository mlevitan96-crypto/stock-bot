#!/usr/bin/env python3
"""
Append missing alpaca_unified_events.jsonl terminal rows from exit_attribution.jsonl.

Deterministic: rebuilds trade_key from trade_id (open_SYM_ISO) + exit row side.
Read-only scan of exit; writes unified + dedicated exit mirror via emit_exit_attribution.

Usage (dry-run):  python scripts/audit/backfill_unified_terminal_from_exit_attribution.py --root . --dry-run
Apply:            python scripts/audit/backfill_unified_terminal_from_exit_attribution.py --root .

NOT trading logic; telemetry repair only. Review output before apply on prod.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Set

TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")


def _load_terminal_trade_ids(unified: Path) -> Set[str]:
    out: Set[str] = set()
    if not unified.is_file():
        return out
    with unified.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("event_type") != "alpaca_exit_attribution":
                continue
            if not r.get("terminal_close"):
                continue
            tid = r.get("trade_id")
            if tid:
                out.add(str(tid))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    logs = root / "logs"
    exit_p = logs / "exit_attribution.jsonl"
    if not exit_p.is_file():
        print("missing", exit_p)
        return 1

    unified = logs / "alpaca_unified_events.jsonl"
    have = _load_terminal_trade_ids(unified)

    from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side

    n = 0
    with exit_p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            tid = rec.get("trade_id")
            if not tid or tid in have:
                continue
            m = TID_RE.match(str(tid))
            if not m:
                continue
            sym, ts_rest = m.group(1), m.group(2)
            side_raw = rec.get("side") or rec.get("direction") or "long"
            sk = normalize_side(side_raw)
            iso = ts_rest if "T" in ts_rest else ts_rest.replace(" ", "T")
            if iso.endswith("Z"):
                iso = iso[:-1] + "+00:00"
            try:
                tk = rec.get("trade_key") or build_trade_key(sym, sk, iso)
            except Exception:
                continue
            ct = rec.get("canonical_trade_id") or tk
            if args.dry_run:
                print("would_backfill", tid, tk)
                n += 1
                continue
            from src.telemetry.alpaca_attribution_emitter import emit_exit_attribution

            snap: Dict[str, Any] = {
                "pnl": rec.get("pnl"),
                "pnl_pct": rec.get("pnl_pct"),
                "pnl_unrealized": None,
                "mfe": None,
                "mae": None,
                "mfe_pct_so_far": None,
                "mae_pct_so_far": None,
                "hold_minutes": rec.get("time_in_trade_minutes"),
            }
            v2c = rec.get("v2_exit_components") if isinstance(rec.get("v2_exit_components"), dict) else {}
            emit_exit_attribution(
                trade_id=str(tid),
                symbol=str(sym),
                winner=str(rec.get("exit_reason") or "backfill"),
                winner_explanation=str(rec.get("exit_regime_reason") or "")[:500],
                trade_key=str(tk),
                canonical_trade_id=str(ct),
                terminal_close=True,
                realized_pnl_usd=float(rec["pnl"]) if rec.get("pnl") is not None else None,
                fees_usd=0.0,
                exit_components_raw=dict(v2c),
                snapshot=snap,
                timestamp=rec.get("timestamp"),
                entry_time_iso=str(rec.get("entry_timestamp") or iso),
                side=str(sk),
            )
            have.add(str(tid))
            n += 1
    print("backfill_count", n, "dry_run" if args.dry_run else "applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
