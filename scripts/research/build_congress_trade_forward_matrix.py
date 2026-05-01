#!/usr/bin/env python3
"""
Build filing-date–anchored congressional trade forward-return matrix.

Requires:
- ``UNUSUAL_WHALES_API_KEY`` (via ``APIConfig`` / env; same as rest of repo)
- ``ALPACA_KEY`` + ``ALPACA_SECRET`` (or ``ALPACA_API_KEY`` / ``ALPACA_SECRET_KEY``)
- ``pip install pyarrow`` for Parquet output

Example::

    python scripts/research/build_congress_trade_forward_matrix.py \\
        --days-back 120 --out data/research/congress_filing_forward_matrix.parquet
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.research.congress_trade_forward_matrix import (  # noqa: E402
    build_matrix_dataframe,
    collect_congress_trades_date_walk,
    load_dotenv_research_then_default,
    print_summary_report,
)


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(REPO), stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return ""


def main() -> int:
    load_dotenv_research_then_default(str(REPO))

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days-back", type=int, default=180, help="Calendar days to walk for UW congress date param")
    ap.add_argument("--end-date", type=str, default="", help="YYYY-MM-DD end of window (default: today UTC)")
    ap.add_argument("--out", type=str, default=str(REPO / "data" / "research" / "congress_filing_forward_matrix.parquet"))
    ap.add_argument("--manifest", type=str, default="", help="Optional JSON sidecar path (default: next to --out)")
    args = ap.parse_args()

    if args.end_date.strip():
        end = date.fromisoformat(args.end_date.strip()[:10])
    else:
        end = datetime.now(timezone.utc).date()

    try:
        import pyarrow  # noqa: F401
    except ImportError:
        print("Missing dependency: pyarrow (required for Parquet). Install with: pip install pyarrow", file=sys.stderr)
        return 1

    from src.uw.uw_client import uw_get

    trades = collect_congress_trades_date_walk(end=end, days_back=int(args.days_back), uw_get_fn=uw_get)
    df, meta = build_matrix_dataframe(trades, uw_get)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)

    manifest_path = Path(args.manifest) if str(args.manifest).strip() else out.with_suffix(".manifest.json")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "end_date": end.isoformat(),
        "days_back": int(args.days_back),
        "parquet": str(out.resolve()),
        "row_count": int(len(df)),
        "meta": meta,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print_summary_report(df, meta)
    print(f"\nWrote: {out.resolve()}")
    print(f"Manifest: {manifest_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
