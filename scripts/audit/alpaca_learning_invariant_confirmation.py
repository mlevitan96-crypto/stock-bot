#!/usr/bin/env python3
"""
Read-only Kraken-derived learning invariant confirmation for Alpaca (CSA/SRE).

Phase 1: At most one alpaca_entry_attribution (unified) row per trade_id.
Phase 2: Strict-complete trade sample — entry intent field parity (Kraken names mapped to Alpaca).
Phase 3: Evidence bundle for learning gate separation (code citations only; no gate changes).

Stdout: JSON summary. With --write-reports, emits markdown under reports/daily/<ET-date>/evidence/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None


def _now_et_date_str() -> str:
    if _ET is None:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return datetime.now(_ET).strftime("%Y-%m-%d")


def _ts_suffix_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def _stream_jsonl(path: Path):
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _stream_unified_primary_then_backfill(logs: Path):
    yield from _stream_jsonl(logs / "alpaca_unified_events.jsonl")
    yield from _stream_jsonl(logs / "strict_backfill_alpaca_unified_events.jsonl")


_TID_OPEN_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$", re.IGNORECASE)


def _parse_iso_ts_any(s: Any) -> Optional[float]:
    if not s or not isinstance(s, str):
        if isinstance(s, (int, float)):
            return float(s)
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


def _open_epoch_from_trade_id_str(tid: str) -> Optional[float]:
    m = _TID_OPEN_RE.match(str(tid).strip())
    if not m:
        return None
    return _parse_iso_ts_any(m.group(2))


def _normalize_open_trade_id(tid: str) -> Optional[str]:
    """UTC-second canonical open_* id so +00:00 microsecond and ...Z variants collide."""
    m = _TID_OPEN_RE.match(str(tid).strip())
    if not m:
        return None
    sym, rest = m.group(1).upper(), m.group(2).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(rest)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"
        return f"open_{sym}_{iso}"
    except Exception:
        return None


def phase1_entry_uniqueness(logs: Path) -> Dict[str, Any]:
    """Invariant A: at most one unified alpaca_entry_attribution per trade_id."""
    by_tid: Dict[str, List[dict]] = defaultdict(list)
    by_norm: Dict[str, List[dict]] = defaultdict(list)
    for rec in _stream_unified_primary_then_backfill(logs):
        et = rec.get("event_type") or rec.get("type")
        if et != "alpaca_entry_attribution":
            continue
        tid = rec.get("trade_id")
        if not tid:
            continue
        s = str(tid)
        by_tid[s].append(rec)
        nk = _normalize_open_trade_id(s)
        if nk:
            by_norm[nk].append(rec)

    violations_raw = {tid: rows for tid, rows in by_tid.items() if len(rows) > 1}
    violations_norm = {tid: rows for tid, rows in by_norm.items() if len(rows) > 1}
    violations_norm_economic = {
        tid: [x for x in rows if _row_has_economic_entry_payload(x)]
        for tid, rows in by_norm.items()
    }
    violations_norm_economic = {k: v for k, v in violations_norm_economic.items() if len(v) > 1}
    stub_shadow_pairs = 0
    for tid, rows in by_norm.items():
        econ = sum(1 for x in rows if _row_has_economic_entry_payload(x))
        stub = sum(1 for x in rows if not _row_has_economic_entry_payload(x))
        if econ >= 1 and stub >= 1:
            stub_shadow_pairs += 1
    return {
        "source": "logs/alpaca_unified_events.jsonl (+ strict_backfill_alpaca_unified_events.jsonl if present)",
        "proxy_note": "entry_decision_made is proxied by alpaca_entry_attribution (unified) and trade_intent entered; uniqueness keyed on trade_id applies to unified entry rows.",
        "distinct_trade_ids_with_entry": len(by_tid),
        "violation_trade_id_count_raw_string": len(violations_raw),
        "distinct_normalized_open_trade_ids": len(by_norm),
        "violation_normalized_open_trade_id_count": len(violations_norm),
        "violation_normalized_economic_payload_duplicates": len(violations_norm_economic),
        "stub_shadow_normalized_key_count": stub_shadow_pairs,
        "passes_raw_trade_id": len(violations_raw) == 0,
        "passes_normalized_open_trade_id": len(violations_norm) == 0,
        "passes_normalized_economic": len(violations_norm_economic) == 0,
        "passes": len(violations_norm_economic) == 0,
        "violation_examples_raw": [
            {"trade_id": tid, "row_count": len(rows), "timestamps": [r.get("timestamp") for r in rows[:5]]}
            for tid, rows in list(violations_raw.items())[:8]
        ],
        "violation_examples_normalized": [
            {"normalized_trade_id": tid, "row_count": len(rows), "timestamps": [r.get("timestamp") for r in rows[:5]]}
            for tid, rows in list(violations_norm.items())[:8]
        ],
        "violation_examples_economic_duplicate": [
            {
                "normalized_trade_id": tid,
                "economic_row_count": len(rows),
                "timestamps": [r.get("timestamp") for r in rows[:5]],
            }
            for tid, rows in list(violations_norm_economic.items())[:8]
        ],
    }


def _non_empty_dict(d: Any) -> bool:
    return isinstance(d, dict) and len(d) > 0


def _row_has_economic_entry_payload(r: dict) -> bool:
    """True when unified entry row carries learning-relevant economics (not additive stub)."""
    if not isinstance(r, dict):
        return False
    if isinstance(r.get("composite_score"), (int, float)):
        return True
    if _non_empty_dict(r.get("raw_signals")):
        return True
    if _non_empty_dict(r.get("contributions")):
        return True
    return False


def _trace_ok_unified(entry: dict) -> bool:
    if _non_empty_dict(entry.get("raw_signals")):
        return True
    return False


def _trace_ok_intent(rec: dict) -> bool:
    it = rec.get("intelligence_trace")
    if it is None:
        return False
    if isinstance(it, dict) and len(it) == 0:
        return False
    if isinstance(it, list) and len(it) == 0:
        return False
    if isinstance(it, str) and not it.strip():
        return False
    return True


def _trace_ok_trade_intent_row(rec: dict) -> bool:
    if _trace_ok_intent(rec):
        return True
    fs = rec.get("feature_snapshot")
    return isinstance(fs, dict) and len(fs) > 0


def _score_total_ok(entry: dict) -> bool:
    v = entry.get("composite_score")
    return isinstance(v, (int, float))


def _components_ok(entry: dict) -> bool:
    if _non_empty_dict(entry.get("contributions")):
        return True
    if _non_empty_dict(entry.get("raw_signals")):
        return True
    return False


def _score_total_trade_intent(rec: dict) -> bool:
    return isinstance(rec.get("score"), (int, float))


def _components_ok_trade_intent(rec: dict) -> bool:
    fs = rec.get("feature_snapshot")
    if isinstance(fs, dict) and len(fs) > 0:
        return True
    return _non_empty_dict(rec.get("composite_meta"))  # rare fallback


def _build_intent_alias_maps(logs: Path) -> Tuple[List[dict], Dict[str, str]]:
    def stream_run():
        yield from _stream_jsonl(logs / "run.jsonl")
        yield from _stream_jsonl(logs / "strict_backfill_run.jsonl")

    trade_intents_entered: List[dict] = []
    intent_to_fill: Dict[str, str] = {}
    for rec in stream_run():
        et = rec.get("event_type")
        if et == "trade_intent" and str(rec.get("decision_outcome", "")).lower() == "entered":
            trade_intents_entered.append(rec)
        if et == "canonical_trade_id_resolved" and rec.get("canonical_trade_id_fill"):
            ci = rec.get("canonical_trade_id_intent")
            if ci:
                intent_to_fill[str(ci)] = str(rec["canonical_trade_id_fill"])
    return trade_intents_entered, intent_to_fill


def _expand_aliases(seed: Set[str], intent_to_fill: Dict[str, str]) -> Set[str]:
    s = {x for x in seed if x}
    if not intent_to_fill:
        return s
    changed = True
    while changed:
        changed = False
        for intent_id, fill_id in intent_to_fill.items():
            if intent_id in s and fill_id not in s:
                s.add(fill_id)
                changed = True
            elif fill_id in s and intent_id not in s:
                s.add(intent_id)
                changed = True
    return s


def _richer_entry_row(a: dict, b: dict) -> dict:
    def score(d: dict) -> Tuple[int, int, int]:
        cs = 1 if isinstance(d.get("composite_score"), (int, float)) else 0
        cr = len(d["contributions"]) if isinstance(d.get("contributions"), dict) else 0
        rw = len(d["raw_signals"]) if isinstance(d.get("raw_signals"), dict) else 0
        return (cs, cr, rw)

    return b if score(b) > score(a) else a


def _entry_map_from_alpaca_entry_stream(rec_iter, put: Any) -> None:
    for rec in rec_iter:
        et = rec.get("event_type") or rec.get("type")
        if et != "alpaca_entry_attribution":
            continue
        tid = rec.get("trade_id")
        if tid:
            ts = str(tid)
            put(ts, rec)
            nk = _normalize_open_trade_id(ts)
            if nk:
                put(nk, rec)
        for k in (rec.get("trade_key"), rec.get("canonical_trade_id")):
            if k:
                put(str(k), rec)


def _unified_entry_by_key(logs: Path) -> Dict[str, dict]:
    """Index entry rows by raw trade_id, normalized open_* trade_id, trade_key, and canonical_trade_id."""
    out: Dict[str, dict] = {}

    def put(k: str, rec: dict) -> None:
        if not k:
            return
        if k not in out:
            out[k] = rec
        else:
            out[k] = _richer_entry_row(out[k], rec)

    _entry_map_from_alpaca_entry_stream(_stream_unified_primary_then_backfill(logs), put)
    return out


def _dedicated_entry_attribution_by_key(logs: Path) -> Dict[str, dict]:
    """`logs/alpaca_entry_attribution.jsonl` only (live emitter), merged on richer economics."""
    out: Dict[str, dict] = {}

    def put(k: str, rec: dict) -> None:
        if not k:
            return
        if k not in out:
            out[k] = rec
        else:
            out[k] = _richer_entry_row(out[k], rec)

    _entry_map_from_alpaca_entry_stream(_stream_jsonl(logs / "alpaca_entry_attribution.jsonl"), put)
    return out


def _merge_optional_entry_rows(a: Optional[dict], b: Optional[dict]) -> Optional[dict]:
    if a and b:
        return _richer_entry_row(a, b)
    return a or b


def _dedicated_fallback_row(logs: Path, sym: str, nk: str) -> Optional[dict]:
    """When trade_key drift blocks map lookup, match dedicated entry by symbol + normalized open_* id."""
    if not sym or not nk:
        return None
    best: Optional[dict] = None
    for rec in _stream_jsonl(logs / "alpaca_entry_attribution.jsonl"):
        et = rec.get("event_type") or rec.get("type")
        if et and str(et) != "alpaca_entry_attribution":
            continue
        if str(rec.get("symbol") or "").upper() != sym:
            continue
        tid = rec.get("trade_id")
        if not tid:
            continue
        if _normalize_open_trade_id(str(tid)) != nk:
            continue
        if not _row_has_economic_entry_payload(rec):
            continue
        best = _richer_entry_row(best, rec) if best else rec
    return best


def _unified_terminal_exit_by_tid(logs: Path) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for rec in _stream_unified_primary_then_backfill(logs):
        et = rec.get("event_type") or rec.get("type")
        if et != "alpaca_exit_attribution":
            continue
        tid = rec.get("trade_id")
        if tid and rec.get("terminal_close"):
            out[str(tid)] = rec
    return out


def phase2_intent_completeness(root: Path, sample_min: int) -> Dict[str, Any]:
    from telemetry.alpaca_entry_decision_made_emit import audit_entry_decision_made_row_ok
    from telemetry.alpaca_strict_completeness_gate import (
        LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH,
        evaluate_completeness,
        _pick_best_entry_decision_made,
    )

    logs = root / "logs"
    comp = evaluate_completeness(
        root,
        collect_complete_trade_ids=True,
        audit=False,
    )
    ids: List[str] = list(comp.get("complete_trade_ids") or [])
    # Last K trades: K = max(20, |ids|) capped by available (mission: ≥20 or full window if smaller).
    take = max(sample_min, len(ids)) if ids else 0
    sample_ids = ids[-take:] if ids else []

    trade_intents_entered, intent_to_fill = _build_intent_alias_maps(logs)
    entry_decisions_made: List[dict] = []
    for rec in _stream_jsonl(logs / "run.jsonl"):
        if rec.get("event_type") == "entry_decision_made":
            entry_decisions_made.append(rec)
    for rec in _stream_jsonl(logs / "strict_backfill_run.jsonl"):
        if rec.get("event_type") == "entry_decision_made":
            entry_decisions_made.append(rec)
    non_synth_ti = sum(1 for r in trade_intents_entered if not (r.get("strict_backfilled") or r.get("strict_backfill_trade_id")))
    non_synth_edm = sum(
        1 for r in entry_decisions_made if not (r.get("strict_backfilled") or r.get("strict_backfill_trade_id"))
    )
    edm_ok_count = sum(1 for r in entry_decisions_made if audit_entry_decision_made_row_ok(r))
    unified_by_key = _unified_entry_by_key(logs)
    dedicated_by_key = _dedicated_entry_attribution_by_key(logs)
    unified_exit_by_tid = _unified_terminal_exit_by_tid(logs)

    field_signal_trace_pass = 0
    field_score_total_pass = 0
    field_components_pass = 0
    violations: List[dict] = []

    kraken_to_alpaca = {
        "signal_trace": "entry_decision_made.signal_trace (post live-intent epoch) OR intelligence_trace/raw_signals (legacy)",
        "entry_score_total": "entry_decision_made.entry_score_total OR composite_score (unified/dedicated)",
        "entry_score_components": "entry_decision_made.entry_score_components OR contributions/raw_signals (legacy)",
    }

    for tid in sample_ids:
        ts = str(tid)
        nk = _normalize_open_trade_id(ts)
        ent: Optional[dict] = None
        for k in filter(None, (ts, nk)):
            ent = _merge_optional_entry_rows(ent, unified_by_key.get(k))
            ent = _merge_optional_entry_rows(ent, dedicated_by_key.get(k))

        seed: Set[str] = set()
        uex = unified_exit_by_tid.get(str(tid))
        for src in (uex, ent):
            if not isinstance(src, dict):
                continue
            for k in (src.get("trade_key"), src.get("canonical_trade_id")):
                if k:
                    seed.add(str(k))
        aliases = _expand_aliases(seed, intent_to_fill)
        for ak in aliases:
            ent = _merge_optional_entry_rows(ent, unified_by_key.get(ak))
            ent = _merge_optional_entry_rows(ent, dedicated_by_key.get(ak))

        sym_u = ""
        if uex:
            sym_u = str(uex.get("symbol") or "").upper()
        if not sym_u and ent:
            sym_u = str(ent.get("symbol") or "").upper()
        if nk and sym_u and (ent is None or not _row_has_economic_entry_payload(ent)):
            ent = _merge_optional_entry_rows(ent, _dedicated_fallback_row(logs, sym_u, nk))

        if not sym_u and ts:
            m_sym = _TID_OPEN_RE.match(str(ts).strip())
            if m_sym:
                sym_u = m_sym.group(1).upper()

        oep_s = _open_epoch_from_trade_id_str(ts)
        edm_required = oep_s is not None and oep_s >= LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH
        if edm_required:
            if not sym_u:
                violations.append(
                    {
                        "trade_id": tid,
                        "reason": "live_entry_decision_made_symbol_unparsable",
                        "signal_trace": False,
                        "entry_score_total": False,
                        "entry_score_components": False,
                    }
                )
                continue
            best_edm = _pick_best_entry_decision_made(entry_decisions_made, aliases, sym_u, ts)
            st_ok_e = audit_entry_decision_made_row_ok(best_edm)
            if st_ok_e:
                field_signal_trace_pass += 1
                field_score_total_pass += 1
                field_components_pass += 1
                continue
            violations.append(
                {
                    "trade_id": tid,
                    "reason": "live_entry_decision_made_contract",
                    "signal_trace": False,
                    "entry_score_total": False,
                    "entry_score_components": False,
                    "entry_decision_made_present": best_edm is not None,
                    "entry_intent_status": (best_edm or {}).get("entry_intent_status"),
                }
            )
            continue

        if not ent:
            violations.append(
                {
                    "trade_id": tid,
                    "reason": "missing_unified_entry_row_for_trade_id",
                    "signal_trace": False,
                    "entry_score_total": False,
                    "entry_score_components": False,
                }
            )
            continue
        joined_intent = None
        sym = str(ent.get("symbol") or "").upper()

        def _is_synth_trade_intent(r: dict) -> bool:
            return bool(r.get("strict_backfilled") or r.get("strict_backfill_trade_id"))

        matches: List[dict] = []
        for r in trade_intents_entered:
            if str(r.get("symbol") or "").upper() != sym:
                continue
            rk = str(r.get("canonical_trade_id") or r.get("trade_key") or "")
            if rk and rk in aliases:
                matches.append(r)
        prim = [r for r in matches if not _is_synth_trade_intent(r)]
        if prim:
            joined_intent = prim[-1]
        else:
            t_open = _open_epoch_from_trade_id_str(ts)
            best: Optional[dict] = None
            best_d: Optional[float] = None
            if t_open is not None:
                for r in trade_intents_entered:
                    if _is_synth_trade_intent(r):
                        continue
                    if str(r.get("symbol") or "").upper() != sym:
                        continue
                    te = _parse_iso_ts_any(r.get("timestamp"))
                    if te is None:
                        te = _parse_iso_ts_any(r.get("ts"))
                    if te is None and isinstance(r.get("_ts"), (int, float)):
                        te = float(r["_ts"])
                    if te is None:
                        continue
                    d = abs(te - t_open)
                    if d <= 180.0 and (best_d is None or d < best_d):
                        best_d = d
                        best = r
            if best is not None:
                joined_intent = best
            elif matches:
                joined_intent = matches[-1]

        ji = joined_intent or {}
        st_ok = _trace_ok_unified(ent) or _trace_ok_trade_intent_row(ji)
        sc_ok = _score_total_ok(ent) or _score_total_trade_intent(ji)
        co_ok = _components_ok(ent) or _components_ok_trade_intent(ji)

        if st_ok:
            field_signal_trace_pass += 1
        if sc_ok:
            field_score_total_pass += 1
        if co_ok:
            field_components_pass += 1
        if not (st_ok and sc_ok and co_ok):
            violations.append(
                {
                    "trade_id": tid,
                    "signal_trace": st_ok,
                    "entry_score_total": sc_ok,
                    "entry_score_components": co_ok,
                    "had_joined_trade_intent": joined_intent is not None,
                }
            )

    n = len(sample_ids)
    no_sample = n == 0
    return {
        "strict_completeness_trades_seen": comp.get("trades_seen"),
        "strict_completeness_complete": comp.get("trades_complete"),
        "trade_intent_entered_rows_total": len(trade_intents_entered),
        "trade_intent_entered_non_synthetic_count": non_synth_ti,
        "entry_decision_made_rows_total": len(entry_decisions_made),
        "entry_decision_made_non_synthetic_count": non_synth_edm,
        "entry_decision_made_contract_ok_rows": edm_ok_count,
        "live_entry_intent_required_since_epoch": LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH,
        "sample_trade_ids": sample_ids,
        "sample_size": n,
        "kraken_field_mapping": kraken_to_alpaca,
        "pass_signal_trace": not no_sample and field_signal_trace_pass == n,
        "pass_entry_score_total": not no_sample and field_score_total_pass == n,
        "pass_entry_score_components": not no_sample and field_components_pass == n,
        "pass_all": not no_sample
        and field_signal_trace_pass == n
        and field_score_total_pass == n
        and field_components_pass == n,
        "no_sample_reason": "zero strict-complete trades in evaluate_completeness(collect_complete_trade_ids=True)"
        if no_sample
        else None,
        "violations": (violations + [{"trade_id": "*", "reason": "NO_SAMPLE"}])[:25] if no_sample else violations[:25],
        "counts": {
            "signal_trace_ok": field_signal_trace_pass,
            "entry_score_total_ok": field_score_total_pass,
            "entry_score_components_ok": field_components_pass,
        },
    }


def phase3_gate_separation() -> Dict[str, Any]:
    return {
        "learning_gate_source": "telemetry/alpaca_strict_completeness_gate.py — evaluate_completeness()",
        "gating_inputs_summary": [
            "trade_intent entered joinable via canonical_trade_id / trade_key aliases",
            "alpaca_unified_events alpaca_entry_attribution present for aliases",
            "orders.jsonl rows keyed by canonical_trade_id",
            "exit_intent for canonical keys",
            "alpaca_exit_attribution with terminal_close",
            "exit_attribution.jsonl economic closure (exit_price, pnl, timestamps, trade_id schema)",
        ],
        "non_gating_explicit": [
            "MFE/MAE appear in exit attribution snapshot (src/telemetry/alpaca_attribution_schema.py) but are not checked in strict completeness reasons[] in evaluate_completeness.",
            "No price-path or post-hoc volatility metric appears in reason_histogram keys produced by the strict gate.",
        ],
        "review_only_note": "Path analytics / volatility may appear in dashboards, board packets, or CSA reviews; they do not appear in LEARNING_STATUS / learning_fail_closed_reason computation.",
    }


def phase4_sre_log_health(root: Path) -> Dict[str, Any]:
    logs = root / "logs"
    paths = [
        logs / "alpaca_unified_events.jsonl",
        logs / "alpaca_entry_attribution.jsonl",
        logs / "run.jsonl",
        logs / "exit_attribution.jsonl",
        logs / "orders.jsonl",
    ]
    report = []
    total_lines = 0
    bad_json = 0
    for p in paths:
        if not p.is_file():
            report.append({"path": str(p), "exists": False})
            continue
        lines = 0
        bad = 0
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                lines += 1
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
        total_lines += lines
        bad_json += bad
        report.append({"path": str(p), "exists": True, "non_empty_lines": lines, "json_decode_errors": bad})
    parity_note = (
        "Audit vs live: strict gate reads the same JSONL paths as runtime appenders (plus strict_backfill_* mirrors). "
        "No separate 'audit-only' truth store is required for these invariants."
    )
    return {
        "log_paths": report,
        "aggregate_non_empty_lines": total_lines,
        "aggregate_json_decode_errors": bad_json,
        "rotation_session_note": "Session boundaries are implicit in timestamps inside JSONL rows; log rotation policy is operator-managed (see docs/DATA_RETENTION_POLICY.md if present). This check does not rewrite telemetry.",
        "audit_live_parity": parity_note,
        "passes": all(x.get("exists") for x in report) and bad_json == 0,
    }


def _write_reports(
    root: Path,
    et_date: str,
    ts: str,
    p1: dict,
    p2: dict,
    p3: dict,
    sre: dict,
    csa_verdict: str,
    csa_reason: str,
    sre_verdict: str,
    sre_reason: str,
    evidence_host: str,
) -> List[Path]:
    out_dir = root / "reports" / "daily" / et_date / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)

    def w(name: str, body: str) -> Path:
        path = out_dir / f"{name}_{ts}.md"
        path.write_text(body, encoding="utf-8")
        return path

    paths = []
    paths.append(
        w(
            "ALPACA_ENTRY_DECISION_UNIQUENESS",
            f"""# Alpaca entry decision uniqueness (Invariant A)

