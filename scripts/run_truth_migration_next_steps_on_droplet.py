#!/usr/bin/env python3
"""Run CURSOR_ONE_BLOCK_TRUTH_MIGRATION_NEXT_STEPS.sh on droplet via DropletClient. Uploads required files then runs."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "truth" / "CURSOR_ONE_BLOCK_TRUTH_MIGRATION_NEXT_STEPS.sh"

# Files the next-steps script requires (relative to repo root)
REQUIRED_FILES = [
    "scripts/truth/capture_droplet_baseline.sh",
    "scripts/truth/run_truth_smoke_test.sh",
    "scripts/truth/CURSOR_ONE_BLOCK_TRUTH_MIGRATION_NEXT_STEPS.sh",
    "scripts/truth/CURSOR_BIND_CTR_TO_STOCK_BOT_SERVICE.sh",
    "src/infra/__init__.py",
    "src/infra/truth_router.py",
    "docs/TRUTH_ROOT_CONTRACT.md",
    "docs/DEPRECATIONS_TRUTH_PATHS.md",
    "reports/truth_migration/TRUTH_MIGRATION_CONTRACT.md",
    "reports/truth_migration/SAFE_TO_APPLY.md",
    "reports/truth_migration/droplet_baseline/path_map.md",
    "tests/__init__.py",
    "tests/test_truth_router.py",
]


def main() -> int:
    if not SCRIPT.is_file():
        print(f"Missing script: {SCRIPT}", file=sys.stderr)
        return 1
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"

    with DropletClient() as c:
        # Create remote dirs and upload all required files (droplet may not have git-pulled yet)
        for rel in REQUIRED_FILES:
            local = REPO / rel
            if not local.is_file():
                print(f"Skip (missing locally): {rel}", file=sys.stderr)
                continue
            remote = f"{pd}/{rel}".replace("\\", "/")
            remote_dir = str(Path(remote).parent).replace("\\", "/")
            c._execute(f"mkdir -p '{remote_dir}'", timeout=5)
            try:
                c.put_file(local, remote)
                print(f"Uploaded: {rel}")
            except Exception as e:
                print(f"Upload failed {rel}: {e}", file=sys.stderr)
        for sh in ["capture_droplet_baseline.sh", "run_truth_smoke_test.sh", "CURSOR_ONE_BLOCK_TRUTH_MIGRATION_NEXT_STEPS.sh"]:
            c._execute(f"sed -i 's/\\r$//' {pd}/scripts/truth/{sh} 2>/dev/null; chmod +x {pd}/scripts/truth/{sh} 2>/dev/null", timeout=5)
        # Run from repo root
        cmd = f"cd {c.project_dir} && REPO={c.project_dir} bash scripts/truth/CURSOR_ONE_BLOCK_TRUTH_MIGRATION_NEXT_STEPS.sh"
        out, err, rc = c._execute(cmd, timeout=300)
    print(out)
    if err:
        print(err, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
