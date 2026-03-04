#!/usr/bin/env python3
"""
A3 shadow test: lower expectancy score floor by one notch — SHADOW ONLY.
No order placement, no live gating changes. Reads blocked_trades, recomputes would-pass under lowered floor,
estimates counterfactual impact (proxy). Writes state/shadow/a3_expectancy_floor_shadow.json and reports/audit/A3_SHADOW_RESULTS.md.

HARD SAFETY: This script does not import or call any order placement or live gating code.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# One notch: documented numeric mapping (baseline 2.5 -> 2.0 for shadow)
DEFAULT_BASELINE_FLOOR = 2.5
DELTA_ONE_NOTCH = 0.5


def _parse_ts(r: dict) -> datetime | None:
    for key in ("ts", "timestamp"):
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
    ap = argparse.ArgumentParser(description="A3 shadow: lower expectancy score floor (shadow only)")
    ap.add_argument("--base-dir", default="", help="Repo root (default: cwd)")
    ap.add_argument("--since-hours", type=float, default=24.0, help="Window: last N hours of blocked_trades")
    ap.add_argument("--baseline-floor", type=float, default=DEFAULT_BASELINE_FLOOR, help="Current score floor (e.g. 2.5)")
    ap.add_argument("--delta", type=float, default=DELTA_ONE_NOTCH, help="One notch reduction (e.g. 0.5 -> effective floor 2.0)")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else Path.cwd()
    base = base.resolve()
    since_hours = max(1.0, args.since_hours)
    baseline_floor = args.baseline_floor
    delta = max(0.0, args.delta)
    effective_floor = baseline_floor - delta

    # Do not import main, execution, or order placement
    blocked_path = base / "state" / "blocked_trades.jsonl"
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    blocked_in_window = []
    for r in _iter_jsonl(blocked_path):
        t = _parse_ts(r)
        if t and t >= cutoff:
            blocked_in_window.append(r)

    floor_breach = [r for r in blocked_in_window if "score_floor_breach" in str(r.get("reason") or r.get("block_reason") or "")]
    would_pass = []
    for r in floor_breach:
        score = r.get("score") or r.get("composite_exec_score") or r.get("candidate_score")
        if score is not None:
            try:
                s = float(score)
                if s >= effective_floor:
                    would_pass.append(r)
            except (TypeError, ValueError):
                pass

    additional_admitted = len(would_pass)

    # Proxy: avg PnL per exit from last-387 or board review file
    avg_pnl_per_exit = 0.0
    proxy_label = "proxy"
    review_path = base / "reports" / "board" / "last387_comprehensive_review.json"
    if review_path.exists():
        try:
            data = json.loads(review_path.read_text(encoding="utf-8"))
            pnl = data.get("pnl") or {}
            total = pnl.get("total_exits") or 1
            total_pnl = pnl.get("total_pnl_attribution_usd") or pnl.get("total_pnl_exit_attribution_usd") or 0
            avg_pnl_per_exit = total_pnl / total if total else 0.0
        except Exception:
            pass
    if avg_pnl_per_exit == 0.0:
        exit_path = base / "logs" / "exit_attribution.jsonl"
        if exit_path.exists():
            pnls = []
            for r in _iter_jsonl(exit_path):
                p = r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd")
                if p is not None:
                    try:
                        pnls.append(float(p))
                    except (TypeError, ValueError):
                        pass
            if pnls:
                avg_pnl_per_exit = sum(pnls[-387:]) / len(pnls[-387:]) if len(pnls) >= 387 else (sum(pnls) / len(pnls))

    estimated_pnl_delta = round(additional_admitted * avg_pnl_per_exit, 2)
    win_rate_delta = None  # not computable without per-block outcome

    tail_risk_notes = []
    if additional_admitted > 0:
        tail_risk_notes.append("Admitting more low-score trades may increase loss concentration; monitor worst-N if promoted to live.")
    if would_pass:
        scores = []
        for r in would_pass:
            s = r.get("score") or r.get("composite_exec_score") or r.get("candidate_score")
            if s is not None:
                try:
                    scores.append(float(s))
                except (TypeError, ValueError):
                    pass
        if scores:
            tail_risk_notes.append(f"Would-admit score range: {min(scores):.2f}–{max(scores):.2f} (effective_floor={effective_floor}).")

    run_ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "scenario_id": "A3",
        "name": "Lower expectancy score floor (shadow only)",
        "run_ts": run_ts,
        "since_hours": since_hours,
        "baseline_floor": baseline_floor,
        "delta_one_notch": delta,
        "effective_floor_shadow": effective_floor,
        "blocked_in_window": len(blocked_in_window),
        "floor_breach_count": len(floor_breach),
        "additional_admitted_trades": additional_admitted,
        "estimated_pnl_delta_usd": estimated_pnl_delta,
        "estimated_pnl_delta_label": proxy_label,
        "win_rate_delta": win_rate_delta,
        "tail_risk_notes": tail_risk_notes,
        "avg_pnl_per_exit_proxy": round(avg_pnl_per_exit, 4),
        "shadow_only": True,
        "no_live_execution_change": True,
    }

    state_dir = base / "state" / "shadow"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "a3_expectancy_floor_shadow.json"
    state_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {state_path}")

    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    md_path = audit_dir / "A3_SHADOW_RESULTS.md"
    md_lines = [
        "# A3 shadow results (expectancy score floor)",
        "",
        f"**Run (UTC):** {run_ts}",
        "",
        "## Parameters",
        "",
        f"- **Since hours:** {since_hours}",
        f"- **Baseline floor:** {baseline_floor}",
        f"- **Delta (one notch):** {delta}",
        f"- **Effective floor (shadow):** {effective_floor}",
        "",
        "## Deltas",
        "",
        f"- **Additional admitted trades (would-pass):** {additional_admitted}",
        f"- **Estimated PnL delta (USD):** {estimated_pnl_delta} **({proxy_label})**",
        f"- **Win rate delta:** {win_rate_delta if win_rate_delta is not None else 'not computable without per-block outcome'}",
        "",
        "## Tail-risk notes",
        "",
    ]
    for n in tail_risk_notes:
        md_lines.append(f"- {n}")
    md_lines.extend([
        "",
        "## Safety",
        "",
        "**Shadow only; no live execution changes.** This script does not import or call order placement or gating code.",
        "",
    ])
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
