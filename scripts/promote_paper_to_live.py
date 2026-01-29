#!/usr/bin/env python3
"""
Promote PAPER config to LIVE.

- Copy config/paper/* → config/live/*
- Update config/versioning.yaml: live.version = live_v{N+1}, live.commit = current git HEAD.
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
PAPER = CONFIG / "paper"
LIVE = CONFIG / "live"


def _bump_version(version_label: str) -> str:
    """Increment version number: live_v1 -> live_v2."""
    if not version_label or "_" not in version_label:
        return "live_v2"
    prefix, rest = version_label.rsplit("_", 1)
    if rest.startswith("v") and rest[1:].isdigit():
        return f"{prefix}_v{int(rest[1:]) + 1}"
    try:
        return f"{prefix}_{int(rest) + 1}"
    except ValueError:
        return "live_v2"


def main() -> int:
    if not PAPER.exists():
        print("[FAIL] config/paper/ not found", file=sys.stderr)
        return 1

    LIVE.mkdir(parents=True, exist_ok=True)
    for f in PAPER.iterdir():
        if f.is_file():
            dest = LIVE / f.name
            shutil.copy2(f, dest)
            print(f"[OK] {f.name} -> config/live/")

    from config.version_loader import get_version, set_version, current_git_commit

    current = get_version("live")
    new_ver = _bump_version(current.get("version") or "live_v1")
    commit = current_git_commit()
    set_version("live", new_ver, commit)
    print(f"[OK] versioning: live.version={new_ver}, live.commit={commit or 'null'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
