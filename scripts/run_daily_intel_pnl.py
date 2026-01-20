#!/usr/bin/env python3
"""
Daily Intelligence P&L (additive)
================================

Inputs (best-effort):
- logs/uw_attribution.jsonl
- logs/exits.jsonl (real exits)
- logs/shadow.jsonl (shadow exits/pnl, if present)

Outputs:
- reports/UW_INTEL_PNL_YYYY-MM-DD.md
- state/uw_intel_pnl_summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.uw_intel_schema import validate_uw_intel_pnl_summary


ATTR_LOG = Path("logs/uw_attribution.jsonl")
EXITS_LOG = Path("logs/exits.jsonl")
SHADOW_LOG = Path("logs/shadow.jsonl")

OUT_REPORT_DIR = Path("reports")
OUT_STATE = Path("state/uw_intel_pnl_summary.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _day_utc(ts: str) -> str:
    # Accept ISO timestamps; fallback to today's date if malformed.
    try:
        # 2026-01-20T12:34:56+00:00
        return str(ts)[:10]
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if isinstance(rec, dict):
                    yield rec
            except Exception:
                continue
    except Exception:
        return


def _extract_pnl_by_symbol_for_day(day: str) -> Dict[str, float]:
    """
    Best-effort realized PnL pct by symbol for the given day.
    Preference order: real exits -> shadow exits.
    """
    pnl: Dict[str, float] = {}

    # Real exits
    for rec in _iter_jsonl(EXITS_LOG):
        ts = str(rec.get("ts") or rec.get("timestamp") or "")
        if _day_utc(ts) != day:
            continue
        sym = str(rec.get("symbol") or "").upper()
        if not sym:
            continue
        v = rec.get("pnl_pct")
        if v is None:
            v = rec.get("pnl_percent")
        try:
            pnl[sym] = float(v)  # overwrite with last seen
        except Exception:
            continue

    # Shadow exits / pnl (only fill missing symbols)
    for rec in _iter_jsonl(SHADOW_LOG):
        ts = str(rec.get("ts") or rec.get("timestamp") or "")
        if _day_utc(ts) != day:
            continue
        sym = str(rec.get("symbol") or "").upper()
        if not sym or sym in pnl:
            continue
        v = rec.get("pnl_pct")
        if v is None:
            v = rec.get("shadow_pnl_pct")
        if v is None:
            v = rec.get("pnl_percent")
        try:
            pnl[sym] = float(v)
        except Exception:
            continue

    return pnl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default: today UTC)")
    args = ap.parse_args()

    day = args.date.strip() or datetime.now(timezone.utc).date().isoformat()
    pnl_by_symbol = _extract_pnl_by_symbol_for_day(day)

    # Aggregate by UW feature using attribution records.
    by_feature: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_feature_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    attr_count = 0
    matched_count = 0
    for rec in _iter_jsonl(ATTR_LOG):
        ts = str(rec.get("timestamp") or "")
        if _day_utc(ts) != day:
            continue
        attr_count += 1
        sym = str(rec.get("symbol") or "").upper()
        feat = rec.get("uw_features") if isinstance(rec.get("uw_features"), dict) else {}
        contrib = rec.get("uw_contribution") if isinstance(rec.get("uw_contribution"), dict) else {}
        score_delta = float(contrib.get("score_delta", 0.0) or 0.0)

        pnl = pnl_by_symbol.get(sym)
        if pnl is None:
            continue
        matched_count += 1
        win = 1 if pnl > 0 else 0

        # Track a small, consistent set of feature keys.
        keys = [
            "flow_strength",
            "darkpool_bias",
            "sentiment",
            "earnings_proximity",
            "sector_alignment",
            "regime_alignment",
        ]
        for k in keys:
            v = feat.get(k)
            # Map sentiment to numeric for aggregation
            if k == "sentiment":
                s = str(v or "NEUTRAL").upper()
                v_num = 1.0 if s == "BULLISH" else (-1.0 if s == "BEARISH" else 0.0)
            else:
                try:
                    v_num = float(v) if v is not None else 0.0
                except Exception:
                    v_num = 0.0
            by_feature[k]["examples"] += 1.0
            by_feature[k]["sum_feature_value"] += float(v_num)
            by_feature[k]["sum_score_delta"] += float(score_delta)
            by_feature[k]["sum_pnl_pct"] += float(pnl)
            by_feature[k]["sum_wins"] += float(win)
            by_feature_counts[k]["n"] += 1

    # Finalize summary
    summary_by_feature: Dict[str, Any] = {}
    for k, agg in by_feature.items():
        n = int(by_feature_counts[k].get("n", 0))
        if n <= 0:
            continue
        summary_by_feature[k] = {
            "n": n,
            "avg_feature_value": round(float(agg.get("sum_feature_value", 0.0)) / n, 6),
            "avg_score_delta": round(float(agg.get("sum_score_delta", 0.0)) / n, 6),
            "avg_pnl_pct": round(float(agg.get("sum_pnl_pct", 0.0)) / n, 6),
            "win_rate": round(float(agg.get("sum_wins", 0.0)) / n, 6),
        }

    doc = {
        "_meta": {"ts": _now_iso(), "date": day, "version": "2026-01-20_uw_intel_pnl_v1"},
        "inputs": {
            "attribution_log_exists": ATTR_LOG.exists(),
            "exits_log_exists": EXITS_LOG.exists(),
            "shadow_log_exists": SHADOW_LOG.exists(),
        },
        "counts": {"attribution_records": attr_count, "matched_to_pnl": matched_count},
        "by_feature": summary_by_feature,
    }

    ok, msg = validate_uw_intel_pnl_summary(doc)
    if not ok:
        print(f"intel pnl schema invalid: {msg}")
        return 2

    OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_STATE.parent.mkdir(parents=True, exist_ok=True)
    OUT_STATE.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")

    report_path = OUT_REPORT_DIR / f"UW_INTEL_PNL_{day}.md"
    lines: List[str] = []
    lines.append(f"# UW Intel P&L — {day}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Attribution records: **{attr_count}**")
    lines.append(f"- Matched to P&L: **{matched_count}**")
    lines.append("")
    lines.append("## Per-feature aggregates (best-effort)")
    if not summary_by_feature:
        lines.append("- No matches available yet (missing exits/shadow PnL or no attribution records).")
    else:
        for k in sorted(summary_by_feature.keys()):
            r = summary_by_feature[k]
            lines.append(f"- **{k}**: n={r['n']}, win_rate={r['win_rate']}, avg_pnl_pct={r['avg_pnl_pct']}, avg_score_delta={r['avg_score_delta']}")
    lines.append("")
    lines.append("## Notes")
    lines.append("- This report is **additive** and may be sparse until exit logs or shadow PnL are available.")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

