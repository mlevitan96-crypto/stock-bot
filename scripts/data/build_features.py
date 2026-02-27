#!/usr/bin/env python3
"""Stub: build features. Campaign uses on-the-fly features from composite/enrichment when needed."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    print("build_features: stub — proceeding with on-the-fly features")
    return 0


if __name__ == "__main__":
    sys.exit(main())
