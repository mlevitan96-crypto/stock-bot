#!/usr/bin/env python3
"""
Postmarket Exit Intel (v2, shadow-only)
======================================

Best-effort postmarket risk flags for shadow v2 positions.

Outputs:
- state/postmarket_exit_intel.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    pos = _read_json(Path("state/shadow_v2_positions.json"))
    post = _read_json(Path("state/postmarket_intel.json"))
    regime = _read_json(Path("state/regime_state.json"))
    r_label = str(regime.get("regime_label", "NEUTRAL") or "NEUTRAL")

    out: Dict[str, Any] = {"_meta": {"ts": _now_iso(), "version": "2026-01-21_exit_postmarket_v1", "mode": ("mock" if bool(args.mock) else "real")}, "symbols": {}, "regime": {"label": r_label}}

    positions = pos.get("positions") if isinstance(pos, dict) else {}
    post_sy = post.get("symbols") if isinstance(post, dict) else {}
    if isinstance(positions, dict):
        for sym, p in positions.items():
            sym_u = str(sym).upper()
            srec = (post_sy or {}).get(sym_u) if isinstance(post_sy, dict) else {}
            # Heuristic: if sentiment flips to neutral, set thesis_invalidated flag (best-effort)
            thesis_invalidated = False
            try:
                sent = str((srec or {}).get("sentiment", "NEUTRAL") or "NEUTRAL").upper()
                if sent == "NEUTRAL":
                    thesis_invalidated = True
            except Exception:
                thesis_invalidated = False
            out["symbols"][sym_u] = {
                "earnings_risk": False,
                "overnight_flow_risk": False,
                "regime_risk": bool(str(r_label).upper() in ("RISK_OFF", "BEAR")),
                "thesis_invalidated": bool(thesis_invalidated),
                "sector_collapse": False,
            }

    Path("state").mkdir(parents=True, exist_ok=True)
    Path("state/postmarket_exit_intel.json").write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print("state/postmarket_exit_intel.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

