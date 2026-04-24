#!/usr/bin/env python3
"""
Flatten Alpaca Harvester-era exit_attribution.jsonl for ML training.

Joins entry-time composite/features from logs/entry_snapshots.jsonl using the **canonical**
``build_trade_key`` (``trade_key`` / ``canonical_trade_id`` on exit or snapshot, else derived
from symbol + side + entry timestamp) **before** ``entry_order_id``. Legacy order-id-only joins
remain as fallback when canonical keys are missing on historical rows.

Falls back to logs/scoring_flow.jsonl wide join when no snapshot exists.

Reads closed trades with **exit timestamp** on/after the floor epoch (same cut as
``compute_canonical_trade_count``), dedupes by canonical trade_key (fallback: trade_id,
then entry order id; last row wins), flattens nested ML blobs with mlf_* column prefix,
writes CSV.

Usage (repo root):
  PYTHONPATH=. python3 scripts/telemetry/alpaca_ml_flattener.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START  # noqa: E402
from telemetry.ml_scoreflow_contract import (  # noqa: E402
    mlf_scoreflow_component_column_names,
    normalize_composite_components_for_ml,
)
from utils.era_cut import learning_excluded_for_exit_record  # noqa: E402
from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side  # noqa: E402
from src.governance.canonical_trade_count import _parse_exit_epoch  # noqa: E402

TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")
ML_BLOB_KEYS = ("entry_uw", "v2_exit_components", "direction_intel_embed")

# Wide join: last composite_calculated for symbol with ts in [entry - lookback, entry].
SCOREFLOW_LOOKBACK_SEC_DEFAULT = 4 * 3600


def _parse_iso_ts(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (TypeError, ValueError):
        return None


def _open_epoch_from_trade_id(tid: Any) -> Optional[float]:
    m = TID_RE.match(str(tid or "").strip())
    if not m:
        return None
    return _parse_iso_ts(m.group(2))


def _iter_jsonl(path: Path) -> Iterator[dict]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                yield o


def _flatten_leaves(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Nested dicts -> underscore paths; scalars only at leaves. Lists -> JSON string."""
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            safe = str(k).replace(".", "_")
            p = f"{prefix}_{safe}" if prefix else safe
            out.update(_flatten_leaves(v, p))
    elif isinstance(obj, list):
        key = prefix or "list"
        try:
            out[key] = json.dumps(obj, separators=(",", ":"), default=str)[:4000]
        except TypeError:
            out[key] = str(obj)[:4000]
    elif obj is None:
        out[prefix] = ""
    elif isinstance(obj, bool):
        out[prefix] = obj
    elif isinstance(obj, (int, float, str)):
        out[prefix] = obj
    else:
        out[prefix] = str(obj)
    return out


def _prefix_mlf(flat: Dict[str, Any], stem: str) -> Dict[str, Any]:
    return {f"mlf_{stem}_{k}": v for k, v in flat.items()}


def _snapshot_canonical_trade_key_from_row(r: dict) -> Optional[str]:
    """Derive ``symbol|LONG|SHORT|epoch`` from snapshot row when possible (matches exit rows)."""
    for k in ("trade_key", "canonical_trade_id"):
        v = str(r.get(k) or "").strip()
        if v and v.count("|") >= 2:
            parts = v.split("|")
            if len(parts) >= 3:
                try:
                    int(parts[-1])
                    return v
                except ValueError:
                    pass
    tid = str(r.get("trade_id") or "").strip()
    m = TID_RE.match(tid)
    if not m:
        return None
    sym = m.group(1)
    iso = m.group(2)
    try:
        return build_trade_key(sym, normalize_side(r.get("side") or "buy"), iso)
    except Exception:
        return None


