#!/usr/bin/env python3
"""
Blocked-signal expectancy pipeline:
  Phase 2: Extract blocked candidates (score_snapshot + blocked_trades) -> blocked_candidates.jsonl
  Phase 3: Replay -> replay_results.jsonl
  Phase 4: Bucket + signal-group analysis -> bucket_analysis.md, signal_group_expectancy.md
  Phase 5: Root cause + edge -> root_cause_and_edge.md
Run from repo root. On droplet: run after fetching logs/score_snapshot.jsonl and state/blocked_trades.jsonl.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "reports" / "blocked_signal_expectancy"
SNAPSHOT_PATH = REPO / "logs" / "score_snapshot.jsonl"
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"

# Map composite components to signal groups for attribution
UW_KEYS = {"options_flow", "dark_pool", "insider", "whale_persistence", "event_alignment"}
REGIME_MACRO_KEYS = {"regime_modifier", "market_tide", "calendar_catalyst", "temporal_motif"}
OTHER_COMPONENT_KEYS = {
    "congress", "shorts_squeeze", "institutional", "iv_term_skew", "smile_slope",
    "toxicity_penalty", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score"
}
TRAILING_STOP_PCT = 0.015
TIME_EXIT_MINUTES = 240


def _parse_ts(v):
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _score_bucket(score):
    if score is None:
        return "unknown"
    try:
        s = float(score)
        lo = int(s * 2) / 2.0
        return f"{lo:.1f}-{lo+0.5:.1f}"
    except Exception:
        return "unknown"


def _component_group_sums(components):
    """components = dict from composite_meta or signal_group_scores."""
    if not isinstance(components, dict):
        return {}
    uw = sum(components.get(k, 0) or 0 for k in UW_KEYS if isinstance(components.get(k), (int, float)))
    regime = sum(components.get(k, 0) or 0 for k in REGIME_MACRO_KEYS if isinstance(components.get(k), (int, float)))
    other = sum(components.get(k, 0) or 0 for k in OTHER_COMPONENT_KEYS if isinstance(components.get(k), (int, float)))
    return {"uw": round(uw, 4), "regime_macro": round(regime, 4), "other_components": round(other, 4)}


def extract_blocked_candidates():
    """Build blocked_candidates from score_snapshot (primary) and blocked_trades (fallback for price/components)."""
    candidates = []
    # 1) score_snapshot: has block_reason, composite_score, signal_group_scores
    if SNAPSHOT_PATH.exists():
        for line in SNAPSHOT_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            gates = r.get("gates") or {}
            block_reason = gates.get("block_reason")
            if block_reason not in ("score_below_min", "expectancy_blocked:score_floor_breach"):
                continue
            composite = r.get("composite_score")
            try:
                composite = float(composite) if composite is not None else None
            except (TypeError, ValueError):
                composite = None
            signal_group_scores = r.get("signal_group_scores")
            if isinstance(signal_group_scores, dict):
                comps = signal_group_scores.get("components") or signal_group_scores
            else:
                comps = {}
            group_sums = _component_group_sums(comps)
            candidates.append({
                "ts": r.get("ts"),
                "ts_iso": r.get("ts_iso"),
                "symbol": r.get("symbol") or "?",
                "composite_score": composite,
                "block_reason": block_reason,
                "signal_group_scores": comps,
                "group_sums": group_sums,
            })
    # 2) blocked_trades: add entry_price and merge components for any missing from snapshot
    bt_by_key = {}
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
            ts = r.get("timestamp") or r.get("ts")
            key = (r.get("symbol"), ts)
            bt_by_key[key] = {
                "decision_price": r.get("would_have_entered_price") or r.get("decision_price"),
                "components": r.get("components") or {},
                "direction": r.get("direction"),
            }
    # Merge: add entry_price to candidates (match by symbol + nearest ts)
    for c in candidates:
        sym = c.get("symbol")
        ts = c.get("ts") or c.get("ts_iso")
        best = None
        for (bsym, bts), bt in bt_by_key.items():
            if bsym != sym:
                continue
            if best is None:
                best = bt
                continue
            # Prefer same ts
            if bts == ts:
                best = bt
                break
        if best:
            c["entry_price"] = best.get("decision_price")
            c["direction"] = best.get("direction", "bullish")
            if not c.get("signal_group_scores") and best.get("components"):
                c["signal_group_scores"] = best["components"]
                c["group_sums"] = _component_group_sums(best["components"])
        c["entry_price"] = c.get("entry_price")
        try:
            c["entry_price"] = float(c["entry_price"]) if c.get("entry_price") is not None else None
        except (TypeError, ValueError):
            c["entry_price"] = None
        c["side"] = "long" if (c.get("direction") or "bullish").lower() == "bullish" else "short"
        c["bucket"] = _score_bucket(c.get("composite_score"))
    return candidates


def load_bars_for_candidate(symbol: str, entry_dt: datetime, max_minutes: int = 300):
    if symbol in (None, "", "?"):
        return []
    try:
        from data.bars_loader import load_bars
    except ImportError:
        return []
    date_str = entry_dt.strftime("%Y-%m-%d")
    end_ts = entry_dt + timedelta(minutes=max_minutes)
    bars = load_bars(symbol, date_str, timeframe="1Min", start_ts=entry_dt, end_ts=end_ts, use_cache=True, fetch_if_missing=True)
    if not bars:
        for tf in ("5Min", "15Min",):
            bars = load_bars(symbol, date_str, timeframe=tf, start_ts=entry_dt, end_ts=end_ts, use_cache=True, fetch_if_missing=True)
            if bars:
                break
    return bars


def replay_one(candidate: dict) -> dict | None:
    symbol = candidate.get("symbol")
    entry_price = candidate.get("entry_price")
    side = candidate.get("side", "long")
    ts = candidate.get("ts") or candidate.get("ts_iso") or candidate.get("timestamp")
    entry_dt = _parse_ts(ts)
    if not entry_dt or not symbol or symbol == "?" or not entry_price or entry_price <= 0:
        return None
    bars = load_bars_for_candidate(symbol, entry_dt, max_minutes=TIME_EXIT_MINUTES + 30)
    if not bars:
        return None
    bar_list = []
    for b in bars:
        t = b.get("t") or b.get("timestamp")
        dt = _parse_ts(t)
        if dt is None or dt < entry_dt:
            continue
        o = float(b.get("o", b.get("open", 0)))
        h = float(b.get("h", b.get("high", 0)))
        l = float(b.get("l", b.get("low", 0)))
        c = float(b.get("c", b.get("close", 0)))
        bar_list.append((dt, o, h, l, c))
    if not bar_list:
        return None
    exit_time = entry_dt + timedelta(minutes=TIME_EXIT_MINUTES)
    mfe_pct = 0.0
    mae_pct = 0.0
    exit_price = entry_price
    exit_reason = "session_end"
    hold_bars = 0
    for i, (dt, o, h, l, c) in enumerate(bar_list):
        hold_bars = i + 1
        if side == "long":
            high_ret = (h - entry_price) / entry_price if entry_price else 0
            low_ret = (l - entry_price) / entry_price if entry_price else 0
        else:
            high_ret = (entry_price - l) / entry_price if entry_price else 0
            low_ret = (entry_price - h) / entry_price if entry_price else 0
        mfe_pct = max(mfe_pct, high_ret * 100)
        mae_pct = min(mae_pct, low_ret * 100)
        if side == "long" and low_ret <= -TRAILING_STOP_PCT:
            exit_price = c
            exit_reason = "trailing_stop"
            break
        if side == "short" and high_ret <= -TRAILING_STOP_PCT:
            exit_price = c
            exit_reason = "trailing_stop"
            break
        if dt >= exit_time:
            exit_price = c
            exit_reason = "time_exit"
            break
    if exit_reason == "session_end" and bar_list:
        exit_price = bar_list[-1][4]
    if side == "long":
        pnl_pct = (exit_price - entry_price) / entry_price * 100 if entry_price else 0
    else:
        pnl_pct = (entry_price - exit_price) / entry_price * 100 if entry_price else 0
    return {
        "symbol": symbol,
        "score": candidate.get("composite_score"),
        "bucket": candidate.get("bucket"),
        "block_reason": candidate.get("block_reason"),
        "pnl_pct": round(pnl_pct, 4),
        "mfe_pct": round(mfe_pct, 4),
        "mae_pct": round(mae_pct, 4),
        "exit_reason": exit_reason,
        "hold_bars": hold_bars,
        "group_sums": candidate.get("group_sums") or {},
    }


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 2
    candidates = extract_blocked_candidates()
    blocked_path = OUT_DIR / "blocked_candidates.jsonl"
    with blocked_path.open("w", encoding="utf-8") as f:
        for c in candidates:
            f.write(json.dumps(c, default=str) + "\n")
    print(f"Phase 2: {len(candidates)} blocked candidates -> {blocked_path}")

    # Phase 3
    replay_results = []
    for c in candidates:
        res = replay_one(c)
        if res is not None:
            replay_results.append(res)
    replay_path = OUT_DIR / "replay_results.jsonl"
    with replay_path.open("w", encoding="utf-8") as f:
        for r in replay_results:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"Phase 3: {len(replay_results)} replayed -> {replay_path}")

    # Phase 4a: buckets
    by_bucket = defaultdict(lambda: {"pnl_pcts": [], "n": 0})
    for r in replay_results:
        b = r.get("bucket") or "unknown"
        by_bucket[b]["pnl_pcts"].append(r.get("pnl_pct", 0))
        by_bucket[b]["n"] += 1
    buckets_sorted = sorted(by_bucket.keys(), key=lambda x: (float(x.split("-")[0]) if "-" in x and x != "unknown" else -1))
    lines = [
        "# Blocked-trade score bucket analysis",
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
        win_rate = wins / n * 100
        vals_sorted = sorted(vals)
        median_pnl = vals_sorted[n // 2] if n else 0
        # Expectancy contribution ~ mean_pnl * (win_rate/100) - |mean_pnl| * (1 - win_rate/100) simplified as mean_pnl
        exp_contrib = mean_pnl  # per-trade avg
        lines.append(f"| {b} | {n} | {mean_pnl:.3f} | {win_rate:.1f}% | {median_pnl:.3f} | {exp_contrib:.3f} |")
    (OUT_DIR / "bucket_analysis.md").write_text("\n".join(lines), encoding="utf-8")

    # Phase 4b: signal-group expectancy (strong vs weak by group sum)
    def strong_weak(replay_list, key):
        with_vals = [(r, r.get("group_sums") or {}) for r in replay_list if isinstance(r.get("group_sums"), dict)]
        vals = [gs.get(key, 0) for _, gs in with_vals]
        if not vals:
            return None, None, 0, 0
        sorted_vals = sorted(vals)
        n = len(sorted_vals)
        top_x = max(1, n // 3)
        bot_x = max(1, n // 3)
        strong_cut = sorted_vals[-top_x]
        weak_cut = sorted_vals[bot_x - 1]
        strong_pnls = [r["pnl_pct"] for r, gs in with_vals if (gs.get(key) or 0) >= strong_cut]
        weak_pnls = [r["pnl_pct"] for r, gs in with_vals if (gs.get(key) or 0) <= weak_cut]
        mean_strong = sum(strong_pnls) / len(strong_pnls) if strong_pnls else 0
        mean_weak = sum(weak_pnls) / len(weak_pnls) if weak_pnls else 0
        return mean_strong, mean_weak, len(strong_pnls), len(weak_pnls)

    sig_lines = [
        "# Signal-group expectancy (strong vs weak)",
        "",
        "| group | n_strong | n_weak | mean_pnl_strong | mean_pnl_weak | delta_expectancy |",
        "|-------|----------|--------|-----------------|---------------|------------------|",
    ]
    for key in ("uw", "regime_macro", "other_components"):
        ms, mw, ns, nw = strong_weak(replay_results, key)
        if ms is None:
            sig_lines.append(f"| {key} | 0 | 0 | - | - | - |")
        else:
            delta = (ms - mw) if (ms is not None and mw is not None) else 0
            sig_lines.append(f"| {key} | {ns} | {nw} | {ms:.3f} | {mw:.3f} | {delta:.3f} |")
    (OUT_DIR / "signal_group_expectancy.md").write_text("\n".join(sig_lines), encoding="utf-8")

    # Phase 5: root cause + edge (template; human/model fills A/B/C and which groups have edge)
    rc = [
        "# Root cause and edge",
        "",
        "## Pipeline audit",
        "- systemd_audit.md, signal_chain_audit.md, scoring_pipeline_audit.md (see reports/scoring_integrity).",
        "",
        "## Bucket analysis summary",
        "- Positive expectancy bucket: see bucket_analysis.md (mean_pnl_pct > 0, win_rate).",
        "",
        "## Signal-group edge",
        "- See signal_group_expectancy.md. Delta > 0 suggests group adds edge when strong.",
        "",
        "## Decision (A/B/C)",
        "- **A** Pipeline partially broken (missing/zeroed signals, stale caches, mis-weighted).",
        "- **B** Pipeline intact; scores weak but informative; some blocked buckets show positive expectancy.",
        "- **C** Both.",
        "",
        "## Signal groups with positive edge",
        "- List groups where mean_pnl_strong > mean_pnl_weak and delta_expectancy > 0.",
        "",
        "## Signal groups noise/negative",
        "- List groups where delta <= 0 or sample too small.",
        "",
    ]
    (OUT_DIR / "root_cause_and_edge.md").write_text("\n".join(rc), encoding="utf-8")
    print("Phase 4-5: bucket_analysis.md, signal_group_expectancy.md, root_cause_and_edge.md")
    return 0


if __name__ == "__main__":
    sys.exit(run())
