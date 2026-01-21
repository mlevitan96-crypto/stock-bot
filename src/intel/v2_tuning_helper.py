#!/usr/bin/env python3
"""
V2 tuning helper (suggestions only; no auto-tuning)
==================================================

Reads:
- state/uw_intel_pnl_summary.json
- logs/uw_attribution.jsonl (tail)

Writes:
- reports/V2_TUNING_SUGGESTIONS_YYYY-MM-DD.md

Contract:
- Additive and safe-by-default.
- Produces suggestions (nudges) but never applies any config changes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _tail_jsonl(path: Path, n: int = 200) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def _suggest_nudge(win_rate: float, avg_pnl: float) -> float:
    """
    Returns a suggested multiplier delta (e.g. +0.10 means +10%).
    Conservative: small nudges only.
    """
    try:
        if win_rate >= 0.60 and avg_pnl > 0:
            return +0.10
        if win_rate <= 0.40 and avg_pnl < 0:
            return -0.15
        if win_rate >= 0.55 and avg_pnl > 0:
            return +0.05
        if win_rate <= 0.45 and avg_pnl < 0:
            return -0.05
    except Exception:
        pass
    return 0.0


def generate_report(date: str = "") -> Path:
    day = date.strip() or _today_utc()
    pnl = _read_json(Path("state/uw_intel_pnl_summary.json"))
    attrib_tail = _tail_jsonl(Path("logs/uw_attribution.jsonl"), n=200)

    byf = pnl.get("by_feature") if isinstance(pnl.get("by_feature"), dict) else {}
    suggestions: List[Tuple[str, float, Dict[str, Any]]] = []
    for feat in ("flow_strength", "darkpool_bias", "sentiment", "earnings_proximity", "sector_alignment", "regime_alignment"):
        r = byf.get(feat)
        if not isinstance(r, dict):
            continue
        win_rate = float(r.get("win_rate", 0.0) or 0.0)
        avg_pnl = float(r.get("avg_pnl_pct", 0.0) or 0.0)
        delta = _suggest_nudge(win_rate, avg_pnl)
        suggestions.append((feat, delta, {"win_rate": win_rate, "avg_pnl_pct": avg_pnl, "n": int(r.get("n", 0) or 0)}))

    out = Path("reports") / f"V2_TUNING_SUGGESTIONS_{day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append(f"# V2 Tuning Suggestions — {day}")
    lines.append("")
    lines.append("## Scope")
    lines.append("- Suggestions only (no auto-tuning). Apply manually by adjusting `COMPOSITE_WEIGHTS_V2['uw']` weight multipliers.")
    lines.append("")

    lines.append("## Suggested UW weight nudges (multipliers)")
    if not suggestions:
        lines.append("- No P&L summary available yet (or no matches).")
    else:
        for feat, delta, meta in suggestions:
            if abs(delta) < 1e-9:
                continue
            sign = "+" if delta >= 0 else ""
            lines.append(f"- **{feat}_weight**: {sign}{int(delta*100)}%  (win_rate={meta['win_rate']}, avg_pnl_pct={meta['avg_pnl_pct']}, n={meta['n']})")
        if all(abs(d) < 1e-9 for _, d, _ in suggestions):
            lines.append("- No strong signals for nudges yet; keep weights unchanged.")
    lines.append("")

    lines.append("## Rationale (best-effort)")
    lines.append("- Uses `state/uw_intel_pnl_summary.json` aggregates and a tail of `logs/uw_attribution.jsonl` to contextualize what the model is using.")
    lines.append("")

    lines.append("## Attribution tail (sample)")
    for rec in attrib_tail[-10:]:
        sym = rec.get("symbol", "")
        d = rec.get("direction", "")
        c = (rec.get("uw_contribution") or {}).get("score_delta", 0.0) if isinstance(rec.get("uw_contribution"), dict) else 0.0
        lines.append(f"- **{sym}** dir={d} uw_score_delta={c}")
    lines.append("")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    p = generate_report("")
    print(str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

