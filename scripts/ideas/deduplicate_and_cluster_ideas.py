#!/usr/bin/env python3
"""
Deduplicate and cluster raw idea pool. Output feeds multi-persona review.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Deduplicate and cluster ideas")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"Input missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    ideas = data.get("ideas", []) or []
    seen = set()
    deduped = []
    for i in ideas:
        if not isinstance(i, dict):
            continue
        key = (i.get("type"), i.get("symbol"), str(i.get("reason_codes")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(i)

    # Cluster by symbol (stub: one cluster per symbol)
    by_symbol: dict[str, list] = {}
    for i in deduped:
        sym = (i.get("symbol") or "unknown")
        by_symbol.setdefault(sym, []).append(i)
    clusters = [{"symbol": sym, "ideas": arr} for sym, arr in sorted(by_symbol.items())]

    out = {
        "date": data.get("date"),
        "ideas": deduped,
        "clusters": clusters,
        "count": len(deduped),
        "cluster_count": len(clusters),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, "ideas:", len(deduped), "clusters:", len(clusters))
    return 0


if __name__ == "__main__":
    sys.exit(main())
