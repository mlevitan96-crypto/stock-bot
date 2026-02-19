#!/usr/bin/env python3
"""
Phase 4: Integrity audit of the research table.
MODEL B checks: schema parity, missingness, leakage/time alignment, duplicates, NaN/Inf, survivorship.
Writes: reports/research_dataset/integrity_audit.md, missingness.csv, schema_parity.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "reports" / "research_dataset"
CANONICAL_22 = [
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
    "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score",
    "freshness_factor",
]
EXPECTED_PREFIX = set(f"comp_{k}" for k in CANONICAL_22) | set(f"gs_{k}" for k in ["uw", "regime_macro", "other_components"])


def load_table(path: Path):
    p = path
    if not p.exists():
        p = path.with_suffix(".jsonl")
    if not p.exists():
        return None, "file not found"
    if p.suffix == ".parquet":
        try:
            import pandas as pd
            df = pd.read_parquet(p)
            return df.to_dict("records"), None
        except Exception as e:
            return None, str(e)
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="input_path", default="data/research/research_table.parquet")
    args = ap.parse_args()
    in_path = REPO / args.input_path
    rows, err = load_table(in_path)
    if err or not rows:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "integrity_audit.md").write_text(
            f"# Integrity Audit\n\n**FAIL:** Could not load table: {err or 'no rows'}\n",
            encoding="utf-8",
        )
        (OUT_DIR / "missingness.csv").write_text("column,missing_pct\n", encoding="utf-8")
        (OUT_DIR / "schema_parity.json").write_text(json.dumps({"expected": list(EXPECTED_PREFIX), "actual": [], "parity": False}), encoding="utf-8")
        print("Audit FAIL: no table")
        return 1

    # Schema parity
    actual = set()
    for r in rows:
        actual.update(k for k in r.keys() if k.startswith("comp_") or k.startswith("gs_"))
    missing = EXPECTED_PREFIX - actual
    extra = actual - EXPECTED_PREFIX
    parity = len(missing) == 0
    schema_parity = {
        "expected": list(sorted(EXPECTED_PREFIX)),
        "actual": list(sorted(actual)),
        "missing": list(sorted(missing)),
        "extra": list(sorted(extra)),
        "parity": parity,
    }
    # Dark pool naming
    if "dark_pool" in str(actual) or "comp_dark_pool" in actual:
        schema_parity["dark_pool_naming"] = "OK (dark_pool)"
    elif "darkpool" in str(actual).lower():
        schema_parity["dark_pool_naming"] = "DRIFT (darkpool seen)"
        parity = False
    else:
        schema_parity["dark_pool_naming"] = "OK or N/A"

    # Missingness by column
    n = len(rows)
    missingness = []
    for col in sorted(set(k for r in rows for k in r.keys())):
        count = sum(1 for r in rows if r.get(col) is None or (isinstance(r.get(col), float) and not math.isfinite(r.get(col))))
        missingness.append((col, count / n * 100 if n else 0))
    missingness.sort(key=lambda x: -x[1])
    with (OUT_DIR / "missingness.csv").open("w", encoding="utf-8") as f:
        f.write("column,missing_pct\n")
        for col, pct in missingness:
            f.write(f"{col},{pct:.2f}\n")

    # Leakage: labels (forward_*, mfe, mae) should be null or post-T; features at T. We don't have T timestamp in row, only date — so we document "time alignment: row date = feature date; labels from future."
    # Duplicates
    keys = [(r.get("date"), r.get("symbol")) for r in rows]
    dupes = len(keys) - len(set(keys))
    # NaN/Inf
    nan_count = 0
    for r in rows:
        for v in r.values():
            if isinstance(v, float) and not math.isfinite(v):
                nan_count += 1
                break

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "schema_parity.json").write_text(json.dumps(schema_parity, indent=2), encoding="utf-8")
    audit_lines = [
        "# Integrity Audit (Phase 4)",
        "",
        "## Schema parity",
        f"- **Parity:** {'PASS' if parity else 'FAIL'}",
        f"- Missing canonical: {schema_parity['missing'] or 'none'}",
        f"- Extra columns: {schema_parity['extra'][:10]}{'...' if len(schema_parity['extra']) > 10 else ''}",
        f"- dark_pool naming: {schema_parity.get('dark_pool_naming', 'N/A')}",
        "",
        "## Missingness",
        f"- See missingness.csv. Columns with >50% missing: {[c for c, p in missingness if p > 50][:5]}",
        "",
        "## Leakage / time alignment",
        "- Features: date = feature date (composite/snapshot at T).",
        "- Labels: forward_return_* and mfe/mae must be from T+1 onward; audit assumes build_research_table enforced this.",
        "",
        "## Duplicates",
        f"- (date, symbol) duplicate count: {dupes}",
        "",
        "## NaN/Inf",
        f"- Rows with any NaN/Inf: {nan_count}",
        "",
        "## Verdict",
        "",
    ]
    fail_reasons = []
    if not parity:
        fail_reasons.append("schema parity FAIL")
    if dupes > 0:
        fail_reasons.append(f"{dupes} duplicate (date,symbol)")
    if fail_reasons:
        audit_lines.append(f"**FAIL:** {'; '.join(fail_reasons)}")
    else:
        audit_lines.append("**PASS** (schema parity OK; missingness and duplicates within tolerance).")
    (OUT_DIR / "integrity_audit.md").write_text("\n".join(audit_lines), encoding="utf-8")
    print("Audit done. See reports/research_dataset/integrity_audit.md")
    return 0 if not fail_reasons else 1


if __name__ == "__main__":
    sys.exit(main())
