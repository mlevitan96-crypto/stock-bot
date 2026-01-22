#!/usr/bin/env python3
"""
Shadow vs live parity checks (read-only)
======================================

Best-effort parity summary between:
- v1 live executed trades (if a v1 attribution log exists)
- v2 shadow activity (shadow_trades events)

Contract:
- Read-only, side-effect free.
- Never raises on malformed input.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from telemetry.feature_families import (  # telemetry-only helper
    FAMILY_UNKNOWN,
    active_v2_families_from_adjustments,
    dominant_v1_family_from_components,
)

def _utc_day_from_ts(ts: Any) -> Optional[str]:
    if ts is None:
        return None
    s = str(ts).strip()
    if len(s) >= 10:
        return s[:10]
    return None


def _parse_iso_to_epoch_seconds(ts: Any) -> Optional[float]:
    try:
        if ts is None:
            return None
        s = str(ts).strip()
        if not s:
            return None
        s = s.replace("Z", "+00:00")
        if "T" not in s and " " in s:
            s = s.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        return float(dt.timestamp())
    except Exception:
        return None


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except Exception:
        return None


def _iter_jsonl_text(text: str) -> Iterable[Dict[str, Any]]:
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                yield obj
        except Exception:
            continue


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _classify(
    *,
    entry_ts_delta_seconds: Optional[float],
    score_delta: Optional[float],
    price_delta_usd: Optional[float],
    missing_fields: List[str],
) -> str:
    if missing_fields:
        # Still emit a classification from the allowed set.
        return "divergent"
    # If fields are missing, they will be represented as 0.0 with missing_fields set.
    if abs(entry_ts_delta_seconds) <= 5.0 and abs(score_delta) <= 0.05 and abs(price_delta_usd) <= 0.05:
        return "perfect_match"
    if abs(entry_ts_delta_seconds) <= 60.0 and abs(score_delta) <= 0.25 and abs(price_delta_usd) <= 0.50:
        return "near_match"
    return "divergent"


def _greedy_match_by_time(
    v1: List[Dict[str, Any]],
    v2: List[Dict[str, Any]],
) -> Tuple[List[Tuple[Dict[str, Any], Dict[str, Any]]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Pair entries by minimizing absolute timestamp deltas (greedy).
    Returns: (paired, remaining_v1, remaining_v2)
    """
    v1_sorted = sorted([r for r in v1 if isinstance(r, dict)], key=lambda r: float(r.get("_entry_epoch") or 0.0))
    v2_sorted = sorted([r for r in v2 if isinstance(r, dict)], key=lambda r: float(r.get("_entry_epoch") or 0.0))

    paired: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    used_v1: Set[int] = set()

    for r2 in v2_sorted:
        e2 = r2.get("_entry_epoch")
        if e2 is None:
            continue
        best_i = None
        best_abs = None
        for i, r1 in enumerate(v1_sorted):
            if i in used_v1:
                continue
            e1 = r1.get("_entry_epoch")
            if e1 is None:
                continue
            d = abs(float(e2) - float(e1))
            if best_abs is None or d < best_abs:
                best_abs = d
                best_i = i
        if best_i is not None:
            used_v1.add(best_i)
            paired.append((v1_sorted[best_i], r2))

    remaining_v1 = [r for i, r in enumerate(v1_sorted) if i not in used_v1]
    paired_v2_ids = {id(r2) for _, r2 in paired}
    remaining_v2 = [r for r in v2_sorted if id(r) not in paired_v2_ids]
    return paired, remaining_v1, remaining_v2


