#!/usr/bin/env python3
"""
Promote all modes to latest: SHADOW → PAPER, SHADOW → LIVE.

- Copy config/shadow/* → config/paper/*
- Copy config/shadow/* → config/live/*
- Update config/versioning.yaml: live.version = live_v{N+1}, paper.version = paper_v{N+1},
  shadow.version = shadow_v{N+1}, all commits = current git HEAD.
- All modes run the newest intelligence + config.
- CONFIG-ONLY, reversible. Restart dashboard only after deploy (never trading engine).
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
LIVE = CONFIG / "live"


def _bump(s: str, prefix: str) -> str:
    if not s or "_" not in s:
        return f"{prefix}_v2"
    p, rest = s.rsplit("_", 1)
    if rest.startswith("v") and rest[1:].isdigit():
        n = int(rest[1:]) + 1
        return f"{p}_v{n}"
    try:
        return f"{p}_{int(rest) + 1}"
    except ValueError:
        return f"{prefix}_v2"


def main() -> int:
    if not SHADOW.exists():
        print("[FAIL] config/shadow/ not found", file=sys.stderr)
        return 1

    from config.version_loader import get_all_versions, set_version, current_git_commit

    commit = current_git_commit()
    all_versions = get_all_versions()

    # Copy shadow → paper
    PAPER.mkdir(parents=True, exist_ok=True)
    for f in SHADOW.iterdir():
        if f.is_file():
            shutil.copy2(f, PAPER / f.name)
            print(f"[OK] shadow/{f.name} -> paper/")

    # Copy shadow → live
    LIVE.mkdir(parents=True, exist_ok=True)
    for f in SHADOW.iterdir():
        if f.is_file():
            shutil.copy2(f, LIVE / f.name)
            print(f"[OK] shadow/{f.name} -> live/")

    # Bump all version numbers and set commit
    live_ver = _bump(all_versions.get("live", {}).get("version") or "live_v1", "live_v")
    paper_ver = _bump(all_versions.get("paper", {}).get("version") or "paper_v1", "paper_v")
    shadow_ver = _bump(all_versions.get("shadow", {}).get("version") or "shadow_v1", "shadow_v")

    set_version("live", live_ver, commit)
    set_version("paper", paper_ver, commit)
    set_version("shadow", shadow_ver, commit)

    print("")
    print("[OK] versioning updated:")
    print(f"  live:  {live_ver}  commit={commit or 'null'}")
    print(f"  paper: {paper_ver}  commit={commit or 'null'}")
    print(f"  shadow: {shadow_ver}  commit={commit or 'null'}")
    print("")
    print("Next: git fetch origin main && git reset --hard origin/main")
    print("      sudo systemctl restart stock-bot-dashboard  # ONLY dashboard, never trading")
    return 0


if __name__ == "__main__":
    sys.exit(main())