def _load_entry_snapshot_indexes(path: Path) -> Dict[str, Dict[str, dict]]:
    """
    Last row wins per key. Indexes:
      - ``by_trade_key``: canonical ``build_trade_key`` (preferred for ML join).
      - ``by_order``: Alpaca ``order_id`` (fallback for legacy rows).
    """
    by_order: Dict[str, dict] = {}
    by_trade_key: Dict[str, dict] = {}
    for r in _iter_jsonl(path):
        if (r.get("msg") or "") != "entry_snapshot":
            continue
        oid = str(r.get("order_id") or "").strip()
        if oid and not oid.upper().startswith("AUDIT-DRYRUN"):
            by_order[oid] = r
        ck = _snapshot_canonical_trade_key_from_row(r)
        if ck:
            by_trade_key[ck] = r
    return {"by_order": by_order, "by_trade_key": by_trade_key}


def _canonical_trade_key_for_exit_row(rec: dict) -> Optional[str]:
    for k in ("trade_key", "canonical_trade_id"):
        v = str(rec.get(k) or "").strip()
        if v and v.count("|") >= 2:
            parts = v.split("|")
            if len(parts) >= 3:
                try:
                    int(parts[-1])
                    return v
                except ValueError:
                    pass
    sym = str(rec.get("symbol_normalized") or rec.get("symbol") or "").upper().strip()
    ets = rec.get("entry_ts") or rec.get("entry_timestamp")
    side = rec.get("position_side") or rec.get("side") or "long"
    if sym and ets:
        try:
            return build_trade_key(sym, normalize_side(side), ets)
        except Exception:
            return None
    return None


def _exit_row_snapshot_lookup_keys(rec: dict) -> List[str]:
    """Lookup order: canonical trade key first, then broker entry order ids."""
    keys: List[str] = []
    ck = _canonical_trade_key_for_exit_row(rec)
    if ck:
        keys.append(ck)
    for k in ("entry_order_id", "entry_orderId"):
        v = rec.get(k)
        if v is not None and str(v).strip():
            keys.append(str(v).strip())
    return keys


def _load_scoring_composite_index(
    path: Path,
) -> Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]]:
    """
    Per symbol: sorted timestamps, parallel list of component dicts and total scores.
    """
    by_sym: Dict[str, List[Tuple[float, Dict[str, Any], float]]] = {}
    for r in _iter_jsonl(path):
        if (r.get("msg") or "") != "composite_calculated":
            continue
        sym = str(r.get("symbol") or "").upper().strip()
        if not sym:
            continue
        ts = _parse_iso_ts(r.get("ts"))
        if ts is None:
            continue
        comp = r.get("components")
        if not isinstance(comp, dict):
            comp = {}
        try:
            score = float(r.get("score")) if r.get("score") is not None else float("nan")
        except (TypeError, ValueError):
            score = float("nan")
        by_sym.setdefault(sym, []).append((ts, comp, score))
    out: Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]] = {}
    for sym, rows in by_sym.items():
        rows.sort(key=lambda x: x[0])
        merged: List[Tuple[float, Dict[str, Any], float]] = []
        for t, c, s in rows:
            if merged and merged[-1][0] == t:
                merged[-1] = (t, c, s)  # same-ts: last line wins
            else:
                merged.append((t, c, s))
        ts_list = [x[0] for x in merged]
        comps = [x[1] for x in merged]
        scores = [x[2] for x in merged]
        out[sym] = (ts_list, comps, scores)
    return out


