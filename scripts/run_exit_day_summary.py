#!/usr/bin/env python3
"""
Exit Day Summary (v2, shadow-only)
=================================

Outputs:
- reports/EXIT_DAY_SUMMARY_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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

    attr = [r for r in _iter_jsonl(Path("logs/exit_attribution.jsonl")) if _day_utc(str(r.get("timestamp") or "")) == day]
    pnl = {}
    try:
        pnl = json.loads(Path("state/exit_intel_pnl_summary.json").read_text(encoding="utf-8"))
    except Exception:
        pnl = {}

    # Rank best/worst by pnl when present
    with_pnl = []
    for r in attr:
        p = r.get("pnl")
        try:
            p = float(p) if p is not None else None
        except Exception:
            p = None
        if p is None:
            continue
        with_pnl.append((p, r))
    best = sorted(with_pnl, key=lambda x: x[0], reverse=True)[:5]
    worst = sorted(with_pnl, key=lambda x: x[0])[:5]

    out = Path("reports") / f"EXIT_DAY_SUMMARY_{day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append(f"# Exit Day Summary (v2) — {day}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Exit attributions: **{len(attr)}**")
    lines.append("")
    lines.append("## Best exits (paper P&L, if available)")
    if not best:
        lines.append("- No P&L data available yet (exit_price not captured in shadow positions).")
    else:
        for p, r in best:
            lines.append(f"- **{r.get('symbol','')}** pnl={p} reason={r.get('exit_reason')}")
    lines.append("")
    lines.append("## Worst exits (paper P&L, if available)")
    if not worst:
        lines.append("- No P&L data available yet.")
    else:
        for p, r in worst:
            lines.append(f"- **{r.get('symbol','')}** pnl={p} reason={r.get('exit_reason')}")
    lines.append("")
    lines.append("## Exit score analysis")
    es = (pnl.get("exit_score_stats") if isinstance(pnl, dict) else {}) or {}
    lines.append(f"- exit_score_stats: `{es}`")
    lines.append("")
    lines.append("## UW deterioration patterns (placeholder)")
    lines.append("- Best-effort: uses components in `logs/exit_attribution.jsonl` (v2_exit_components).")
    lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

