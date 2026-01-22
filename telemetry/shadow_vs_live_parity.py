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
from typing import Any, Dict, Iterable, List, Optional, Set


def _utc_day_from_ts(ts: Any) -> Optional[str]:
    if ts is None:
        return None
    s = str(ts).strip()
    if len(s) >= 10:
        return s[:10]
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
        for r in _iter_jsonl_text(v1_text):
            ts = r.get("ts") or r.get("timestamp")
            if _utc_day_from_ts(ts) != day:
                continue
            sym = str(r.get("symbol", "") or "").upper()
            if sym:
                v1_syms.add(sym)
                v1_recs += 1

        shadow_candidates: Set[str] = set()
        shadow_entries: Set[str] = set()
        shadow_exits: Set[str] = set()
        shadow_recs = 0
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
            if et == "shadow_exit":
                shadow_exits.add(sym)

        overlap_candidates = sorted(list(v1_syms & shadow_candidates))
        overlap_entries = sorted(list(v1_syms & shadow_entries))

        v1_present = bool(v1_text.strip())
        shadow_present = bool(shadow_text.strip())

        return {
            "_meta": {"date": str(day), "kind": "shadow_vs_live_parity", "version": "2026-01-22_v1"},
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
            },
            "overlap": {
                "v1_vs_shadow_candidates_symbols": overlap_candidates,
                "v1_vs_shadow_entries_symbols": overlap_entries,
                "v1_only_symbols": sorted(list(v1_syms - shadow_candidates)),
                "shadow_only_candidate_symbols": sorted(list(shadow_candidates - v1_syms)),
            },
            "notes": {
                "parity_available": bool(v1_present and shadow_present),
                "warning": "Best-effort: uses v1 attribution log if present; schema may vary across versions.",
            },
        }
    except Exception as e:
        return {"_meta": {"date": str(day), "kind": "shadow_vs_live_parity", "version": "2026-01-22_v1"}, "error": str(e)}