def _last_known_composite_wide(
    index: Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]],
    symbol: str,
    entry_epoch: Optional[float],
    lookback_sec: float = SCOREFLOW_LOOKBACK_SEC_DEFAULT,
    *,
    allow_unbounded_fallback: bool = True,
) -> Tuple[Optional[float], Optional[Dict[str, Any]], Optional[float], str]:
    """
    Last Known Score: newest composite_calculated with ts <= entry_epoch and
    entry_epoch - ts <= lookback_sec (default 4h).

    If ``allow_unbounded_fallback`` and nothing falls in the window, use the newest
    composite still <= entry (may be older than lookback). Tier is recorded on the row.
    """
    if entry_epoch is None:
        return None, None, None, "none"
    sym = symbol.upper().strip()
    if not sym:
        return None, None, None, "none"
    bucket = index.get(sym)
    if not bucket:
        return None, None, None, "none"
    ts_list, comps, scores = bucket
    lo = float(entry_epoch) - float(lookback_sec)
    i = bisect_right(ts_list, float(entry_epoch)) - 1
    if i < 0:
        return None, None, None, "none"
    if ts_list[i] >= lo:
        return ts_list[i], comps[i], scores[i], "4h_window"
    if allow_unbounded_fallback:
        return ts_list[i], comps[i], scores[i], "unbounded_fallback"
    return None, None, None, "none"


def _exit_row_dedupe_key(rec: dict) -> Optional[str]:
    """
    Align cardinality with ``compute_canonical_trade_count``: prefer stable canonical trade_key,
    then Alpaca trade_id, then entry order id (orphan rows without trade_id).
    """
    ck = _canonical_trade_key_for_exit_row(rec)
    if ck:
        return f"ck:{ck}"
    tid = str(rec.get("trade_id") or "").strip()
    if tid:
        return f"id:{tid}"
    for k in ("entry_order_id", "entry_orderId"):
        v = rec.get(k)
        if v is not None and str(v).strip():
            return f"oid:{str(v).strip()}"
    return None


def _dedupe_exit_rows(rows: List[dict]) -> List[dict]:
    """Last row wins per canonical dedupe key (matches governance trade unit)."""
    by_key: Dict[str, dict] = {}
    order: List[str] = []
    for r in rows:
        dk = _exit_row_dedupe_key(r)
        if not dk:
            continue
        if dk not in by_key:
            order.append(dk)
        by_key[dk] = r
    return [by_key[k] for k in order]


def _filter_strict_cohort(rec: dict, floor_epoch: float) -> bool:
    """
    Match ``compute_canonical_trade_count(..., floor_epoch=...)``: era cut + exit timestamp
    on/after floor (not open-instant floor), so flattener row count aligns with canonical trades.
    """
    if learning_excluded_for_exit_record(rec):
        return False
    ex = _parse_exit_epoch(rec)
    if ex is None or ex < float(floor_epoch):
        return False
    return True


def _apply_exit_quality_pct_fields(rec: dict, row: Dict[str, Any]) -> None:
    """
    Top-level ML targets from ``exit_quality_metrics`` (truth from ``compute_exit_quality_metrics``).

    Stored JSON may use ``mfe`` / ``mae`` (price units) or ``mfe_pct`` / ``mae_pct`` when present.
    We always emit ``exit_mfe_pct`` and ``exit_mae_pct`` as **percent of entry price** when
    ``entry_price`` is available; otherwise fall back to raw scalar (legacy rows).
    """
    eqm = rec.get("exit_quality_metrics")
    if not isinstance(eqm, dict):
        return
    mfe_raw = eqm.get("mfe_pct")
    if mfe_raw is None:
        mfe_raw = eqm.get("mfe")
    mae_raw = eqm.get("mae_pct")
    if mae_raw is None:
        mae_raw = eqm.get("mae")
    ep = row.get("entry_price")
    if ep in (None, ""):
        ep = rec.get("entry_price")
    try:
        epf = float(ep) if ep not in (None, "") else None
    except (TypeError, ValueError):
        epf = None
    if mfe_raw is not None and str(mfe_raw).strip() != "":
        try:
            mf = float(mfe_raw)
            if epf and epf > 0:
                row["exit_mfe_pct"] = round(mf / epf * 100.0, 6)
            else:
                row["exit_mfe_pct"] = round(mf, 6)
        except (TypeError, ValueError):
            pass
    if mae_raw is not None and str(mae_raw).strip() != "":
        try:
            ma = float(mae_raw)
            if epf and epf > 0:
                row["exit_mae_pct"] = round(abs(ma) / epf * 100.0, 6)
            else:
                row["exit_mae_pct"] = round(abs(ma), 6)
        except (TypeError, ValueError):
            pass


