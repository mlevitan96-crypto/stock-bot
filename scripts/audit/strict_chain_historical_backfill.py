#!/usr/bin/env python3
"""
Additive repair for strict completeness: append strict_backfill_* JSONL rows from exit_attribution truth.

Reads closed trades from logs/exit_attribution.jsonl, derives trade_key / canonical_trade_id,
and appends (idempotent per trade_id):
  - logs/strict_backfill_run.jsonl       — trade_intent(entered), exit_intent, entry_decision_made, canonical_trade_id_resolved
  - logs/strict_backfill_orders.jsonl   — order row with canonical_trade_id
  - emit_entry_attribution (unified + entry mirror) when missing primary unified terminal for that trade_id

Does NOT change strategy, orders, or execution. Safe to re-run; skips trade_ids already present in backfill run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")


def _parse_ts(s: Any) -> Optional[float]:
    if not s:
        return None
    try:
        t = str(s).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _load_jsonl_event_types(path: Path, types: Set[str], tail_mb: int = 80) -> Dict[str, Set[str]]:
    """Map event_type -> set of trade_ids seen (for entry_decision_made uses trade_id field)."""
    out: Dict[str, Set[str]] = {t: set() for t in types}
    if not path.is_file():
        return out
    try:
        size = path.stat().st_size
        start = max(0, size - tail_mb * 1024 * 1024)
        with path.open("rb") as f:
            f.seek(start)
            if start > 0:
                f.readline()
            for raw in f:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                et = o.get("event_type")
                tid = o.get("trade_id")
                if et in out and tid:
                    out[et].add(str(tid))
        for t in types:
            out.setdefault(t, set())
    except OSError:
        pass
    return out


def _canonical_trade_ids_seen_in_orders(logs: Path, ord_bf: Path, *, tail_mb: int = 48) -> Set[str]:
    """
    Union of canonical_trade_id values from strict_backfill_orders + tail of orders.jsonl.
    Used to detect live run_intent/EDM without a matching order row (restart / TWAP / logger gap).
    """
    out: Set[str] = set()
    for path in (ord_bf,):
        if not path.is_file():
            continue
        try:
            for line in path.open(encoding="utf-8", errors="replace"):
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                c = o.get("canonical_trade_id")
                if c:
                    out.add(str(c))
        except OSError:
            pass
    primary = logs / "orders.jsonl"
    if not primary.is_file():
        return out
    try:
        size = primary.stat().st_size
        start = max(0, size - tail_mb * 1024 * 1024)
        with primary.open("rb") as fh:
            fh.seek(start)
            if start > 0:
                fh.readline()
            for raw in fh:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                c = o.get("canonical_trade_id")
                if c:
                    out.add(str(c))
    except OSError:
        pass
    return out


def _iter_jsonl_tail_dicts(path: Path, *, tail_mb: int) -> Iterator[dict]:
    if not path.is_file():
        return
    try:
        size = path.stat().st_size
        start = max(0, size - tail_mb * 1024 * 1024)
        with path.open("rb") as fh:
            fh.seek(start)
            if start > 0:
                fh.readline()
            for raw in fh:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def _load_unified_entry_canonical_by_trade_id(logs: Path, *, tail_mb: int = 512) -> Dict[str, str]:
    """
    Last-seen ``canonical_trade_id`` (or ``trade_key``) per ``trade_id`` on
    ``alpaca_entry_attribution``, in gate order: primary unified then strict backfill unified.

    Uses a large tail because ``alpaca_unified_events.jsonl`` can grow quickly; a small tail
    drops same-day ``alpaca_entry_attribution`` rows and breaks displacement intent→fill bridges.
    """
    out: Dict[str, str] = {}
    for basename in ("alpaca_unified_events.jsonl", "strict_backfill_alpaca_unified_events.jsonl"):
        for o in _iter_jsonl_tail_dicts(logs / basename, tail_mb=tail_mb):
            if o.get("event_type") != "alpaca_entry_attribution":
                continue
            tid = o.get("trade_id")
            if not tid:
                continue
            c = o.get("canonical_trade_id") or o.get("trade_key")
            if c:
                out[str(tid)] = str(c)
    return out


def _load_canonical_trade_id_resolved_pairs(
    logs: Path, run_bf: Path, *, tail_mb_run: int = 96
) -> Set[Tuple[str, str]]:
    """(intent_canonical, fill_canonical) edges already present (idempotency)."""
    pairs: Set[Tuple[str, str]] = set()
    if run_bf.is_file():
        try:
            for line in run_bf.open(encoding="utf-8", errors="replace"):
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if o.get("event_type") != "canonical_trade_id_resolved":
                    continue
                ci = o.get("canonical_trade_id_intent")
                cf = o.get("canonical_trade_id_fill")
                if ci and cf:
                    pairs.add((str(ci), str(cf)))
        except OSError:
            pass
    for o in _iter_jsonl_tail_dicts(logs / "run.jsonl", tail_mb=tail_mb_run):
        if o.get("event_type") != "canonical_trade_id_resolved":
            continue
        ci = o.get("canonical_trade_id_intent")
        cf = o.get("canonical_trade_id_fill")
        if ci and cf:
            pairs.add((str(ci), str(cf)))
    return pairs


def _apply_intent_fill_alias_backfills(
    exit_path: Path,
    run_bf: Path,
    unified_entry_ct: Dict[str, str],
    orders_ct: Set[str],
    resolver_pairs: Set[Tuple[str, str]],
    *,
    dry_run: bool,
    now_iso: str,
) -> int:
    """
    Strict gate expands aliases via ``canonical_trade_id_resolved`` (undirected).
    Bridge epoch / displacement rows can log unified entry under one canonical and
    exit+orders under another; without an edge, ``missing_unified_entry_attribution`` fires.
    """
    from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side

    written = 0
    with exit_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ex = json.loads(line)
            except json.JSONDecodeError:
                continue
            tid = ex.get("trade_id")
            sym = (ex.get("symbol") or "").strip().upper()
            if not tid or not sym:
                continue
            m = TID_RE.match(str(tid))
            if not m:
                continue
            ts_rest = m.group(2)
            iso = ts_rest if "T" in ts_rest else ts_rest.replace(" ", "T")
            if iso.endswith("Z"):
                iso = iso[:-1] + "+00:00"
            side_raw = ex.get("side") or ex.get("direction") or "long"
            sk = normalize_side(side_raw)
            try:
                tk = ex.get("trade_key") or build_trade_key(sym, sk, iso)
            except Exception:
                continue
            tk = str(tk)
            ct = str(ex.get("canonical_trade_id") or tk)
            if ct not in orders_ct:
                continue
            uc = unified_entry_ct.get(str(tid))
            if not uc or str(uc) == str(ct):
                continue
            pair = (str(uc), str(ct))
            if pair in resolver_pairs:
                continue
            if dry_run:
                written += 1
                continue
            row = {
                "ts": now_iso,
                "event_type": "canonical_trade_id_resolved",
                "symbol": sym,
                "canonical_trade_id_intent": str(uc),
                "canonical_trade_id_fill": str(ct),
                "trade_id": str(tid),
                "action": "strict_chain_intent_fill_alias_backfill",
            }
            run_bf.parent.mkdir(parents=True, exist_ok=True)
            with run_bf.open("a", encoding="utf-8") as out:
                out.write(json.dumps(row, default=str) + "\n")
            resolver_pairs.add(pair)
            written += 1
    return written


def _components_from_exit(ex: dict) -> Dict[str, float]:
    raw = ex.get("components") if isinstance(ex.get("components"), dict) else {}
    out: Dict[str, float] = {}
    for k, v in raw.items():
        try:
            if isinstance(v, (int, float)):
                out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    if not out and isinstance(ex.get("v2_exit_components"), dict):
        for k, v in ex["v2_exit_components"].items():
            try:
                out[str(k)] = float(v) if isinstance(v, (int, float)) else float(v)
            except (TypeError, ValueError):
                continue
    if not out:
        sc = ex.get("score") or ex.get("entry_score")
        try:
            if sc is not None:
                out["_entry_score_proxy"] = float(sc)
        except (TypeError, ValueError):
            pass
    return out


def apply_strict_chain_backfill(
    root: Path,
    *,
    dry_run: bool = False,
    max_trades: int = 5000,
) -> Dict[str, Any]:
    """
    Idempotent strict_backfill_* repair from exit_attribution.jsonl.
    Safe for periodic / in-process calls (e.g. integrity cycle before strict gate).
    Returns metadata dict; does not print (CLI main() prints).
    """
    root = root.resolve()
    logs = root / "logs"
    rpath = str(root)
    if rpath not in sys.path:
        sys.path.insert(0, rpath)

    exit_path = logs / "exit_attribution.jsonl"
    run_bf = logs / "strict_backfill_run.jsonl"
    ord_bf = logs / "strict_backfill_orders.jsonl"

    if not exit_path.is_file():
        return {
            "ok": False,
            "applied": 0,
            "dry_run": dry_run,
            "exit_attribution_missing": True,
        }

    have_bf = _load_jsonl_event_types(run_bf, {"entry_decision_made", "trade_intent"})
    have_edm = set(have_bf.get("entry_decision_made", set()))
    have_ti = set(have_bf.get("trade_intent", set()))
    have_edm |= _load_jsonl_event_types(logs / "run.jsonl", {"entry_decision_made"}).get(
        "entry_decision_made", set()
    )
    have_ti |= _load_jsonl_event_types(logs / "run.jsonl", {"trade_intent"}).get("trade_intent", set())

    from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side
    from telemetry.alpaca_entry_decision_made_emit import build_entry_decision_made_record

    orders_ct = _canonical_trade_ids_seen_in_orders(logs, ord_bf, tail_mb=48)
    unified_entry_ct = _load_unified_entry_canonical_by_trade_id(logs)

    applied = 0
    orders_only_applied = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    with exit_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if applied >= max_trades:
                break
            line = line.strip()
            if not line:
                continue
            try:
                ex = json.loads(line)
            except json.JSONDecodeError:
                continue
            tid = ex.get("trade_id")
            sym = (ex.get("symbol") or "").strip().upper()
            if not tid or not sym:
                continue
            m = TID_RE.match(str(tid))
            if not m:
                continue

            ts_rest = m.group(2)
            iso = ts_rest if "T" in ts_rest else ts_rest.replace(" ", "T")
            if iso.endswith("Z"):
                iso = iso[:-1] + "+00:00"
            side_raw = ex.get("side") or ex.get("direction") or "long"
            sk = normalize_side(side_raw)
            try:
                tk = ex.get("trade_key") or build_trade_key(sym, sk, iso)
            except Exception:
                continue
            tk = str(tk)
            ct = str(ex.get("canonical_trade_id") or tk)

            # Live path already emitted EDM + entered trade_intent, but orders logger missed the key
            # (common after restarts / partial submit paths). Append additive order row only.
            if str(tid) in have_edm and str(tid) in have_ti:
                if ct in orders_ct:
                    continue
                if dry_run:
                    applied += 1
                    orders_only_applied += 1
                    continue
                ord_rec = {
                    "type": "order",
                    "symbol": sym,
                    "side": "buy" if sk.upper() == "LONG" else "sell",
                    "status": "filled",
                    "canonical_trade_id": ct,
                    "trade_key": tk,
                    "action": "strict_chain_orders_only_backfill",
                    "trade_id": str(tid),
                }
                ord_bf.parent.mkdir(parents=True, exist_ok=True)
                with ord_bf.open("a", encoding="utf-8") as out:
                    out.write(json.dumps({"ts": now_iso, **ord_rec}, default=str) + "\n")
                orders_ct.add(ct)
                applied += 1
                orders_only_applied += 1
                continue

            comps = _components_from_exit(ex)
            cluster: Dict[str, Any] = {
                "direction": "bullish" if sk.upper() == "LONG" else "bearish",
                "composite_meta": {
                    "components": comps,
                    "policy_id": "strict_chain_historical_backfill_v1",
                    "attribution_policy": "strict_chain_historical_backfill_v1",
                },
            }
            intel = {
                "intent_id": str(uuid.uuid4()),
                "symbol": sym,
                "ts": iso,
                "signal_layers": {"alpha_signals": []},
            }
            _de = str(uuid.uuid4())
            _sn = sym
            _tb = "300s|0"

            try:
                es = ex.get("entry_score") if ex.get("entry_score") is not None else ex.get("score")
                try:
                    es_f = float(es) if es is not None else 0.0
                except (TypeError, ValueError):
                    es_f = 0.0
                edm = build_entry_decision_made_record(
                    symbol=sym,
                    side="buy" if sk.upper() == "LONG" else "sell",
                    score=es_f,
                    comps=comps,
                    cluster=cluster,
                    intelligence_trace=intel,
                    canonical_trade_id=ct,
                    trade_id_open=str(tid),
                    decision_event_id=_de,
                    time_bucket_id=_tb,
                    symbol_normalized=_sn,
                )
            except Exception as e:
                print("skip_build_edm", tid, e)
                continue

            if dry_run:
                applied += 1
                continue

            run_lines: List[dict] = []

            run_lines.append(
                {
                    "event_type": "canonical_trade_id_resolved",
                    "symbol": sym,
                    "canonical_trade_id_intent": ct,
                    "canonical_trade_id_fill": tk,
                    "decision_event_id": _de,
                    "symbol_normalized": _sn,
                    "time_bucket_id": _tb,
                    "trade_id": str(tid),
                    "ts": now_iso,
                }
            )
            run_lines.append(
                {
                    "event_type": "trade_intent",
                    "symbol": sym,
                    "side": "buy" if sk.upper() == "LONG" else "sell",
                    "score": float(ex.get("entry_score") or ex.get("score") or 0) or 0.0,
                    "decision_outcome": "entered",
                    "canonical_trade_id": ct,
                    "trade_key": tk,
                    "trade_id": str(tid),
                    "entry_intent_synthetic": False,
                    "entry_intent_source": "strict_chain_historical_backfill",
                    "ts": now_iso,
                }
            )
            run_lines.append(
                {
                    "event_type": "exit_intent",
                    "symbol": sym,
                    "close_reason": str(ex.get("exit_reason") or "historical_backfill"),
                    "canonical_trade_id": ct,
                    "trade_key": tk,
                    "trade_id": str(tid),
                    "ts": now_iso,
                }
            )

            run_bf.parent.mkdir(parents=True, exist_ok=True)
            with run_bf.open("a", encoding="utf-8") as out:
                for rec in run_lines:
                    out.write(json.dumps({"ts": now_iso, **rec}, default=str) + "\n")
                out.write(json.dumps({"ts": now_iso, **edm}, default=str) + "\n")

            ord_rec = {
                "type": "order",
                "symbol": sym,
                "side": "buy" if sk.upper() == "LONG" else "sell",
                "status": "filled",
                "canonical_trade_id": ct,
                "trade_key": tk,
                "action": "strict_chain_historical_backfill",
                "trade_id": str(tid),
            }
            with ord_bf.open("a", encoding="utf-8") as out:
                out.write(json.dumps({"ts": now_iso, **ord_rec}, default=str) + "\n")

            try:
                from src.telemetry.alpaca_attribution_emitter import emit_entry_attribution

                emit_entry_attribution(
                    trade_id=str(tid),
                    symbol=sym,
                    side=sk,
                    decision="OPEN_LONG" if sk.upper() == "LONG" else "OPEN_SHORT",
                    decision_reason="strict_chain_historical_backfill",
                    trade_key=tk,
                    raw_signals=comps,
                    weights={k: 1.0 for k in comps},
                    contributions={k: float(v) for k, v in comps.items()},
                    composite_score=float(ex.get("entry_score") or ex.get("score") or 0) or None,
                    entry_threshold=None,
                    timestamp=iso,
                    schema_role="exit_proxy",
                    is_repair_row=True,
                )
            except Exception as ex_emit:
                print("emit_entry_attribution_failed", tid, ex_emit)

            have_edm.add(str(tid))
            have_ti.add(str(tid))
            applied += 1

    resolver_pairs = _load_canonical_trade_id_resolved_pairs(logs, run_bf)
    alias_bridge_applied = _apply_intent_fill_alias_backfills(
        exit_path,
        run_bf,
        unified_entry_ct,
        orders_ct,
        resolver_pairs,
        dry_run=dry_run,
        now_iso=now_iso,
    )

    return {
        "ok": True,
        "applied": applied,
        "orders_only_applied": orders_only_applied,
        "alias_bridge_applied": alias_bridge_applied,
        "dry_run": dry_run,
        "exit_attribution_missing": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-trades", type=int, default=5000)
    args = ap.parse_args()
    meta = apply_strict_chain_backfill(
        args.root, dry_run=args.dry_run, max_trades=args.max_trades
    )
    if meta.get("exit_attribution_missing"):
        print("missing", args.root.resolve() / "logs" / "exit_attribution.jsonl")
        return 1
    print(
        "backfill_count",
        meta["applied"],
        "orders_only",
        meta.get("orders_only_applied", 0),
        "alias_bridge",
        meta.get("alias_bridge_applied", 0),
        "dry_run" if args.dry_run else "applied",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
