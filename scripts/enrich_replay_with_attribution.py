#!/usr/bin/env python3
"""
Enrich blocked_expectancy replay_results with attribution from blocked_trades so downstream
conditional/research pipeline has group_sums and components. Use when blocked_signal_expectancy
replay is empty but blocked_expectancy replay exists. No live trade code touched.
Reads: reports/blocked_expectancy/extracted_candidates.jsonl, replay_results.jsonl, state/blocked_trades.jsonl.
Writes: reports/blocked_signal_expectancy/replay_results.jsonl (and bucket_analysis + signal_group_expectancy).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

BE_DIR = REPO / "reports" / "blocked_expectancy"
BS_DIR = REPO / "reports" / "blocked_signal_expectancy"
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"

UW_KEYS = {"flow", "dark_pool", "insider", "whale", "event"}
REGIME_MACRO_KEYS = {"regime", "market_tide", "calendar", "motif_bonus"}
OTHER_KEYS = {
    "congress", "shorts_squeeze", "institutional", "iv_skew", "smile",
    "toxicity_penalty", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score"
}


def _component_group_sums(comp):
    if not isinstance(comp, dict):
        return {}
    uw = sum(comp.get(k, 0) or 0 for k in UW_KEYS if isinstance(comp.get(k), (int, float)))
    reg = sum(comp.get(k, 0) or 0 for k in REGIME_MACRO_KEYS if isinstance(comp.get(k), (int, float)))
    other = sum(comp.get(k, 0) or 0 for k in OTHER_KEYS if isinstance(comp.get(k), (int, float)))
    return {"uw": round(uw, 4), "regime_macro": round(reg, 4), "other_components": round(other, 4)}


def _norm_ts(ts):
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return int(ts)
    s = str(ts).strip()
    if s.isdigit():
        return int(s)
    return s


def main() -> int:
    extracted_path = BE_DIR / "extracted_candidates.jsonl"
    replay_path = BE_DIR / "replay_results.jsonl"
    if not extracted_path.exists() or not replay_path.exists():
        print("blocked_expectancy extracted_candidates or replay_results missing")
        return 1
    candidates = []
    for line in extracted_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            candidates.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    replay_results = []
    for line in replay_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            replay_results.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if len(candidates) != len(replay_results) or not replay_results:
        print("candidate/replay length mismatch or empty replay")
        return 1

    # Build (symbol, ts) -> attribution from blocked_trades
    bt_attribution = {}
    if BLOCKED_PATH.exists():
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
            sym = (r.get("symbol") or "?").strip().upper()
            ts = _norm_ts(r.get("timestamp") or r.get("ts"))
            att = r.get("attribution_snapshot") or {}
            comp = att.get("weighted_contributions") or r.get("components") or {}
            gs = att.get("group_sums")
            if not gs and isinstance(comp, dict):
                gs = _component_group_sums(comp)
            bt_attribution[(sym, ts)] = {"group_sums": gs or {}, "components": comp if isinstance(comp, dict) else {}}
            bt_attribution[(sym, str(ts))] = bt_attribution[(sym, ts)]

    enriched = []
    for i, rec in enumerate(replay_results):
        c = candidates[i] if i < len(candidates) else {}
        sym = (c.get("symbol") or rec.get("symbol") or "?").strip().upper()
        ts = _norm_ts(c.get("timestamp"))
        att = bt_attribution.get((sym, ts)) or bt_attribution.get((sym, str(ts))) or {}
        gs = att.get("group_sums") or {}
        comp = att.get("components") or {}
        enriched.append({
            "symbol": rec.get("symbol", sym),
            "score": rec.get("score"),
            "bucket": rec.get("bucket", c.get("bucket")),
            "block_reason": rec.get("reason", c.get("reason")),
            "pnl_pct": rec.get("pnl_pct", 0),
            "mfe_pct": rec.get("mfe_pct", 0),
            "mae_pct": rec.get("mae_pct", 0),
            "exit_reason": rec.get("exit_reason"),
            "hold_bars": rec.get("hold_bars", 0),
            "group_sums": gs,
            "components": comp,
        })

    BS_DIR.mkdir(parents=True, exist_ok=True)
    with (BS_DIR / "replay_results.jsonl").open("w", encoding="utf-8") as f:
        for r in enriched:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"Enriched {len(enriched)} replay rows -> {BS_DIR / 'replay_results.jsonl'}")

    # Write bucket_analysis and signal_group_expectancy so downstream has non-empty files
    by_bucket = defaultdict(lambda: {"pnl_pcts": [], "n": 0})
    for r in enriched:
        b = r.get("bucket") or "unknown"
        by_bucket[b]["pnl_pcts"].append(r.get("pnl_pct", 0))
        by_bucket[b]["n"] += 1
    buckets_sorted = sorted(by_bucket.keys(), key=lambda x: (float(x.split("-")[0]) if "-" in x and x != "unknown" else -1))
    blines = [
        "# Blocked-trade score bucket analysis (enriched)",
        "",
        "| bucket | n | mean_pnl_pct | win_rate | median_pnl_pct | mean_expectancy_contribution |",
        "|--------|---|--------------|----------|----------------|------------------------------|",
    ]
    for b in buckets_sorted:
        vals = by_bucket[b]["pnl_pcts"]
        n = len(vals)
        if n == 0:
            continue
        mean_pnl = sum(vals) / n
        wins = sum(1 for v in vals if v > 0)
        wr = wins / n * 100
        med = sorted(vals)[n // 2]
        blines.append(f"| {b} | {n} | {mean_pnl:.3f} | {wr:.1f}% | {med:.3f} | {mean_pnl:.3f} |")
    (BS_DIR / "bucket_analysis.md").write_text("\n".join(blines), encoding="utf-8")

    def strong_weak(key):
        with_vals = [(r, r.get("group_sums") or {}) for r in enriched if isinstance(r.get("group_sums"), dict) and r.get("group_sums")]
        vals = [gs.get(key, 0) for _, gs in with_vals]
        if not vals:
            return None, None, 0, 0
        sorted_vals = sorted(vals)
        n = len(sorted_vals)
        tx = max(1, n // 3)
        strong_cut = sorted_vals[-tx]
        weak_cut = sorted_vals[tx - 1]
        strong_pnls = [r["pnl_pct"] for r, gs in with_vals if (gs.get(key) or 0) >= strong_cut]
        weak_pnls = [r["pnl_pct"] for r, gs in with_vals if (gs.get(key) or 0) <= weak_cut]
        ms = sum(strong_pnls) / len(strong_pnls) if strong_pnls else 0
        mw = sum(weak_pnls) / len(weak_pnls) if weak_pnls else 0
        return ms, mw, len(strong_pnls), len(weak_pnls)
    slines = [
        "# Signal-group expectancy (strong vs weak) (enriched)",
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
