#!/usr/bin/env python3
"""
Run the Alpaca bars pipeline (run_bars_pipeline.py) on the droplet via SSH.
Uses DropletClient. Prints full console output, then fetches reports/bars/* and
writes them to reports/bars_droplet_run_<timestamp>/ for external review.
If run_bars_pipeline.py is missing on droplet (e.g. not yet pushed), deploys
bars scripts via SFTP then runs.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ROOT = "/root/stock-bot"
# Local paths to deploy when pipeline script is missing on droplet (relative to REPO)
BARS_DEPLOY_FILES = [
    "scripts/run_bars_pipeline.py",
    "scripts/check_alpaca_env.py",
    "scripts/bars_universe_and_range.py",
    "scripts/fetch_alpaca_bars.py",
    "scripts/write_bars_cache_status.py",
    "scripts/audit_bars.py",
    "scripts/blocked_expectancy_analysis.py",
    "data/bars_loader.py",
    "scripts/run_droplet_truth_run.py",
]
BARS_REPORTS = [
    "reports/bars/alpaca_env_check.md",
    "reports/bars/universe_and_range.md",
    "reports/bars/incomplete_symbols.md",
    "reports/bars/cache_status.md",
    "reports/bars/integrity_audit.md",
    "reports/bars/PROOF.md",
]
EXTRA_FOR_REVIEW = [
    "reports/blocked_expectancy/bucket_analysis.md",
    "reports/blocked_expectancy/replay_results.jsonl",
]


def safe_print(text: str, file=None) -> None:
    if not text:
        return
    safe = text.replace("\u2192", "->").replace("\u2014", "-").encode("ascii", errors="replace").decode("ascii")
    f = file or sys.stdout
    f.write(safe)
    if not safe.endswith("\n"):
        f.write("\n")
    f.flush()


def _deploy_bars_scripts(c) -> None:
    """Upload bars pipeline scripts to droplet via SFTP."""
    sftp = c.ssh_client.open_sftp()
    try:
        for rel in BARS_DEPLOY_FILES:
            local = REPO / rel
            if not local.exists():
                continue
            remote = f"{ROOT}/{rel}"
            remote_dir = str(Path(remote).parent)
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                parts = Path(remote_dir).parts
                for i in range(1, len(parts) + 1):
                    d = "/".join(parts[:i])
                    if d == "/":
                        continue
                    try:
                        sftp.mkdir(d)
                    except OSError:
                        pass
            sftp.put(str(local), remote)
            safe_print(f"Deployed {rel} -> {remote}")
    finally:
        sftp.close()


def main() -> int:
    from droplet_client import DropletClient

    # Run: pull latest then run pipeline (source .env on droplet)
    cmd_no_reset = f"cd {ROOT} && [ -f .env ] && set -a && source .env && set +a; python3 scripts/run_bars_pipeline.py"
    cmd_with_reset = (
        f"cd {ROOT} && "
        "git fetch origin && git reset --hard origin/main && "
        "[ -f .env ] && set -a && source .env && set +a; "
        "python3 scripts/run_bars_pipeline.py"
    )
    safe_print("=== Bars pipeline on droplet (full output) ===\n")
    with DropletClient() as c:
        out, err, rc = c._execute(cmd_with_reset, timeout=900)
        combined = (out or "") + (err or "")
        if rc == 2 and "run_bars_pipeline.py" in combined and ("can't open file" in combined or "No such file" in combined):
            safe_print("Pipeline script missing on droplet; deploying bars scripts via SFTP...\n")
            _deploy_bars_scripts(c)
            out, err, rc = c._execute(cmd_no_reset, timeout=900)
        safe_print(out or "")
        if err:
            safe_print(err, file=sys.stderr)
        if rc != 0:
            safe_print(f"\n[Pipeline exit code: {rc}]", file=sys.stderr)

        # Fetch reports for external review
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_dir = REPO / "reports" / f"bars_droplet_run_{stamp}"
        out_dir.mkdir(parents=True, exist_ok=True)
        all_rel = BARS_REPORTS + EXTRA_FOR_REVIEW
        for rel in all_rel:
            out_text, _, _ = c._execute(f"cat {ROOT}/{rel} 2>/dev/null || echo ''", timeout=10)
            text = (out_text or "").strip()
            name = Path(rel).name
            if name == "replay_results.jsonl":
                lines = text.splitlines()
                if len(lines) > 100:
                    text = "\n".join(lines[:100]) + "\n... (" + str(len(lines)) + " lines total)"
            (out_dir / name).write_text(text or f"(empty or missing: {rel})", encoding="utf-8")
        # Write a summary that repeats the one-block output
        summary_path = out_dir / "EXTERNAL_REVIEW_SUMMARY.md"
        summary_lines = [
            "# Bars pipeline – droplet run summary",
            "",
            "Generated: " + stamp + " UTC",
            "",
            "## Required one-block output",
            "",
            "See pipeline stdout above (and PIPELINE_STDOUT.txt in this folder) for:",
            "- Alpaca env check: PASS/FAIL",
            "- Symbols fetched: N",
            "- Date range covered",
            "- Bars coverage: min/median/max %",
            "- Replay pnl non-zero: YES/NO",
            "- Verdict: BARS READY — REAL PNL ENABLED / BARS MISSING — FIX REQUIRED",
            "",
            "## Artifacts in this folder",
            "",
        ]
        for rel in all_rel:
            summary_lines.append(f"- `{Path(rel).name}`")
        summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
        (out_dir / "PIPELINE_STDOUT.txt").write_text((out or "") + (err or ""), encoding="utf-8")
        safe_print(f"\n=== Reports saved to {out_dir} for external review ===")
        safe_print(f"Summary: {summary_path}")

    return rc


if __name__ == "__main__":
    sys.exit(main())
