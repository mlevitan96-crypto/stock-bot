#!/usr/bin/env python3
"""
Diagnose shadow starvation: blocked_trades > 0 but no shadow_candidate (or equivalent)
for the same period. Policy: WARN only; see docs/ALPACA_SHADOW_STARVATION_POLICY.md.

Usage:
  python scripts/diagnose_shadow_starvation.py [--date YYYY-MM-DD] [--report PATH] [--strict]
  --strict: exit 1 when starvation detected (optional; not enforced by default).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"
SHADOW_PATH = REPO / "logs" / "shadow.jsonl"


def _iter_jsonl(path: Path, date_str: str | None):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if date_str:
                ts = rec.get("timestamp") or rec.get("ts") or ""
                if isinstance(ts, str) and not ts.startswith(date_str):
                    continue
            yield rec
        except Exception:
            continue


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnose shadow starvation (WARN only by default)")
    ap.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    ap.add_argument("--report", default=None, help="Write summary to PATH")
    ap.add_argument("--strict", action="store_true", help="Exit 1 when starvation detected (use only after approval)")
    args = ap.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    blocked_symbols: set[str] = set()
    shadow_candidate_symbols: set[str] = set()
    shadow_variant_symbols: set[str] = set()

    for rec in _iter_jsonl(BLOCKED_PATH, date_str):
        if isinstance(rec, dict) and rec.get("symbol"):
            blocked_symbols.add(str(rec["symbol"]).strip().upper())

    for rec in _iter_jsonl(SHADOW_PATH, date_str):
        if not isinstance(rec, dict):
            continue
        et = rec.get("event_type") or ""
        sym = (rec.get("symbol") or "").strip().upper()
        if et == "shadow_candidate" and sym:
            shadow_candidate_symbols.add(sym)
        if et == "shadow_variant_decision" and sym:
            shadow_variant_symbols.add(sym)

    shadow_any = shadow_candidate_symbols | shadow_variant_symbols
    starved = blocked_symbols - shadow_any
    n_blocked = len(blocked_symbols)
    n_shadow = len(shadow_any)
    starvation = n_blocked > 0 and n_shadow == 0
    partial = n_blocked > 0 and len(starved) > 0 and len(shadow_any) > 0

    lines = [
        f"Shadow starvation diagnostic ({date_str})",
        f"Blocked trade symbols: {n_blocked}",
        f"Shadow candidate/variant symbols: {n_shadow}",
        f"Starved (blocked but no shadow): {len(starved)}",
        "",
    ]
    if starved:
        lines.append("Starved symbols (sample): " + ", ".join(sorted(starved)[:20]))
        if len(starved) > 20:
            lines.append(f"  ... and {len(starved) - 20} more")
    if starvation:
        lines.append("")
        lines.append("WARN: Shadow starvation — at least one blocked trade and zero shadow candidates/variants for this date.")
    elif partial:
        lines.append("")
        lines.append("WARN: Partial shadow coverage — some blocked symbols have no shadow candidate/variant.")
    else:
        lines.append("")
        lines.append("OK: No starvation (no blocked trades, or all blocked symbols have shadow coverage).")

    report_text = "\n".join(lines)
    print(report_text)

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report_text, encoding="utf-8")

    if args.strict and (starvation or partial):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