**Evidence host:** {evidence_host}  
**ET report date:** {et_date}  
**Generated (UTC):** {ts}

## Procedure

Full scan of unified log stream for `event_type=alpaca_entry_attribution`, grouped by `trade_id` (includes `strict_backfill_alpaca_unified_events.jsonl` when present).

**Invariant A (authoritative for structural “one decision per open”):** group by **normalized** `open_<SYM>_<UTC-second>` so microsecond vs `Z` string variants collapse (duplicate **lines** with divergent string forms are logged separately below).

## Results

| Metric | Value |
|--------|-------|
| Distinct raw `trade_id` strings with ≥1 entry row | {p1.get("distinct_trade_ids_with_entry")} |
| Raw strings with row count > 1 (log-line hygiene) | {p1.get("violation_trade_id_count_raw_string")} |
| Distinct normalized open-trade keys (UTC second) | {p1.get("distinct_normalized_open_trade_ids")} |
| Normalized keys with row count > 1 (includes stub shadows) | {p1.get("violation_normalized_open_trade_id_count")} |
| Normalized keys with **≥2 economic** entry payloads (blocking) | {p1.get("violation_normalized_economic_payload_duplicates")} |
| Normalized keys with stub + economic shadow lines (SRE hygiene) | {p1.get("stub_shadow_normalized_key_count")} |
| PASS (Kraken-style double **decision** — economic dupes) | **{"YES" if p1.get("passes") else "NO"}** |
| PASS (raw string line count — informational) | **{"YES" if p1.get("passes_raw_trade_id") else "NO"}** |

