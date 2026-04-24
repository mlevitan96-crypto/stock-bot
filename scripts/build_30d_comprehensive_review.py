#!/usr/bin/env python3
"""
Build 30-day or last-N-exits comprehensive review bundle for the Board.
Uses real attribution, exit_attribution, blocked_trades; includes counter-intelligence and
learning/telemetry summary so learning and board review use the same scope and output how to proceed.

Outputs: reports/board/30d_comprehensive_review.json and .md.

Usage:
  On droplet: cd /root/stock-bot && python3 scripts/build_30d_comprehensive_review.py
  By trade count (same scope as learning): python scripts/build_30d_comprehensive_review.py --last-n-exits 387
  Local 30d:  python scripts/build_30d_comprehensive_review.py [--base-dir .] [--end-date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _parse_ts(r: dict) -> datetime | None:
    """Get UTC datetime from record (ts, timestamp, exit_ts)."""
    for key in ("ts", "timestamp", "exit_ts"):
        v = r.get(key)
        if v is None:
            continue
        try:
            if isinstance(v, (int, float)):
                return datetime.fromtimestamp(v, tz=timezone.utc)
            s = str(v).replace("Z", "+00:00").strip()[:26]
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return None


def _day_utc(ts) -> str:
    if ts is None:
        return ""
    s = str(ts)[:10]
    return s if len(s) == 10 and s[4] == "-" else ""


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _load_30d_window(base: Path, end_date: str, days: int = 30) -> tuple[list[str], list, list, list]:
    try:
        t = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return [], [], [], []
    start = t - timedelta(days=days - 1)
    window_days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    attr = [r for r in _iter_jsonl(base / "logs" / "attribution.jsonl")
            if _day_utc(r.get("ts") or r.get("timestamp")) in window_days]
    exit_attr = [r for r in _iter_jsonl(base / "logs" / "exit_attribution.jsonl")
                 if _day_utc(r.get("ts") or r.get("timestamp") or r.get("exit_ts")) in window_days]
    blocked = [r for r in _iter_jsonl(base / "state" / "blocked_trades.jsonl")
               if _day_utc(r.get("ts") or r.get("timestamp")) in window_days]
    return window_days, attr, exit_attr, blocked


def _load_last_n_exits(base: Path, n: int) -> tuple[str, str, list, list, list]:
    """Load last N exits from exit_attribution; then attribution and blocked in same time window. Returns (window_start, window_end, exit_attr, attr, blocked)."""
    exit_path = base / "logs" / "exit_attribution.jsonl"
    if not exit_path.exists():
        return "", "", [], [], []
    lines = [
        ln for ln in exit_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if ln.strip()
    ]
    recent_lines = lines[-n:] if len(lines) > n else lines
    exit_attr = []
    for line in recent_lines:
        try:
            exit_attr.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not exit_attr:
        return "", "", [], [], []
    timestamps = []
    for r in exit_attr:
        t = _parse_ts(r)
        if t:
            timestamps.append(t)
    if not timestamps:
        return "", "", exit_attr, [], []
    min_ts = min(timestamps)
    max_ts = max(timestamps)
    window_start = min_ts.strftime("%Y-%m-%d")
    window_end = max_ts.strftime("%Y-%m-%d")

    attr = []
    for r in _iter_jsonl(base / "logs" / "attribution.jsonl"):
        t = _parse_ts(r)
        if t and min_ts <= t <= max_ts:
            attr.append(r)
    blocked = []
    for r in _iter_jsonl(base / "state" / "blocked_trades.jsonl"):
        t = _parse_ts(r)
        if t and min_ts <= t <= max_ts:
            blocked.append(r)
    return window_start, window_end, exit_attr, attr, blocked


def _counter_intelligence(attr: list, blocked: list, avg_pnl_per_exit: float = 0.0) -> dict:
    """Counter-intelligence summary: blocking patterns, gate effectiveness, executed vs blocked.
    C1 promoted: opportunity_cost_ranked_reasons (top N by estimated opportunity cost)."""
    out = {
        "blocking_patterns": {},
        "gate_effectiveness": {},
        "executed_count": len(attr),
        "blocked_count": len(blocked),
        "opportunity_cost_ranked_reasons": [],
    }
    if not blocked:
        return out
    reasons: Counter = Counter()
    for r in blocked:
        reason = str(r.get("reason") or r.get("block_reason") or "unknown").strip() or "unknown"
        reasons[reason] += 1
    out["blocking_patterns"] = dict(reasons.most_common(20))
    gate_effect = defaultdict(lambda: {"count": 0, "avg_score": 0.0})
    for r in blocked:
        reason = str(r.get("reason") or r.get("block_reason") or "unknown").strip() or "unknown"
        gate_effect[reason]["count"] += 1
        gate_effect[reason]["avg_score"] += float(r.get("score") or 0)
    for k, v in gate_effect.items():
        out["gate_effectiveness"][k] = {
            "count": v["count"],
            "avg_score": round(v["avg_score"] / v["count"], 2) if v["count"] else 0,
        }
    # C1: opportunity cost ranking (proxy = count * avg_pnl_per_exit; most negative = highest cost)
    ranked = []
    for reason, count in reasons.most_common(20):
        est_opportunity_cost = round(count * avg_pnl_per_exit, 2)
        ge = out["gate_effectiveness"].get(reason, {})
        ranked.append({
            "reason": reason,
            "blocked_count": count,
            "estimated_opportunity_cost_usd": est_opportunity_cost,
            "avg_score": ge.get("avg_score"),
            "notes": "Proxy: uses executed-trade avg PnL per exit; not per-block outcome.",
        })
    out["opportunity_cost_ranked_reasons"] = ranked
    return out


def _learning_telemetry_summary(exit_attr: list) -> dict:
    """Of the exits in scope, how many have full direction telemetry (intel_snapshot_entry)."""
    total = len(exit_attr)
    telemetry = 0
    for r in exit_attr:
        embed = r.get("direction_intel_embed")
        if isinstance(embed, dict):
            snap = embed.get("intel_snapshot_entry")
            if isinstance(snap, dict) and snap:
                telemetry += 1
    pct = round(100.0 * telemetry / total, 2) if total else 0.0
    return {
        "total_exits_in_scope": total,
        "telemetry_backed": telemetry,
        "pct_telemetry": pct,
        "ready_for_replay": total >= 100 and pct >= 90.0,
    }


def _how_to_proceed(pnl: dict, counter_intel: dict, learning: dict, blocked_total: int) -> list[str]:
    """Synthesize recommendations for how to proceed."""
    recs = []
    if learning.get("ready_for_replay"):
        recs.append("Replay gate met (≥100 exits with ≥90% telemetry in scope). Run direction replay when ready.")
    elif learning.get("total_exits_in_scope", 0) > 0:
        need = 100 - learning.get("telemetry_backed", 0)
        recs.append(f"Continue capture: need {learning.get('telemetry_backed', 0)}/100 telemetry-backed in last-100 window; run replay when ≥90%.")
    if blocked_total > 0 and counter_intel.get("blocking_patterns"):
        items = list(counter_intel["blocking_patterns"].items())
        top_reason = max(items, key=lambda x: x[1]) if items else (None, 0)
        if top_reason[0]:
            recs.append(f"Review blocked trades: top reason '{top_reason[0]}' ({top_reason[1]} blocks). Consider counter-intel report for missed opportunities.")
    if pnl.get("total_pnl_attribution_usd") is not None and pnl.get("total_pnl_attribution_usd", 0) < 0:
        recs.append("PnL negative in scope; use board personas for top 5 recommendations (entry/exit/gates).")
    recs.append("Board task: each persona 3 ideas → agree top 5 with owner, metric, success criteria.")
    return recs


def _normalize_direction(r: dict) -> str:
    """Normalize direction/position_side/side to long or short for aggregation."""
    d = r.get("direction") or r.get("position_side") or r.get("side") or ""
    d = str(d).strip().lower()
    if d in ("bullish", "long", "buy"):
        return "long"
    if d in ("bearish", "short", "sell"):
        return "short"
    return "unknown"


def _architecture_summary() -> str:
    return """- Entry: composite score (UW + flow + dark pool + gamma + vol + option volume), expectancy gate, capacity/displacement/momentum gates.
