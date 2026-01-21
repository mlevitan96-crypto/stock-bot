#!/usr/bin/env python3
"""
Shadow Day Summary (v2)
=======================

Inputs:
- logs/shadow_trades.jsonl
- logs/uw_attribution.jsonl (tail)
- state/uw_intel_pnl_summary.json
- state/regime_state.json

Output:
- reports/SHADOW_DAY_SUMMARY_YYYY-MM-DD.md
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


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else datetime.now(timezone.utc).date().isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


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


def _side_from_direction(direction: str) -> str:
    d = str(direction or "").lower()
    if d in ("bearish", "short", "sell"):
        return "short"
    return "long"


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _compute_pnl_usd_pct(entry_price: float, exit_price: float, qty: float, side: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        e = float(entry_price)
        x = float(exit_price)
        q = float(qty)
        if e <= 0 or x <= 0 or q <= 0:
            return None, None
        pnl = q * (e - x) if str(side) == "short" else q * (x - e)
        pct = pnl / (q * e) if (q * e) > 0 else None
        return float(pnl), (float(pct) if pct is not None else None)
    except Exception:
        return None, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    args = ap.parse_args()
    day = args.date.strip() or datetime.now(timezone.utc).date().isoformat()

    shadow_path = Path("logs/shadow_trades.jsonl")
    attrib_path = Path("logs/uw_attribution.jsonl")
    pnl = _read_json(Path("state/uw_intel_pnl_summary.json"))
    regime = _read_json(Path("state/regime_state.json"))

    trades = []
    entries: Dict[str, Dict[str, Any]] = {}
    exits: Dict[str, Dict[str, Any]] = {}
    for rec in _iter_jsonl(shadow_path):
        if _day_utc(str(rec.get("ts") or "")) != day:
            continue
        et = str(rec.get("event_type", "") or "")
        if et == "shadow_trade_candidate":
            trades.append(rec)
        elif et == "shadow_entry_opened":
            tid = str(rec.get("trade_id") or "") or f"{rec.get('symbol','')}-{rec.get('entry_ts','')}"
            entries[tid] = rec
        elif et == "shadow_exit":
            tid = str(rec.get("trade_id") or "") or f"{rec.get('symbol','')}-{rec.get('entry_ts','')}"
            exits[tid] = rec

    sectors = []
    syms = []
    v2_scores = []
    v1_scores = []
    for r in trades:
        syms.append(str(r.get("symbol", "")))
        v2_scores.append(float(r.get("v2_score", 0.0) or 0.0))
        v1_scores.append(float(r.get("v1_score", 0.0) or 0.0))
        snap = r.get("uw_attribution_snapshot") if isinstance(r.get("uw_attribution_snapshot"), dict) else {}
        sec = ((snap.get("v2_uw_sector_profile") or {}) if isinstance(snap.get("v2_uw_sector_profile"), dict) else {}).get("sector", "UNKNOWN")
        sectors.append(str(sec))

    # Biggest "winners/losers" are best-effort: rank by v2_score (no realized P&L in this log yet)
    ranked = sorted(trades, key=lambda x: float(x.get("v2_score", 0.0) or 0.0), reverse=True)
    top = ranked[:5]
    bottom = list(reversed(ranked[-5:])) if ranked else []

    # UW feature usage summary: count non-zero adjustments
    feat_counts = Counter()
    for r in trades:
        snap = r.get("uw_attribution_snapshot") if isinstance(r.get("uw_attribution_snapshot"), dict) else {}
        adj = snap.get("v2_uw_adjustments") if isinstance(snap.get("v2_uw_adjustments"), dict) else {}
        for k, v in adj.items():
            if k == "total":
                continue
            try:
                if abs(float(v)) > 1e-6:
                    feat_counts[k] += 1
            except Exception:
                continue

    out = Path("reports") / f"SHADOW_DAY_SUMMARY_{day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append(f"# Shadow Day Summary (v2) — {day}")
    lines.append("")
    lines.append("## 1. Overview")
    lines.append(f"- Shadow trade candidates: **{len(trades)}**")
    lines.append(f"- Unique symbols: **{len(set(syms))}**")
    lines.append(f"- Sectors: **{dict(Counter(sectors))}**")
    lines.append("")

    lines.append("## 2. Biggest would-be winners/losers (by v2 score, best-effort)")
    if not trades:
        lines.append("- No shadow trade candidates logged.")
    else:
        lines.append("### Top 5")
        for r in top:
            lines.append(f"- **{r.get('symbol','')}** v2_score={r.get('v2_score')} v1_score={r.get('v1_score')} dir={r.get('direction')}")
        lines.append("")
        lines.append("### Bottom 5")
        for r in bottom:
            lines.append(f"- **{r.get('symbol','')}** v2_score={r.get('v2_score')} v1_score={r.get('v1_score')} dir={r.get('direction')}")
    lines.append("")

    lines.append("## 3. UW feature usage summary (count of non-zero adjustments)")
    if feat_counts:
        for k, c in feat_counts.most_common():
            lines.append(f"- **{k}**: {c}")
    else:
        lines.append("- No UW adjustment usage detected in logged candidates.")
    lines.append("")

    lines.append("## 4. Regime timeline vs v2 behavior (snapshot)")
    if regime:
        lines.append(f"- Regime: **{regime.get('regime_label','NEUTRAL')}** (conf {regime.get('regime_confidence',0.0)})")
    else:
        lines.append("- Regime state missing.")
    lines.append("")

    lines.append("## 5. Paper P&L (realized, best-effort)")
    realized: List[Dict[str, Any]] = []
    for tid, ent in entries.items():
        ex = exits.get(tid)
        if not isinstance(ex, dict):
            continue
        sym = str(ent.get("symbol", "") or ex.get("symbol", "")).upper()
        side = str(ent.get("side") or _side_from_direction(str(ent.get("direction", ""))))
        ep = _safe_float(ent.get("entry_price"))
        xp = _safe_float(ex.get("exit_price"))
        qty = _safe_float(ex.get("qty") or ent.get("qty") or 0.0) or 0.0
        pnl_usd = _safe_float(ex.get("pnl"))
        pnl_pct = _safe_float(ex.get("pnl_pct"))
        if pnl_usd is None and ep is not None and xp is not None and qty > 0:
            pnl_usd, pnl_pct = _compute_pnl_usd_pct(ep, xp, qty, side)

        sec = "UNKNOWN"
        reg_lbl = ""
        try:
            snap = ent.get("intel_snapshot") if isinstance(ent.get("intel_snapshot"), dict) else {}
            sp = snap.get("v2_uw_sector_profile") if isinstance(snap.get("v2_uw_sector_profile"), dict) else {}
            rp = snap.get("v2_uw_regime_profile") if isinstance(snap.get("v2_uw_regime_profile"), dict) else {}
            sec = str(sp.get("sector", sec) or sec)
            reg_lbl = str(rp.get("regime_label", "") or "")
        except Exception:
            pass

        realized.append(
            {
                "trade_id": tid,
                "symbol": sym,
                "side": side,
                "entry_price": ep,
                "exit_price": xp,
                "qty": qty,
                "pnl_usd": pnl_usd,
                "pnl_pct": pnl_pct,
                "exit_reason": str(ex.get("v2_exit_reason", "") or ""),
                "sector": sec,
                "regime": reg_lbl,
            }
        )

    if not realized:
        lines.append("- No realized shadow exits logged today (need `shadow_entry_opened` + `shadow_exit`).")
    else:
        total_pnl = sum(float(r.get("pnl_usd") or 0.0) for r in realized if r.get("pnl_usd") is not None)
        wins = sum(1 for r in realized if (r.get("pnl_usd") is not None and float(r.get("pnl_usd") or 0.0) > 0))
        lines.append(f"- Closed shadow trades: **{len(realized)}**")
        lines.append(f"- Total realized PnL (USD): **{round(total_pnl, 2)}**")
        lines.append(f"- Win rate: **{round((wins / max(1, len(realized))) * 100.0, 2)}%**")
        lines.append("")

        by_sym = defaultdict(float)
        by_sec = defaultdict(float)
        by_reg = defaultdict(float)
        for r in realized:
            p = float(r.get("pnl_usd") or 0.0)
            by_sym[str(r.get("symbol", ""))] += p
            by_sec[str(r.get("sector", "UNKNOWN") or "UNKNOWN")] += p
            by_reg[str(r.get("regime", "") or "")] += p

        lines.append("### PnL by symbol (USD)")
        for k, v in sorted(by_sym.items(), key=lambda kv: kv[1], reverse=True)[:20]:
            lines.append(f"- **{k}**: {round(v, 2)}")
        lines.append("")
        lines.append("### PnL by sector (USD)")
        for k, v in sorted(by_sec.items(), key=lambda kv: kv[1], reverse=True)[:20]:
            lines.append(f"- **{k or 'UNKNOWN'}**: {round(v, 2)}")
        lines.append("")
        lines.append("### PnL by regime (USD)")
        for k, v in sorted(by_reg.items(), key=lambda kv: kv[1], reverse=True)[:20]:
            lines.append(f"- **{k or 'UNKNOWN'}**: {round(v, 2)}")
        lines.append("")
        lines.append("### Closed trades (details, up to 20)")
        for r in realized[:20]:
            lines.append(
                f"- **{r.get('symbol')}** side={r.get('side')} qty={r.get('qty')} "
                f"entry={r.get('entry_price')} exit={r.get('exit_price')} "
                f"pnl_usd={r.get('pnl_usd')} reason={r.get('exit_reason')} sector={r.get('sector')} regime={r.get('regime')}"
            )
    lines.append("")

    lines.append("## Inputs")
    lines.append(f"- shadow_trades: `{shadow_path}` exists={shadow_path.exists()}")
    lines.append(f"- uw_attribution: `{attrib_path}` exists={attrib_path.exists()}")
    lines.append(f"- uw_intel_pnl_summary: `state/uw_intel_pnl_summary.json` exists={Path('state/uw_intel_pnl_summary.json').exists()}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