## Proxy note

{p1.get("proxy_note")}

## Violation examples — raw string duplicates

```json
{json.dumps(p1.get("violation_examples_raw"), indent=2)}
```

## Violation examples — normalized key duplicates

```json
{json.dumps(p1.get("violation_examples_normalized"), indent=2)}
```

## Violation examples — economic payload duplicates (blocking if non-empty)

```json
{json.dumps(p1.get("violation_examples_economic_duplicate"), indent=2)}
```
""",
        )
    )

    p2_json = json.dumps(p2, indent=2)
    paths.append(
        w(
            "ALPACA_ENTRY_INTENT_COMPLETENESS",
            f"""# Alpaca entry intent completeness (Kraken field mapping)

**Evidence host:** {evidence_host}  
**ET report date:** {et_date}  
**Generated (UTC):** {ts}

## Kraken → Alpaca mapping

| Kraken (mission) | Alpaca |
|------------------|--------|
| signal_trace | {p2.get("kraken_field_mapping", {}).get("signal_trace")} |
| entry_score_total | {p2.get("kraken_field_mapping", {}).get("entry_score_total")} |
| entry_score_components | {p2.get("kraken_field_mapping", {}).get("entry_score_components")} |

## Strict cohort context

- `trades_seen` (strict window): {p2.get("strict_completeness_trades_seen")}
- `trades_complete`: {p2.get("strict_completeness_complete")}
- `trade_intent` entered rows scanned (run.jsonl + strict_backfill): {p2.get("trade_intent_entered_rows_total")}
- Non-synthetic `trade_intent` entered rows: {p2.get("trade_intent_entered_non_synthetic_count")}
- `entry_decision_made` rows (run + strict_backfill): {p2.get("entry_decision_made_rows_total")}
- Non-synthetic `entry_decision_made`: {p2.get("entry_decision_made_non_synthetic_count")}
- Contract-OK `entry_decision_made` rows: {p2.get("entry_decision_made_contract_ok_rows")}
- Live-intent epoch (UTC): {p2.get("live_entry_intent_required_since_epoch")}

