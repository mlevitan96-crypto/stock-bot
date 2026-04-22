#!/usr/bin/env python3
"""
Retro-heal trade intent telemetry: lift gut_confluence_score and shadow_fractal_vapor to top level.

- Heals ``logs/trade_intents.log`` if it exists (JSONL-style one JSON object per line).
- Always heals ``logs/run.jsonl`` rows where ``event_type == \"trade_intent\"``.

Atomic replace via temp file + os.replace. Creates ``*.bak.retroheal`` backup first.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(os.environ.get("STOCK_BOT_ROOT", "/root/stock-bot")).resolve()
LOGS = ROOT / "logs"
TI = LOGS / "trade_intents.log"
RUN = LOGS / "run.jsonl"


def _find_gut(obj: Any, depth: int) -> Optional[float]:
    import math

    if depth < 0 or not isinstance(obj, dict):
        return None
    for k in ("_gut_confluence_score", "gut_confluence_score"):
        if k in obj and obj[k] is not None:
            try:
                v = float(obj[k])
                if math.isfinite(v):
                    return v
            except (TypeError, ValueError):
                pass
    for v in obj.values():
        if isinstance(v, dict):
            r = _find_gut(v, depth - 1)
            if r is not None:
                return r
        if isinstance(v, list):
            for it in v[:50]:
                if isinstance(it, dict):
                    r = _find_gut(it, depth - 1)
                    if r is not None:
                        return r
    return None


def _find_fractal(obj: Any, depth: int) -> Optional[dict]:
    if depth < 0 or not isinstance(obj, dict):
        return None
    for k in ("_shadow_fractal_vapor", "shadow_fractal_vapor"):
        if k in obj and isinstance(obj[k], dict) and obj[k]:
            return obj[k]
    for v in obj.values():
        if isinstance(v, dict):
            r = _find_fractal(v, depth - 1)
            if r is not None:
                return r
        if isinstance(v, list):
            for it in v[:50]:
                if isinstance(it, dict):
                    r = _find_fractal(it, depth - 1)
                    if r is not None:
                        return r
    return None


def _lift_record(rec: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Return (changed, healed_rec)."""
    roots = []
    for key in ("cluster", "metadata", "feature_snapshot", "displacement_context", "intelligence_trace"):
        v = rec.get(key)
        if isinstance(v, dict):
            roots.append(v)
    gut = rec.get("gut_confluence_score")
    frac = rec.get("shadow_fractal_vapor")
    changed = False
    if gut is None:
        gv = None
        for r in roots:
            gv = _find_gut(r, 7)
            if gv is not None:
                break
        if gv is None:
            gv = _find_gut(rec, 10)
        if gv is not None:
            rec["gut_confluence_score"] = float(gv)
            changed = True
    if frac is None:
        fv = None
        for r in roots:
            fv = _find_fractal(r, 7)
            if fv is not None:
                break
        if fv is None:
            fv = _find_fractal(rec, 10)
        if isinstance(fv, dict):
            rec["shadow_fractal_vapor"] = fv
            changed = True
    return changed, rec


def _heal_jsonl_file(src: Path) -> dict:
    stats = {"path": str(src), "lines_in": 0, "lines_out": 0, "trade_intent_rows": 0, "rows_changed": 0, "errors": 0}
    if not src.is_file():
        stats["skipped"] = "missing"
        return stats
    bak = src.with_suffix(src.suffix + ".bak.retroheal")
    tmp = src.with_suffix(src.suffix + ".retroheal.tmp")
    shutil.copy2(src, bak)
    with src.open(encoding="utf-8", errors="replace") as fin, tmp.open("w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            stats["lines_in"] += 1
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                stats["errors"] += 1
                fout.write(line + "\n")
                stats["lines_out"] += 1
                continue
            if d.get("event_type") == "trade_intent":
                stats["trade_intent_rows"] += 1
                ch, d2 = _lift_record(d)
                if ch:
                    stats["rows_changed"] += 1
                fout.write(json.dumps(d2, separators=(",", ":"), default=str) + "\n")
            else:
                fout.write(json.dumps(d, separators=(",", ":"), default=str) + "\n")
            stats["lines_out"] += 1
    os.replace(tmp, src)
    stats["replaced"] = True
    stats["backup"] = str(bak)
    return stats


def main() -> int:
    out = {"root": str(ROOT), "files": []}
    if TI.exists():
        out["files"].append(_heal_jsonl_file(TI))
    else:
        out["files"].append({"path": str(TI), "skipped": "trade_intents_log_missing"})
    out["files"].append(_heal_jsonl_file(RUN))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