def _uw_gamma_skew_and_tide(entry_uw: Any) -> Tuple[float, float]:
    """
    First-class columns for options-flow / tide (ALP-UW-003).

    ``uw_gamma_skew`` prefers ``greeks_gamma`` (UW v2 composite component), then ``iv_skew``.
    ``uw_tide_score`` maps ``market_tide``. Missing values -> (0.0, 0.0) so strict ML gates
    still see finite numerics; nested ``entry_uw`` / ``components`` / ``v2`` blobs are scanned.
    """
    z = 0.0
    if not isinstance(entry_uw, dict):
        return z, z

    def _scalar(v: Any) -> Optional[float]:
        if v is None or isinstance(v, bool):
            return None
        if isinstance(v, (int, float)):
            try:
                x = float(v)
                return x if x == x and abs(x) < 1e308 else None
            except (TypeError, ValueError):
                return None
        if isinstance(v, dict):
            for kk in ("score", "value", "tide", "net", "gamma", "skew", "composite"):
                if kk in v:
                    s = _scalar(v.get(kk))
                    if s is not None:
                        return s
            return None
        try:
            x = float(v)
            return x if x == x else None
        except (TypeError, ValueError):
            return None

    def _pick(d: Any) -> Tuple[Optional[float], Optional[float]]:
        if not isinstance(d, dict):
            return None, None
        g = _scalar(d.get("greeks_gamma"))
        if g is None:
            g = _scalar(d.get("iv_skew"))
        t = _scalar(d.get("market_tide"))
        return g, t

    g_out, t_out = _pick(entry_uw)
    comp = entry_uw.get("components")
    if isinstance(comp, dict):
        g2, t2 = _pick(comp)
        if g_out is None:
            g_out = g2
        if t_out is None:
            t_out = t2
    v2 = entry_uw.get("v2")
    if isinstance(v2, dict):
        for subk in ("components", "feature_snapshot"):
            sub = v2.get(subk)
            if isinstance(sub, dict):
                g2, t2 = _pick(sub)
                if g_out is None:
                    g_out = g2
                if t_out is None:
                    t_out = t2
    return (float(g_out) if g_out is not None else z, float(t_out) if t_out is not None else z)


def _first_nonblank(*values: Any) -> Any:
    for value in values:
        if value is not None and str(value).strip() != "":
            return value
    return None


def _is_zero_pnl(rec: dict) -> bool:
    pnl = rec.get("pnl")
    if pnl is None:
        pnl = rec.get("realized_pnl_usd")
    try:
        return abs(float(pnl)) < 1e-9
    except (TypeError, ValueError):
        return False


def _entry_price_for_base_row(rec: dict) -> Any:
    entry_price = _first_nonblank(
        rec.get("entry_price"),
        rec.get("avg_entry_price"),
        rec.get("entry_fill_price"),
        rec.get("entry_filled_avg_price"),
    )
    if entry_price is not None:
        return entry_price
    if _is_zero_pnl(rec):
        # Some same-instant displacement/flat rows have unresolved entry order ids but
        # still carry the broker execution price on the close side. For a true flat
        # trade, entry and exit price are identical, so keep the ML target complete.
        return _first_nonblank(rec.get("exit_price"), rec.get("price"), rec.get("filled_avg_price"))
    return None


