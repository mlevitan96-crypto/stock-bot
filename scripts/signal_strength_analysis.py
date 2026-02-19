#!/usr/bin/env python3
"""
Signal strengthening loop — Phase 1 & 2.
Run on droplet. Reads:
  - reports/blocked_expectancy/replay_results.jsonl
  - reports/blocked_signal_expectancy/replay_results.jsonl (has group_sums)
  - reports/blocked_signal_expectancy/blocked_candidates.jsonl (full components)
Joins replay outcome (pnl) with signal breakdown, labels WINNER/LOSER, computes
per-signal stats and edge ranking. Writes to reports/signal_strength/.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "reports" / "signal_strength"
REPLAY_BE = REPO / "reports" / "blocked_expectancy" / "replay_results.jsonl"
REPLAY_BS = REPO / "reports" / "blocked_signal_expectancy" / "replay_results.jsonl"
CANDIDATES_BS = REPO / "reports" / "blocked_signal_expectancy" / "blocked_candidates.jsonl"
BLOCKED_TRADES = REPO / "state" / "blocked_trades.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _quantiles(vals: list[float]) -> tuple[float, float, float]:
    if not vals:
        return 0.0, 0.0, 0.0
    s = sorted(vals)
    n = len(s)
    p25 = s[int(n * 0.25)] if n else 0.0
    p50 = s[n // 2] if n else 0.0
    p75 = s[int(n * 0.75)] if n else 0.0
    return p25, p50, p75


def _corr(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x) / n) or 1e-12
    sy = math.sqrt(sum((b - my) ** 2 for b in y) / n) or 1e-12
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (n * sx * sy)


def run_phase1_phase2() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prefer replay with group_sums (blocked_signal_expectancy)
    replays = _load_jsonl(REPLAY_BS)
    if not replays:
        replays = _load_jsonl(REPLAY_BE)
    # If replay has no group_sums, join with blocked_trades via extracted_candidates (same order)
    if replays and not any(r.get("group_sums") for r in replays):
        extracted = _load_jsonl(REPO / "reports" / "blocked_expectancy" / "extracted_candidates.jsonl")
        bt_list = _load_jsonl(BLOCKED_TRADES)
        bt_by_sym = defaultdict(list)
        for b in bt_list:
            sym = b.get("symbol")
            if sym:
                bt_by_sym[sym].append(b)
        for i, r in enumerate(replays):
            sym = r.get("symbol")
            if not sym and i < len(extracted):
                sym = extracted[i].get("symbol")
            if not sym:
                continue
            best = None
            for b in bt_by_sym.get(sym, [])[:30]:
                comp = b.get("components") or {}
                if isinstance(comp, dict) and comp:
                    best = comp
                    break
            if best:
                r["components"] = best
                uw = sum(float(best.get(k, 0) or 0) for k in ("options_flow", "dark_pool", "insider", "whale_persistence", "event_alignment"))
                reg = sum(float(best.get(k, 0) or 0) for k in ("regime_modifier", "market_tide", "calendar_catalyst", "temporal_motif"))
                other = sum(float(best.get(k, 0) or 0) for k in best if k not in ("options_flow", "dark_pool", "insider", "whale_persistence", "event_alignment", "regime_modifier", "market_tide", "calendar_catalyst", "temporal_motif"))
                r["group_sums"] = {"uw": round(uw, 4), "regime_macro": round(reg, 4), "other_components": round(other, 4)}
    if not replays:
        (OUT_DIR / "win_loss_signal_profile.md").write_text(
            "# Win/Loss Signal Profile\n\nNo replay data found. Run blocked_expectancy and blocked_signal_expectancy on droplet first.\n",
            encoding="utf-8",
        )
        (OUT_DIR / "signal_edge_ranking.md").write_text("# Signal Edge Ranking\n\nNo data.\n", encoding="utf-8")
        return 0

    # Join with candidates for full components if available (same order as pipeline)
    candidates = _load_jsonl(CANDIDATES_BS)
    if len(candidates) >= len(replays):
        for i, r in enumerate(replays):
            if i < len(candidates):
                c = candidates[i]
                if not r.get("group_sums") and c.get("group_sums"):
                    r["group_sums"] = c.get("group_sums")
                if not r.get("components") and c.get("signal_group_scores"):
                    r["components"] = c.get("signal_group_scores")

    winners = [r for r in replays if (r.get("pnl_pct") or 0) > 0]
    losers = [r for r in replays if (r.get("pnl_pct") or 0) <= 0]
    n_win, n_lose = len(winners), len(losers)

    # Signal keys: group_sums (uw, regime_macro, other_components) + any component keys from first row
    all_keys = set()
    for r in replays:
        gs = r.get("group_sums") or {}
        all_keys.update(gs.keys())
        comp = r.get("components") or {}
        if isinstance(comp, dict):
            all_keys.update(comp.keys())
    signal_keys = sorted(all_keys)

    lines = [
        "# Win/Loss Signal Profile",
        "",
        f"Total replayed: {len(replays)} | WINNER (pnl>0): {n_win} | LOSER (pnl<=0): {n_lose}",
        "",
        "## Per-signal: mean(WINNERS) vs mean(LOSERS), distribution, correlation with pnl",
        "",
        "| signal | mean_winner | mean_loser | delta_mean | p25_w | p50_w | p75_w | p25_l | p50_l | p75_l | corr_pnl |",
        "|--------|-------------|------------|------------|-------|-------|-------|-------|-------|-------|----------|",
    ]

    edge_rows = []
    for key in signal_keys:
        win_vals = []
        lose_vals = []
        all_vals = []
        pnl_vals = []
        for r in replays:
            pnl = float(r.get("pnl_pct") or 0)
            gs = r.get("group_sums") or {}
            comp = r.get("components") or {}
            v = None
            if key in gs:
                v = float(gs[key]) if gs[key] is not None else None
            elif isinstance(comp, dict) and key in comp:
                v = float(comp[key]) if comp[key] is not None else None
            if v is None:
                continue
            all_vals.append((v, pnl))
            if pnl > 0:
                win_vals.append(v)
            else:
                lose_vals.append(v)
            pnl_vals.append(pnl)
        if not all_vals:
            continue
        vals_only = [x[0] for x in all_vals]
        mean_w = sum(win_vals) / len(win_vals) if win_vals else 0.0
        mean_l = sum(lose_vals) / len(lose_vals) if lose_vals else 0.0
        delta = mean_w - mean_l
        p25_w, p50_w, p75_w = _quantiles(win_vals)
        p25_l, p50_l, p75_l = _quantiles(lose_vals)
        corr = _corr(vals_only, pnl_vals)
        lines.append(
            f"| {key} | {mean_w:.4f} | {mean_l:.4f} | {delta:+.4f} | {p25_w:.3f} | {p50_w:.3f} | {p75_w:.3f} | {p25_l:.3f} | {p50_l:.3f} | {p75_l:.3f} | {corr:+.3f} |"
        )
        edge_rows.append((key, delta, corr, len(vals_only)))

    (OUT_DIR / "win_loss_signal_profile.md").write_text("\n".join(lines), encoding="utf-8")

    # Phase 2: Edge ranking
    edge_rows.sort(key=lambda x: (-abs(x[1]), -abs(x[2])))
    edge_positive = [(k, d, c, n) for k, d, c, n in edge_rows if d > 0 and c >= 0]
    edge_negative = [(k, d, c, n) for k, d, c, n in edge_rows if d < 0 and c <= 0]
    neutral = [(k, d, c, n) for k, d, c, n in edge_rows if (k, d, c, n) not in edge_positive and (k, d, c, n) not in edge_negative]

    rank_lines = [
        "# Signal Edge Ranking",
        "",
        "## EDGE_POSITIVE (increase weight)",
        "",
    ]
    for k, d, c, n in edge_positive[:15]:
        rank_lines.append(f"- **{k}** delta_mean={d:+.4f} corr_pnl={c:+.3f} n={n}")
    rank_lines.extend(["", "## EDGE_NEGATIVE (decrease or zero weight)", ""])
    for k, d, c, n in edge_negative[:15]:
        rank_lines.append(f"- **{k}** delta_mean={d:+.4f} corr_pnl={c:+.3f} n={n}")
    rank_lines.extend(["", "## NEUTRAL/NOISE", ""])
    for k, d, c, n in neutral[:10]:
        rank_lines.append(f"- {k} delta_mean={d:+.4f} corr_pnl={c:+.3f} n={n}")
    (OUT_DIR / "signal_edge_ranking.md").write_text("\n".join(rank_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(run_phase1_phase2())
