#!/usr/bin/env python3
"""
Strict-scope quant edge analysis — actionable aggregates from exit_attribution (Workstreams B–H lite).

Filters to the same strict cohort as export_strict_quant_edge_review_cohort / evaluate_completeness.
Writes Markdown + JSON under reports/ for board review (not a substitute for full trade_facts / SPI).

Usage:
  PYTHONPATH=. python3 scripts/audit/run_strict_quant_edge_analysis.py --root /root/stock-bot \\
    --open-ts-epoch 1774458080
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)


def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _norm_reason(s: Any) -> str:
    t = str(s or "unknown").strip().lower()
    return t[:120] if t else "unknown"


def _norm_side(rec: dict) -> str:
    s = str(rec.get("side") or rec.get("direction") or "long").strip().upper()
    if s in ("BUY", "LONG"):
        return "LONG"
    if s in ("SELL", "SHORT"):
        return "SHORT"
    return s or "UNKNOWN"


def _load_exit_by_trade_id(root: Path) -> Dict[str, dict]:
    """Last row per trade_id from primary + strict_backfill exit_attribution."""
    out: Dict[str, dict] = {}
    logs = root / "logs"
    for name in ("exit_attribution.jsonl", "strict_backfill_exit_attribution.jsonl"):
        p = logs / name
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tid = rec.get("trade_id")
                if tid:
                    out[str(tid)] = rec
    return out


def _component_keys(rec: dict) -> List[str]:
    comp = rec.get("v2_exit_components")
    if not isinstance(comp, dict):
        return []
    return sorted(str(k) for k in comp.keys() if k)


def _rollup(rows: List[dict]) -> Tuple[List[dict], Dict[str, Any]]:
    pnls = [_safe_float(r.get("pnl")) for r in rows]
    valid = [p for p in pnls if p is not None]
    n = len(rows)
    n_pnl = len(valid)

    by_reason: Dict[str, List[float]] = defaultdict(list)
    by_side: Dict[str, List[float]] = defaultdict(list)
    by_entry_reg: Dict[str, List[float]] = defaultdict(list)
    by_exit_reg: Dict[str, List[float]] = defaultdict(list)
    hold_times: List[float] = []
    v2_scores: List[float] = []

    for r in rows:
        p = _safe_float(r.get("pnl"))
        if p is None:
            continue
        by_reason[_norm_reason(r.get("exit_reason"))].append(p)
        by_side[_norm_side(r)].append(p)
        by_entry_reg[str(r.get("entry_regime") or "UNKNOWN").strip() or "UNKNOWN"].append(p)
        by_exit_reg[str(r.get("exit_regime") or "UNKNOWN").strip() or "UNKNOWN"].append(p)
        hm = _safe_float(r.get("time_in_trade_minutes"))
        if hm is not None:
            hold_times.append(hm)
        vs = _safe_float(r.get("v2_exit_score"))
        if vs is not None:
            v2_scores.append(vs)

    def _slice_stats(groups: Dict[str, List[float]]) -> List[dict]:
        out = []
        for k, vals in sorted(groups.items(), key=lambda x: -len(x[1])):
            s = sum(vals)
            out.append(
                {
                    "bucket": k,
                    "n": len(vals),
                    "sum_pnl_usd": round(s, 4),
                    "avg_pnl_usd": round(s / len(vals), 4) if vals else 0.0,
                    "win_rate": round(sum(1 for v in vals if v > 0) / len(vals), 4) if vals else 0.0,
                }
            )
        return out

    # Component participation (exit-time v2 components)
    comp_when_present: Dict[str, List[float]] = defaultdict(list)
    for r in rows:
        p = _safe_float(r.get("pnl"))
        if p is None:
            continue
        keys = _component_keys(r)
        if not keys:
            continue
        for ck in keys:
            comp_when_present[ck].append(p)

    comp_stats = []
    for ck, vals in sorted(comp_when_present.items(), key=lambda x: -abs(sum(x[1]))):
        if len(vals) < 3:
            continue
        s = sum(vals)
        comp_stats.append(
            {
                "component": ck,
                "n": len(vals),
                "sum_pnl_usd": round(s, 4),
                "avg_pnl_usd": round(s / len(vals), 4),
                "win_rate": round(sum(1 for v in vals if v > 0) / len(vals), 4),
            }
        )
    comp_stats = sorted(comp_stats, key=lambda x: x["avg_pnl_usd"])

    summary = {
        "trades_in_cohort": n,
        "trades_with_pnl": n_pnl,
        "sum_pnl_usd": round(sum(valid), 4) if valid else None,
        "avg_pnl_usd": round(statistics.mean(valid), 4) if valid else None,
        "median_pnl_usd": round(statistics.median(valid), 4) if valid else None,
        "win_rate": round(sum(1 for v in valid if v > 0) / len(valid), 4) if valid else None,
        "avg_hold_minutes": round(statistics.mean(hold_times), 2) if hold_times else None,
        "avg_v2_exit_score": round(statistics.mean(v2_scores), 4) if v2_scores else None,
        "by_exit_reason": _slice_stats(by_reason),
        "by_side": _slice_stats(by_side),
        "by_entry_regime": _slice_stats(by_entry_reg),
        "by_exit_regime": _slice_stats(by_exit_reg),
        "exit_v2_component_expectancy": comp_stats[:40],
    }
    return comp_stats, summary


def _suggest_actions(summary: Dict[str, Any]) -> List[dict]:
    """Heuristic HOW prompts — human/board must confirm."""
    out: List[dict] = []
    for row in summary.get("by_exit_reason") or []:
        n, avg, s = row.get("n", 0), row.get("avg_pnl_usd", 0), row.get("sum_pnl_usd", 0)
        if n < 5:
            continue
        if avg < -0.5 and s < -5:
            out.append(
                {
                    "topic": "exit_reason",
                    "bucket": row["bucket"],
                    "signal": "negative_expectancy",
                    "suggested_levers": ["CHANGE_EXIT", "GATE"],
                    "how": (
                        f"Exit reason `{row['bucket']}` has avg_pnl={avg} over n={n}. "
                        "Review v2 thresholds / time-exit vs stop mix; consider gating entries when this exit dominates."
                    ),
                    "confidence": "medium",
                }
            )
        elif avg > 1.0 and n >= 10:
            out.append(
                {
                    "topic": "exit_reason",
                    "bucket": row["bucket"],
                    "signal": "positive_expectancy",
                    "suggested_levers": ["KEEP", "SIZE"],
                    "how": (
                        f"Exit reason `{row['bucket']}` contributes avg_pnl={avg} (n={n}). "
                        "Success review: test scale-up only if not regime-fragile."
                    ),
                    "confidence": "medium",
                }
            )

    sides = {r["bucket"]: r for r in (summary.get("by_side") or [])}
    for side in ("LONG", "SHORT"):
        r = sides.get(side)
        if not r or r.get("n", 0) < 8:
            continue
        avg = r.get("avg_pnl_usd", 0)
        if avg < -0.3:
            out.append(
                {
                    "topic": "direction",
                    "bucket": side,
                    "signal": "weak_side",
                    "suggested_levers": ["FLIP", "GATE", "SIZE"],
                    "how": (
                        f"Side {side} avg_pnl={avg} (n={r['n']}). "
                        "Board: structural short/long bias? Consider separate thresholds or size down this side."
                    ),
                    "confidence": "low",
                }
            )

    worst = (summary.get("exit_v2_component_expectancy") or [])[:5]
    for row in worst:
        if row.get("avg_pnl_usd", 0) > -0.2:
            break
        if row.get("n", 0) < 8:
            continue
        out.append(
            {
                "topic": "exit_v2_component",
                "bucket": row["component"],
                "signal": "toxic_exit_component_mass",
                "suggested_levers": ["GATE", "KILL"],
                "how": (
                    f"When `{row['component']}` is non-zero at exit, avg_pnl={row['avg_pnl_usd']} (n={row['n']}). "
                    "Investigate whether this component drives premature exits or marks bad regimes."
                ),
                "confidence": "low",
            }
        )
    return out


def _top_trades(rows: List[dict], *, worst: bool, k: int = 12) -> List[dict]:
    scored = []
    for r in rows:
        p = _safe_float(r.get("pnl"))
        if p is None:
            continue
        scored.append(
            {
                "trade_id": r.get("trade_id"),
                "symbol": r.get("symbol"),
                "pnl_usd": round(p, 4),
                "exit_reason": _norm_reason(r.get("exit_reason")),
                "side": _norm_side(r),
                "hold_min": _safe_float(r.get("time_in_trade_minutes")),
            }
        )
    scored.sort(key=lambda x: x["pnl_usd"], reverse=not worst)
    return scored[:k]


def _md_report(
    gate: Dict[str, Any],
    summary: Dict[str, Any],
    actions: List[dict],
    top_win: List[dict],
    top_loss: List[dict],
    missing: int,
) -> str:
    lines: List[str] = []
    lines.append("# Strict quant edge analysis (actionable summary)")
    lines.append("")
    lines.append(f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- **Root:** `{gate.get('root')}`")
    lines.append(f"- **open_ts_epoch:** {gate.get('open_ts_epoch')}")
    lines.append(f"- **LEARNING_STATUS:** {gate.get('LEARNING_STATUS')}")
    lines.append(
        f"- **Strict cohort:** trades_seen={gate.get('trades_seen')} complete={gate.get('trades_complete')} "
        f"incomplete={gate.get('trades_incomplete')}"
    )
    lines.append(f"- **Exit rows matched:** {summary['trades_in_cohort']} (missing exit rows for cohort ids: **{missing}**)")
    lines.append("")
    lines.append("## 1. PnL headline (strict cohort)")
    lines.append("")
    lines.append(f"- Sum PnL (USD): **{summary.get('sum_pnl_usd')}**")
    lines.append(f"- Avg / median: **{summary.get('avg_pnl_usd')}** / **{summary.get('median_pnl_usd')}**")
    lines.append(f"- Win rate: **{summary.get('win_rate')}**")
    lines.append(f"- Avg hold (min): **{summary.get('avg_hold_minutes')}**")
    lines.append(f"- Avg v2 exit score: **{summary.get('avg_v2_exit_score')}**")
    lines.append("")
    lines.append("## 2. Directional truth (long vs short)")
    lines.append("")
    lines.append("| Side | n | Sum PnL | Avg PnL | Win rate |")
    lines.append("|------|---|---------|---------|----------|")
    for r in summary.get("by_side") or []:
        lines.append(
            f"| {r['bucket']} | {r['n']} | {r['sum_pnl_usd']} | {r['avg_pnl_usd']} | {r['win_rate']} |"
        )
    lines.append("")
    lines.append("## 3. Exit reason pressure (Workstream E)")
    lines.append("")
    lines.append("| Exit reason (norm) | n | Sum PnL | Avg PnL | Win rate |")
    lines.append("|--------------------|---|---------|---------|----------|")
    for r in (summary.get("by_exit_reason") or [])[:25]:
        lines.append(
            f"| {r['bucket'][:60]} | {r['n']} | {r['sum_pnl_usd']} | {r['avg_pnl_usd']} | {r['win_rate']} |"
        )
    lines.append("")
    lines.append("## 4. Regime slices (entry / exit)")
    lines.append("")
    lines.append("### Entry regime")
    lines.append("| Regime | n | Sum PnL | Avg PnL |")
    lines.append("|--------|---|---------|---------|")
    for r in (summary.get("by_entry_regime") or [])[:15]:
        lines.append(f"| {r['bucket']} | {r['n']} | {r['sum_pnl_usd']} | {r['avg_pnl_usd']} |")
    lines.append("")
    lines.append("### Exit regime")
    lines.append("| Regime | n | Sum PnL | Avg PnL |")
    lines.append("|--------|---|---------|---------|")
    for r in (summary.get("by_exit_regime") or [])[:15]:
        lines.append(f"| {r['bucket']} | {r['n']} | {r['sum_pnl_usd']} | {r['avg_pnl_usd']} |")
    lines.append("")
    lines.append("## 5. Suggested actions (heuristic — confirm with board)")
    lines.append("")
    if not actions:
        lines.append("- No automated suggestions (insufficient depth or balanced buckets).")
    else:
        for i, a in enumerate(actions, 1):
            lines.append(f"{i}. **{a.get('topic')} / {a.get('bucket')}** — {a.get('how')}")
            lines.append(f"   - Levers: `{a.get('suggested_levers')}` | confidence: **{a.get('confidence')}**")
    lines.append("")
    lines.append("## 6. Worst / best trades (PnL)")
    lines.append("")
    lines.append("### Worst")
    for r in top_loss:
        lines.append(
            f"- `{r.get('symbol')}` pnl={r.get('pnl_usd')} reason={r.get('exit_reason')} "
            f"side={r.get('side')} hold_min={r.get('hold_min')} id={r.get('trade_id')}"
        )
    lines.append("")
    lines.append("### Best")
    for r in top_win:
        lines.append(
            f"- `{r.get('symbol')}` pnl={r.get('pnl_usd')} reason={r.get('exit_reason')} "
            f"side={r.get('side')} hold_min={r.get('hold_min')} id={r.get('trade_id')}"
        )
    lines.append("")
    lines.append("## 7. Exit v2 components (lowest avg PnL when present, n≥3)")
    lines.append("")
    lines.append("| Component | n | Avg PnL | Sum PnL | Win rate |")
    lines.append("|-----------|---|---------|---------|----------|")
    for r in (summary.get("exit_v2_component_expectancy") or [])[:20]:
        lines.append(
            f"| {str(r['component'])[:40]} | {r['n']} | {r['avg_pnl_usd']} | {r['sum_pnl_usd']} | {r['win_rate']} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("*Scope: strict cohort exit rows only. For full trade_facts / SPI / blocked opportunity, extend pipeline per docs/ALPACA_MASSIVE_QUANT_EDGE_REVIEW_FRAMEWORK.md.*")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Strict cohort quant edge analysis → reports/")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--open-ts-epoch",
        type=float,
        default=None,
        help="UTC epoch floor for strict cohort (default: STRICT_EPOCH_START)",
    )
    ap.add_argument(
        "--out-md",
        type=Path,
        default=None,
        help="Markdown output path (default: reports/ALPACA_STRICT_QUANT_EDGE_ANALYSIS_<UTC>.md)",
    )
    ap.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="JSON output path (default: reports/ALPACA_STRICT_QUANT_EDGE_ANALYSIS_<UTC>.json)",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    open_ts = float(args.open_ts_epoch) if args.open_ts_epoch is not None else float(STRICT_EPOCH_START)

    r = evaluate_completeness(
        root,
        open_ts_epoch=open_ts,
        audit=False,
        collect_strict_cohort_trade_ids=True,
    )
    cohort = set(str(x) for x in (r.get("strict_cohort_trade_ids") or []))
    exit_map = _load_exit_by_trade_id(root)
    rows: List[dict] = []
    for tid in cohort:
        rec = exit_map.get(tid)
        if rec:
            rows.append(rec)
    missing = len(cohort) - len(rows)

    _, summary = _rollup(rows)
    actions = _suggest_actions(summary)
    top_win = _top_trades(rows, worst=False, k=12)
    top_loss = _top_trades(rows, worst=True, k=12)

    gate_meta = {
        "root": str(root),
        "open_ts_epoch": open_ts,
        "LEARNING_STATUS": r.get("LEARNING_STATUS"),
        "trades_seen": r.get("trades_seen"),
        "trades_complete": r.get("trades_complete"),
        "trades_incomplete": r.get("trades_incomplete"),
        "cohort_trade_ids": len(cohort),
        "exit_rows_matched": len(rows),
        "cohort_ids_missing_exit_row": missing,
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    out_dir = root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md = args.out_md or (out_dir / f"ALPACA_STRICT_QUANT_EDGE_ANALYSIS_{stamp}.md")
    out_json = args.out_json or (out_dir / f"ALPACA_STRICT_QUANT_EDGE_ANALYSIS_{stamp}.json")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate": gate_meta,
        "summary": summary,
        "suggested_actions": actions,
        "top_winners": top_win,
        "top_losers": top_loss,
    }

    md = _md_report(gate_meta, summary, actions, top_win, top_loss, missing)
    out_md.write_text(md, encoding="utf-8")
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"out_md": str(out_md), "out_json": str(out_json), "gate": gate_meta}, indent=2))
    if missing > 0:
        print(f"WARNING: {missing} strict cohort trade_ids have no exit_attribution row", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