def _base_trade_fields(rec: dict) -> Dict[str, Any]:
    side = rec.get("position_side") or rec.get("side") or ""
    pnl = rec.get("pnl")
    if pnl is None:
        pnl = rec.get("realized_pnl_usd")
    hld = rec.get("time_in_trade_minutes")
    if hld is None:
        sec = (rec.get("exit_quality_metrics") or {}).get("time_in_trade_sec")
        if sec is not None:
            try:
                hld = float(sec) / 60.0
            except (TypeError, ValueError):
                hld = None
    return {
        "symbol": rec.get("symbol"),
        "side": side,
        "realized_pnl_usd": pnl,
        "holding_time_minutes": hld,
        "trade_id": rec.get("trade_id"),
        "trade_key": rec.get("trade_key") or rec.get("canonical_trade_id"),
        "entry_ts": rec.get("entry_ts") or rec.get("entry_timestamp"),
        "exit_ts": rec.get("exit_ts") or rec.get("timestamp"),
        "entry_price": _entry_price_for_base_row(rec),
        "exit_price": rec.get("exit_price") or rec.get("price"),
        "qty": rec.get("qty"),
        "variant_id": rec.get("variant_id"),
        "composite_version": rec.get("composite_version"),
        "strict_open_epoch_utc": _open_epoch_from_trade_id(rec.get("trade_id")),
    }


def _load_run_intent_ai_index(root: Path) -> Dict[str, Dict[str, Any]]:
    """Last trade_intent row wins per trade_id / canonical_trade_id / trade_key (for ML AI columns)."""
    path = root / "logs" / "run.jsonl"
    out: Dict[str, Dict[str, Any]] = {}
    if not path.is_file():
        return out
    for r in _iter_jsonl(path):
        if str(r.get("event_type") or "") != "trade_intent":
            continue
        blob = {
            "ai_approved_v1": r.get("ai_approved_v1"),
            "ai_approved_v2": r.get("ai_approved_v2"),
            "ai_approved_v3_shadow": r.get("ai_approved_v3_shadow"),
        }
        for key in ("trade_id", "canonical_trade_id", "trade_key"):
            v = r.get(key)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                out[s] = blob
    return out


def _entry_epoch_for_scoring(rec: dict, row: Dict[str, Any]) -> Optional[float]:
    """Prefer entry_ts on row, then raw record timestamps, then open instant from trade_id."""
    t = _parse_iso_ts(row.get("entry_ts"))
    if t is not None:
        return t
    t = _parse_iso_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
    if t is not None:
        return t
    return _open_epoch_from_trade_id(rec.get("trade_id"))


