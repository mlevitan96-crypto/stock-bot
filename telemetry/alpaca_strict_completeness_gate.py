"""
Strict completeness (A) evaluation for Alpaca logs (read-only). Used by audits and pytest.

AUTHORITATIVE_JOIN_KEY (Alpaca strict joins):
  Per closed trade, use ``trade_key`` from unified exit (or derived from
  ``open_{SYM}_{entry_ts}`` + exit side). Intent-time vs fill-time IDs are linked via
  ``canonical_trade_id_resolved`` (intent <-> fill) and expanded as an undirected alias
  set for all joins. Per-symbol ``latest fill`` is not used as the key (multi-trade
  collision on the same ticker).
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side

try:
    from telemetry.alpaca_entry_decision_made_emit import audit_entry_decision_made_row_ok as _audit_edm_ok
except Exception:  # pragma: no cover - optional during bootstrap
    _audit_edm_ok = None  # type: ignore

# Forward-only strict learning era (UTC epoch). Used when ``open_ts_epoch`` is set: cohort
# membership requires position **open** time parsed from ``trade_id`` (open_<SYM>_<ISO>) >= this floor.
STRICT_EPOCH_START = 1774458080.0  # 2026-03-25T17:01:20Z

# Trades opened on/after this UTC instant must have a LIVE `entry_decision_made` row (OK, non-synthetic).
LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH = datetime(2026, 3, 28, 0, 0, tzinfo=timezone.utc).timestamp()

AUTHORITATIVE_JOIN_KEY_RULE = (
    "Per closed trade: trade_key from unified alpaca_exit_attribution (or derived from "
    "open_{SYM}_{entry_ts} trade_id + exit row side). Expand aliases using undirected "
    "canonical_trade_id_intent <-> canonical_trade_id_fill edges from run.jsonl so "
    "trade_intent(entered) keyed at intent-time still joins to fill-time keys. "
    "Do not use a single per-symbol 'latest fill' as the join key (multiple positions "
    "per symbol would collide)."
)

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None


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


def _stream_jsonl_primary_then_backfill(logs: Path, basename: str):
    """Primary ``logs/{basename}`` then additive ``logs/strict_backfill_{basename}`` (no primary mutation)."""
    yield from _stream_jsonl(logs / basename)
    bf = logs / f"strict_backfill_{basename}"
    yield from _stream_jsonl(bf)


def market_open_epoch_today_et() -> Optional[float]:
    if _ET is None:
        return None
    now_et = datetime.now(_ET)
    d = now_et.date()
    open_et = datetime(d.year, d.month, d.day, 9, 30, tzinfo=_ET)
    return open_et.timestamp()


def _open_epoch_from_trade_id(tid: str, tid_re: Any) -> Optional[float]:
    """Parse open instant from trade_id ``open_<SYM>_<ISO8601>`` suffix."""
    m = tid_re.match(str(tid).strip())
    if not m:
        return None
    return _parse_iso_ts(m.group(2))


def _pick_best_entry_decision_made(
    entry_rows: List[dict],
    aliases: Set[str],
    sym: str,
    trade_tid: str,
) -> Optional[dict]:
    from telemetry.alpaca_entry_decision_made_emit import score_entry_decision_made_row

    cands: List[dict] = []
    for er in entry_rows:
        if str(er.get("symbol") or "").upper() != sym:
            continue
        if str(er.get("trade_id") or "") == trade_tid:
            cands.append(er)
            continue
        for kk in (er.get("canonical_trade_id"), er.get("trade_key")):
            if kk and str(kk) in aliases:
                cands.append(er)
                break
    if not cands:
        return None
    return max(cands, key=score_entry_decision_made_row)


def _expand_canonical_aliases(seed_ids: Set[str], intent_to_fill: Dict[str, str]) -> Set[str]:
    """Closure of seed IDs with undirected intent<->fill edges from canonical_trade_id_resolved."""
    s = {x for x in seed_ids if x}
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


def evaluate_completeness(
    root: Path,
    open_ts_epoch: Optional[float] = None,
    *,
    audit: bool = False,
    forward_since_epoch: Optional[float] = None,
    exit_ts_max_epoch: Optional[float] = None,
    collect_complete_trade_ids: bool = False,
    collect_strict_cohort_trade_ids: bool = False,
) -> Dict[str, Any]:
    """Evaluate strict completeness since market open (ET today) or custom open_ts_epoch (UTC).

    If ``forward_since_epoch`` is set (UTC epoch), each closed trade is split by **position open**
    time parsed from ``trade_id`` (``open_<SYM>_<ISO>``): ``>= forward_since_epoch`` → forward cohort;
    otherwise legacy. Counters ``forward_*`` and ``legacy_*`` are populated (global ``trades_*`` unchanged).

    If ``exit_ts_max_epoch`` is set, exclude ``exit_attribution`` rows whose exit timestamp is **strictly after**
    this UTC epoch (bounded window ending at exchange close).
    """
    root = root.resolve()
    logs = root / "logs"
    exit_path = logs / "exit_attribution.jsonl"
    run_path = logs / "run.jsonl"
    unified_path = logs / "alpaca_unified_events.jsonl"
    orders_path = logs / "orders.jsonl"
    main_py = root / "main.py"

    open_ts = open_ts_epoch if open_ts_epoch is not None else market_open_epoch_today_et()

    precheck: List[str] = []
    if not exit_path.is_file():
        precheck.append("missing_exit_attribution_jsonl")
    if not unified_path.is_file():
        precheck.append("missing_alpaca_unified_events_jsonl")
    if not orders_path.is_file():
        precheck.append("missing_orders_jsonl")
    if not run_path.is_file():
        precheck.append("missing_run_jsonl")

    unified_entry: Dict[str, dict] = {}
    unified_exit_by_tid: Dict[str, dict] = {}
    for rec in _stream_jsonl_primary_then_backfill(logs, "alpaca_unified_events.jsonl"):
        et = rec.get("event_type") or rec.get("type")
        if et == "alpaca_entry_attribution":
            for k in (rec.get("trade_key"), rec.get("canonical_trade_id")):
                if k:
                    unified_entry[str(k)] = rec
        elif et == "alpaca_exit_attribution":
            tid = rec.get("trade_id")
            if tid and rec.get("terminal_close"):
                unified_exit_by_tid[str(tid)] = rec

    orders_by_ct: Dict[str, List[dict]] = {}
    for rec in _stream_jsonl_primary_then_backfill(logs, "orders.jsonl"):
        ct = rec.get("canonical_trade_id")
        if ct:
            orders_by_ct.setdefault(str(ct), []).append(rec)

    exit_intents_by_ct: Dict[str, List[dict]] = defaultdict(list)
    trade_intents_entered: List[dict] = []
    entry_decisions_made: List[dict] = []
    intent_to_fill: Dict[str, str] = {}
    for rec in _stream_jsonl_primary_then_backfill(logs, "run.jsonl"):
        et = rec.get("event_type")
        if et == "exit_intent":
            for _ek in (rec.get("canonical_trade_id"), rec.get("trade_key")):
                if _ek:
                    exit_intents_by_ct[str(_ek)].append(rec)
        if et == "trade_intent" and str(rec.get("decision_outcome", "")).lower() == "entered":
            trade_intents_entered.append(rec)
        if et == "entry_decision_made":
            entry_decisions_made.append(rec)
        if et == "canonical_trade_id_resolved" and rec.get("canonical_trade_id_fill"):
            cf = str(rec["canonical_trade_id_fill"])
            ci = rec.get("canonical_trade_id_intent")
            if ci:
                intent_to_fill[str(ci)] = cf

    code_structural = False
    if main_py.is_file():
        try:
            txt = main_py.read_text(encoding="utf-8", errors="replace")
            entered_branch = 'elif (decision_outcome or "").lower() == "entered":'
            if "_ctid = None" in txt and '"canonical_trade_id": _ctid' in txt and entered_branch not in txt:
                code_structural = True
        except Exception:
            pass

    TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")
    closed: List[tuple] = []
    for rec in _stream_jsonl(exit_path):
        ex_ts = _parse_iso_ts(rec.get("timestamp"))
        if open_ts is not None and (ex_ts is None or ex_ts < open_ts):
            continue
        if exit_ts_max_epoch is not None and ex_ts is not None and ex_ts > float(exit_ts_max_epoch):
            continue
        tid = rec.get("trade_id")
        sym = rec.get("symbol")
        ent = rec.get("entry_timestamp")
        if not tid or not sym:
            continue
        closed.append((str(tid), str(sym).upper(), str(ent or ""), rec))

    # Entry-based strict cohort: when exit-window floor is set, exclude pre-era opens (close can be post-era).
    strict_cohort_exclusion_reasons: Counter = Counter()
    excluded_trade_ids_capped: List[str] = []
    strict_cohort_excluded_preera_open_count = 0
    closed_cohort: List[tuple] = []
    entry_era_floor: Optional[float] = open_ts if open_ts is not None else None
    for row in closed:
        tid, sym, ent_iso, rec = row[0], row[1], row[2], row[3]
        if entry_era_floor is None:
            closed_cohort.append(row)
            continue
        oep = _open_epoch_from_trade_id(tid, TID_RE)
        if oep is None:
            strict_cohort_exclusion_reasons["OPEN_TIME_UNPARSABLE_FROM_TRADE_ID"] += 1
            if len(excluded_trade_ids_capped) < 20:
                excluded_trade_ids_capped.append(str(tid))
            continue
        if oep < entry_era_floor:
            strict_cohort_exclusion_reasons["PREERA_OPEN"] += 1
            strict_cohort_excluded_preera_open_count += 1
            if len(excluded_trade_ids_capped) < 20:
                excluded_trade_ids_capped.append(str(tid))
            continue
        closed_cohort.append(row)

    closed = closed_cohort

    reason_hist: Counter = Counter()
    incomplete_ex: List[dict] = []
    incomplete_ids_by_reason: Dict[str, List[str]] = defaultdict(list)
    chain_matrices_sample: List[dict] = []
    chain_matrices_complete_sample: List[dict] = []
    complete = 0
    complete_trade_ids: List[str] = []
    strict_cohort_trade_ids: List[str] = []

    fwd_seen = fwd_cmp = fwd_inc = 0
    leg_seen = leg_cmp = leg_inc = 0

    for tid, sym, ent_iso, rec in closed:
        if collect_strict_cohort_trade_ids and len(strict_cohort_trade_ids) < 5000:
            strict_cohort_trade_ids.append(tid)
        reasons: List[str] = []
        uexit = unified_exit_by_tid.get(tid)
        uexit = uexit if (uexit and uexit.get("terminal_close")) else None
        tk: Optional[str] = None
        if uexit:
            tk = uexit.get("trade_key") or uexit.get("canonical_trade_id")
            if tk:
                tk = str(tk)
        if not tk:
            m = TID_RE.match(tid)
            if m:
                gsym, grest = m.group(1), m.group(2)
                _sk = normalize_side(rec.get("side") or rec.get("direction") or "LONG")
                try:
                    tk = build_trade_key(gsym, _sk, grest)
                except Exception:
                    tk = None
        join_key = str(tk or "")
        seed_ids: Set[str] = set()
        if join_key:
            seed_ids.add(join_key)
        aliases = _expand_canonical_aliases(seed_ids, intent_to_fill)

        oep_trade = _open_epoch_from_trade_id(tid, TID_RE)
        if (
            _audit_edm_ok is not None
            and oep_trade is not None
            and oep_trade >= LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH
        ):
            best_edm = _pick_best_entry_decision_made(entry_decisions_made, aliases, sym, tid)
            if not _audit_edm_ok(best_edm):
                reasons.append("live_entry_decision_made_missing_or_blocked")

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

        if not tk:
            reasons.append("cannot_derive_trade_key")
        else:
            if not aliases:
                reasons.append("cannot_resolve_join_aliases")
            if not entry_decision_ok:
                reasons.append("entry_decision_not_joinable_by_canonical_trade_id")
            if not unified_ok:
                reasons.append("missing_unified_entry_attribution")
            if not orders_ok:
                reasons.append("no_orders_rows_with_canonical_trade_id")
            if not exit_int_ok:
                reasons.append("missing_exit_intent_for_canonical_trade_id")
        if not uexit:
            reasons.append("missing_unified_exit_attribution_terminal")
        ep = rec.get("exit_price")
        if ep is None or (isinstance(ep, (int, float)) and float(ep) <= 0):
            reasons.append("exit_attribution_missing_positive_exit_price")
        if rec.get("pnl") is None:
            reasons.append("missing_pnl_economic_closure")
        t_entry = _parse_iso_ts(ent_iso)
        t_exit = _parse_iso_ts(rec.get("timestamp"))
        if t_entry and t_exit and t_exit < t_entry:
            reasons.append("temporal_exit_before_entry")
        if not TID_RE.match(tid):
            reasons.append("trade_id_schema_unexpected")

        oep_for_split = _open_epoch_from_trade_id(tid, TID_RE)
        is_forward_cohort = False
        if forward_since_epoch is not None and oep_for_split is not None:
            is_forward_cohort = oep_for_split >= float(forward_since_epoch)

        if reasons:
            for r in reasons:
                reason_hist[r] += 1
                ids_l = incomplete_ids_by_reason[r]
                if len(ids_l) < 10:
                    ids_l.append(tid)
            if len(incomplete_ex) < 8:
                incomplete_ex.append(
                    {
                        "trade_id": tid,
                        "trade_key": tk,
                        "authoritative_join_key": join_key,
                        "reasons": reasons,
                    }
                )
            if audit and len(chain_matrices_sample) < 5:
                chain_matrices_sample.append(
                    {
                        "trade_id": tid,
                        "symbol": sym,
                        "forward_cohort": is_forward_cohort,
                        "authoritative_join_key": join_key,
                        "trade_key_from_exit": tk,
                        "alias_sample": sorted(aliases)[:16],
                        "matrix": {
                            "trade_intent_entered_present": entry_decision_ok,
                            "unified_entry_attribution_present": unified_ok,
                            "orders_rows_canonical_trade_id_present": orders_ok,
                            "exit_intent_keyed_present": exit_int_ok,
                            "unified_exit_attribution_terminal_close": bool(
                                uexit and uexit.get("terminal_close")
                            ),
                            "exit_attribution_jsonl_row": True,
                        },
                        "reasons": list(reasons),
                    }
                )
            if forward_since_epoch is not None:
                if is_forward_cohort:
                    fwd_seen += 1
                    fwd_inc += 1
                else:
                    leg_seen += 1
                    leg_inc += 1
        else:
            complete += 1
            if collect_complete_trade_ids and len(complete_trade_ids) < 50_000:
                complete_trade_ids.append(tid)
            if audit and len(chain_matrices_complete_sample) < 3:
                chain_matrices_complete_sample.append(
                    {
                        "trade_id": tid,
                        "symbol": sym,
                        "forward_cohort": is_forward_cohort,
                        "authoritative_join_key": join_key,
                        "trade_key_from_exit": tk,
                        "alias_sample": sorted(aliases)[:16],
                        "matrix": {
                            "trade_intent_entered_present": entry_decision_ok,
                            "unified_entry_attribution_present": unified_ok,
                            "orders_rows_canonical_trade_id_present": orders_ok,
                            "exit_intent_keyed_present": exit_int_ok,
                            "unified_exit_attribution_terminal_close": bool(
                                uexit and uexit.get("terminal_close")
                            ),
                            "exit_attribution_jsonl_row": True,
                        },
                        "reasons": [],
                    }
                )
            if forward_since_epoch is not None:
                if is_forward_cohort:
                    fwd_seen += 1
                    fwd_cmp += 1
                else:
                    leg_seen += 1
                    leg_cmp += 1

    structural = code_structural or any("STRUCTURAL" in str(x) for x in precheck)
    vacuous_zero_trades = len(closed) == 0
    blocked = bool(precheck) or vacuous_zero_trades or (len(closed) - complete) > 0 or structural

    if not blocked:
        learning_fail_closed_reason = None
        learning_status = "ARMED"
    else:
        learning_status = "BLOCKED"
        if precheck:
            learning_fail_closed_reason = "precheck:" + ",".join(precheck)
        elif structural:
            learning_fail_closed_reason = "structural_trade_intent_path"
        elif vacuous_zero_trades:
            learning_fail_closed_reason = "NO_POST_DEPLOY_PROOF_YET"
        else:
            learning_fail_closed_reason = "incomplete_trade_chain"

    forward_perfect = (
        forward_since_epoch is not None and fwd_seen > 0 and fwd_inc == 0 and not precheck and not structural
    )
    forward_vacuous = forward_since_epoch is not None and fwd_seen == 0

    out: Dict[str, Any] = {
        "ROOT": str(root),
        "OPEN_TS_UTC_EPOCH": open_ts,
        "EXIT_TS_UTC_EPOCH_MAX": exit_ts_max_epoch,
        "FORWARD_SINCE_UTC_EPOCH": forward_since_epoch,
        "STRICT_EPOCH_START": STRICT_EPOCH_START,
        "strict_cohort_entry_era_floor_applied": entry_era_floor is not None,
        "strict_cohort_excluded_preera_open_count": strict_cohort_excluded_preera_open_count,
        "strict_cohort_exclusion_reasons": dict(strict_cohort_exclusion_reasons),
        "excluded_trade_ids_capped": list(excluded_trade_ids_capped),
        "precheck": precheck,
        "trades_seen": len(closed),
        "trades_complete": complete,
        "trades_incomplete": len(closed) - complete,
        "reason_histogram": dict(reason_hist),
        "incomplete_examples": incomplete_ex,
        "code_structural_trade_intent_no_canonical_on_entered": code_structural,
        "LEARNING_STATUS": learning_status,
        "learning_fail_closed_reason": learning_fail_closed_reason,
        "AUTHORITATIVE_JOIN_KEY_RULE": AUTHORITATIVE_JOIN_KEY_RULE,
        "legacy_trades_seen": leg_seen if forward_since_epoch is not None else None,
        "legacy_trades_complete": leg_cmp if forward_since_epoch is not None else None,
        "legacy_trades_incomplete": leg_inc if forward_since_epoch is not None else None,
        "forward_trades_seen": fwd_seen if forward_since_epoch is not None else None,
        "forward_trades_complete": fwd_cmp if forward_since_epoch is not None else None,
        "forward_trades_incomplete": fwd_inc if forward_since_epoch is not None else None,
        "FORWARD_CHAIN_PERFECT": forward_perfect,
        "FORWARD_COHORT_VACUOUS": forward_vacuous,
        "LEGACY_DEBT_QUARANTINED_NOTE": (
            "Legacy cohort (open < FORWARD_SINCE_UTC_EPOCH) may remain incomplete; "
            "do not use for forward causal certification."
            if forward_since_epoch is not None
            else None
        ),
    }
    if audit:
        out["incomplete_trade_ids_by_reason"] = {k: list(v) for k, v in incomplete_ids_by_reason.items()}
        out["chain_matrices_sample"] = chain_matrices_sample
        out["chain_matrices_complete_sample"] = chain_matrices_complete_sample
    if collect_complete_trade_ids:
        out["complete_trade_ids"] = complete_trade_ids
    if collect_strict_cohort_trade_ids:
        out["strict_cohort_trade_ids"] = strict_cohort_trade_ids
    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Alpaca strict completeness gate (local root)")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--open-ts-epoch",
        type=float,
        default=None,
        help="UTC epoch floor for exit_attribution rows (post-deploy windows)",
    )
    ap.add_argument(
        "--audit",
        action="store_true",
        help="Include incomplete_trade_ids_by_reason and chain_matrices_sample",
    )
    ap.add_argument(
        "--forward-since-epoch",
        type=float,
        default=None,
        help="UTC epoch: split forward vs legacy by position open time from trade_id",
    )
    ap.add_argument(
        "--exit-ts-max-epoch",
        type=float,
        default=None,
        help="UTC epoch: exclude exit_attribution rows with exit timestamp after this instant",
    )
    ap.add_argument(
        "--forward-exit-zero",
        action="store_true",
        help="Exit 0 iff forward cohort non-vacuous and forward_trades_incomplete==0 (ignores global LEARNING_STATUS)",
    )
    args = ap.parse_args()
    r = evaluate_completeness(
        args.root,
        open_ts_epoch=args.open_ts_epoch,
        audit=args.audit,
        forward_since_epoch=args.forward_since_epoch,
        exit_ts_max_epoch=args.exit_ts_max_epoch,
    )
    print(json.dumps(r, indent=2))
    if args.forward_exit_zero and args.forward_since_epoch is not None:
        if r.get("FORWARD_COHORT_VACUOUS"):
            return 1
        return 0 if r.get("forward_trades_incomplete") == 0 else 1
    return 0 if r["LEARNING_STATUS"] == "ARMED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
