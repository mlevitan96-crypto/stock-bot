#!/usr/bin/env python3
"""
Promote SHADOW config to PAPER.

- Copy config/shadow/* → config/paper/*
- Update config/versioning.yaml: paper.version = paper_v{N+1}, paper.commit = current git HEAD.
- CONFIG-ONLY, reversible. Restart dashboard only after deploy.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

CONFIG = REPO / "config"
SHADOW = CONFIG / "shadow"
PAPER = CONFIG / "paper"


def _bump_version(version_label: str) -> str:
    """Increment version number: paper_v2 -> paper_v3."""
    if not version_label or "_" not in version_label:
        return "paper_v2"
    prefix, rest = version_label.rsplit("_", 1)
    if rest.startswith("v") and rest[1:].isdigit():
        return f"{prefix}_v{int(rest[1:]) + 1}"
    try:
        return f"{prefix}_{int(rest) + 1}"
    except ValueError:
        return "paper_v2"


def main() -> int:
    if not SHADOW.exists():
        print("[FAIL] config/shadow/ not found", file=sys.stderr)
        return 1

    PAPER.mkdir(parents=True, exist_ok=True)
    for f in SHADOW.iterdir():
        if f.is_file():
            dest = PAPER / f.name
            shutil.copy2(f, dest)
            print(f"[OK] {f.name} -> config/paper/")

    from config.version_loader import get_version, set_version, current_git_commit

    current = get_version("paper")
    new_ver = _bump_version(current.get("version") or "paper_v1")
    commit = current_git_commit()
    set_version("paper", new_ver, commit)
    print(f"[OK] versioning: paper.version={new_ver}, paper.commit={commit or 'null'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