def build_rows(
    root: Path,
    floor_epoch: float,
    scoring_index: Optional[Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]]],
    entry_snap_index: Optional[Dict[str, Dict[str, dict]]] = None,
    *,
    run_intent_ai: Optional[Dict[str, Dict[str, Any]]] = None,
    scoreflow_lookback_sec: float = SCOREFLOW_LOOKBACK_SEC_DEFAULT,
    scoreflow_unbounded_fallback: bool = True,
) -> List[Dict[str, Any]]:
    exit_path = root / "logs" / "exit_attribution.jsonl"
    raw = list(_iter_jsonl(exit_path))
    deduped = _dedupe_exit_rows(raw)
    out: List[Dict[str, Any]] = []
    for rec in deduped:
        if not _filter_strict_cohort(rec, floor_epoch):
            continue
        row: Dict[str, Any] = _base_trade_fields(rec)
        entry_epoch = _entry_epoch_for_scoring(rec, row)
        sym_join = (
            str(rec.get("symbol_normalized") or rec.get("symbol") or row.get("symbol") or "")
            .upper()
            .strip()
        )

        snap: Optional[dict] = None
        snap_match: Optional[str] = None
        if entry_snap_index:
            by_tk = entry_snap_index.get("by_trade_key") or {}
            by_o = entry_snap_index.get("by_order") or {}
            for ek in _exit_row_snapshot_lookup_keys(rec):
                if ek in by_tk:
                    snap = by_tk[ek]
                    snap_match = "canonical_trade_key"
                    break
                if ek in by_o:
                    snap = by_o[ek]
                    snap_match = "entry_order_id"
                    break

        for blob_key in ML_BLOB_KEYS:
            blob = rec.get(blob_key)
            if isinstance(blob, dict) and blob:
                flat = _flatten_leaves(blob)
                stem = blob_key.replace(".", "_")
                row.update(_prefix_mlf(flat, stem))

        _apply_exit_quality_pct_fields(rec, row)

        row["mlf_ml_feature_source"] = "none"
        comp_norm: Dict[str, float]
        if snap:
            row["mlf_ml_feature_source"] = "entry_snapshot"
            row["mlf_scoreflow_join_tier"] = "entry_snapshot"
            if snap_match:
                row["mlf_entry_snapshot_match"] = snap_match
            row["mlf_scoreflow_lookback_sec_applied"] = scoreflow_lookback_sec
            tss = _parse_iso_ts(snap.get("timestamp_utc"))
            if tss is not None:
                row["mlf_scoreflow_snapshot_ts_epoch"] = tss
                row["mlf_scoreflow_snapshot_age_sec"] = (
                    float(entry_epoch) - float(tss) if entry_epoch is not None else ""
                )
            comp = snap.get("components")
            comp_norm = normalize_composite_components_for_ml(comp if isinstance(comp, dict) else {})
            row.update(_prefix_mlf(_flatten_leaves(comp_norm), "scoreflow_components"))
            tot_raw = snap.get("composite_score")
            try:
                tot = float(tot_raw) if tot_raw is not None else float("nan")
            except (TypeError, ValueError):
                tot = float("nan")
            if tot == tot:
                row["mlf_scoreflow_total_score"] = tot
            else:
                row["mlf_scoreflow_total_score"] = round(sum(comp_norm.values()), 6)
                row["mlf_scoreflow_total_score_imputed"] = 1
        elif scoring_index:
            _ts_c, comp, tot, tier = _last_known_composite_wide(
                scoring_index,
                sym_join,
                entry_epoch,
                lookback_sec=scoreflow_lookback_sec,
                allow_unbounded_fallback=scoreflow_unbounded_fallback,
            )
            row["mlf_ml_feature_source"] = (
                "scoreflow_wide" if tier not in (None, "none") else "none"
            )
            row["mlf_scoreflow_lookback_sec_applied"] = scoreflow_lookback_sec
            row["mlf_scoreflow_join_tier"] = tier
            if _ts_c is not None:
                row["mlf_scoreflow_snapshot_ts_epoch"] = _ts_c
                row["mlf_scoreflow_snapshot_age_sec"] = (
                    float(entry_epoch) - float(_ts_c) if entry_epoch is not None else ""
                )
            comp_norm = normalize_composite_components_for_ml(comp if isinstance(comp, dict) else {})
            row.update(_prefix_mlf(_flatten_leaves(comp_norm), "scoreflow_components"))
            if tot is not None and tot == tot:  # not NaN
                row["mlf_scoreflow_total_score"] = tot
            else:
                row["mlf_scoreflow_total_score"] = round(sum(comp_norm.values()), 6)
                row["mlf_scoreflow_total_score_imputed"] = 1
        else:
            # No entry_snapshot row and no scoring_flow index (or index miss): finite neutral
            # scoreflow vector — strict ML gate needs numeric columns; flag for downstream filters.
            comp_norm = normalize_composite_components_for_ml({})
            row.update(_prefix_mlf(_flatten_leaves(comp_norm), "scoreflow_components"))
            row["mlf_scoreflow_total_score"] = 0.0
            row["mlf_scoreflow_total_score_imputed"] = 1
            row["mlf_scoreflow_features_neutral_no_join"] = 1
            row.setdefault("mlf_scoreflow_join_tier", "none")

        # v2_uw_inputs (entry_uw) does not include greeks_gamma / market_tide; those live on the
        # entry-time composite components (scoreflow join). Merge so first-class UW columns match
        # mlf_scoreflow_components_greeks_gamma / mlf_scoreflow_components_market_tide.
        merged_uw: Dict[str, Any] = {}
        eu = rec.get("entry_uw")
        if isinstance(eu, dict) and eu:
            merged_uw = dict(eu)
        merged_uw["components"] = comp_norm
        _g_uc, _t_uc = _uw_gamma_skew_and_tide(merged_uw)
        row["uw_gamma_skew"] = _g_uc
        row["uw_tide_score"] = _t_uc

        if run_intent_ai:
            _keys_ai: List[str] = []
            try:
                _keys_ai.extend([k for k in _exit_row_snapshot_lookup_keys(rec) if k])
            except Exception:
                pass
            _tid_ai = rec.get("trade_id")
            if _tid_ai:
                _keys_ai.append(str(_tid_ai).strip())
            for _ek in _keys_ai:
                if _ek and _ek in run_intent_ai:
                    _blob = run_intent_ai[_ek]
                    row["ai_approved_v1"] = _blob.get("ai_approved_v1")
                    row["ai_approved_v2"] = _blob.get("ai_approved_v2")
                    row["ai_approved_v3_shadow"] = _blob.get("ai_approved_v3_shadow")
                    break

        from src.core.ml_feature_normalization import normalize_features_for_side

        row = normalize_features_for_side(row, str(row.get("side") or ""))
        out.append(row)
    return out