- Exit: signal_decay, time stop, trailing stop, regime-based exits; exit pressure v3.
- Universe: daily universe from UW + survivorship; sector/regime filters.
- Execution: Alpaca paper; cooldowns, concentration limits, max positions per cycle.
- Data: attribution.jsonl, exit_attribution.jsonl, master_trade_log.jsonl, blocked_trades.jsonl; EOD root cause, exit effectiveness v2, governance loop."""


def main() -> int:
    ap = argparse.ArgumentParser(description="Build 30-day or last-N-exits comprehensive review bundle for Board")
    ap.add_argument("--base-dir", default="", help="Repo root (default: script parent)")
    ap.add_argument("--end-date", default="", help="End date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--out-dir", default="", help="Output dir (default: reports/board)")
    ap.add_argument("--days", type=int, default=30, help="Window size in days (when not using --last-n-exits)")
    ap.add_argument("--last-n-exits", type=int, default=0, help="Use last N exits as scope (same as learning baseline; e.g. 387). Overrides date window.")
    ap.add_argument("--output-basename", default="30d_comprehensive_review", help="Output file basename (default 30d_comprehensive_review; use last387_comprehensive_review for last-N run).")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    end_date = (args.end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")).strip()
    out_dir = Path(args.out_dir) if args.out_dir else (REPO / "reports" / "board")
    basename = (args.output_basename or "30d_comprehensive_review").strip() or "30d_comprehensive_review"
    days = max(1, args.days)
    use_last_n = max(0, args.last_n_exits)

    if use_last_n:
        window_start, window_end, exit_attr, attr, blocked = _load_last_n_exits(base, use_last_n)
        window_days = [window_start, window_end] if window_start else []
        scope_label = f"last {len(exit_attr)} exits"
        if not exit_attr:
            print("No exit_attribution data or empty last-n window", file=sys.stderr)
            return 1
    else:
        window_days, attr, exit_attr, blocked = _load_30d_window(base, end_date, days)
        window_start, window_end = (window_days[0], window_days[-1]) if window_days else ("", "")
        scope_label = f"{days} days"
        if not window_days:
            print("Invalid end-date or no window", file=sys.stderr)
            return 1

    # PnL and win rate (from attribution; exit_attribution for exits-only PnL)
    pnls_attr = [float(r.get("pnl_usd") or r.get("pnl") or 0) for r in attr]
    pnls_exit = [float(r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd") or 0) for r in exit_attr]
    total_pnl_attr = sum(pnls_attr)
    total_pnl_exit = sum(pnls_exit)
    wins_attr = sum(1 for p in pnls_attr if p > 0)
    total_trades = len(pnls_attr) or 1
    win_rate = wins_attr / total_trades

    # Exit reason distribution
    exit_reasons: Counter = Counter()
    for r in exit_attr + attr:
        reason = str(r.get("exit_reason") or r.get("close_reason") or r.get("reason") or "unknown").strip() or "unknown"
        exit_reasons[reason] += 1
    exit_reason_dist = dict(exit_reasons.most_common(20))

    # Hold time
    hold_minutes = []
    for r in exit_attr:
        h = r.get("time_in_trade_minutes") or r.get("hold_minutes")
        if h is not None:
            try:
                hold_minutes.append(float(h))
            except (TypeError, ValueError):
                pass
    avg_hold_minutes = sum(hold_minutes) / len(hold_minutes) if hold_minutes else None

    # Blocked by reason
    blocked_reasons: Counter = Counter()
    for r in blocked:
        reason = str(r.get("reason") or r.get("block_reason") or "unknown").strip() or "unknown"
        blocked_reasons[reason] += 1
    blocked_dist = dict(blocked_reasons.most_common(20))

    # Long vs short breakdown (from exit_attribution then attribution)
    direction_pnl: dict[str, list[float]] = {}
    direction_count: Counter = Counter()
    for r in exit_attr if exit_attr else attr:
        d = _normalize_direction(r)
        direction_count[d] += 1
        pnl = float(r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd") or 0)
        direction_pnl.setdefault(d, []).append(pnl)
    by_direction = {}
    for d in ("long", "short", "unknown"):
        if d not in direction_pnl:
            continue
        pnls = direction_pnl[d]
        by_direction[d] = {
            "count": len(pnls),
            "total_pnl_usd": round(sum(pnls), 2),
            "win_rate": round(sum(1 for p in pnls if p > 0) / len(pnls), 4) if pnls else None,
        }

    # Optional: 30-day rolling window from board (if available)
    rolling_30 = {}
    try:
        from board.eod.rolling_windows import build_rolling_windows
        rolling_30 = build_rolling_windows(base, end_date, window_sizes=[30])
    except Exception:
        pass

    # Avg PnL per exit (for C1 opportunity-cost proxy)
    total_exits = len(exit_attr) or 1
    avg_pnl_per_exit = total_pnl_exit / total_exits
    # Counter-intelligence (blocked vs executed, gate effectiveness; C1 opportunity-cost ranking)
    counter_intel = _counter_intelligence(attr, blocked, avg_pnl_per_exit)
    # Learning/telemetry summary over same scope (same exits we're reviewing)
    learning = _learning_telemetry_summary(exit_attr)
    pnl_dict = {
        "total_pnl_attribution_usd": round(total_pnl_attr, 2),
        "total_pnl_exit_attribution_usd": round(total_pnl_exit, 2),
        "total_trades": len(attr),
        "total_exits": len(exit_attr),
        "win_rate": round(win_rate, 4),
        "avg_hold_minutes": round(avg_hold_minutes, 2) if avg_hold_minutes is not None else None,
    }
    how_to_proceed = _how_to_proceed(pnl_dict, counter_intel, learning, len(blocked))

    payload = dict(
        scope=scope_label,
        window_start=window_start,
        window_end=window_end,
        end_date=end_date,
        days=days if not use_last_n else None,
        last_n_exits=use_last_n if use_last_n else None,
        architecture_summary=_architecture_summary(),
        pnl=pnl_dict,
        exit_reason_distribution=exit_reason_dist,
        blocked_trade_distribution=blocked_dist,
        blocked_total=len(blocked),
        by_direction=by_direction,
        rolling_30_day=rolling_30,
        counter_intelligence=counter_intel,
        learning_telemetry=learning,
        how_to_proceed=how_to_proceed,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{basename}.json"
    md_path = out_dir / f"{basename}.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    pct_telem = learning.get("pct_telemetry", 0)
    ready_str = "Yes" if learning.get("ready_for_replay") else "No"
    avg_hold_str = str(round(avg_hold_minutes, 1)) if avg_hold_minutes is not None else "N/A"
    md_lines = []
    md_lines.append("# Comprehensive Review — Board Input")
    md_lines.append("")
    md_lines.append(f"**Scope:** {scope_label}. **Window:** {window_start} to {window_end}. **End date:** {end_date}.")
    md_lines.append("")
    md_lines.append("## Architecture (current)")
    md_lines.append("")
    md_lines.append(_architecture_summary())
    md_lines.append("")
    md_lines.append("## PnL & activity")
    md_lines.append("")
    md_lines.append(f"- **Total PnL (attribution):** ${total_pnl_attr:.2f}")
    md_lines.append(f"- **Total PnL (exit attribution):** ${total_pnl_exit:.2f}")
    md_lines.append(f"- **Total executed trades:** {len(attr)}")
    md_lines.append(f"- **Total exits:** {len(exit_attr)}")
    md_lines.append(f"- **Win rate:** {win_rate:.1%}")
    md_lines.append(f"- **Avg hold (minutes):** " + avg_hold_str)
    md_lines.append(f"- **Blocked trades:** {len(blocked)}")
    md_lines.append("")
    md_lines.append("## Learning & telemetry (same scope)")
    md_lines.append("")
    md_lines.append(f"- **Exits in scope:** {learning.get('total_exits_in_scope', 0)}")
    md_lines.append(f"- **Telemetry-backed:** {learning.get('telemetry_backed', 0)} ({pct_telem}%)")
    md_lines.append(f"- **Ready for replay (≥100 exits, ≥90% telemetry):** " + ready_str)
    md_lines.append("")
    md_lines.append("## Counter-intelligence (blocked trades)")
    md_lines.append("")
    md_lines.append("*C1 promoted: opportunity-cost ranking is first-class below (reporting only; no gating changes).*")
    md_lines.append("")
    md_lines.append(f"- **Blocked in scope:** {counter_intel.get('blocked_count', 0)}")
    for reason, count in list(counter_intel.get("blocking_patterns", {}).items())[:10]:
        md_lines.append("- `" + str(reason) + "`: " + str(count))
    oc_ranked = counter_intel.get("opportunity_cost_ranked_reasons") or []
    if oc_ranked:
        md_lines.append("")
        md_lines.append("### Opportunity-cost ranked reasons (C1)")
        md_lines.append("")
        for item in oc_ranked[:10]:
            r, c, cost, avg_s, _ = item.get("reason"), item.get("blocked_count"), item.get("estimated_opportunity_cost_usd"), item.get("avg_score"), item.get("notes")
            md_lines.append(f"- `{r}`: blocked_count={c}, estimated_opportunity_cost_usd={cost}, avg_score={avg_s}")
    md_lines.append("")
    md_lines.append("## Long vs short")
    md_lines.append("")
    if by_direction:
        for d in ("long", "short", "unknown"):
            if d not in by_direction:
                continue
            b = by_direction[d]
            wr_val = b.get("win_rate")
            wr = f", win_rate={wr_val:.1%}" if wr_val is not None else ""
            cval = b.get("count")
            pval = b.get("total_pnl_usd")
            md_lines.append(f"- **{d}:** count={cval}, total_pnl_usd={pval}{wr}")
    else:
        md_lines.append("- No direction breakdown; direction/position_side missing in logs.")
    md_lines.extend([
        "",
        "## Exit reason distribution",
        "",
    ])
    for reason, count in exit_reasons.most_common(15):
        md_lines.append(f"- `{reason}`: {count}")
    md_lines.extend(["", "## How to proceed", ""])
    for rec in how_to_proceed:
        md_lines.append(f"- {rec}")
    board_task = (
        "Each persona (Equity Skeptic, Income Strategist, Risk Officer, Promotion Judge, "
        "Customer Advocate, Innovation Officer, SRE) must produce **3 ideas** to improve PnL and stop losing money. "
        "Then the Board must **agree on the top 5** recommendations with owner, metric, and 3/5-day success criteria."
    )
    direction_review = (
        "**Direction review:** If the market was down but almost all executed trades are long, "
        "the Board should consider: (1) Is LONG_ONLY enabled on droplet? (2) Is flow/cache sentiment skewed bullish? "
        "See reports/audit/LONG_SHORT_TRADE_LOGIC_AUDIT.md and run scripts/verify_long_short_on_droplet.py on droplet for direction mix and LONG_ONLY status."
    )
    md_lines.extend([
        "",
        "## Board task",
        "",
        board_task,
        "",
        direction_review,
        "",
    ])
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
