#!/usr/bin/env python3
"""Stub: build canonical dataset. Campaign proceeds with raw data if this is missing or no-op."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    # No-op: campaign uses logs/attribution, logs/exit_attribution, data/bars when available
    print("build_canonical_dataset: stub — proceeding with raw data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