def _collect_headers(rows: List[Dict[str, Any]]) -> List[str]:
    base = [
        "symbol",
        "side",
        "realized_pnl_usd",
        "holding_time_minutes",
        "trade_id",
        "trade_key",
        "entry_ts",
        "exit_ts",
        "entry_price",
        "exit_price",
        "qty",
        "variant_id",
        "composite_version",
        "strict_open_epoch_utc",
        "exit_mfe_pct",
        "exit_mae_pct",
    ]
    extras = sorted({k for r in rows for k in r.keys() if k not in base})
    return base + extras


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca ML cohort flattener (Harvester era).")
    ap.add_argument("--root", type=Path, default=REPO_ROOT, help="Repo root (default: inferred).")
    ap.add_argument(
        "--floor-epoch",
        type=float,
        default=float(STRICT_EPOCH_START),
        help="Include trades with open instant >= this UTC epoch (default: STRICT_EPOCH_START).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help=f"Output CSV (default: reports/Gemini/alpaca_ml_cohort_flat.csv under --root).",
    )
    ap.add_argument(
        "--no-scoring-flow",
        action="store_true",
        help="Skip logs/scoring_flow.jsonl composite join.",
    )
    ap.add_argument(
        "--no-entry-snapshots",
        action="store_true",
        help="Skip logs/entry_snapshots.jsonl (use only scoring_flow wide join).",
    )
    ap.add_argument(
        "--scoreflow-lookback-sec",
        type=float,
        default=float(SCOREFLOW_LOOKBACK_SEC_DEFAULT),
        help="Preferred max age (seconds) of last composite before entry (default: 14400 = 4h).",
    )
    ap.add_argument(
        "--no-scoreflow-unbounded-fallback",
        action="store_true",
        help="If set, do not use older-than-lookback composites when nothing falls in the 4h window.",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    out_path = (args.out or (root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scoring_path = root / "logs" / "scoring_flow.jsonl"
    scoring_index = None if args.no_scoring_flow else _load_scoring_composite_index(scoring_path)

    entry_snap_path = root / "logs" / "entry_snapshots.jsonl"
    entry_snap_index = (
        None
        if args.no_entry_snapshots
        else _load_entry_snapshot_indexes(entry_snap_path)
    )

    run_intent_ai = _load_run_intent_ai_index(root)

    rows = build_rows(
        root,
        args.floor_epoch,
        scoring_index,
        entry_snap_index,
        run_intent_ai=run_intent_ai,
        scoreflow_lookback_sec=args.scoreflow_lookback_sec,
        scoreflow_unbounded_fallback=not args.no_scoreflow_unbounded_fallback,
    )
    headers = list(_collect_headers(rows))
    # Strict ML cohort (alpaca_cohort_train) allowlist — always present in header even if 0 rows.
    for _c in mlf_scoreflow_component_column_names():
        if _c not in headers:
            headers.append(_c)
    for _t in ("mlf_scoreflow_total_score", "mlf_scoreflow_total_score_imputed"):
        if _t not in headers:
            headers.append(_t)
    for _u in ("uw_gamma_skew", "uw_tide_score"):
        if _u not in headers:
            headers.append(_u)
    for _ai in ("ai_approved_v1", "ai_approved_v2", "ai_approved_v3_shadow"):
        if _ai not in headers:
            headers.append(_ai)

    def _apply_sub_dollar_csv_precision(row: Dict[str, Any]) -> None:
        """Apex: sub-$1 entry cohort uses 4dp prices / 4dp USD PnL on CSV (finer above $1)."""
        try:
            ref = float(row.get("entry_price") or 0)
        except (TypeError, ValueError):
            ref = 0.0
        sub = 0 < abs(ref) < 1.0
        for k in ("entry_price", "exit_price"):
            v = row.get(k)
            if v in (None, ""):
                continue
            try:
                x = float(v)
            except (TypeError, ValueError):
                continue
            row[k] = round(x, 4) if sub else round(x, 6)
        v2 = row.get("realized_pnl_usd")
        if v2 in (None, ""):
            return
        try:
            u = float(v2)
        except (TypeError, ValueError):
            return
        row["realized_pnl_usd"] = round(u, 4) if sub else round(u, 2)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            _apply_sub_dollar_csv_precision(r)
            w.writerow({h: r.get(h, "") for h in headers})

    n = len(rows)
    if n:
        tot_col = "mlf_scoreflow_total_score"
        from_snap = sum(1 for r in rows if r.get("mlf_ml_feature_source") == "entry_snapshot")
        from_sf = sum(1 for r in rows if r.get("mlf_ml_feature_source") == "scoreflow_wide")
        if entry_snap_index is not None:
            by_ck = sum(1 for r in rows if r.get("mlf_entry_snapshot_match") == "canonical_trade_key")
            by_oid = sum(1 for r in rows if r.get("mlf_entry_snapshot_match") == "entry_order_id")
            print(
                f"entry_snapshot_join_pct: {100.0 * from_snap / n:.2f} ({from_snap}/{n}) "
                f"[canonical_trade_key={by_ck}, entry_order_id_fallback={by_oid}]"
            )
        with_snap = sum(1 for r in rows if r.get("mlf_scoreflow_snapshot_ts_epoch") not in (None, ""))
        with_tot = sum(
            1
            for r in rows
            if r.get(tot_col) not in (None, "")
            and str(r.get(tot_col)).strip() != ""
        )
        in_4h = sum(1 for r in rows if r.get("mlf_scoreflow_join_tier") == "4h_window")
        fb = sum(1 for r in rows if r.get("mlf_scoreflow_join_tier") == "unbounded_fallback")
        es_tier = sum(1 for r in rows if r.get("mlf_scoreflow_join_tier") == "entry_snapshot")
        if scoring_index is not None or entry_snap_index is not None:
            print(
                f"scoreflow_snapshot_coverage_pct: {100.0 * with_snap / n:.2f} ({with_snap}/{n}) "
                f"[entry_snapshot_tier={es_tier}; wide 4h_tier={in_4h} fallback_tier={fb}; "
                f"scoreflow_lookback={args.scoreflow_lookback_sec:.0f}s; unbounded_fallback="
                f"{'off' if args.no_scoreflow_unbounded_fallback else 'on'}; scoreflow_wide_rows={from_sf}]"
            )
        print(f"scoreflow_total_score_populated_pct: {100.0 * with_tot / n:.2f} ({with_tot}/{n})")
    print(f"wrote {n} rows -> {out_path}")
    print(f"floor_epoch={args.floor_epoch} STRICT_EPOCH_START={STRICT_EPOCH_START}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
