#!/usr/bin/env python3
"""
Build uw_expanded_intel.json from premarket/postmarket intel and uw_flow_cache.
Canonical location: data/uw_expanded_intel.json (config/registry CacheFiles.UW_EXPANDED_INTEL).
Observability-only: does not change trading decisions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def main() -> int:
    base = ROOT
    premarket = _load(base / "state" / "premarket_intel.json")
    postmarket = _load(base / "state" / "postmarket_intel.json")
    cache = _load(base / "data" / "uw_flow_cache.json")

    out: dict = {}
    symbols = set()
    for d in (premarket, postmarket, cache):
        for k in (d or {}).keys():
            if isinstance(k, str) and not k.startswith("_"):
                symbols.add(k)

    for sym in symbols:
        merged: dict = {}
        for src_name, src in [
            ("premarket", premarket),
            ("postmarket", postmarket),
            ("cache", cache),
        ]:
            data = (src or {}).get(sym)
            if isinstance(data, dict):
                merged.update(data)
            elif isinstance(data, str):
                try:
                    merged.update(json.loads(data))
                except Exception:
                    pass
        if merged:
            out[sym] = merged

    out_path = base / "data" / "uw_expanded_intel.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(out_path)
    print(f"Wrote {len(out)} symbols to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
