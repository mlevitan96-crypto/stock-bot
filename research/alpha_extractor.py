"""
Local lab: alpha-oriented feature table prep — log returns and profitability correlation viz.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def compute_log_returns(price: pd.Series) -> pd.Series:
    """Natural log returns: ln(p_t / p_{t-1})."""
    s = pd.to_numeric(price, errors="coerce")
    return np.log(s / s.shift(1))


def run_alpha_extraction(
    df: pd.DataFrame,
    *,
    target_col: str = "is_profitable",
    price_col: str | None = None,
    output_dir: Path | None = None,
    heatmap_filename: str = "alpha_feature_correlation_heatmap.png",
) -> pd.DataFrame:
    """
    Optionally append ``log_return`` from ``price_col``; rank numeric features by absolute
    correlation with ``target_col``; save a correlation heatmap of the top 10 plus the target.
    """
    out = df.copy()
    if price_col:
        if price_col not in out.columns:
            raise ValueError(f"price_col {price_col!r} not in dataframe columns")
        out["log_return"] = compute_log_returns(out[price_col])

    if target_col not in out.columns:
        raise ValueError(f"Missing target column {target_col!r}")

    y = pd.to_numeric(out[target_col], errors="coerce")
    feature_cols: list[str] = []
    for c in out.columns:
        if c == target_col:
            continue
        x = pd.to_numeric(out[c], errors="coerce")
        if (x.notna() & y.notna()).sum() >= 2:
            feature_cols.append(c)
    if not feature_cols:
        raise ValueError("No usable numeric feature columns found")

    corrs: dict[str, float] = {}
    for c in feature_cols:
        x = pd.to_numeric(out[c], errors="coerce")
        valid = x.notna() & y.notna()
        corrs[c] = float(x[valid].corr(y[valid]))

    ranked = sorted(corrs.keys(), key=lambda c: abs(corrs[c]), reverse=True)[:10]
    if not ranked:
        raise ValueError("Could not compute correlations for any feature")

    plot_cols = ranked + [target_col]
    corr_mat = out[plot_cols].apply(pd.to_numeric, errors="coerce").corr()

    out_dir = output_dir or Path("research/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / heatmap_filename

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_mat, annot=True, fmt=".2f", cmap="RdBu_r", center=0, square=True)
    plt.title("Top 10 features vs is_profitable (correlation matrix)")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Alpha lab: log returns + correlation heatmap.")
    parser.add_argument("csv", type=Path, help="Input CSV with numeric features and target")
    parser.add_argument("--target", default="is_profitable", help="Target column (default: is_profitable)")
    parser.add_argument("--price-col", default=None, help="If set, append log_return from this price series")
    parser.add_argument("--out-dir", type=Path, default=Path("research/out"))
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    run_alpha_extraction(
        df,
        target_col=args.target,
        price_col=args.price_col,
        output_dir=args.out_dir,
    )
    print(f"Wrote heatmap under {args.out_dir}")


if __name__ == "__main__":
    main()