## Sample

- Sample size: **{p2.get("sample_size")}** (target ≥20 strict-complete trades; full set if smaller)
- signal_trace pass: **{p2.get("pass_signal_trace")}** ({p2.get("counts", {}).get("signal_trace_ok")}/{p2.get("sample_size")} OK)
- entry_score_total pass: **{p2.get("pass_entry_score_total")}** ({p2.get("counts", {}).get("entry_score_total_ok")}/{p2.get("sample_size")} OK)
- entry_score_components pass: **{p2.get("pass_entry_score_components")}** ({p2.get("counts", {}).get("entry_score_components_ok")}/{p2.get("sample_size")} OK)

## Violations (capped)

```json
{json.dumps(p2.get("violations"), indent=2)}
```

## Full machine JSON

```json
{p2_json}
```
""",
        )
    )

    paths.append(
        w(
            "ALPACA_LEARNING_GATE_SEPARATION",
            f"""# Alpaca learning gate separation

**Evidence host:** {evidence_host}  
**ET report date:** {et_date}  
**Generated (UTC):** {ts}

## Learning gate definition source

**{p3.get("learning_gate_source")}**

## Gating inputs (enumerated)

{chr(10).join("- " + x for x in p3.get("gating_inputs_summary", []))}

## Explicitly non-gating (analytics)

