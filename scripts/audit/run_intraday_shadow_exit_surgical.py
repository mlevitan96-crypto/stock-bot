#!/usr/bin/env python3
"""
Shadow exit surgical — run ON DROPLET after forensic.
Reads INTRADAY_EXIT_LAG_AND_GIVEBACK_<date>.json (must include
unrealized_pnl_at_first_eligibility and first_firing_condition).
Produces:
  1) Eligibility-to-exit lag distribution
  2) First-firing exit condition (which fires first vs counts)
  3) Shadow policy: exit-on-first-eligibility captured vs current realized PnL
CSA/SRE: shadow is counterfactual only; no live behavior change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "reports" / "audit"
DATE_STR = "2026-03-09"


def main() -> int:
    ap = argparse.ArgumentParser(description="Shadow exit-on-first-eligibility surgical (run on droplet after forensic)")
    ap.add_argument("--date", default=DATE_STR)
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()
    date_str = args.date
    base = Path(args.base_dir) if args.base_dir else REPO
    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    lag_path = audit_dir / f"INTRADAY_EXIT_LAG_AND_GIVEBACK_{date_str}.json"
    if not lag_path.exists():
        print(f"BLOCKER: {lag_path} not found. Run forensic first on droplet.", file=sys.stderr)
        return 1

    data = json.loads(lag_path.read_text(encoding="utf-8"))
    trades = data.get("trades", [])
    if not trades:
        print("No trades in lag artifact.", file=sys.stderr)
        return 0

    # 1) Lag distribution (trades with non-null lag_minutes)
    lag_minutes_list = [t["lag_minutes"] for t in trades if t.get("lag_minutes") is not None]
    lag_minutes_list = [float(x) for x in lag_minutes_list]
    n_lag = len(lag_minutes_list)
    if n_lag:
        sorted_lag = sorted(lag_minutes_list)
        mean_lag = sum(sorted_lag) / n_lag
        median_lag = sorted_lag[n_lag // 2] if n_lag else None
        p90 = sorted_lag[int(0.90 * n_lag)] if n_lag >= 10 else (sorted_lag[-1] if sorted_lag else None)
        p95 = sorted_lag[int(0.95 * n_lag)] if n_lag >= 20 else (sorted_lag[-1] if sorted_lag else None)
        # Histogram: 0-5, 5-15, 15-30, 30-60, 60+
        buckets = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 1e9)]
        hist = {}
        for lo, hi in buckets:
            key = f"{lo}-{hi}" if hi < 1e8 else "60+"
            hist[key] = sum(1 for x in sorted_lag if lo <= x < hi)
        lag_dist = {
            "date": date_str,
            "count_with_lag": n_lag,
            "min_minutes": round(min(sorted_lag), 2),
            "max_minutes": round(max(sorted_lag), 2),
            "mean_minutes": round(mean_lag, 2),
            "median_minutes": round(median_lag, 2) if median_lag is not None else None,
            "p90_minutes": round(p90, 2) if p90 is not None else None,
            "p95_minutes": round(p95, 2) if p95 is not None else None,
            "histogram_minutes": hist,
        }
    else:
        lag_dist = {"date": date_str, "count_with_lag": 0, "note": "No trades with lag_minutes."}

    (audit_dir / f"INTRADAY_ELIGIBILITY_EXIT_LAG_DISTRIBUTION_{date_str}.json").write_text(
        json.dumps(lag_dist, indent=2), encoding="utf-8"
    )

    # 2) First-firing exit condition
    condition_counts = {}
    for t in trades:
        c = t.get("first_firing_condition") or "unknown"
        condition_counts[c] = condition_counts.get(c, 0) + 1
    first_fire = {
        "date": date_str,
        "total_trades": len(trades),
        "first_firing_condition_counts": condition_counts,
        "trades_with_eligibility": sum(1 for t in trades if t.get("first_firing_condition")),
    }
    (audit_dir / f"INTRADAY_EXIT_CONDITION_FIRST_FIRE_{date_str}.json").write_text(
        json.dumps(first_fire, indent=2), encoding="utf-8"
    )

    # 3) Shadow: exit-on-first-eligibility vs current realized
    current_realized = sum(float(t.get("realized_pnl_usd") or 0) for t in trades)
    shadow_trades = [t for t in trades if t.get("unrealized_pnl_at_first_eligibility") is not None]
    shadow_captured = sum(float(t.get("unrealized_pnl_at_first_eligibility") or 0) for t in shadow_trades)
    delta = shadow_captured - current_realized
    shadow_out = {
        "date": date_str,
        "policy": "exit_on_first_eligibility_shadow",
        "current_realized_pnl_usd": round(current_realized, 4),
        "shadow_captured_pnl_usd": round(shadow_captured, 4),
        "delta_usd": round(delta, 4),
        "trades_with_shadow_pnl": len(shadow_trades),
        "total_trades": len(trades),
        "per_trade_sample": [
            {
                "trade_id": t.get("trade_id"),
                "symbol": t.get("symbol"),
                "realized_pnl_usd": t.get("realized_pnl_usd"),
                "unrealized_pnl_at_first_eligibility": t.get("unrealized_pnl_at_first_eligibility"),
                "first_firing_condition": t.get("first_firing_condition"),
            }
            for t in shadow_trades[:20]
        ],
    }
    (audit_dir / f"INTRADAY_SHADOW_EXIT_ON_FIRST_ELIGIBILITY_{date_str}.json").write_text(
        json.dumps(shadow_out, indent=2), encoding="utf-8"
    )

    # 4) CSA summary MD
    md_lines = [
        "# Shadow exit surgical — " + date_str,
        "",
        "**Authority:** Droplet. Shadow = counterfactual only; no live change.",
        "",
        "## 1) Eligibility-to-exit lag distribution",
        "",
        f"- Count (trades with lag): {lag_dist.get('count_with_lag', 0)}",
        f"- Min / max (min): {lag_dist.get('min_minutes')} / {lag_dist.get('max_minutes')}",
        f"- Mean / median (min): {lag_dist.get('mean_minutes')} / {lag_dist.get('median_minutes')}",
        f"- P90 / P95 (min): {lag_dist.get('p90_minutes')} / {lag_dist.get('p95_minutes')}",
        "",
        "## 2) First-firing exit condition",
        "",
        json.dumps(condition_counts, indent=2),
        "",
        "## 3) Shadow: exit-on-first-eligibility",
        "",
        f"- Current realized PnL (USD): {shadow_out['current_realized_pnl_usd']}",
        f"- Shadow captured PnL (USD): {shadow_out['shadow_captured_pnl_usd']}",
        f"- Delta (shadow − realized): {shadow_out['delta_usd']}",
        "",
        "## 4) Best practices",
        "",
        "- Do not promote shadow to live without further validation and A/B or phased rollout.",
        "- Use lag distribution to set monitoring SLOs (e.g. p95 lag < N min).",
        "- First-firing condition informs which exit rule to tune first.",
        "",
    ]
    (audit_dir / f"INTRADAY_SHADOW_EXIT_SURGICAL_SUMMARY_{date_str}.md").write_text("\n".join(md_lines), encoding="utf-8")

    print("Wrote 4 shadow surgical artifacts for", date_str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
