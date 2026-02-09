#!/usr/bin/env python3
"""
Exit Timing Diagnostic — hold-time by mode:strategy and exit_reason, expectancy, flags.

Reads logs/exit_attribution.jsonl (and logs/attribution.jsonl for close_reason).
Outputs JSON + Markdown report. Flags exit_reasons with negative expectancy or very short holds.

Usage: python scripts/exit_timing_diagnostic.py [--days 14] [--base-dir PATH] [--out-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else ""


def _iter_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
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


def _parse_ts(x) -> datetime | None:
    if x is None:
        return None
    s = str(x).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Exit timing diagnostic")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--base-dir", type=Path, default=ROOT)
    ap.add_argument("--out-dir", type=Path, default=None, help="Write report here (default: stdout only)")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    logs = base / "logs"
    exit_path = logs / "exit_attribution.jsonl"
    attr_path = logs / "attribution.jsonl"

    today = datetime.now(timezone.utc).date()
    days_back = max(1, min(args.days, 60))
    window_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_back)]

    exit_rows = _iter_jsonl(exit_path)
    attr_rows = _iter_jsonl(attr_path)
    exit_in_window = [r for r in exit_rows if _day_utc(r.get("ts") or r.get("timestamp") or r.get("exit_ts") or "") in window_days]
    attr_in_window = [r for r in attr_rows if _day_utc(r.get("ts") or r.get("timestamp") or "") in window_days]

    # Hold-time per record (seconds)
    def hold_seconds(r: dict) -> float | None:
        ht = r.get("hold_time_seconds") or r.get("hold_seconds")
        if ht is not None and not isinstance(ht, bool):
            try:
                return float(ht)
            except (TypeError, ValueError):
                pass
        tmin = r.get("time_in_trade_minutes")
        if tmin is not None:
            try:
                return float(tmin) * 60.0
            except (TypeError, ValueError):
                pass
        et = _parse_ts(r.get("entry_ts") or r.get("entry_timestamp"))
        xt = _parse_ts(r.get("exit_ts") or r.get("ts") or r.get("timestamp"))
        if et and xt:
            return (xt - et).total_seconds()
        return None

    # By exit_reason (from exit_attribution and attribution close_reason)
    reason_hold: dict[str, list[float]] = defaultdict(list)
    reason_pnl: dict[str, list[float]] = defaultdict(list)
    reason_count: dict[str, int] = defaultdict(int)
    mode_strategy_hold: dict[str, list[float]] = defaultdict(list)
    mode_strategy_count: dict[str, int] = defaultdict(int)

    for r in exit_in_window:
        reason = r.get("exit_reason") or r.get("close_reason") or r.get("reason") or "unknown"
        reason_count[reason] += 1
        hs = hold_seconds(r)
        if hs is not None:
            reason_hold[reason].append(hs)
        pnl = r.get("pnl_usd") or r.get("pnl")
        if pnl is not None:
            try:
                reason_pnl[reason].append(float(pnl))
            except (TypeError, ValueError):
                pass
        mode = r.get("mode") or "UNKNOWN"
        strategy = r.get("strategy") or "UNKNOWN"
        key = f"{mode}:{strategy}"
        mode_strategy_count[key] += 1
        if hs is not None:
            mode_strategy_hold[key].append(hs)

    for r in attr_in_window:
        reason = r.get("close_reason") or r.get("exit_reason") or r.get("reason") or "unknown"
        if reason == "unknown":
            continue
        reason_count[reason] += 1
        hs = hold_seconds(r)
        if hs is not None:
            reason_hold[reason].append(hs)
        pnl = r.get("pnl_usd") or r.get("pnl")
        if pnl is not None:
            try:
                reason_pnl[reason].append(float(pnl))
            except (TypeError, ValueError):
                pass

    # Expectancy per reason (avg PnL)
    reason_expectancy: dict[str, float] = {}
    for reason, pnls in reason_pnl.items():
        if pnls:
            reason_expectancy[reason] = sum(pnls) / len(pnls)

    # Flags: negative expectancy, very short holds (e.g. median < 10 min)
    SHORT_HOLD_SEC = 600  # 10 min
    flagged_negative = [r for r, e in reason_expectancy.items() if e < 0]
    flagged_short = []
    for reason, holds in reason_hold.items():
        if len(holds) >= 3:
            sorted_holds = sorted(holds)
            mid = len(sorted_holds) // 2
            median_hold = sorted_holds[mid]
            if median_hold < SHORT_HOLD_SEC:
                flagged_short.append((reason, median_hold, len(holds)))

    # Build report
    by_reason = []
    for reason in sorted(reason_count.keys(), key=lambda x: -reason_count[x]):
        holds = reason_hold.get(reason) or []
        pnls = reason_pnl.get(reason) or []
        avg_hold = sum(holds) / len(holds) if holds else None
        exp = reason_expectancy.get(reason)
        by_reason.append({
            "exit_reason": reason,
            "count": reason_count[reason],
            "avg_hold_seconds": round(avg_hold, 2) if avg_hold is not None else None,
            "expectancy_usd": round(exp, 4) if exp is not None else None,
            "n_with_hold": len(holds),
            "n_with_pnl": len(pnls),
        })

    by_mode_strategy = []
    for key in sorted(mode_strategy_count.keys()):
        holds = mode_strategy_hold.get(key) or []
        avg_hold = sum(holds) / len(holds) if holds else None
        by_mode_strategy.append({
            "mode_strategy": key,
            "count": mode_strategy_count[key],
            "avg_hold_seconds": round(avg_hold, 2) if avg_hold is not None else None,
        })

    report = {
        "window_days": window_days[:5],
        "total_exits": len(exit_in_window),
        "total_attribution_closes": len([r for r in attr_in_window if (r.get("close_reason") or r.get("exit_reason") or r.get("reason"))]),
        "by_exit_reason": by_reason,
        "by_mode_strategy": by_mode_strategy,
        "flagged_negative_expectancy": flagged_negative,
        "flagged_short_hold": [{"reason": r, "median_hold_seconds": m, "n": n} for r, m, n in flagged_short],
    }

    md_lines = [
        "# Exit Timing Diagnostic",
        f"Window: last {days_back} days",
        f"Exits in window: {report['total_exits']}",
        "",
        "## By exit_reason (top)",
        "",
    ]
    for rec in by_reason[:15]:
        md_lines.append(f"- **{rec['exit_reason']}** count={rec['count']} avg_hold_s={rec['avg_hold_seconds']} expectancy_usd={rec['expectancy_usd']}")
    md_lines.append("")
    md_lines.append("## By mode:strategy")
    for rec in by_mode_strategy[:10]:
        md_lines.append(f"- **{rec['mode_strategy']}** count={rec['count']} avg_hold_s={rec['avg_hold_seconds']}")
    md_lines.append("")
    md_lines.append("## Flagged: negative expectancy")
    for r in flagged_negative:
        md_lines.append(f"- {r}")
    md_lines.append("")
    md_lines.append("## Flagged: very short median hold (< 10 min)")
    for item in report["flagged_short_hold"]:
        md_lines.append(f"- {item['reason']} median_hold_s={item['median_hold_seconds']} n={item['n']}")

    print(json.dumps(report, indent=2))
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "exit_timing_diagnostic.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (args.out_dir / "exit_timing_diagnostic.md").write_text("\n".join(md_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
