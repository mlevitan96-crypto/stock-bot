#!/usr/bin/env python3
"""
Read-only uplift + blocked summary for Profit V2 evidence (bootstrap on matched exits).

Join: exit_attribution tail vs score_snapshot on symbol + nearest ts_iso/ts.
Estimates high-vs-low median split on selected UW-related components (flow, dark_pool, whale).

Also tallies blocked_trades.jsonl by block_reason / reason field.

Outputs JSON suitable for PROFIT_V2_SIGNAL_UW_UPLIFT.json and blocked causal appendix.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]

UW_KEYS = ("flow", "dark_pool", "whale", "etf_flow", "greeks_gamma")


def _parse_ts(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("Z", "+00:00")
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s[:32])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (TypeError, ValueError):
        return None


def _components_from_snapshot(row: dict) -> Dict[str, float]:
    sgs = row.get("signal_group_scores")
    if not isinstance(sgs, dict):
        return {}
    comps = sgs.get("components")
    if not isinstance(comps, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in comps.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def _load_jsonl_tail(path: Path, max_rows: int) -> List[dict]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    chunk = lines[-max_rows:] if len(lines) > max_rows else lines
    out: List[dict] = []
    for ln in chunk:
        ln = ln.strip()
        if not ln:
            continue
        try:
            o = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if isinstance(o, dict):
            out.append(o)
    return out


def _match_snapshots(
    exits: List[dict], snaps: List[dict]
) -> List[Tuple[dict, dict, float]]:
    """Return (exit, snap, delta_sec) best snap at or before exit time per symbol."""
    by_sym: Dict[str, List[Tuple[float, dict]]] = defaultdict(list)
    for s in snaps:
        sym = str(s.get("symbol") or "").upper()
        ts = _parse_ts(s.get("ts_iso") or s.get("timestamp"))
        if not sym or ts is None:
            continue
        by_sym[sym].append((ts, s))
    for sym in by_sym:
        by_sym[sym].sort(key=lambda x: x[0])
    matched: List[Tuple[dict, dict, float]] = []
    for e in exits:
        sym = str(e.get("symbol") or "").upper()
        et = _parse_ts(e.get("exit_ts") or e.get("timestamp"))
        if not sym or et is None:
            continue
        arr = by_sym.get(sym)
        if not arr:
            continue
        ts_list = [t for t, _ in arr]
        i = bisect_left(ts_list, et) - 1
        if i < 0:
            continue
        snap = arr[i][1]
        matched.append((e, snap, et - ts_list[i]))
    return matched


def _split_uplift(vals_high: List[float], vals_low: List[float], n_boot: int, seed: int) -> Dict[str, float]:
    rng = random.Random(seed)
    if not vals_high or not vals_low:
        return {"mean_high": float("nan"), "mean_low": float("nan"), "delta": float("nan")}
    dh = sum(vals_high) / len(vals_high)
    dl = sum(vals_low) / len(vals_low)
    deltas = []
    for _ in range(n_boot):
        hh = [vals_high[rng.randrange(len(vals_high))] for _ in range(len(vals_high))]
        ll = [vals_low[rng.randrange(len(vals_low))] for _ in range(len(vals_low))]
        deltas.append(sum(hh) / len(hh) - sum(ll) / len(ll))
    deltas.sort()
    lo = deltas[int(0.025 * (len(deltas) - 1))] if deltas else float("nan")
    hi = deltas[int(0.975 * (len(deltas) - 1))] if deltas else float("nan")
    return {
        "mean_high": round(dh, 6),
        "mean_low": round(dl, 6),
        "delta_mean": round(dh - dl, 6),
        "bootstrap_p95_low": round(lo, 6),
        "bootstrap_p95_high": round(hi, 6),
        "n_high": len(vals_high),
        "n_low": len(vals_low),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--max-exit", type=int, default=25000)
    ap.add_argument("--max-snap", type=int, default=60000)
    ap.add_argument("--max-blocked", type=int, default=15000)
    ap.add_argument("--evidence-dir", type=Path, required=True)
    ap.add_argument("--n-bootstrap", type=int, default=400)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    root = args.root.resolve()
    ev = args.evidence_dir.resolve()
    ev.mkdir(parents=True, exist_ok=True)

    exits = _load_jsonl_tail(root / "logs" / "exit_attribution.jsonl", args.max_exit)
    snaps = _load_jsonl_tail(root / "logs" / "score_snapshot.jsonl", args.max_snap)
    blocked_path = root / "state" / "blocked_trades.jsonl"
    if not blocked_path.is_file():
        blocked_path = root / "logs" / "blocked_trades.jsonl"
    blocked = _load_jsonl_tail(blocked_path, args.max_blocked)

    matched = _match_snapshots(exits, snaps)
    pnl_key = "pnl"
    uplifts: Dict[str, Any] = {}
    for key in UW_KEYS:
        xs: List[Tuple[float, float]] = []  # (component, pnl)
        for e, snap, _ in matched:
            comps = _components_from_snapshot(snap)
            if key not in comps:
                continue
            pnl = e.get(pnl_key)
            try:
                pnl_f = float(pnl)
            except (TypeError, ValueError):
                continue
            xs.append((comps[key], pnl_f))
        if len(xs) < 10:
            uplifts[key] = {"n": len(xs), "note": "insufficient rows"}
            continue
        xs.sort(key=lambda t: t[0])
        mid = len(xs) // 2
        low = [p for _, p in xs[:mid]]
        high = [p for _, p in xs[mid:]]
        uplifts[key] = {
            "n": len(xs),
            "median_split_on_component": round(xs[mid][0], 6),
            "bootstrap": _split_uplift(high, low, args.n_bootstrap, args.seed),
        }

    b_reasons = Counter()
    for b in blocked:
        r = b.get("block_reason") or b.get("reason") or b.get("gate_reason") or "unknown"
        b_reasons[str(r)[:120]] += 1

    out = {
        "matched_exit_snapshot_pairs": len(matched),
        "exit_tail_rows": len(exits),
        "snapshot_tail_rows": len(snaps),
        "blocked_tail_rows": len(blocked),
        "uw_component_uplift_bootstrap": uplifts,
        "blocked_reason_counts_tail": dict(b_reasons.most_common(40)),
        "disclaimer": "Median split is not causal; small n; same-sample bootstrap for exploration only.",
    }
    (ev / "PROFIT_V2_SIGNAL_UW_UPLIFT.json").write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")

    md = [
        "# PROFIT_V2_SIGNAL_UW_UPLIFT\n",
        f"- Matched exit↔snapshot pairs: **{len(matched)}**\n",
        "- Bootstrap: 2.5–97.5 percentile of high-vs-low mean PnL difference (median split on component).\n",
        "\n## Per-component summary\n",
    ]
    for k, v in uplifts.items():
        md.append(f"### `{k}`\n\n```json\n{json.dumps(v, indent=2)}\n```\n")
    (ev / "PROFIT_V2_SIGNAL_UW_UPLIFT.md").write_text("".join(md), encoding="utf-8")

    blk = {
        "blocked_tail_rows": len(blocked),
        "top_reasons": dict(b_reasons.most_common(25)),
        "note": "Counterfactual PnL for blocked names requires bars + symbol-time alignment; see bars artifact.",
    }
    (ev / "PROFIT_V2_BLOCKED_MISSED_CAUSAL.json").write_text(json.dumps(blk, indent=2, sort_keys=True), encoding="utf-8")
    (ev / "PROFIT_V2_BLOCKED_MISSED_CAUSAL.md").write_text(
        "# PROFIT_V2_BLOCKED_MISSED_CAUSAL\n\n"
        f"- Blocked tail rows: **{len(blocked)}**\n"
        "- Ranked reasons (counts):\n\n"
        + "\n".join(f"  - `{k}`: {v}" for k, v in b_reasons.most_common(20))
        + "\n",
        encoding="utf-8",
    )
    print("Wrote uplift + blocked artifacts to", ev, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
