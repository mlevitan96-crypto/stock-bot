#!/usr/bin/env python3
"""Forward cohort parity + trace (run on droplet). Stdout: one JSON object."""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side
except Exception:

    def normalize_side(side: Any) -> str:  # type: ignore
        s = str(side or "long").lower()
        return "LONG" if s in ("buy", "long") else "SHORT"

    def build_trade_key(sym: Any, side: Any, entry_time: Any) -> str:  # type: ignore
        return f"{sym}|{normalize_side(side)}|0"

TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")


def _parse_iso_ts(s: Any) -> Optional[float]:
    if not s or not isinstance(s, str):
        return None
    try:
        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def _open_epoch(tid: str) -> Optional[float]:
    m = TID_RE.match(str(tid).strip())
    if not m:
        return None
    return _parse_iso_ts(m.group(2))


def _iter_jsonl(p: Path):
    if not p.is_file():
        return
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("/root/stock-bot"))
    ap.add_argument("--deploy-epoch", type=float, required=True)
    ap.add_argument("--trace-sample", type=int, default=15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    root = args.root.resolve()
    logs = root / "logs"
    dep = float(args.deploy_epoch)

    # Forward economic closes: exit_attribution with trade_id open >= deploy
    exit_rows: List[dict] = []
    for r in _iter_jsonl(logs / "exit_attribution.jsonl"):
        tid = r.get("trade_id")
        if not tid:
            continue
        oep = _open_epoch(str(tid))
        if oep is None or oep < dep:
            continue
        exit_rows.append(r)

    # Unified terminal closes for same trade_ids
    unified_term: Set[str] = set()
    for r in _iter_jsonl(logs / "alpaca_unified_events.jsonl"):
        if r.get("event_type") != "alpaca_exit_attribution":
            continue
        if not r.get("terminal_close"):
            continue
        tid = r.get("trade_id")
        if tid:
            oep = _open_epoch(str(tid))
            if oep is not None and oep >= dep:
                unified_term.add(str(tid))

    forward_close_ids = {str(r["trade_id"]) for r in exit_rows}
    missing_unified = sorted(forward_close_ids - unified_term)

    # Emit failures since deploy (by line ts if present)
    emit_fails = 0
    fail_path = logs / "alpaca_emit_failures.jsonl"
    if fail_path.is_file():
        for line in fail_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_iso_ts(o.get("ts"))
            if ts and ts >= dep:
                emit_fails += 1

    # trade_intent entered forward: canonical + trade_key
    intents_ok = 0
    intents_bad: List[str] = []
    for r in _iter_jsonl(logs / "run.jsonl"):
        if r.get("event_type") != "trade_intent":
            continue
        if str(r.get("decision_outcome", "")).lower() != "entered":
            continue
        ct = r.get("canonical_trade_id")
        tk = r.get("trade_key")
        # Forward if we can tie to a canonical epoch >= dep (symbol|SIDE|epoch)
        forward_intent = False
        if ct and "|" in str(ct):
            try:
                ep = int(str(ct).split("|")[-1])
                if ep >= int(dep):
                    forward_intent = True
            except ValueError:
                pass
        if not forward_intent:
            continue
        if ct and tk:
            intents_ok += 1
        else:
            intents_bad.append(str(r.get("symbol") or "?"))

    # Trace sample
    random.seed(args.seed)
    sample_ids = random.sample(
        list(forward_close_ids), min(args.trace_sample, len(forward_close_ids))
    )
    traces: List[dict] = []

    # Index run.jsonl intents by canonical/trade_key
    intents_by_key: Dict[str, List[dict]] = defaultdict(list)
    for r in _iter_jsonl(logs / "run.jsonl"):
        if r.get("event_type") != "trade_intent":
            continue
        if str(r.get("decision_outcome", "")).lower() != "entered":
            continue
        for k in (r.get("canonical_trade_id"), r.get("trade_key")):
            if k:
                intents_by_key[str(k)].append(r)

    orders_by_ct: Dict[str, List[dict]] = defaultdict(list)
    for r in _iter_jsonl(logs / "orders.jsonl"):
        ct = r.get("canonical_trade_id")
        if ct:
            orders_by_ct[str(ct)].append(r)

    for tid in sample_ids:
        ex = next((x for x in exit_rows if str(x.get("trade_id")) == tid), None)
        ct = ex.get("canonical_trade_id") if ex else None
        tk = ex.get("trade_key") if ex else None
        if not ct and not tk and ex:
            m = TID_RE.match(tid)
            if m:
                sk = normalize_side(ex.get("side") or "long")
                try:
                    tk = build_trade_key(m.group(1), sk, m.group(2))
                except Exception:
                    tk = None
        keys = [k for k in (ct, tk) if k]
        intent_hit = any(bool(intents_by_key.get(k)) for k in keys)
        ord_hit = any(bool(orders_by_ct.get(k)) for k in keys)
        traces.append(
            {
                "trade_id": tid,
                "exit_has_canonical_trade_id": bool(ex and ex.get("canonical_trade_id")),
                "exit_has_trade_key": bool(ex and ex.get("trade_key")),
                "unified_terminal_close": tid in unified_term,
                "trade_intent_entered_match": intent_hit,
                "orders_match": ord_hit,
            }
        )

    parity_ok = len(forward_close_ids) == len(unified_term) and emit_fails == 0
    trace_ok = (
        all(
            t["unified_terminal_close"]
            and t["trade_intent_entered_match"]
            and t["orders_match"]
            and t["exit_has_canonical_trade_id"]
            for t in traces
        )
        if traces
        else False
    )

    result = {
        "deploy_epoch_utc": dep,
        "forward_economic_closes": len(forward_close_ids),
        "forward_unified_terminal_closes": len(unified_term),
        "parity_exact": len(forward_close_ids) == len(unified_term),
        "missing_unified_for_forward_closes_sample": missing_unified[:20],
        "alpaca_emit_failures_since_deploy": emit_fails,
        "forward_trade_intents_with_ct_and_tk": intents_ok,
        "forward_trade_intents_bad": intents_bad[:20],
        "trace_sample_size": len(traces),
        "trace_all_pass": trace_ok,
        "traces": traces,
        "LEGACY_DEBT_QUARANTINED": "Opens before deploy epoch are excluded from forward counts",
        "forward_cohort_vacuous": len(forward_close_ids) == 0,
    }
    print(json.dumps(result, indent=2))
    if len(forward_close_ids) == 0:
        return 2
    if not parity_ok or not trace_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
