#!/usr/bin/env python3
"""
Scoring pipeline auditor (open positions).

Outputs:
1) Table: symbol | entry_score | current_score | delta | last_score_update
2) For 5-10 symbols: raw inputs, component scores, final composite.
3) Verdict: Are current scores meaningful? YES/NO/UNKNOWN

Data sources (best-effort):
- Open positions: state/position_metadata.json
- Current scores: logs/scoring_flow.jsonl (msg == composite_calculated)
- UW cache: data/uw_flow_cache.json (for recomputation + feature variance)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


STATE_POS_META = Path("state/position_metadata.json")
LOG_SCORING_FLOW = Path("logs/scoring_flow.jsonl")
UW_CACHE = Path("data/uw_flow_cache.json")


def _safe_json_load(p: Path, default: Any) -> Any:
    try:
        if not p.exists():
            return default
        raw = p.read_text(encoding="utf-8", errors="ignore")
        if not raw.strip():
            return default
        return json.loads(raw)
    except Exception:
        return default


def _tail_jsonl(p: Path, max_lines: int = 20000) -> List[dict]:
    if not p.exists():
        return []
    try:
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        lines = lines[-max_lines:]
        rows = []
        for ln in lines:
            ln = (ln or "").strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                continue
        return rows
    except Exception:
        return []


def _parse_ts(ts: Optional[str]) -> Optional[str]:
    if not ts:
        return None
    try:
        # scoring_flow uses ISO in main.py (now_iso)
        return str(ts)
    except Exception:
        return None


def _last_score_by_symbol(scoring_rows: List[dict]) -> Dict[str, Tuple[float, Optional[str]]]:
    out: Dict[str, Tuple[float, Optional[str]]] = {}
    for r in scoring_rows:
        if r.get("msg") != "composite_calculated":
            continue
        sym = r.get("symbol")
        if not sym:
            continue
        try:
            score = float(r.get("score", 0.0) or 0.0)
        except Exception:
            score = 0.0
        out[str(sym)] = (score, _parse_ts(r.get("ts")))
    return out


def _fmt(x: Any) -> str:
    try:
        if x is None:
            return "-"
        if isinstance(x, float):
            return f"{x:.3f}"
        return str(x)
    except Exception:
        return "-"


def _print_table(rows: List[List[str]], headers: List[str]) -> None:
    cols = len(headers)
    widths = [len(h) for h in headers]
    for r in rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(r[i]))
    fmt = " | ".join("{:" + str(w) + "}" for w in widths)
    sep = "-+-".join("-" * w for w in widths)
    print(fmt.format(*headers))
    print(sep)
    for r in rows:
        print(fmt.format(*r))


def main() -> int:
    pos_meta = _safe_json_load(STATE_POS_META, {})
    if not isinstance(pos_meta, dict):
        pos_meta = {}
    held = sorted([s for s in pos_meta.keys() if isinstance(s, str) and s and not s.startswith("_")])

    scoring_rows = _tail_jsonl(LOG_SCORING_FLOW, max_lines=80000)
    last_scores = _last_score_by_symbol(scoring_rows)

    table_rows: List[List[str]] = []
    current_scores: List[float] = []
    for sym in held:
        entry = 0.0
        try:
            entry = float((pos_meta.get(sym) or {}).get("entry_score", 0.0) or 0.0)
        except Exception:
            entry = 0.0
        cur, ts = last_scores.get(sym, (None, None))  # type: ignore[assignment]
        cur_score = float(cur) if cur is not None else None
        if cur_score is not None:
            current_scores.append(cur_score)
        delta = (cur_score - entry) if (cur_score is not None) else None
        table_rows.append([
            sym,
            _fmt(entry),
            _fmt(cur_score),
            _fmt(delta),
            ts or "-",
        ])

    print("\n=== 1) Open positions: entry vs current score ===\n")
    if not held:
        print("No open positions found in state/position_metadata.json (file missing or empty).")
    else:
        _print_table(table_rows, ["symbol", "entry_score", "current_score", "delta", "last_score_update"])

    print("\n=== 2) Scoring pipeline diagnosis (sample symbols) ===\n")
    uw_cache = _safe_json_load(UW_CACHE, {})
    if not isinstance(uw_cache, dict):
        uw_cache = {}

    sample = held[:10] if held else [s for s in uw_cache.keys() if isinstance(s, str) and not s.startswith("_")][:10]
    if not sample:
        print("No symbols available to diagnose (missing state + missing data/uw_flow_cache.json).")
    else:
        try:
            import uw_enrichment_v2 as uw_enrich
            import uw_composite_v2 as uw_comp
        except Exception as e:
            print(f"Cannot import scoring modules (uw_enrichment_v2/uw_composite_v2): {e}")
            uw_enrich = None  # type: ignore
            uw_comp = None  # type: ignore

        for sym in sample:
            raw = uw_cache.get(sym, {})
            if not isinstance(raw, dict):
                continue
            print(f"\n--- {sym} ---")
            if uw_enrich and uw_comp:
                enriched = uw_enrich.enrich_signal(sym, uw_cache, "mixed") or raw
                composite = uw_comp.compute_composite_score_v3(sym, enriched, "mixed") or {}
                # Raw feature inputs (high-signal)
                inputs = {
                    "sentiment": enriched.get("sentiment"),
                    "conviction": enriched.get("conviction"),
                    "freshness": enriched.get("freshness"),
                    "dark_pool_notional_1h": (enriched.get("dark_pool", {}) or {}).get("total_notional_1h"),
                    "trade_count": enriched.get("trade_count"),
                }
                print("raw_inputs:", json.dumps(inputs, default=str))
                print("components:", json.dumps(composite.get("components", {}), default=str))
                print("score:", composite.get("score"))
                print("notes:", composite.get("notes"))
            else:
                print("raw_cache_keys:", sorted(list(raw.keys()))[:25])

    print("\n=== 3) Verdict: Are current scores meaningful? ===\n")
    verdict = "UNKNOWN"
    if len(current_scores) >= 5:
        mean = sum(current_scores) / len(current_scores)
        var = sum((x - mean) ** 2 for x in current_scores) / len(current_scores)
        stdev = math.sqrt(var)
        # Heuristic: tight clustering is suspicious unless market is truly flat.
        verdict = "NO" if stdev < 0.10 else "YES"
        print(f"n={len(current_scores)} mean={mean:.3f} stdev={stdev:.3f} -> {verdict}")
    elif len(current_scores) > 0:
        print(f"Only {len(current_scores)} current_score values found; cannot judge variance robustly.")
    else:
        print("No current scores found (missing logs/scoring_flow.jsonl).")
    print(f"\nAnswer: {verdict}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