def build_shadow_vs_live_parity(
    *,
    day: str,
    v1_attribution_log_path: str,
    shadow_trades_log_path: str,
) -> Dict[str, Any]:
    try:
        v1_text = _read_text(v1_attribution_log_path)
        shadow_text = _read_text(shadow_trades_log_path)

        v1_syms: Set[str] = set()
        v1_recs = 0
        v1_entries_by_symbol: Dict[str, List[Dict[str, Any]]] = {}
        for r in _iter_jsonl_text(v1_text):
            ts = r.get("ts") or r.get("timestamp")
            if _utc_day_from_ts(ts) != day:
                continue
            sym = str(r.get("symbol", "") or "").upper()
            if sym:
                v1_syms.add(sym)
                v1_recs += 1
            # v1 entry rows: trade_id starts with "open_" and has context.entry_ts/entry_price/entry_score
            try:
                trade_id = str(r.get("trade_id", "") or "")
                if not trade_id.startswith("open_"):
                    continue
                ctx = r.get("context") if isinstance(r.get("context"), dict) else {}
                ent_ts = ctx.get("entry_ts")
                ent_epoch = _parse_iso_to_epoch_seconds(ent_ts)
                if ent_epoch is None:
                    continue
                comps = ctx.get("components") if isinstance(ctx.get("components"), dict) else {}
                fam = dominant_v1_family_from_components(comps)
                v1_entries_by_symbol.setdefault(sym, []).append(
                    {
                        "symbol": sym,
                        "v1_entry_ts": str(ent_ts or ""),
                        "_entry_epoch": ent_epoch,
                        "v1_score_at_entry": _safe_float(ctx.get("entry_score") or ctx.get("score")),
                        "v1_price_at_entry": _safe_float(ctx.get("entry_price")),
                        "side": str(ctx.get("position_side") or ctx.get("side") or ""),
                        "feature_family": str(fam or FAMILY_UNKNOWN),
                    }
                )
            except Exception:
                continue

        shadow_candidates: Set[str] = set()
        shadow_entries: Set[str] = set()
        shadow_exits: Set[str] = set()
        shadow_recs = 0
        v2_entries_by_symbol: Dict[str, List[Dict[str, Any]]] = {}
        for r in _iter_jsonl_text(shadow_text):
            ts = r.get("ts") or r.get("timestamp")
            if _utc_day_from_ts(ts) != day:
                continue
            shadow_recs += 1
            sym = str(r.get("symbol", "") or "").upper()
            et = str(r.get("event_type", "") or "")
            if not sym:
                continue
            if et == "shadow_trade_candidate":
                shadow_candidates.add(sym)
            if et == "shadow_entry_opened":
                shadow_entries.add(sym)
                ent_ts = r.get("entry_ts") or r.get("ts") or r.get("timestamp")
                ent_epoch = _parse_iso_to_epoch_seconds(ent_ts)
                if ent_epoch is not None:
                    snap = r.get("intel_snapshot") if isinstance(r.get("intel_snapshot"), dict) else {}
                    adjs = snap.get("v2_uw_adjustments") if isinstance(snap.get("v2_uw_adjustments"), dict) else {}
                    v2_fams = sorted(list(active_v2_families_from_adjustments(adjs))) if adjs else []
                    if not v2_fams:
                        v2_fams = [FAMILY_UNKNOWN]
                    v2_entries_by_symbol.setdefault(sym, []).append(
                        {
                            "symbol": sym,
                            "v2_entry_ts": str(ent_ts or ""),
                            "_entry_epoch": ent_epoch,
                            "v2_score_at_entry": _safe_float(r.get("v2_score")),
                            "v2_price_at_entry": _safe_float(r.get("entry_price")),
                            "side": str(r.get("side") or ""),
                            "v2_feature_families": v2_fams,
                        }
                    )
            if et == "shadow_exit":
                shadow_exits.add(sym)

        overlap_candidates = sorted(list(v1_syms & shadow_candidates))
        overlap_entries = sorted(list(v1_syms & shadow_entries))

        v1_present = bool(v1_text.strip())
        shadow_present = bool(shadow_text.strip())

        # Entry parity rows (per symbol, best-effort)
        allowed_classifications = {"perfect_match", "near_match", "divergent", "missing_in_v1", "missing_in_v2"}
        entry_parity_rows: List[Dict[str, Any]] = []
        mean_ts_deltas: List[float] = []
        mean_score_deltas: List[float] = []
        mean_price_deltas: List[float] = []
        match_hits = 0
        match_total = 0
        class_counts: Dict[str, int] = {k: 0 for k in allowed_classifications}

        all_syms = sorted(set(list(v1_entries_by_symbol.keys()) + list(v2_entries_by_symbol.keys())))
        for sym in all_syms:
            v1_entries = v1_entries_by_symbol.get(sym, []) or []
            v2_entries = v2_entries_by_symbol.get(sym, []) or []
            paired, rem_v1, rem_v2 = _greedy_match_by_time(v1_entries, v2_entries)

            for r1, r2 in paired:
                missing_fields: List[str] = []
                v1_entry_ts = r1.get("v1_entry_ts")
                v2_entry_ts = r2.get("v2_entry_ts")
                e1 = r1.get("_entry_epoch")
                e2 = r2.get("_entry_epoch")
                entry_ts_delta_seconds = (float(e2) - float(e1)) if (e1 is not None and e2 is not None) else 0.0

                v1_score = _safe_float(r1.get("v1_score_at_entry"))
                v2_score = _safe_float(r2.get("v2_score_at_entry"))
                if v1_score is None:
                    missing_fields.append("v1_score_at_entry")
                if v2_score is None:
                    missing_fields.append("v2_score_at_entry")
                v1_score_n = float(v1_score) if v1_score is not None else 0.0
                v2_score_n = float(v2_score) if v2_score is not None else 0.0
                score_delta = float(v2_score_n - v1_score_n)

                v1_price = _safe_float(r1.get("v1_price_at_entry"))
                v2_price = _safe_float(r2.get("v2_price_at_entry"))
                if v1_price is None:
                    missing_fields.append("v1_price_at_entry")
                if v2_price is None:
                    missing_fields.append("v2_price_at_entry")
                v1_price_n = float(v1_price) if v1_price is not None else 0.0
                v2_price_n = float(v2_price) if v2_price is not None else 0.0
                price_delta_usd = float(v2_price_n - v1_price_n)

                cls = _classify(
                    entry_ts_delta_seconds=entry_ts_delta_seconds,
                    score_delta=score_delta,
                    price_delta_usd=price_delta_usd,
                    missing_fields=missing_fields,
                )
                if cls not in allowed_classifications:
                    cls = "divergent"

                match_total += 1
                if cls in ("perfect_match", "near_match"):
                    match_hits += 1
                class_counts[cls] = int(class_counts.get(cls, 0)) + 1

                if entry_ts_delta_seconds is not None:
                    mean_ts_deltas.append(float(entry_ts_delta_seconds))
                mean_score_deltas.append(float(score_delta))
                mean_price_deltas.append(float(price_delta_usd))

                entry_parity_rows.append(
                    {
                        "symbol": sym,
                        "v1_entry_ts": str(v1_entry_ts or ""),
                        "v2_entry_ts": str(v2_entry_ts or ""),
                        "entry_ts_delta_seconds": float(entry_ts_delta_seconds),
                        "v1_score_at_entry": float(v1_score_n),
                        "v2_score_at_entry": float(v2_score_n),
                        "score_delta": score_delta,
                        "v1_price_at_entry": float(v1_price_n),
                        "v2_price_at_entry": float(v2_price_n),
                        "price_delta_usd": price_delta_usd,
                        "classification": cls,
                        "missing_fields": sorted(list(set(missing_fields))),
                        "v1_side": str(r1.get("side") or ""),
                        "v2_side": str(r2.get("side") or ""),
                        "feature_family": str(r1.get("feature_family") or (r2.get("v2_feature_families") or [FAMILY_UNKNOWN])[0]),
                        "v2_feature_families": list(r2.get("v2_feature_families") or [FAMILY_UNKNOWN]),
                    }
                )

            for r1 in rem_v1:
                cls = "missing_in_v2"
                class_counts[cls] = int(class_counts.get(cls, 0)) + 1
                entry_parity_rows.append(
                    {
                        "symbol": sym,
                        "v1_entry_ts": str(r1.get("v1_entry_ts") or ""),
                        "v2_entry_ts": "",
                        "entry_ts_delta_seconds": 0.0,
                        "v1_score_at_entry": float(_safe_float(r1.get("v1_score_at_entry")) or 0.0),
                        "v2_score_at_entry": 0.0,
                        "score_delta": 0.0,
                        "v1_price_at_entry": float(_safe_float(r1.get("v1_price_at_entry")) or 0.0),
                        "v2_price_at_entry": 0.0,
                        "price_delta_usd": 0.0,
                        "classification": cls,
                        "missing_fields": ["v2_entry_ts", "v2_score_at_entry", "v2_price_at_entry"],
                        "v1_side": str(r1.get("side") or ""),
                        "v2_side": "",
                        "feature_family": str(r1.get("feature_family") or FAMILY_UNKNOWN),
                        "v2_feature_families": [FAMILY_UNKNOWN],
                    }
                )
            for r2 in rem_v2:
                cls = "missing_in_v1"
                class_counts[cls] = int(class_counts.get(cls, 0)) + 1
                entry_parity_rows.append(
                    {
                        "symbol": sym,
                        "v1_entry_ts": "",
                        "v2_entry_ts": str(r2.get("v2_entry_ts") or ""),
                        "entry_ts_delta_seconds": 0.0,
                        "v1_score_at_entry": 0.0,
                        "v2_score_at_entry": float(_safe_float(r2.get("v2_score_at_entry")) or 0.0),
                        "score_delta": 0.0,
                        "v1_price_at_entry": 0.0,
                        "v2_price_at_entry": float(_safe_float(r2.get("v2_price_at_entry")) or 0.0),
                        "price_delta_usd": 0.0,
                        "classification": cls,
                        "missing_fields": ["v1_entry_ts", "v1_score_at_entry", "v1_price_at_entry"],
                        "v1_side": "",
                        "v2_side": str(r2.get("side") or ""),
                        "feature_family": str((r2.get("v2_feature_families") or [FAMILY_UNKNOWN])[0]),
                        "v2_feature_families": list(r2.get("v2_feature_families") or [FAMILY_UNKNOWN]),
                    }
                )

        def _mean(xs: List[float]) -> float:
            return float(sum(xs) / float(len(xs))) if xs else 0.0

        return {
            "_meta": {"date": str(day), "kind": "shadow_vs_live_parity", "version": "2026-01-22_v2_entry_parity"},
            "inputs": {
                "v1_attribution_log_path": v1_attribution_log_path,
                "shadow_trades_log_path": shadow_trades_log_path,
                "v1_log_present": v1_present,
                "shadow_log_present": shadow_present,
            },
            "counts": {
                "v1_records_today": int(v1_recs),
                "v1_unique_symbols_today": int(len(v1_syms)),
                "shadow_records_today": int(shadow_recs),
                "shadow_candidate_symbols_today": int(len(shadow_candidates)),
                "shadow_entry_symbols_today": int(len(shadow_entries)),
                "shadow_exit_symbols_today": int(len(shadow_exits)),
                "v1_entry_events_today": int(sum(len(v) for v in v1_entries_by_symbol.values())),
                "v2_shadow_entry_events_today": int(sum(len(v) for v in v2_entries_by_symbol.values())),
                "entry_parity_rows": int(len(entry_parity_rows)),
            },
            "overlap": {
                "v1_vs_shadow_candidates_symbols": overlap_candidates,
                "v1_vs_shadow_entries_symbols": overlap_entries,
                "v1_only_symbols": sorted(list(v1_syms - shadow_candidates)),
                "shadow_only_candidate_symbols": sorted(list(shadow_candidates - v1_syms)),
            },
            "entry_parity": {
                "rows": entry_parity_rows,
                "allowed_classifications": sorted(list(allowed_classifications)),
                "classification_counts": class_counts,
            },
            "aggregate_metrics": {
                "mean_entry_ts_delta_seconds": _mean(mean_ts_deltas),
                "mean_score_delta": _mean(mean_score_deltas),
                "mean_price_delta_usd": _mean(mean_price_deltas),
                "match_rate": (float(match_hits) / float(match_total)) if match_total else 0.0,
                "matched_pairs": int(match_total),
            },
            "notes": {
                "parity_available": bool(v1_present and shadow_present),
                "missing_fields": [],
                "warning": "Best-effort: v1 entry fields are read from attribution.context; v2 entry fields from shadow_entry_opened. Uses greedy nearest-timestamp matching per symbol.",
            },
        }
    except Exception as e:
        return {"_meta": {"date": str(day), "kind": "shadow_vs_live_parity", "version": "2026-01-22_v2_entry_parity"}, "error": str(e)}

