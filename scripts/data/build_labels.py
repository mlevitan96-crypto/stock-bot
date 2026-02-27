#!/usr/bin/env python3
"""Stub: build labels. Campaign uses implicit labels (PnL from attribution) for profitability."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    print("build_labels: stub — proceeding with implicit labels (PnL)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