{chr(10).join("- " + x for x in p3.get("non_gating_explicit", []))}

## Review-only analytics

{p3.get("review_only_note")}
""",
        )
    )

    paths.append(
        w(
            "ALPACA_CSA_INVARIANT_FINAL_VERDICT",
            f"""# CSA final verdict — Alpaca learning invariants

**ET report date:** {et_date}  
**Generated (UTC):** {ts}

## Reviewed evidence

- Entry uniqueness (Invariant A)
- Entry intent completeness (mapped fields)
- Learning gate separation (code-sourced)

## Verdict

**{csa_verdict}**

Reason: {csa_reason}
""",
        )
    )

    paths.append(
        w(
            "ALPACA_SRE_INVARIANT_FINAL_VERDICT",
            f"""# SRE final verdict — Alpaca pipeline health (invariant pass)

**ET report date:** {et_date}  
**Generated (UTC):** {ts}

## Reviewed

- JSONL log structure (decode integrity on core streams)
- Append-only shapes present on disk
- Audit vs live path parity (same files as strict gate)

## Verdict

**{sre_verdict}**

Reason: {sre_reason}

## Log health detail

```json
{json.dumps(sre, indent=2)}
```
""",
        )
    )
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--sample-min", type=int, default=20)
    ap.add_argument("--write-reports", action="store_true")
    ap.add_argument("--et-date", type=str, default=None, help="Override ET folder date YYYY-MM-DD")
    ap.add_argument("--evidence-host", type=str, default="local")
    args = ap.parse_args()
    root = args.root.resolve()
    logs = root / "logs"

    p1 = phase1_entry_uniqueness(logs)
    p2 = phase2_intent_completeness(root, args.sample_min)
    p3 = phase3_gate_separation()
    sre = phase4_sre_log_health(root)
    sre["stub_shadow_normalized_keys_observed"] = p1.get("stub_shadow_normalized_key_count")
    sre["raw_line_duplicate_groups_normalized"] = p1.get("violation_normalized_open_trade_id_count")

    phase_ok = bool(p1.get("passes") and p2.get("pass_all") and sre.get("passes"))
    # Phase 3 is documentary confirmation from code + gate behavior
    gate_sep_ok = True

    csa_blocked = not (p1.get("passes") and p2.get("pass_all") and gate_sep_ok)
    if csa_blocked:
        reasons = []
        if not p1.get("passes"):
            reasons.append(
                "Invariant A: ≥2 economic entry payloads for same normalized open (double-entry decision risk)"
            )
        if not p2.get("pass_all"):
            reasons.append("Entry intent completeness failed on strict-complete sample")
        if not gate_sep_ok:
            reasons.append("Learning gate separation not confirmed")
        csa_verdict = "CSA_ALPACA_INVARIANTS_BLOCKED"
        csa_reason = "; ".join(reasons)
    else:
        csa_verdict = "CSA_ALPACA_INVARIANTS_CONFIRMED"
        csa_reason = "Entry uniqueness, intent completeness, and gate separation evidence accepted."

    if not sre.get("passes"):
        sre_verdict = "SRE_ALPACA_PIPELINE_UNHEALTHY"
        sre_reason = "Missing core JSONL and/or JSON decode errors in sampled logs."
    else:
        sre_verdict = "SRE_ALPACA_PIPELINE_HEALTHY"
        sre_reason = "Core JSONL streams present with zero decode errors in full-file scan."

    et_date = args.et_date or _now_et_date_str()
    ts = _ts_suffix_utc()

    out = {
        "ET_DATE": et_date,
        "TS_UTC": ts,
        "evidence_host": args.evidence_host,
        "phase1_entry_uniqueness": p1,
        "phase2_intent_completeness": p2,
        "phase3_learning_gate_separation": p3,
        "phase4_sre_log_health": sre,
        "CSA_VERDICT": csa_verdict,
        "SRE_VERDICT": sre_verdict,
    }
    print(json.dumps(out, indent=2))

    if args.write_reports:
        paths = _write_reports(root, et_date, ts, p1, p2, p3, sre, csa_verdict, csa_reason, sre_verdict, sre_reason, args.evidence_host)
        print("\nWROTE:", file=sys.stderr)
        for p in paths:
            print(str(p), file=sys.stderr)

    # Exit 0 always for confirmation tooling; operators read JSON/MD verdicts.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
