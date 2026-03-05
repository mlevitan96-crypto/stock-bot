#!/usr/bin/env python3
"""
B2 daily evaluator. Run on droplet (DROPLET_RUN=1 recommended).
Reads baseline (B2_LIVE_PAPER_START_SNAPSHOT.json), B2 suppressions, exit_attribution in window.
Computes: b2_suppression_count/rate, exit_reason_mix_delta, avg_hold_delta, pnl_delta, tail_risk.
Writes: reports/board/B2_DAILY_STATUS.md, B2_DAILY_STATUS.json; appends state/b2_daily_history.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _parse_ts(r: dict) -> datetime | None:
    for key in ("ts", "timestamp", "exit_ts"):
        v = r.get(key)
        if v is None:
            continue
        try:
            if isinstance(v, (int, float)):
                return datetime.fromtimestamp(float(v), tz=timezone.utc)
            s = str(v).replace("Z", "+00:00").strip()[:26]
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return None


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


def main() -> int:
    ap = argparse.ArgumentParser(description="B2 daily evaluator (run on droplet)")
    ap.add_argument("--since-hours", type=float, default=24.0, help="Evaluation window in hours")
    ap.add_argument("--base-dir", default="", help="Repo root (default: script parent)")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    since_hours = max(0.1, args.since_hours)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    board_dir = base / "reports" / "board"
    state_dir = base / "state"
    board_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    # Baseline
    baseline_path = base / "reports" / "board" / "B2_LIVE_PAPER_START_SNAPSHOT.json"
    if not baseline_path.exists():
        print(f"Baseline not found: {baseline_path}", file=sys.stderr)
        return 1
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    base_pnl = (baseline.get("pnl") or {})
    base_exit = (baseline.get("exit_reason_summary") or {})
    baseline_avg_hold = base_pnl.get("avg_hold_minutes")
    baseline_pnl_usd = base_pnl.get("total_pnl_attribution_usd")
    baseline_signal_decay_pct = base_exit.get("signal_decay_share_pct")
    baseline_exits = base_pnl.get("total_exits") or 1

    # B2 suppressions in window
    b2_path = base / "logs" / "b2_suppressed_signal_decay.jsonl"
    b2_suppressions = []
    for rec in _iter_jsonl(b2_path):
        ts = _parse_ts(rec) or _parse_ts({"ts": rec.get("timestamp")})
        if ts and ts >= cutoff:
            b2_suppressions.append(rec)
    b2_suppression_count = len(b2_suppressions)

    # Exits in window (from exit_attribution.jsonl)
    exit_path = base / "logs" / "exit_attribution.jsonl"
    exits_in_window = []
    for rec in _iter_jsonl(exit_path):
        ts = _parse_ts(rec)
        if ts and ts >= cutoff:
            exits_in_window.append(rec)
    total_exits_window = len(exits_in_window)
    b2_suppression_rate = (b2_suppression_count / total_exits_window) if total_exits_window else 0.0

    # Exit reason mix (signal_decay share)
    exit_reasons: Counter = Counter()
    for r in exits_in_window:
        reason = str(r.get("exit_reason") or r.get("close_reason") or r.get("reason") or "unknown").strip() or "unknown"
        exit_reasons[reason] += 1
    signal_decay_count = sum(c for k, c in exit_reasons.items() if "signal_decay" in k.lower())
    current_signal_decay_pct = round(100.0 * signal_decay_count / total_exits_window, 2) if total_exits_window else 0.0
    exit_reason_mix_delta_pct = (current_signal_decay_pct - baseline_signal_decay_pct) if baseline_signal_decay_pct is not None else None

    # Avg hold minutes
    hold_minutes = []
    for r in exits_in_window:
        h = r.get("time_in_trade_minutes") or r.get("hold_minutes")
        if h is not None:
            try:
                hold_minutes.append(float(h))
            except (TypeError, ValueError):
                pass
    avg_hold_current = sum(hold_minutes) / len(hold_minutes) if hold_minutes else None
    avg_hold_minutes_delta = (avg_hold_current - baseline_avg_hold) if (avg_hold_current is not None and baseline_avg_hold is not None) else None

    # PnL attribution delta (window total vs baseline per-exit scaled to same N for comparison we use window total and baseline total)
    pnls = [float(r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd") or 0) for r in exits_in_window]
    total_pnl_window = sum(pnls)
    pnl_attribution_delta_usd = (total_pnl_window - (baseline_pnl_usd * total_exits_window / baseline_exits)) if baseline_exits and baseline_pnl_usd is not None else total_pnl_window
    expectancy_per_exit = total_pnl_window / total_exits_window if total_exits_window else None
    baseline_expectancy = baseline_pnl_usd / baseline_exits if baseline_exits else None

    # Tail risk: worst 5% of exits by PnL
    pnls_sorted = sorted(pnls) if pnls else []
    n_5pct = max(1, len(pnls_sorted) // 20)
    worst_5pct_pnls = pnls_sorted[:n_5pct]
    worst_5pct_mean = sum(worst_5pct_pnls) / len(worst_5pct_pnls) if worst_5pct_pnls else None
    tail_risk_summary = {
        "worst_5pct_count": len(worst_5pct_pnls),
        "worst_5pct_mean_pnl_usd": round(worst_5pct_mean, 2) if worst_5pct_mean is not None else None,
        "worst_single_pnl_usd": round(min(pnls), 2) if pnls else None,
    }

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    payload = {
        "evaluated_at": now.isoformat(),
        "since_hours": since_hours,
        "window_exits": total_exits_window,
        "b2_suppression_count": b2_suppression_count,
        "b2_suppression_rate": round(b2_suppression_rate, 4),
        "exit_reason_mix_delta_pct": exit_reason_mix_delta_pct,
        "current_signal_decay_pct": current_signal_decay_pct,
        "baseline_signal_decay_pct": baseline_signal_decay_pct,
        "avg_hold_minutes_delta": round(avg_hold_minutes_delta, 2) if avg_hold_minutes_delta is not None else None,
        "current_avg_hold_minutes": round(avg_hold_current, 2) if avg_hold_current is not None else None,
        "pnl_attribution_delta_usd": round(pnl_attribution_delta_usd, 2) if pnl_attribution_delta_usd is not None else None,
        "total_pnl_window_usd": round(total_pnl_window, 2),
        "expectancy_per_exit_usd": round(expectancy_per_exit, 4) if expectancy_per_exit is not None else None,
        "baseline_expectancy_per_exit_usd": round(baseline_expectancy, 4) if baseline_expectancy is not None else None,
        "tail_risk_summary": tail_risk_summary,
        "paper_safety_violation_count": None,
    }

    # Paper safety violation count (for tripwire)
    violation_path = base / "state" / "paper_safety_violation.json"
    if violation_path.exists():
        try:
            v = json.loads(violation_path.read_text(encoding="utf-8"))
            payload["paper_safety_violation_count"] = v.get("count", 0)
        except Exception:
            payload["paper_safety_violation_count"] = 0
    else:
        payload["paper_safety_violation_count"] = 0

    status_path = board_dir / "B2_DAILY_STATUS.json"
    status_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Append daily history for sustained_negative_delta (3+ days)
    history_path = state_dir / "b2_daily_history.jsonl"
    history_rec = {
        "date": today,
        "evaluated_at": now.isoformat(),
        "window_exits": total_exits_window,
        "expectancy_per_exit_usd": round(expectancy_per_exit, 4) if expectancy_per_exit is not None else None,
        "baseline_expectancy_per_exit_usd": round(baseline_expectancy, 4) if baseline_expectancy is not None else None,
        "total_pnl_window_usd": round(total_pnl_window, 2),
    }
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(history_rec, default=str) + "\n")

    # Recommendation placeholder (enforcer or post-step will set Promote/Hold/Rollback)
    recommendation = "Hold"
    reason_bullets = [
        f"Window: {total_exits_window} exits in last {since_hours:.0f}h; B2 suppressions: {b2_suppression_count} (rate {b2_suppression_rate:.2%}).",
        f"Signal_decay share: {current_signal_decay_pct}% (baseline {baseline_signal_decay_pct}%); delta {exit_reason_mix_delta_pct:+.1f}%." if exit_reason_mix_delta_pct is not None else "Exit reason mix vs baseline: N/A.",
        f"PnL window: ${total_pnl_window:.2f}; expectancy/exit: ${expectancy_per_exit:.2f} (baseline ${baseline_expectancy:.2f})." if expectancy_per_exit is not None and baseline_expectancy is not None else "PnL: see JSON.",
    ]
    payload["recommendation"] = recommendation
    payload["reason_bullets"] = reason_bullets

    md_lines = [
        "# B2 Daily Status",
        "",
        f"**Evaluated (UTC):** {payload['evaluated_at']}",
        f"**Window:** last {since_hours:.0f} hours",
        "",
        "## Metrics vs baseline",
        "",
        f"- **B2 suppressions:** {b2_suppression_count} (rate {b2_suppression_rate:.2%})",
        f"- **Exits in window:** {total_exits_window}",
        f"- **Signal_decay share:** {current_signal_decay_pct}% (baseline {baseline_signal_decay_pct}%); delta {exit_reason_mix_delta_pct:+.1f}%" if exit_reason_mix_delta_pct is not None else "-",
        f"- **Avg hold delta (min):** {avg_hold_minutes_delta:+.1f}" if avg_hold_minutes_delta is not None else "-",
        f"- **PnL window (USD):** {total_pnl_window:.2f}; expectancy/exit: {expectancy_per_exit:.2f}" if expectancy_per_exit is not None else "-",
        f"- **Tail (worst 5% mean USD):** {tail_risk_summary.get('worst_5pct_mean_pnl_usd')}" if tail_risk_summary.get("worst_5pct_mean_pnl_usd") is not None else "-",
        f"- **paper_safety_violation count:** {payload.get('paper_safety_violation_count', 'N/A')}",
        "",
        "## Recommendation",
        "",
        f"**{recommendation}**",
        "",
        "**Reason:**",
        "",
    ] + [f"- {b}" for b in reason_bullets] + ["", "---", "See B2_DAILY_STATUS.json for full payload.", ""]
    (board_dir / "B2_DAILY_STATUS.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"B2_DAILY_STATUS written ({total_exits_window} exits, {b2_suppression_count} B2 suppressions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
