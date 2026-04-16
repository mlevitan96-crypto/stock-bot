#!/usr/bin/env bash
# N=10 downstream stress: rebuild flat cohort, inject ml_expected_eod_return into a temp CSV,
# run Alpha Arena trainer + decile analysis (read-only analytics on the augmented schema).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"

echo "[n10] flattener -> reports/Gemini/alpaca_ml_cohort_flat.csv"
"$PY" scripts/telemetry/alpaca_ml_flattener.py --root "$ROOT"

SRC_IX="${ROOT}/reports/Gemini/alpaca_ml_cohort_flat_UW_IX.csv"
STRESS="${ROOT}/reports/Gemini/_n10_stress_ml_col.csv"
if [[ ! -f "$SRC_IX" ]]; then
  echo "ERROR: missing ${SRC_IX} (generate UW cohort + interaction expand on the droplet or locally)." >&2
  exit 1
fi

echo "[n10] inject ml_expected_eod_return -> ${STRESS}"
export N10_ROOT="$ROOT"
"$PY" - <<'PY'
import csv
import os
import sys
from pathlib import Path

root = Path(os.environ["N10_ROOT"]).resolve()
src = root / "reports" / "Gemini" / "alpaca_ml_cohort_flat_UW_IX.csv"
dst = root / "reports" / "Gemini" / "_n10_stress_ml_col.csv"
if not src.is_file():
    sys.exit("missing UW_IX")
with src.open(newline="", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f)
    rows = list(r)
    fields = list(r.fieldnames or [])
if "ml_expected_eod_return" not in fields:
    fields.append("ml_expected_eod_return")
dst.parent.mkdir(parents=True, exist_ok=True)
with dst.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for row in rows:
        if "ml_expected_eod_return" not in row or not str(row.get("ml_expected_eod_return", "")).strip():
            row["ml_expected_eod_return"] = "0.0"
        w.writerow({k: row.get(k, "") for k in fields})
print("wrote", dst, "rows", len(rows))
PY

echo "[n10] alpha_arena_trainer (CV smoke on augmented CSV)"
"$PY" scripts/research/alpha_arena_trainer.py \
  --csv "$STRESS" \
  --target-col target_ret_eod_rth \
  --cv 2

echo "[n10] alpaca_decile_pnl_analysis on augmented CSV"
"$PY" scripts/analysis/alpaca_decile_pnl_analysis.py --root "$ROOT" --csv "$STRESS"

echo "[n10] OK — downstream scripts completed without crash."
