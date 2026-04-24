#!/usr/bin/env python3
"""
Forensics for strict completeness repair targets: merged primary + strict_backfill_* streams.
Read-only. Writes JSON report to stdout or --json-out.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO = Path(__file__).resolve().parents[2]
TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")


def _parse_iso(s: Any) -> Optional[float]:
    if not s or not isinstance(s, str):
        return None
    try:
        from datetime import datetime, timezone

        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def _stream(path: Path):
    if not path.is_file():
        return
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _merged(logs: Path, name: str):
    yield from _stream(logs / name)
    yield from _stream(logs / f"strict_backfill_{name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument(
        "--trade-ids",
        nargs="*",
        default=[
            "open_PFE_2026-03-26T14:29:25.977370+00:00",
            "open_QQQ_2026-03-26T15:10:28.882493+00:00",
            "open_WMT_2026-03-26T15:10:28.883737+00:00",
            "open_HOOD_2026-03-26T15:51:38.174449+00:00",
            "open_LCID_2026-03-26T15:51:38.396698+00:00",
            "open_CAT_2026-03-26T16:34:40.245664+00:00",
        ],
    )
    args = ap.parse_args()
    root = args.root.resolve()
    logs = root / "logs"
    targets: Set[str] = set(args.trade_ids)

    exits: Dict[str, dict] = {}
    for r in _stream(logs / "exit_attribution.jsonl"):
        tid = r.get("trade_id")
        if tid and str(tid) in targets:
            exits[str(tid)] = r

    unified_exit: Dict[str, dict] = {}
    unified_entry_keys: Set[str] = set()
    for r in _merged(logs, "alpaca_unified_events.jsonl"):
        et = r.get("event_type") or r.get("type")
        if et == "alpaca_exit_attribution" and r.get("terminal_close"):
            tid = r.get("trade_id")
            if tid and str(tid) in targets:
                unified_exit[str(tid)] = r
        if et == "alpaca_entry_attribution":
            for k in (r.get("trade_key"), r.get("canonical_trade_id")):
                if k:
                    unified_entry_keys.add(str(k))

    intents_entered: List[dict] = []
    exit_intents: List[dict] = []
    resolved: List[dict] = []
    for r in _merged(logs, "run.jsonl"):
        et = r.get("event_type")
        if et == "trade_intent" and str(r.get("decision_outcome", "")).lower() == "entered":
            intents_entered.append(r)
        if et == "exit_intent":
            exit_intents.append(r)
        if et == "canonical_trade_id_resolved" and r.get("canonical_trade_id_fill"):
            resolved.append(r)

    orders_by_sym: Dict[str, List[dict]] = {}
    for r in _merged(logs, "orders.jsonl"):
        sym = str(r.get("symbol") or "").upper()
        if sym:
            orders_by_sym.setdefault(sym, []).append(r)

    sys.path.insert(0, str(REPO))
    from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side
    from telemetry.alpaca_strict_completeness_gate import _expand_canonical_aliases

    rows = []
    for tid in sorted(targets):
        ex = exits.get(tid)
        ux = unified_exit.get(tid)
        m = TID_RE.match(tid)
        sym = m.group(1).upper() if m else "?"
        entry_iso = m.group(2) if m else ""
        side = normalize_side((ex or {}).get("side") or (ex or {}).get("direction") or "long")
        tk = None
        try:
            tk = build_trade_key(sym, side, entry_iso) if m and ex else None
        except Exception:
            tk = None
        ct = None
        if ux:
            ct = ux.get("canonical_trade_id") or ux.get("trade_key")
        if not ct and ex:
            ct = ex.get("canonical_trade_id")
        if not ct and tk:
            ct = tk

        seed = {str(x) for x in (tk, ct) if x}
        itf: Dict[str, str] = {}
        for rr in resolved:
            ci = rr.get("canonical_trade_id_intent")
            cf = rr.get("canonical_trade_id_fill")
            if ci and cf:
                itf[str(ci)] = str(cf)
        aliases = _expand_canonical_aliases(seed, itf)

        def has_entered() -> bool:
            return any(
                str(r.get("symbol") or "").upper() == sym
                and (
                    str(r.get("canonical_trade_id") or "") in aliases
                    or str(r.get("trade_key") or "") in aliases
                )
                for r in intents_entered
            )

        def has_exit_intent() -> bool:
            return any(
                str(r.get("canonical_trade_id") or "") in aliases or str(r.get("trade_key") or "") in aliases
                for r in exit_intents
            )

        def has_unified_entry() -> bool:
            return bool(aliases & unified_entry_keys)

        def has_orders() -> bool:
            for r in orders_by_sym.get(sym, []):
                oct = r.get("canonical_trade_id")
                if oct and str(oct) in aliases:
                    return True
            return False

        orders_hits = []
        for k in aliases:
            for r in orders_by_sym.get(sym, []):
                oct = r.get("canonical_trade_id")
                if oct and str(oct) == k:
                    orders_hits.append(r.get("id") or r.get("client_order_id"))
                elif k and str(oct) == str(k):
                    orders_hits.append(r.get("id"))

        rows.append(
            {
                "trade_id": tid,
                "symbol": sym,
                "exit_attribution_present": bool(ex),
                "unified_exit_terminal_present": bool(ux),
                "derived_trade_key": tk,
                "canonical_trade_id_used": str(ct) if ct else None,
                "alias_count": len(aliases),
                "entered_trade_intent_joinable": has_entered(),
                "exit_intent_joinable": has_exit_intent(),
                "unified_entry_present": has_unified_entry(),
                "orders_row_with_canonical_in_aliases": has_orders(),
                "order_ids_matching_symbol": orders_hits[:5],
                "missing_legs": [
                    x
                    for x, ok in [
                        ("entered", has_entered()),
                        ("unified_entry", has_unified_entry()),
                        ("orders_canonical", has_orders()),
                        ("exit_intent", has_exit_intent()),
                    ]
                    if not ok
                ],
            }
        )

    out = {"ROOT": str(root), "targets": sorted(targets), "per_trade": rows}
    js = json.dumps(out, indent=2)
    print(js)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(js, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
