#!/usr/bin/env python3
"""
EOD confirmation: verify today's EOD ran, re-run if needed, push to GitHub.

- verify_eod_run(date_str): check board/eod/out/<date_str>/ and canonical files
- run_full_eod(date_str): run full EOD pipeline and write_daily_bundle
- push_eod_to_github(date_str): git add, commit, push
- run_eod_confirmation(): main entrypoint (verify → re-run if needed → push)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

log = logging.getLogger(__name__)

# Required keys inside derived_deltas.json
DERIVED_DELTAS_REQUIRED_KEYS = ("rolling_windows", "missed_money", "variant_attribution")
ALLOWED_EXTENSIONS = {".json", ".md", ".txt", ".csv"}
DISALLOWED_SUFFIXES = (".gz", ".jsonl.gz")
# Canonical files we require for "valid" (bundle_writer output)
REQUIRED_CANONICAL_FILES = ("eod_board.json", "derived_deltas.json", "eod_board.md", "eod_review.md", "weekly_review.md")
MAX_CANONICAL_FILES = 11  # 9 from bundle_writer + 2 from multi_day_analysis (json + md)


def verify_eod_run(date_str: str, repo_root: Path | None = None) -> dict[str, Any]:
    """
    Check for existence of board/eod/out/<date_str>/ and canonical files.
    Check eod_board.json is valid JSON and derived_deltas.json has
    rolling_windows, missed_money, variant_attribution.
    Return structured result: exists, missing_files, valid, reason.
    """
    base = repo_root or REPO_ROOT
    out_dir = base / "board" / "eod" / "out" / date_str
    result: dict[str, Any] = dict(
        exists=False,
        missing_files=[],
        valid=False,
        reason="",
    )

    if not out_dir.is_dir():
        result["reason"] = f"board/eod/out/{date_str}/ does not exist"
        return result

    result["exists"] = True
    missing: list[str] = []
    for f in REQUIRED_CANONICAL_FILES:
        if not (out_dir / f).is_file():
            missing.append(f)
    result["missing_files"] = missing

    # Check for disallowed files (e.g. .gz) in date dir (excluding legacy/)
    for p in out_dir.iterdir():
        if p.is_dir() and p.name == "legacy":
            continue
        if p.is_file():
            suf = p.suffix
            if p.name.endswith(".jsonl.gz"):
                suf = ".jsonl.gz"
            if suf in DISALLOWED_SUFFIXES:
                result["missing_files"] = list(set(result["missing_files"]) | {f"disallowed: {p.name}"})
                result["reason"] = result["reason"] or f"Disallowed file in output: {p.name}"
            elif suf not in ALLOWED_EXTENSIONS:
                result["missing_files"] = list(set(result["missing_files"]) | {f"disallowed_ext: {p.name}"})

    if missing and not result["reason"]:
        result["reason"] = f"Missing required files: {missing}"

    # eod_board.json must exist and be valid JSON
    eod_board_path = out_dir / "eod_board.json"
    if not eod_board_path.is_file():
        result["missing_files"] = list(set(result["missing_files"]) | {"eod_board.json"})
        result["reason"] = result["reason"] or "eod_board.json missing"
    else:
        try:
            json.loads(eod_board_path.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            result["valid"] = False
            result["reason"] = f"eod_board.json invalid JSON: {e}"
            return result

    # derived_deltas.json must exist and include rolling_windows, missed_money, variant_attribution
    derived_path = out_dir / "derived_deltas.json"
    if not derived_path.is_file():
        result["missing_files"] = list(set(result["missing_files"]) | {"derived_deltas.json"})
        result["reason"] = result["reason"] or "derived_deltas.json missing"
    else:
        try:
            data = json.loads(derived_path.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(data, dict):
                result["reason"] = "derived_deltas.json root is not an object"
            else:
                for key in DERIVED_DELTAS_REQUIRED_KEYS:
                    if key not in data:
                        result["missing_files"] = list(set(result["missing_files"]) | {f"derived_deltas.{key}"})
                if any(k not in data for k in DERIVED_DELTAS_REQUIRED_KEYS):
                    result["reason"] = result["reason"] or (
                        f"derived_deltas.json missing keys: "
                        f"{[k for k in DERIVED_DELTAS_REQUIRED_KEYS if k not in data]}"
                    )
        except Exception as e:
            result["valid"] = False
            result["reason"] = f"derived_deltas.json invalid or unreadable: {e}"
            return result

    if result["missing_files"] or result["reason"]:
        result["valid"] = False
        if not result["reason"]:
            result["reason"] = f"Missing or invalid: {result['missing_files']}"
        return result

    # Count files (allowed extensions only); must be <= MAX_CANONICAL_FILES
    file_count = sum(
        1 for p in out_dir.iterdir()
        if p.is_file() and p.suffix in ALLOWED_EXTENSIONS
    )
    if file_count > MAX_CANONICAL_FILES:
        result["valid"] = False
        result["reason"] = f"Canonical outputs exceed {MAX_CANONICAL_FILES} files (found {file_count})"
        return result

    result["valid"] = True
    result["reason"] = "OK"
    return result


def run_full_eod(date_str: str, repo_root: Path | None = None) -> None:
    """
    Run the entire EOD pipeline for date_str: rolling windows, multi-day analysis,
    missed-money computation, board generation, weekly synthesis, bundle_writer.write_daily_bundle.
    Ensures no .gz in output and canonical outputs <= 10 files.
    Fails hard if verify_eod_run still invalid after run.
    """
    base = repo_root or REPO_ROOT
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    os.chdir(base)

    # 1) Multi-day analysis (writes board/eod/out/<date>/multi_day_analysis.json and .md)
    rma = subprocess.run(
        [sys.executable, str(base / "scripts" / "run_multi_day_analysis.py"), "--date", date_str],
        cwd=base,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if rma.returncode != 0:
        log.warning("run_multi_day_analysis exited %s: %s", rma.returncode, rma.stderr or rma.stdout)

    # 2) Full EOD (rolling windows, board generation, write_daily_bundle) via run_stock_quant_officer_eod with --date
    # Use --skip-wheel-closure so confirmation re-run can complete and push when prior closure is missing
    eod_argv = [sys.executable, str(SCRIPT_DIR / "run_stock_quant_officer_eod.py"), "--date", date_str, "--skip-wheel-closure"]
    eod = subprocess.run(eod_argv, cwd=base, timeout=600)
    if eod.returncode != 0:
        raise SystemExit(f"EOD pipeline failed with exit code {eod.returncode}")

    # Re-verify
    result = verify_eod_run(date_str, repo_root=base)
    if not result.get("valid"):
        raise SystemExit(f"EOD re-run completed but verification failed: {result.get('reason', 'unknown')}")


def push_eod_to_github(date_str: str, repo_root: Path | None = None) -> None:
    """
    Stage board/eod/out/<date_str>/, commit with message
    'EOD report for <date_str> (auto-confirmed and pushed)', push to origin main.
    On push failure: retry once; if still failing, write state/eod_push_failed_<date_str>.json.
    """
    base = repo_root or REPO_ROOT
    state_dir = base / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    failed_path = state_dir / f"eod_push_failed_{date_str}.json"

    rel_dir = f"board/eod/out/{date_str}"
    abs_dir = base / "board" / "eod" / "out" / date_str
    if not abs_dir.is_dir():
        log.error("EOD dir does not exist: %s", abs_dir)
        _write_push_failed(failed_path, date_str, "EOD directory does not exist")
        return

    def run_git(args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + args,
            cwd=base,
            capture_output=True,
            text=True,
            timeout=60,
        )

    add = run_git(["add", rel_dir])
    if add.returncode != 0:
        log.error("git add failed: %s", add.stderr or add.stdout)
        _write_push_failed(failed_path, date_str, add.stderr or add.stdout or "git add failed")
        return

    commit = run_git(["commit", "-m", f"EOD report for {date_str} (auto-confirmed and pushed)"])
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout or "") + (commit.stderr or ""):
        log.warning("git commit: %s", commit.stderr or commit.stdout)

    for attempt in (1, 2):
        push = run_git(["push", "origin", "main"])
        if push.returncode == 0:
            log.info("Pushed EOD report for %s to origin main", date_str)
            return
        log.warning("git push attempt %s failed: %s", attempt, push.stderr or push.stdout)
    _write_push_failed(failed_path, date_str, push.stderr or push.stdout or "git push failed after 2 attempts")


def _write_push_failed(path: Path, date_str: str, reason: str) -> None:
    try:
        path.write_text(
            json.dumps({"date": date_str, "reason": reason}, indent=2),
            encoding="utf-8",
        )
        log.error("Wrote push failure state to %s", path)
    except Exception as e:
        log.exception("Could not write push failed state: %s", e)


def run_eod_confirmation(repo_root: Path | None = None) -> None:
    """
    Main entrypoint: date_str = today (YYYY-MM-DD).
    If verify_eod_run exists and valid → push_eod_to_github.
    Else → run_full_eod then push_eod_to_github.
    """
    base = repo_root or REPO_ROOT
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = verify_eod_run(date_str, repo_root=base)

    if not result.get("exists") or not result.get("valid"):
        log.warning("EOD missing or incomplete — re-running.")
        run_full_eod(date_str, repo_root=base)

    push_eod_to_github(date_str, repo_root=base)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_eod_confirmation()
