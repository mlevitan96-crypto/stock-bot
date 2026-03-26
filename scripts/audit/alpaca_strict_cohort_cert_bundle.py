#!/usr/bin/env python3
"""
Strict cohort certification bundle: gate + parity (strict window) + up to N traces.

Parity: strict_cohort trade_ids with economic close == unified terminal_close rows for same tids (0 tolerance).
Traces: sampled from complete_trade_ids only; each trace must match full strict chain (same legs as gate).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

REPO = Path(__file__).resolve().parents[2]


def _parse_iso_ts(s: Any) -> Optional[float]:
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


TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")


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
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--open-ts-epoch", type=float, required=True)
    ap.add_argument("--trace-sample", type=int, default=15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    root = args.root.resolve()
    sys.path.insert(0, str(REPO))
    from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side
    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    gate = evaluate_completeness(
        root,
        open_ts_epoch=args.open_ts_epoch,
        audit=True,
        collect_complete_trade_ids=True,
        collect_strict_cohort_trade_ids=True,
    )

    logs = root / "logs"
    cohort: Set[str] = set(gate.get("strict_cohort_trade_ids") or [])

    unified_term: Set[str] = set()
    for r in _iter_jsonl(logs / "alpaca_unified_events.jsonl"):
        if r.get("event_type") != "alpaca_exit_attribution":
            continue
        if not r.get("terminal_close"):
            continue
        tid = r.get("trade_id")
        if tid and str(tid) in cohort:
            unified_term.add(str(tid))

    econ_in_cohort = len(cohort)
    parity_exact = econ_in_cohort == len(unified_term) and cohort == unified_term
    missing_unified = sorted(cohort - unified_term)[:30]

    # Build indexes for traces (same join model as gate)
    intent_to_fill: Dict[str, str] = {}
    trade_intents_entered: List[dict] = []
    exit_intents_by_ct: Dict[str, List[dict]] = defaultdict(list)
    for r in _iter_jsonl(logs / "run.jsonl"):
        et = r.get("event_type")
        if et == "canonical_trade_id_resolved" and r.get("canonical_trade_id_fill"):
            ci = r.get("canonical_trade_id_intent")
            if ci:
                intent_to_fill[str(ci)] = str(r["canonical_trade_id_fill"])
        if et == "exit_intent":
            for _ek in (r.get("canonical_trade_id"), r.get("trade_key")):
                if _ek:
                    exit_intents_by_ct[str(_ek)].append(r)
        if et == "trade_intent" and str(r.get("decision_outcome", "")).lower() == "entered":
            trade_intents_entered.append(r)

    from telemetry.alpaca_strict_completeness_gate import _expand_canonical_aliases

    unified_entry: Dict[str, dict] = {}
    unified_exit_by_tid: Dict[str, dict] = {}
    for r in _iter_jsonl(logs / "alpaca_unified_events.jsonl"):
        et = r.get("event_type") or r.get("type")
        if et == "alpaca_entry_attribution":
            for k in (r.get("trade_key"), r.get("canonical_trade_id")):
                if k:
                    unified_entry[str(k)] = r
        elif et == "alpaca_exit_attribution":
            tid = r.get("trade_id")
            if tid and r.get("terminal_close"):
                unified_exit_by_tid[str(tid)] = r

    orders_by_ct: Dict[str, List[dict]] = defaultdict(list)
    for r in _iter_jsonl(logs / "orders.jsonl"):
        ct = r.get("canonical_trade_id")
        if ct:
            orders_by_ct[str(ct)].append(r)

    complete_ids: List[str] = list(gate.get("complete_trade_ids") or [])
    random.seed(args.seed)
    sample_n = min(args.trace_sample, len(complete_ids))
    sample_ids = random.sample(complete_ids, sample_n) if complete_ids and sample_n > 0 else []

    # exit row by tid
    exit_by_tid: Dict[str, dict] = {}
    for r in _iter_jsonl(logs / "exit_attribution.jsonl"):
        tid = r.get("trade_id")
        if tid and str(tid) in cohort:
            exit_by_tid[str(tid)] = r

    floor = int(args.open_ts_epoch)
    cohort_syms: Set[str] = set()
    for tid in cohort:
        m = TID_RE.match(tid)
        if m:
            cohort_syms.add(m.group(1).upper())

    entered_epoch_ge_floor = 0
    entered_for_cohort_symbol = 0
    for r in trade_intents_entered:
        ct = r.get("canonical_trade_id")
        tk = r.get("trade_key")
        if not ct or not tk:
            continue
        ct_s = str(ct)
        sym = str(r.get("symbol") or r.get("ticker") or "").upper()
        matched_sym = sym and sym in cohort_syms
        if not matched_sym and "|" in ct_s:
            prefix = ct_s.split("|", 1)[0].upper()
            matched_sym = prefix in cohort_syms
        if matched_sym:
            entered_for_cohort_symbol += 1
        if "|" in ct_s:
            try:
                ep = int(ct_s.split("|")[-1])
                if ep >= floor:
                    entered_epoch_ge_floor += 1
            except ValueError:
                pass

    # Non-vacuous: economic rows in era + evidence of entered telemetry (cohort-matched, epoch, or any complete strict chain).
    entered_signal_non_vacuous = max(
        entered_epoch_ge_floor,
        entered_for_cohort_symbol,
        1 if (gate.get("trades_complete") or 0) > 0 else 0,
    )

    traces: List[dict] = []
    for tid in sample_ids:
        rec = exit_by_tid.get(tid)
        sym = str(rec.get("symbol") or "").upper() if rec else ""
        uexit = unified_exit_by_tid.get(tid)
        uexit = uexit if (uexit and uexit.get("terminal_close")) else None
        tk = None
        if uexit:
            tk = uexit.get("trade_key") or uexit.get("canonical_trade_id")
            if tk:
                tk = str(tk)
        if not tk and rec:
            m = TID_RE.match(tid)
            if m:
                sk = normalize_side(rec.get("side") or rec.get("direction") or "LONG")
                try:
                    tk = build_trade_key(m.group(1), sk, m.group(2))
                except Exception:
                    tk = None
        join_key = str(tk or "")
        seed_ids = {join_key} if join_key else set()
        aliases = _expand_canonical_aliases(seed_ids, intent_to_fill)

        entry_decision_ok = any(
            str(r.get("symbol") or "").upper() == sym
            and (
                str(r.get("canonical_trade_id") or "") in aliases
                or str(r.get("trade_key") or "") in aliases
            )
            for r in trade_intents_entered
        )
        unified_ok = bool(aliases) and any(k in unified_entry for k in aliases)
        orders_ok = bool(aliases) and any(k in orders_by_ct for k in aliases)
        exit_int_ok = bool(aliases) and any(k in exit_intents_by_ct for k in aliases)

        traces.append(
            {
                "trade_id": tid,
                "exit_has_canonical_trade_id": bool(rec and rec.get("canonical_trade_id")),
                "exit_has_trade_key": bool(rec and rec.get("trade_key")),
                "trade_intent_entered_match": entry_decision_ok,
                "orders_rows_canonical_trade_id_present": orders_ok,
                "exit_intent_keyed_present": exit_int_ok,
                "unified_entry_attribution_present": unified_ok,
                "unified_exit_attribution_terminal_close": bool(uexit),
                "all_strict_legs_ok": bool(
                    entry_decision_ok
                    and orders_ok
                    and exit_int_ok
                    and unified_ok
                    and uexit
                ),
            }
        )

    trace_all_pass = bool(
        traces
        and all(t["all_strict_legs_ok"] and t["unified_exit_attribution_terminal_close"] for t in traces)
    )
    non_vacuous = econ_in_cohort > 0 and entered_signal_non_vacuous > 0
    out: Dict[str, Any] = {
        "open_ts_epoch": args.open_ts_epoch,
        "gate": {k: v for k, v in gate.items() if k not in ("complete_trade_ids", "strict_cohort_trade_ids")},
        "strict_cohort_economic_closes": econ_in_cohort,
        "strict_cohort_unified_terminal_closes": len(unified_term),
        "parity_exact": parity_exact,
        "missing_unified_terminal_trade_ids_sample": missing_unified,
        "entered_trade_intents_epoch_ge_floor": entered_epoch_ge_floor,
        "entered_trade_intents_for_cohort_symbol": entered_for_cohort_symbol,
        "entered_signal_non_vacuous": entered_signal_non_vacuous,
        "non_vacuous": non_vacuous,
        "trace_sample_size": len(traces),
        "trace_all_pass": trace_all_pass,
        "traces": traces,
        "cert_ok": bool(
            gate.get("LEARNING_STATUS") == "ARMED"
            and non_vacuous
            and parity_exact
            and trace_all_pass
            and len(traces) >= 15
        ),
    }

    js = json.dumps(out, indent=2)
    print(js)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(js, encoding="utf-8")

    return 0 if out["cert_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
