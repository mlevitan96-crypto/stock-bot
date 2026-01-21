#!/usr/bin/env python3
"""
Premarket Exit Intel (v2, shadow-only)
=====================================

Identifies shadow v2 positions at risk due to:
- earnings proximity
- overnight flow deterioration (best-effort via premarket intel deltas)
- regime shifts (via state/regime_state.json)

Outputs:
- state/premarket_exit_intel.json
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
    pm = _read_json(Path("state/premarket_intel.json"))
    regime = _read_json(Path("state/regime_state.json"))
    r_label = str(regime.get("regime_label", "NEUTRAL") or "NEUTRAL")

    out: Dict[str, Any] = {"_meta": {"ts": _now_iso(), "version": "2026-01-21_exit_premarket_v1", "mock": bool(args.mock)}, "symbols": {}, "regime": {"label": r_label}}

    positions = pos.get("positions") if isinstance(pos, dict) else {}
    pm_sy = pm.get("symbols") if isinstance(pm, dict) else {}
    if isinstance(positions, dict):
        for sym, p in positions.items():
            sym_u = str(sym).upper()
            srec = (pm_sy or {}).get(sym_u) if isinstance(pm_sy, dict) else {}
            earnings_days = srec.get("earnings_proximity") if isinstance(srec, dict) else None
            earnings_risk = False
            try:
                if earnings_days is not None and int(earnings_days) <= 3:
                    earnings_risk = True
            except Exception:
                earnings_risk = False
            # Simple regime risk flag
            risk_off = str(r_label).upper() in ("RISK_OFF", "BEAR")
            out["symbols"][sym_u] = {
                "earnings_risk": bool(earnings_risk),
                "overnight_flow_risk": False,  # placeholder (needs overnight delta feed)
                "regime_risk": bool(risk_off),
                "thesis_invalidated": False,
                "sector_collapse": False,
            }

    Path("state").mkdir(parents=True, exist_ok=True)
    Path("state/premarket_exit_intel.json").write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print("state/premarket_exit_intel.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

