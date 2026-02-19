#!/usr/bin/env python3
"""
Conditional expectancy analysis: compute expectancy by signal × slice from replay_results.
Reads reports/blocked_signal_expectancy/replay_results.jsonl; writes reports/signal_strength/conditional_expectancy.md.
Run from repo root. Run after blocked_signal_expectancy_pipeline.py.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REPLAY_PATH = REPO / "reports" / "blocked_signal_expectancy" / "replay_results.jsonl"
OUT_DIR = REPO / "reports" / "signal_strength"
SIGNAL_GROUPS = ("uw", "regime_macro", "other_components")
COMPONENT_SIGNALS = ("flow", "dark_pool", "market_tide", "calendar", "regime", "whale", "event")


def _tertile_bounds(vals):
    """Return (low_cut, high_cut) so that low <= low_cut, mid, high >= high_cut."""
    if not vals:
        return None, None
    s = sorted(vals)
    n = len(s)
    t = max(1, n // 3)
    low_cut = s[t - 1]
    high_cut = s[-t] if n >= 2 * t else s[t - 1]
    return low_cut, high_cut


def _median(vals):
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[len(s) // 2]


def load_replay() -> list[dict]:
    out = []
    if not REPLAY_PATH.exists():
        return out
    for line in REPLAY_PATH.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def add_slices(replay: list[dict]) -> None:
    """Add slice labels to each record (mutates in place)."""
    gs_uw = [(r.get("group_sums") or {}).get("uw", 0) for r in replay if isinstance(r.get("group_sums"), dict)]
    gs_reg = [(r.get("group_sums") or {}).get("regime_macro", 0) for r in replay if isinstance(r.get("group_sums"), dict)]
    gs_oth = [(r.get("group_sums") or {}).get("other_components", 0) for r in replay if isinstance(r.get("group_sums"), dict)]
    flow_vals = []
    dp_vals = []
    tide_vals = []
    cal_vals = []
    for r in replay:
        comp = r.get("components") or {}
        flow_vals.append(comp.get("flow") if isinstance(comp.get("flow"), (int, float)) else 0)
        dp_vals.append(comp.get("dark_pool") if isinstance(comp.get("dark_pool"), (int, float)) else 0)
        tide_vals.append(comp.get("market_tide") if isinstance(comp.get("market_tide"), (int, float)) else 0)
        cal_vals.append(comp.get("calendar") if isinstance(comp.get("calendar"), (int, float)) else 0)

    tuw = _tertile_bounds(gs_uw) if gs_uw else (None, None)
    treg = _tertile_bounds(gs_reg) if gs_reg else (None, None)
    toth = _tertile_bounds(gs_oth) if gs_oth else (None, None)
    flow_med = _median(flow_vals) if flow_vals else 0
    dp_med = _median(dp_vals) if dp_vals else 0
    tide_med = _median(tide_vals) if tide_vals else 0
    cal_med = _median(cal_vals) if cal_vals else 0

    for r in replay:
        gs = r.get("group_sums") or {}
        comp = r.get("components") or {}
        uw = gs.get("uw") if isinstance(gs.get("uw"), (int, float)) else 0
        reg = gs.get("regime_macro") if isinstance(gs.get("regime_macro"), (int, float)) else 0
        oth = gs.get("other_components") if isinstance(gs.get("other_components"), (int, float)) else 0
        flow = comp.get("flow") if isinstance(comp.get("flow"), (int, float)) else 0
        dp = comp.get("dark_pool") if isinstance(comp.get("dark_pool"), (int, float)) else 0
        tide = comp.get("market_tide") if isinstance(comp.get("market_tide"), (int, float)) else 0
        cal = comp.get("calendar") if isinstance(comp.get("calendar"), (int, float)) else 0

        r["slice_uw"] = "low" if tuw[0] is not None and uw <= tuw[0] else ("high" if tuw[1] is not None and uw >= tuw[1] else "mid")
        r["slice_regime_macro"] = "low" if treg[0] is not None and reg <= treg[0] else ("high" if treg[1] is not None and reg >= treg[1] else "mid")
        r["slice_other"] = "low" if toth[0] is not None and oth <= toth[0] else ("high" if toth[1] is not None and oth >= toth[1] else "mid")
        r["slice_flow"] = "present" if flow > flow_med else "absent"
        r["slice_dark_pool"] = "present" if dp > 0 else "absent"
        r["slice_market_tide"] = "high" if tide >= tide_med and tide_med is not None else "low"
        r["slice_calendar"] = "on" if cal >= cal_med and cal_med is not None else "off"
        r["bucket"] = r.get("bucket") or "unknown"


def run():
    replay = load_replay()
    if not replay:
        lines = [
            "# Conditional Expectancy (Phase 2)",
            "",
            "No replay data. Run `blocked_signal_expectancy_pipeline.py` first (and ensure score_snapshot.jsonl / blocked_trades.jsonl have attribution).",
            "",
        ]
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "conditional_expectancy.md").write_text("\n".join(lines), encoding="utf-8")
        print("conditional_expectancy.md written (no data).")
        return 0

    add_slices(replay)

    # Expectancy by slice (overall)
    slice_dims = ["bucket", "slice_uw", "slice_regime_macro", "slice_other", "slice_flow", "slice_dark_pool", "slice_market_tide", "slice_calendar"]
    by_slice = defaultdict(lambda: {"pnl": [], "n": 0})
    for r in replay:
        for dim in slice_dims:
            val = r.get(dim) or "unknown"
            key = f"{dim}={val}"
            by_slice[key]["pnl"].append(r.get("pnl_pct", 0))
            by_slice[key]["n"] += 1

    lines = [
        "# Conditional Expectancy (Phase 2)",
        "",
        "## Expectancy by slice (overall mean_pnl, n, win_rate)",
        "",
        "| slice | n | mean_pnl_pct | win_rate |",
        "|-------|---|--------------|----------|",
    ]
    for key in sorted(by_slice.keys()):
        pnls = by_slice[key]["pnl"]
        n = len(pnls)
        if n == 0:
            continue
        mean_pnl = sum(pnls) / n
        win_rate = sum(1 for p in pnls if p > 0) / n * 100
        lines.append(f"| {key} | {n} | {mean_pnl:.3f} | {win_rate:.1f}% |")

    # Signal × condition: for each signal (group or component), for each slice level, mean_pnl and n
    lines.extend([
        "",
        "## Signal × condition (mean_pnl_pct, n) — positive expectancy highlighted",
        "",
    ])

    for sig in list(SIGNAL_GROUPS) + list(COMPONENT_SIGNALS):
        if sig in SIGNAL_GROUPS:
            vals = [(r, (r.get("group_sums") or {}).get(sig, 0)) for r in replay]
        else:
            vals = [(r, (r.get("components") or {}).get(sig, 0)) for r in replay]
        vals = [(r, v) for r, v in vals if isinstance(v, (int, float))]
        if not vals:
            continue
        # Tertile or present/absent for this signal
        vlist = [v for _, v in vals]
        tlo, thi = _tertile_bounds(vlist)
        med = _median(vlist)
        cond_pnls = defaultdict(list)
        for r, v in vals:
            if sig in ("flow", "dark_pool"):
                cond = "present" if v > 0 else "absent"
            else:
                cond = "low" if tlo is not None and v <= tlo else ("high" if thi is not None and v >= thi else "mid")
            cond_pnls[cond].append(r.get("pnl_pct", 0))
        line_parts = [f"**{sig}**"]
        for cond in ("absent", "low", "mid", "high", "present", "on", "off"):
            pnls = cond_pnls.get(cond, [])
            if not pnls:
                continue
            mean_p = sum(pnls) / len(pnls)
            line_parts.append(f"{cond}=({mean_p:.3f}, n={len(pnls)})")
        if len(line_parts) > 1:
            lines.append("- " + " ".join(line_parts))

    # Cross: slice_uw × slice_regime_macro
    cross = defaultdict(list)
    for r in replay:
        k = f"uw={r.get('slice_uw')}, regime_macro={r.get('slice_regime_macro')}"
        cross[k].append(r.get("pnl_pct", 0))
    lines.extend([
        "",
        "## Interaction: uw × regime_macro",
        "",
        "| slice | n | mean_pnl_pct | win_rate |",
        "|-------|---|--------------|----------|",
    ])
    for k in sorted(cross.keys()):
        pnls = cross[k]
        n = len(pnls)
        mean_pnl = sum(pnls) / n
        wr = sum(1 for p in pnls if p > 0) / n * 100
        lines.append(f"| {k} | {n} | {mean_pnl:.3f} | {wr:.1f}% |")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "conditional_expectancy.md").write_text("\n".join(lines), encoding="utf-8")
    print("conditional_expectancy.md written.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
