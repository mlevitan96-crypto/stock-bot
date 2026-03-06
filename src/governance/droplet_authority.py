"""
Droplet Data Authority guard.

Per memory_bank/TELEMETRY_STANDARD.md: the droplet is the single source of truth for
trade data, telemetry, attribution, backtests, replays, and governance decisions.
Local analysis is INVALID for conclusions; allowed only for schema validation or
dry-run debugging with --allow-local-dry-run.

Usage in analysis/replay/backtest/governance scripts:
  1. Add args via add_droplet_authority_args(parser).
  2. After parse_args(), call require_droplet_authority(script_name, args, repo_root).
  3. When run on droplet, caller must set DROPLET_RUN=1 and pass --droplet-run --deployed-commit <hash>.
"""

from __future__ import annotations

import json
import os
import sys
from argparse import ArgumentParser, Namespace
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def is_droplet() -> bool:
    """True if this process is running on the droplet (authoritative environment)."""
    return (os.environ.get("DROPLET_RUN") or os.environ.get("ON_DROPLET")) == "1"


def add_droplet_authority_args(parser: ArgumentParser) -> None:
    """Add --allow-local-dry-run, --droplet-run, --deployed-commit to parser."""
    parser.add_argument(
        "--allow-local-dry-run",
        action="store_true",
        help="Allow running locally for schema/debug only; output is NON-AUTHORITATIVE.",
    )
    parser.add_argument(
        "--droplet-run",
        action="store_true",
        help="Mark this run as authoritative (required when DROPLET_RUN=1).",
    )
    parser.add_argument(
        "--deployed-commit",
        type=str,
        default="",
        metavar="HASH",
        help="Commit hash deployed on droplet (required for authoritative run).",
    )


def require_droplet_authority(
    script_name: str,
    args: Namespace,
    repo_root: Path,
) -> None:
    """
    Enforce droplet-only data authority. Call after parsing args.

    - Local without --allow-local-dry-run: print error and exit 1.
    - Local with --allow-local-dry-run: print warning and return (non-authoritative).
    - Droplet without --droplet-run and --deployed-commit: print error and exit 1.
    - Droplet with both: write state/last_droplet_analysis.json and return.
    """
    allow_local = getattr(args, "allow_local_dry_run", False)
    droplet_run = getattr(args, "droplet_run", False)
    deployed_commit = (getattr(args, "deployed_commit", None) or "").strip()

    if not is_droplet():
        if allow_local:
            print(
                "WARNING: Running locally with --allow-local-dry-run. Results are NON-AUTHORITATIVE.",
                file=sys.stderr,
            )
            return
        print(
            "ERROR: This analysis must be run on the droplet. Local results are invalid.",
            file=sys.stderr,
        )
        print(
            "Use --allow-local-dry-run only for schema validation or dry-run debugging.",
            file=sys.stderr,
        )
        sys.exit(1)

    # On droplet: authoritative run requires explicit flags
    if not droplet_run or not deployed_commit:
        print(
            "ERROR: Authoritative run on droplet requires --droplet-run and --deployed-commit <hash>.",
            file=sys.stderr,
        )
        sys.exit(1)

    run_ts = datetime.now(timezone.utc).isoformat()
    state_dir = repo_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "last_droplet_analysis.json"
    state = {
        "script": script_name,
        "deployed_commit": deployed_commit,
        "run_ts": run_ts,
    }
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
