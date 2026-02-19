#!/usr/bin/env python3
"""
When bars are unavailable and replay is empty, build minimal replay_results and reports
from blocked_trades so the truth run can still produce A/B/C output (counts, research table, verdict).
No live trade code. No bars required.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"
BE_DIR = REPO / "reports" / "blocked_expectancy"
BS_DIR = REPO / "reports" / "blocked_signal_expectancy"

UW_KEYS = {"flow", "dark_pool", "insider", "whale", "event"}
REGIME_KEYS = {"regime", "market_tide", "calendar", "motif_bonus"}
OTHER_KEYS = {
    "congress", "shorts_squeeze", "institutional", "iv_skew", "smile",
    "toxicity_penalty", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score"
}


def _score_bucket(score):
    if score is None:
        return "unknown"
    try:
        s = float(score)
        lo = int(s * 2) / 2.0
        return f"{lo:.1f}-{lo+0.5:.1f}"
    except Exception:
        return "unknown"


def _component_group_sums(comp):
    if not isinstance(comp, dict):
        return {}
    uw = sum(comp.get(k, 0) or 0 for k in UW_KEYS if isinstance(comp.get(k), (int, float)))
    reg = sum(comp.get(k, 0) or 0 for k in REGIME_KEYS if isinstance(comp.get(k), (int, float)))
    other = sum(comp.get(k, 0) or 0 for k in OTHER_KEYS if isinstance(comp.get(k), (int, float)))
    return {"uw": round(uw, 4), "regime_macro": round(reg, 4), "other_components": round(other, 4)}


def main() -> int:
    if not BLOCKED_PATH.exists():
        print("state/blocked_trades.jsonl missing")
        return 1
    rows = []
    for line in BLOCKED_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        reason = (r.get("reason") or r.get("block_reason") or "").strip()
        if reason not in ("score_below_min", "expectancy_blocked:score_floor_breach"):
            continue
        score = r.get("score") or r.get("candidate_score")
        try:
            score = float(score) if score is not None else None
        except (TypeError, ValueError):
            score = None
        att = r.get("attribution_snapshot") or {}
        comp = att.get("weighted_contributions") or r.get("components") or {}
        gs = att.get("group_sums")
        if not gs and isinstance(comp, dict):
            gs = _component_group_sums(comp)
        rows.append({
            "symbol": (r.get("symbol") or "?").strip().upper(),
            "score": score,
            "bucket": _score_bucket(score),
            "block_reason": reason,
            "pnl_pct": 0.0,
            "mfe_pct": 0.0,
            "mae_pct": 0.0,
            "exit_reason": "no_bars",
            "hold_bars": 0,
            "group_sums": gs or {},
            "components": comp if isinstance(comp, dict) else {},
        })
    if not rows:
        print("No eligible blocked_trades rows")
        return 1
    BS_DIR.mkdir(parents=True, exist_ok=True)
    with (BS_DIR / "replay_results.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    by_bucket = defaultdict(lambda: {"pnl_pcts": [], "n": 0})
    for r in rows:
        b = r.get("bucket") or "unknown"
        by_bucket[b]["pnl_pcts"].append(r.get("pnl_pct", 0))
        by_bucket[b]["n"] += 1
    buckets_sorted = sorted(by_bucket.keys(), key=lambda x: (float(x.split("-")[0]) if "-" in x and x != "unknown" else -1))
    blines = [
        "# Blocked-trade score bucket analysis (minimal, no bars)",
        "",
        "| bucket | n | mean_pnl_pct | win_rate | median_pnl_pct | mean_expectancy_contribution |",
        "|--------|---|--------------|----------|----------------|------------------------------|",
    ]
    for b in buckets_sorted:
        vals = by_bucket[b]["pnl_pcts"]
        n = len(vals)
        mean_pnl = sum(vals) / n
        wins = sum(1 for v in vals if v > 0)
        wr = wins / n * 100
        med = sorted(vals)[n // 2] if vals else 0
        blines.append(f"| {b} | {n} | {mean_pnl:.3f} | {wr:.1f}% | {med:.3f} | {mean_pnl:.3f} |")
    (BS_DIR / "bucket_analysis.md").write_text("\n".join(blines), encoding="utf-8")
    def strong_weak(key):
        with_vals = [(r, r.get("group_sums") or {}) for r in rows if (r.get("group_sums") or {}).get(key) is not None]
        if not with_vals:
            return None, None, 0, 0
        vals = [gs.get(key, 0) for _, gs in with_vals]
        sorted_vals = sorted(vals)
        n = len(sorted_vals)
        tx = max(1, n // 3)
        sc = sorted_vals[-tx]
        wc = sorted_vals[tx - 1]
        sp = [r["pnl_pct"] for r, gs in with_vals if (gs.get(key) or 0) >= sc]
        wp = [r["pnl_pct"] for r, gs in with_vals if (gs.get(key) or 0) <= wc]
        return sum(sp) / len(sp) if sp else 0, sum(wp) / len(wp) if wp else 0, len(sp), len(wp)
    slines = [
        "# Signal-group expectancy (minimal, no bars)",
        "",
        "| group | n_strong | n_weak | mean_pnl_strong | mean_pnl_weak | delta_expectancy |",
        "|-------|----------|--------|-----------------|---------------|------------------|",
    ]
    for key in ("uw", "regime_macro", "other_components"):
        ms, mw, ns, nw = strong_weak(key)
        if ms is None:
            slines.append(f"| {key} | 0 | 0 | - | - | - |")
        else:
            slines.append(f"| {key} | {ns} | {nw} | {ms:.3f} | {mw:.3f} | {(ms - mw):.3f} |")
    (BS_DIR / "signal_group_expectancy.md").write_text("\n".join(slines), encoding="utf-8")
    print(f"Minimal replay: {len(rows)} rows from blocked_trades (no bars; pnl=0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
