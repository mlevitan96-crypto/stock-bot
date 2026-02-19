#!/usr/bin/env python3
"""
Phase 5: Baseline edge tests — univariate deciles, conditional deciles by regime, walk-forward OOS.
Writes: reports/research_dataset/baseline_results.md, conditional_edge_results.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "reports" / "research_dataset"
SIGNAL_COLS = [f"gs_{g}" for g in ("uw", "regime_macro", "other_components")] + [f"comp_{c}" for c in ("flow", "dark_pool", "market_tide", "regime")]
LABEL_COLS = ["forward_return_5d", "forward_return_10d", "forward_return_20d"]


def load_table(path: Path):
    p = path
    if not p.exists():
        p = path.with_suffix(".jsonl")
    if not p.exists():
        return None
    if p.suffix == ".parquet":
        try:
            import pandas as pd
            return pd.read_parquet(p).to_dict("records")
        except Exception:
            return None
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _decile_rank(val, sorted_vals):
    if not sorted_vals or val is None or (isinstance(val, float) and not math.isfinite(val)):
        return None
    n = len(sorted_vals)
    for i, v in enumerate(sorted_vals):
        if val <= v:
            return max(1, min(10, int(10 * (i + 1) / n)))
    return 10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="input_path", default="data/research/research_table.parquet")
    args = ap.parse_args()
    in_path = REPO / args.input_path
    rows = load_table(in_path)
    if not rows:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "baseline_results.md").write_text("# Baseline Results\n\nNo table.\n", encoding="utf-8")
        (OUT_DIR / "conditional_edge_results.md").write_text("# Conditional Edge Results\n\nNo table.\n", encoding="utf-8")
        print("No table; baseline reports written (empty).")
        return 0

    # Find label col present
    sample = rows[0]
    label_col = None
    for L in LABEL_COLS:
        if L in sample and sample.get(L) is not None:
            try:
                float(sample[L])
                label_col = L
                break
            except (TypeError, ValueError):
                pass
    if not label_col:
        label_col = "forward_return_5d"  # use for decile even if null
    # Univariate deciles vs label
    decile_lift = {}
    for sig in SIGNAL_COLS:
        if sig not in sample:
            continue
        vals = []
        for r in rows:
            v = r.get(sig)
            if v is not None and isinstance(v, (int, float)) and math.isfinite(v):
                vals.append((v, r.get(label_col)))
        if not vals:
            continue
        sorted_sig = sorted(v for v, _ in vals)
        by_dec = defaultdict(list)
        for v, lab in vals:
            d = _decile_rank(v, sorted_sig)
            if d is not None and lab is not None and isinstance(lab, (int, float)) and math.isfinite(lab):
                by_dec[d].append(lab)
        if not by_dec:
            continue
        dec_means = {d: sum(by_dec[d]) / len(by_dec[d]) for d in by_dec if by_dec[d]}
        if len(dec_means) >= 2:
            low_d = min(dec_means.keys())
            high_d = max(dec_means.keys())
            lift = dec_means.get(high_d, 0) - dec_means.get(low_d, 0)
            decile_lift[sig] = {"lift": lift, "decile_means": dec_means, "n": len(vals)}

    # Time-split OOS: last 20% of dates = OOS
    dates = sorted(set(r.get("date") for r in rows if r.get("date")))
    if len(dates) >= 5:
        cut = int(len(dates) * 0.8)
        oos_dates = set(dates[cut:])
        oos_rows = [r for r in rows if r.get("date") in oos_dates]
        oos_lift = {}
        for sig in SIGNAL_COLS:
            if sig not in sample:
                continue
            vals = [(r.get(sig), r.get(label_col)) for r in oos_rows]
            vals = [(v, l) for v, l in vals if v is not None and l is not None and isinstance(v, (int, float)) and isinstance(l, (int, float)) and math.isfinite(v) and math.isfinite(l)]
            if len(vals) < 10:
                continue
            sorted_sig = sorted(v for v, _ in vals)
            by_dec = defaultdict(list)
            for v, lab in vals:
                d = _decile_rank(v, sorted_sig)
                if d is not None:
                    by_dec[d].append(lab)
            dec_means = {d: sum(by_dec[d]) / len(by_dec[d]) for d in by_dec if by_dec[d]}
            if dec_means:
                lift = dec_means.get(max(dec_means.keys()), 0) - dec_means.get(min(dec_means.keys()), 0)
                oos_lift[sig] = lift
    else:
        oos_lift = {}

    # Baseline report
    bl_lines = [
        "# Baseline Results (Phase 5)",
        "",
        f"- **Label:** {label_col}",
        f"- **Rows:** {len(rows)}",
        "",
        "## Univariate decile lift (in-sample)",
        "",
        "| signal | lift (high_dec - low_dec) |",
        "|--------|---------------------------|",
    ]
    for sig in sorted(decile_lift.keys(), key=lambda s: -abs(decile_lift[s].get("lift", 0))):
        bl_lines.append(f"| {sig} | {decile_lift[sig]['lift']:.4f} |")
    bl_lines.extend(["", "## Walk-forward OOS (last 20% dates)", ""])
    if oos_lift:
        for sig in sorted(oos_lift.keys(), key=lambda s: -abs(oos_lift[s])):
            bl_lines.append(f"- **{sig}** OOS lift: {oos_lift[sig]:.4f}")
    else:
        bl_lines.append("- Insufficient dates for OOS split or no valid labels.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "baseline_results.md").write_text("\n".join(bl_lines), encoding="utf-8")

    # Conditional: by regime (spy_1w or vol proxy if present)
    reg_col = None
    for c in ("spy_1w_ret", "vol_regime_proxy"):
        if c in sample and any(r.get(c) is not None for r in rows):
            reg_col = c
            break
    cond_lines = [
        "# Conditional Edge Results (Phase 5)",
        "",
        "## By regime (conditional deciles)",
        "",
    ]
    if reg_col:
        # Split up/down or high/low
        reg_vals = [r.get(reg_col) for r in rows if r.get(reg_col) is not None and isinstance(r.get(reg_col), (int, float))]
        if reg_vals:
            med = sorted(reg_vals)[len(reg_vals) // 2]
            up_rows = [r for r in rows if (r.get(reg_col) or 0) >= med]
            down_rows = [r for r in rows if (r.get(reg_col) or 0) < med]
            for regime_name, sub in [("regime_up", up_rows), ("regime_down", down_rows)]:
                cond_lines.append(f"### {regime_name} (n={len(sub)})")
                for sig in SIGNAL_COLS[:6]:
                    if sig not in sample:
                        continue
                    vals = [(r.get(sig), r.get(label_col)) for r in sub]
                    vals = [(v, l) for v, l in vals if v is not None and l is not None and isinstance(v, (int, float)) and isinstance(l, (int, float))]
                    if len(vals) < 5:
                        continue
                    sorted_sig = sorted(v for v, _ in vals)
                    by_dec = defaultdict(list)
                    for v, lab in vals:
                        d = _decile_rank(v, sorted_sig)
                        if d is not None:
                            by_dec[d].append(lab)
                    if by_dec:
                        dec_means = {d: sum(by_dec[d]) / len(by_dec[d]) for d in by_dec}
                        lift = dec_means.get(max(dec_means.keys()), 0) - dec_means.get(min(dec_means.keys()), 0)
                        cond_lines.append(f"- {sig} lift: {lift:.4f}")
                cond_lines.append("")
    else:
        cond_lines.append("No regime column with data; skip conditional by regime.")
    (OUT_DIR / "conditional_edge_results.md").write_text("\n".join(cond_lines), encoding="utf-8")
    print("Baseline and conditional results written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
