#!/usr/bin/env python3
"""
Read latest reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md and assert DATA_READY parses.
Writes JSON evidence to stdout or --out-json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Repo root
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from telemetry.alpaca_telegram_integrity.warehouse_summary import (  # noqa: E402
    parse_coverage_markdown,
)


def _latest_coverage_path(reports: Path) -> Path | None:
    """Newest ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md under reports/ (flat or daily/**)."""
    if not reports.is_dir():
        return None
    best: tuple[float, Path] | None = None
    for p in reports.glob("ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md"):
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if best is None or m > best[0]:
            best = (m, p)
    for p in reports.glob("daily/**/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md"):
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if best is None or m > best[0]:
            best = (m, p)
    return best[1] if best else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=_ROOT)
    ap.add_argument("--out-json", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    path = _latest_coverage_path(root / "reports")
    text = ""
    if path and path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_coverage_markdown(text)
    dr = parsed.get("data_ready_yes")
    ok = dr is not None
    out: dict = {
        "coverage_path": str(path) if path else None,
        "data_ready_yes": dr,
        "parse_ok": ok,
        "execution_join_pct": parsed.get("execution_join_pct"),
    }
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
