#!/usr/bin/env python3
"""
Specialist Tier Monitoring Orchestrator
Authoritative Source: MEMORY_BANK.md

Orchestrates daily and weekly audit reports, commits and pushes to GitHub.

Daily (Mon-Thu post-market): Runs daily_alpha_audit.py
Friday (post-market): Runs daily_alpha_audit.py + friday_eow_audit.py + regime_persistence_audit.py

All reports are committed and pushed to origin/main immediately.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json

BASE_DIR = Path(__file__).parent


def run_command(cmd: list, cwd: Path = None) -> tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    
    Args:
        cmd: List of command and arguments
        cwd: Working directory (defaults to BASE_DIR)
    
    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    if cwd is None:
        cwd = BASE_DIR
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out: {' '.join(cmd)}"
    except Exception as e:
        return 1, "", str(e)


def git_commit_and_push(report_files: list[Path], commit_message: str) -> bool:
    """
    Commit report files and push to origin/main.
    
    Args:
        report_files: List of report file paths to commit
        commit_message: Git commit message
    
    Returns:
        True if successful, False otherwise
    """
    # Add files to git
    for file_path in report_files:
        returncode, stdout, stderr = run_command(["git", "add", str(file_path.relative_to(BASE_DIR))])
        if returncode != 0:
            print(f"Error adding {file_path} to git: {stderr}", file=sys.stderr)
            return False
    
    # Commit
    returncode, stdout, stderr = run_command(["git", "commit", "-m", commit_message])
    if returncode != 0:
        if "nothing to commit" in stderr.lower():
            print("No changes to commit")
            return True  # Not an error - files already committed
        print(f"Error committing: {stderr}", file=sys.stderr)
        return False
    
    # Push
    returncode, stdout, stderr = run_command(["git", "push", "origin", "main"])
    if returncode != 0:
        print(f"Error pushing to origin/main: {stderr}", file=sys.stderr)
        return False
    
    print(f"Successfully committed and pushed: {commit_message}")
    return True


def run_daily_audit(target_date: datetime = None) -> Path:
    """Run daily alpha audit and return report file path"""
    cmd = [sys.executable, "daily_alpha_audit.py"]
    if target_date:
        cmd.extend(["--date", target_date.strftime("%Y-%m-%d")])
    
    returncode, stdout, stderr = run_command(cmd)
    if returncode != 0:
        print(f"Error running daily_alpha_audit.py: {stderr}", file=sys.stderr)
        sys.exit(1)
    
    # Parse output to find report file
    # daily_alpha_audit.py prints: "Daily Alpha Audit report written to: reports/daily_alpha_audit_YYYY-MM-DD.json"
    for line in stdout.split('\n'):
        if "written to:" in line.lower():
            file_path = line.split("written to:")[-1].strip()
            return Path(file_path)
    
    # Fallback: construct expected path
    if target_date:
        date_str = target_date.strftime("%Y-%m-%d")
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return BASE_DIR / "reports" / f"daily_alpha_audit_{date_str}.json"


def run_friday_eow_audit(friday_date: datetime = None) -> Path:
    """Run Friday EOW audit and return report file path"""
    cmd = [sys.executable, "friday_eow_audit.py"]
    if friday_date:
        cmd.extend(["--date", friday_date.strftime("%Y-%m-%d")])
    
    returncode, stdout, stderr = run_command(cmd)
    if returncode != 0:
        print(f"Error running friday_eow_audit.py: {stderr}", file=sys.stderr)
        sys.exit(1)
    
    # Parse output
    for line in stdout.split('\n'):
        if "written to:" in line.lower():
            file_path = line.split("written to:")[-1].strip()
            return Path(file_path)
    
    # Fallback
    if friday_date:
        date_str = friday_date.strftime("%Y-%m-%d")
    else:
        today = datetime.now(timezone.utc)
        days_since_friday = (today.weekday() - 4) % 7
        friday_date = today - timedelta(days=days_since_friday)
        date_str = friday_date.strftime("%Y-%m-%d")
    return BASE_DIR / "reports" / f"EOW_structural_audit_{date_str}.md"


def run_regime_persistence_audit(friday_date: datetime = None) -> Path:
    """Run regime persistence audit and return report file path"""
    cmd = [sys.executable, "regime_persistence_audit.py"]
    if friday_date:
        cmd.extend(["--date", friday_date.strftime("%Y-%m-%d")])
    
    returncode, stdout, stderr = run_command(cmd)
    if returncode != 0:
        print(f"Error running regime_persistence_audit.py: {stderr}", file=sys.stderr)
        sys.exit(1)
    
    # Parse output
    for line in stdout.split('\n'):
        if "written to:" in line.lower():
            file_path = line.split("written to:")[-1].strip()
            return Path(file_path)
    
    # Fallback
    if friday_date:
        date_str = friday_date.strftime("%Y-%m-%d")
    else:
        today = datetime.now(timezone.utc)
        days_since_friday = (today.weekday() - 4) % 7
        friday_date = today - timedelta(days=days_since_friday)
        date_str = friday_date.strftime("%Y-%m-%d")
    return BASE_DIR / "reports" / f"weekly_regime_persistence_{date_str}.json"


def main():
    """Main orchestrator logic"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Specialist Tier Monitoring Orchestrator")
    parser.add_argument("--date", type=str, help="Date to analyze (YYYY-MM-DD), defaults to today")
    parser.add_argument("--force-friday", action="store_true", help="Force Friday EOW audits even if not Friday")
    parser.add_argument("--skip-git", action="store_true", help="Skip git commit and push (for testing)")
    
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = datetime.now(timezone.utc)
    
    day_of_week = target_date.weekday()  # 0=Monday, 4=Friday
    
    report_files = []
    commit_messages = []
    
    # Always run daily audit
    print("Running Daily Alpha Audit...")
    daily_report = run_daily_audit(target_date)
    if daily_report.exists():
        report_files.append(daily_report)
        commit_messages.append(f"Daily Alpha Audit {target_date.strftime('%Y-%m-%d')} - MEMORY_BANK.md Specialist Tier Monitoring")
        print(f"✓ Daily audit complete: {daily_report}")
    
    # Run Friday audits if it's Friday or forced
    if day_of_week == 4 or args.force_friday:  # Friday
        # Find Friday of the week
        days_since_friday = (target_date.weekday() - 4) % 7
        friday_date = target_date - timedelta(days=days_since_friday)
        
        print("Running Friday EOW Structural Audit...")
        eow_report = run_friday_eow_audit(friday_date)
        if eow_report.exists():
            report_files.append(eow_report)
            commit_messages.append(f"Friday EOW Audit {friday_date.strftime('%Y-%m-%d')} - MEMORY_BANK.md Specialist Tier Monitoring")
            print(f"✓ Friday EOW audit complete: {eow_report}")
        
        print("Running Regime Persistence Audit...")
        regime_report = run_regime_persistence_audit(friday_date)
        if regime_report.exists():
            report_files.append(regime_report)
            commit_messages.append(f"Regime Persistence Audit {friday_date.strftime('%Y-%m-%d')} - MEMORY_BANK.md Specialist Tier Monitoring")
            print(f"✓ Regime persistence audit complete: {regime_report}")
    
    # Commit and push to GitHub
    if not args.skip_git and report_files:
        # Combine commit messages
        combined_message = " | ".join(commit_messages)
        success = git_commit_and_push(report_files, combined_message)
        
        if success:
            print(f"\n✅ All reports committed and pushed to origin/main")
            print(f"Reports: {', '.join(str(f.relative_to(BASE_DIR)) for f in report_files)}")
        else:
            print(f"\n❌ Error committing/pushing reports", file=sys.stderr)
            sys.exit(1)
    elif args.skip_git:
        print(f"\n⚠️  Git commit/push skipped (--skip-git flag)")
        print(f"Reports generated: {', '.join(str(f.relative_to(BASE_DIR)) for f in report_files)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
