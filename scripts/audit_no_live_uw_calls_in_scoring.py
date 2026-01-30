#!/usr/bin/env python3
"""
Audit: scoring and snapshot paths must NOT call UW directly.
They must consume artifacts only (state/data json).
Fails non-zero if violated.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Modules that form the scoring/snapshot path; must NOT import or call uw_client
SCORING_MODULES = [
    "uw_composite_v2.py",
    "uw_enrichment_v2.py",
    "telemetry/signal_snapshot_writer.py",
]
FORBIDDEN_PATTERNS = [
    r"from\s+src\.uw\.uw_client\s+import",
    r"from\s+uw_client\s+import",
    r"uw_get\s*\(",
    r"uw_http_get\s*\(",
]


def main() -> int:
    violations = []
    for mod in SCORING_MODULES:
        path = REPO / mod
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pat in FORBIDDEN_PATTERNS:
            for m in re.finditer(pat, text):
                violations.append((mod, m.group(0).strip()[:80]))
    if violations:
        for mod, snippet in violations:
            print(f"VIOLATION: {mod} contains UW call: {snippet}", file=sys.stderr)
        print("Scoring must read only from artifacts (uw_flow_cache, premarket_intel, expanded_intel).", file=sys.stderr)
        return 1
    print("OK: scoring path consumes artifacts only; no live UW calls.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
