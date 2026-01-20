#!/usr/bin/env python3
"""
Run regime detector and write `state/regime_state.json`.

Additive helper for dashboards/health checks.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from src.intel.regime_detector import write_regime_state
    doc = write_regime_state()
    print("state/regime_state.json")
    return 0 if isinstance(doc, dict) and doc else 1


if __name__ == "__main__":
    raise SystemExit(main())

