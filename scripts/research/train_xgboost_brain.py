#!/usr/bin/env python3
"""
Session-horizon XGBoost on Alpha-10 cohort: binary label (+1.3% TP before -0.65% SL).

Uses only feature columns mapped to FLOW, DARK, SENT, and GEX buckets
(see ``massive_alpha_review.ALPHA10_GROUPS``). Missing values imputed to 0.0 for trees.

Usage (repo root):
  PYTHONPATH=. python scripts/research/train_xgboost_brain.py \\
    --in-jsonl reports/research/alpha10_labeled_cohort.jsonl \\
    --out-model models/live_whale_v1.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _load_mar():
    spec = importlib.util.spec_from_file_location(
        "massive_alpha_review",
        _ROOT / "scripts" / "research" / "massive_alpha_review.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _load_rows(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _feature_columns_for_buckets(mar: Any, all_keys: List[str], want: Set[str]) -> List[str]:
    name_to_idx = {mar.ALPHA10_GROUPS[i][0]: i for i in range(len(mar.ALPHA10_GROUPS))}
    idxs = {name_to_idx[n] for n in want}
    out = [k for k in all_keys if mar._assign_group(k) in idxs]
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-jsonl", type=Path, default=_ROOT / "reports" / "research" / "alpha10_labeled_cohort.jsonl")
    ap.add_argument("--out-model", type=Path, default=_ROOT / "models" / "live_whale_v1.json")
    args = ap.parse_args()
    path = args.in_jsonl.resolve()
    if not path.is_file():
        print(f"Missing input: {path}", file=sys.stderr)
        return 2

    try:
        import xgboost as xgb  # type: ignore
    except ImportError:
        print("Install xgboost: pip install xgboost", file=sys.stderr)
        return 2

    mar = _load_mar()
    rows = _load_rows(path)
    if len(rows) < 20:
        print("Too few rows to train.", file=sys.stderr)
        return 2

    keys_set: set[str] = set()
    for r in rows:
        fe = r.get("features")
        if isinstance(fe, dict):
            keys_set.update(str(k) for k in fe.keys())
    all_keys = sorted(keys_set)
    want = {"FLOW", "DARK", "SENT", "GEX"}
    feat_cols = _feature_columns_for_buckets(mar, all_keys, want)
    if not feat_cols:
        print("No FLOW/DARK/SENT/GEX columns found in cohort.", file=sys.stderr)
        return 2

    X = np.zeros((len(rows), len(feat_cols)), dtype=float)
    y = np.zeros(len(rows), dtype=np.int32)
    for i, r in enumerate(rows):
        y[i] = int(r.get("label", 0))
        fe = r.get("features") if isinstance(r.get("features"), dict) else {}
        for j, k in enumerate(feat_cols):
            v = fe.get(k)
            if v is None:
                continue
            try:
                fv = float(v)
                if math.isfinite(fv):
                    X[i, j] = fv
            except (TypeError, ValueError):
                continue

    clf = xgb.XGBClassifier(
        max_depth=3,
        n_estimators=50,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=42,
        eval_metric="logloss",
        n_jobs=0,
    )
    try:
        import pandas as pd

        clf.fit(pd.DataFrame(X, columns=feat_cols), y)
    except ImportError:
        clf.fit(X, y)
        try:
            clf.get_booster().feature_names = list(feat_cols)
        except Exception:
            pass

    args.out_model.parent.mkdir(parents=True, exist_ok=True)
    # Native JSON (portable for embedding / xgb.load_model in services).
    clf.get_booster().save_model(str(args.out_model))

    # Brief fit summary to stdout (SRE visibility).
    try:
        proba = clf.predict_proba(X)[:, 1]
        acc = float(np.mean((proba >= 0.5).astype(int) == y))
        print(f"features_used={len(feat_cols)} rows={len(rows)} train_acc_threshold05={acc:.4f}")
        print("columns:", ",".join(feat_cols))
    except Exception:
        pass
    print(f"Wrote {args.out_model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
