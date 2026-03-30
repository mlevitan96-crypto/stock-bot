#!/usr/bin/env python3
"""
Post-era-cut signal firing test: compute scores only (no orders, no broker side effects beyond read).

Usage (repo root): python3 scripts/audit/alpaca_post_cut_signal_firing_test.py [--out-md PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")


def _et_date() -> str:
    import subprocess

    try:
        r = subprocess.run(
            ["bash", "-lc", "TZ=America/New_York date +%Y-%m-%d"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _top_components(composite: Dict[str, Any], n: int = 3) -> List[Tuple[str, float]]:
    comps = composite.get("components") if isinstance(composite.get("components"), dict) else {}
    if not comps:
        return []
    ranked = sorted(
        ((str(k), float(v)) for k, v in comps.items() if isinstance(v, (int, float))),
        key=lambda x: -abs(x[1]),
    )
    return ranked[:n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=str, default="SPY,QQQ,AAPL,MSFT,NVDA,JPM,XLE,GOOGL,META")
    ap.add_argument("--out-md", type=str, default="")
    args = ap.parse_args()
    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    from config.registry import CacheFiles, read_json, StateFiles

    uw_cache = read_json(REPO / CacheFiles.UW_FLOW_CACHE, default={})
    if not isinstance(uw_cache, dict):
        uw_cache = {}

    current_regime = "mixed"
    for regime_file in [getattr(StateFiles, "REGIME_DETECTOR_STATE", None), StateFiles.REGIME_DETECTOR]:
        if not regime_file:
            continue
        rp = REPO / regime_file
        if rp.exists():
            try:
                data = json.loads(rp.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    current_regime = data.get("current_regime") or data.get("regime") or "mixed"
                    break
            except Exception:
                pass

    import uw_composite_v2 as uw_v2  # type: ignore

    try:
        import uw_enrichment_v2 as uw_enrich  # type: ignore
    except ImportError:
        uw_enrich = None  # type: ignore

    rows: List[Dict[str, Any]] = []
    for symbol in syms:
        flags: List[str] = []
        raw = uw_cache.get(symbol)
        if not raw:
            flags.append("missing_uw_cache_symbol")
            rows.append(
                {
                    "symbol": symbol,
                    "final_score": None,
                    "top_signals": [],
                    "flags": flags,
                }
            )
            continue
        enriched = raw
        if uw_enrich:
            try:
                enriched = uw_enrich.enrich_signal(symbol, uw_cache, current_regime) or raw
            except Exception as e:
                flags.append(f"enrich_error:{type(e).__name__}")
        try:
            composite = uw_v2.compute_composite_score_v2(symbol, enriched, current_regime)
        except Exception as e:
            rows.append(
                {
                    "symbol": symbol,
                    "final_score": None,
                    "top_signals": [],
                    "flags": flags + [f"compute_error:{type(e).__name__}"],
                }
            )
            continue
        if not composite:
            flags.append("empty_composite")
            score = None
        else:
            score = composite.get("score")
            try:
                score_f = float(score) if score is not None else None
                if score_f is not None and score_f != score_f:
                    flags.append("nan_score")
            except (TypeError, ValueError):
                flags.append("non_numeric_score")
        top = _top_components(composite or {}, 3)
        rows.append(
            {
                "symbol": symbol,
                "final_score": score,
                "top_signals": [f"{a}={b:.4f}" for a, b in top],
                "flags": flags,
            }
        )

    et = _et_date()
    ev = REPO / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out_md) if args.out_md else ev / "ALPACA_POST_CUT_SIGNAL_FIRING_TEST.md"

    lines: List[str] = []
    lines.append("# ALPACA POST-CUT SIGNAL FIRING TEST\n\n")
    lines.append(f"- UTC: `{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}`\n")
    lines.append(f"- Regime used: `{current_regime}`\n")
    lines.append("- **Mode:** scoring only — **no orders**.\n\n")
    lines.append("| symbol | final_score | top_3_components | flags |\n")
    lines.append("| --- | --- | --- | --- |\n")
    any_hard_fail = False
    for r in rows:
        fs = r.get("final_score")
        fs_s = "" if fs is None else f"{float(fs):.4f}"
        top = ", ".join(r.get("top_signals") or [])
        fl = ", ".join(r.get("flags") or []) or "—"
        if r.get("final_score") is None or (r.get("flags") and "missing_uw_cache" in str(r.get("flags"))):
            any_hard_fail = any_hard_fail or bool(r.get("flags"))
        lines.append(f"| {r.get('symbol')} | {fs_s} | {top} | {fl} |\n")

    lines.append("\n## JSON\n\n```json\n")
    lines.append(json.dumps(rows, indent=2))
    lines.append("\n```\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(json.dumps({"written": str(out_path), "rows": len(rows)}, indent=2))
    bad = [r.get("symbol") for r in rows if r.get("final_score") is None]
    return 0 if not bad else 2


if __name__ == "__main__":
    raise SystemExit(main())
