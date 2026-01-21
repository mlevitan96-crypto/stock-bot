#!/usr/bin/env python3
"""
Exit Intelligence P&L Analytics (v2, shadow-only)
================================================

Reads:
- logs/exit_attribution.jsonl
- logs/shadow_trades.jsonl

Writes:
- state/exit_intel_pnl_summary.json
- reports/EXIT_INTEL_PNL_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else datetime.now(timezone.utc).date().isoformat()


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
            if isinstance(rec, dict):
                yield rec
        except Exception:
            continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    args = ap.parse_args()
    day = args.date.strip() or datetime.now(timezone.utc).date().isoformat()

    attr_path = Path("logs/exit_attribution.jsonl")
    rows = [r for r in _iter_jsonl(attr_path) if _day_utc(str(r.get("timestamp") or "")) == day]

    by_reason: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_reason_n: Dict[str, int] = defaultdict(int)
    by_regime: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_sector: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    time_bins = Counter()
    exit_scores: List[float] = []

    for r in rows:
        reason = str(r.get("exit_reason", "unknown") or "unknown")
        pnl = r.get("pnl")
        try:
            pnl_f = float(pnl) if pnl is not None else None
        except Exception:
            pnl_f = None
        tmin = r.get("time_in_trade_minutes")
        try:
            tmin_f = float(tmin) if tmin is not None else None
        except Exception:
            tmin_f = None
        reg = str(r.get("exit_regime", "") or "")
        sec = str(((r.get("exit_sector_profile") or {}) if isinstance(r.get("exit_sector_profile"), dict) else {}).get("sector", "UNKNOWN") or "UNKNOWN")
        try:
            es = float(r.get("v2_exit_score", 0.0) or 0.0)
            exit_scores.append(es)
        except Exception:
            pass

        by_reason_n[reason] += 1
        if pnl_f is not None:
            by_reason[reason]["sum_pnl"] += pnl_f
            by_reason[reason]["wins"] += 1.0 if pnl_f > 0 else 0.0
            by_regime[reg]["sum_pnl"] += pnl_f
            by_regime[reg]["n"] += 1.0
            by_sector[sec]["sum_pnl"] += pnl_f
            by_sector[sec]["n"] += 1.0

        if tmin_f is not None:
            if tmin_f < 30:
                time_bins["<30m"] += 1
            elif tmin_f < 120:
                time_bins["30-120m"] += 1
            elif tmin_f < 360:
                time_bins["2-6h"] += 1
            else:
                time_bins[">6h"] += 1

    summary_by_reason: Dict[str, Any] = {}
    for reason, n in by_reason_n.items():
        n_int = int(n)
        sum_pnl = float(by_reason[reason].get("sum_pnl", 0.0))
        wins = float(by_reason[reason].get("wins", 0.0))
        # Only compute averages when pnl present
        summary_by_reason[reason] = {
            "n": n_int,
            "avg_pnl": round(sum_pnl / max(1.0, float(n_int)), 6),
            "win_rate": round(wins / max(1.0, float(n_int)), 6),
        }

    def _avg_map(m: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in m.items():
            n = float(v.get("n", 0.0))
            out[k or ""] = {"n": int(n), "avg_pnl": round(float(v.get("sum_pnl", 0.0)) / max(1.0, n), 6)}
        return out

    doc = {
        "_meta": {"ts": _now_iso(), "date": day, "version": "2026-01-21_exit_pnl_v1"},
        "counts": {"exit_attributions": len(rows)},
        "by_exit_reason": summary_by_reason,
        "by_regime": _avg_map(by_regime),
        "by_sector": _avg_map(by_sector),
        "time_in_trade_bins": dict(time_bins),
        "exit_score_stats": {
            "n": len(exit_scores),
            "min": min(exit_scores) if exit_scores else None,
            "max": max(exit_scores) if exit_scores else None,
            "mean": round(sum(exit_scores) / len(exit_scores), 6) if exit_scores else None,
        },
    }

    Path("state").mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("state/exit_intel_pnl_summary.json").write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")

    report = Path("reports") / f"EXIT_INTEL_PNL_{day}.md"
    lines: List[str] = []
    lines.append(f"# Exit Intel P&L — {day}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Exit attributions: **{len(rows)}**")
    lines.append("")
    lines.append("## Win rate / Avg P&L by exit reason")
    for k in sorted(summary_by_reason.keys()):
        r = summary_by_reason[k]
        lines.append(f"- **{k}**: n={r['n']}, win_rate={r['win_rate']}, avg_pnl={r['avg_pnl']}")
    lines.append("")
    lines.append("## Regime impact (avg P&L)")
    for k, r in sorted(doc["by_regime"].items()):
        lines.append(f"- **{k or 'UNKNOWN'}**: n={r['n']}, avg_pnl={r['avg_pnl']}")
    lines.append("")
    lines.append("## Sector impact (avg P&L)")
    for k, r in sorted(doc["by_sector"].items()):
        lines.append(f"- **{k or 'UNKNOWN'}**: n={r['n']}, avg_pnl={r['avg_pnl']}")
    lines.append("")
    lines.append("## Time in trade distribution")
    lines.append(f"- {dict(time_bins)}")
    lines.append("")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

