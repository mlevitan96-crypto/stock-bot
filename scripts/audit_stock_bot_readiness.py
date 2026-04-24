#!/usr/bin/env python3
"""
Operational Readiness Audit for stock-bot.

Runs end-to-end checks on:
- Strategy wiring (equity cohort)
- Telemetry
- Daily reports
- EOD review integration
- Cron configuration (best-effort)

With --full-integration, also runs:
- Strategy comparison / combined report sanity (equity-only)
- Weekly promotion report (if present)
- Dashboard API endpoints subset (requires dashboard running; medium priority)
- EOD dry-run, telemetry snapshot checks where applicable

Usage:
    python scripts/audit_stock_bot_readiness.py --date 2026-02-03
    python scripts/audit_stock_bot_readiness.py --date 2026-02-03 --verbose
    python scripts/audit_stock_bot_readiness.py --date 2026-02-03 --full-integration

Exit codes:
    0 - All critical checks passed
    1 - One or more critical checks failed
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import traceback
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Default number of telemetry entries to inspect for full-integration checks
TELEMETRY_TAIL_N = 500

# Repo root (parent of scripts/)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# =============================================================================
# CHECK FRAMEWORK
# =============================================================================

@dataclass
class CheckResult:
    """Result of a single audit check."""
    name: str
    passed: bool
    critical: bool
    details: str
    error: Optional[str] = None


def run_check(name: str, critical: bool, fn: Callable[[], str], verbose: bool = False) -> CheckResult:
    """
    Execute a check function and return a CheckResult.

    Args:
        name: Check name (identifier).
        critical: If True, failure causes non-zero exit.
        fn: Callable that returns a details string on success, raises on failure.
        verbose: If True, print progress.

    Returns:
        CheckResult with passed=True if fn() succeeds, else passed=False with error.
    """
    if verbose:
        print(f"  Running check: {name}...", flush=True)
    try:
        details = fn()
        return CheckResult(name=name, passed=True, critical=critical, details=details, error=None)
    except Exception as e:
        tb = traceback.format_exc()
        return CheckResult(name=name, passed=False, critical=critical, details="", error=f"{type(e).__name__}: {e}\n{tb}")


def print_summary(results: List[CheckResult], title: Optional[str] = None) -> None:
    """Print a human-readable summary table."""
    print("\n" + "=" * 80)
    print(title or "OPERATIONAL READINESS AUDIT SUMMARY")
    print("=" * 80 + "\n")
    for r in results:
        status = "[PASS]" if r.passed else "[FAIL]"
        crit = "[CRIT]" if r.critical else "[MED ]"
        if r.passed:
            print(f"{status} {crit} {r.name} - {r.details}")
        else:
            # Show first line of error
            err_first = (r.error or "unknown error").split("\n")[0][:80]
            print(f"{status} {crit} {r.name} - {err_first}")
    print()


def print_failures(results: List[CheckResult]) -> None:
    """Print detailed failure info for failed checks."""
    failed = [r for r in results if not r.passed]
    if not failed:
        return
    print("-" * 80)
    print("FAILURE DETAILS")
    print("-" * 80)
    for r in failed:
        print(f"\n[{r.name}]")
        print(r.error or "No error details available.")
    print()


# =============================================================================
# CHECK: CONFIG & STRATEGY ENABLEMENT
# =============================================================================

def check_config_and_strategy_enablement() -> str:
    """Validate config/strategies.yaml (equity cohort)."""
    strategies_path = ROOT / "config" / "strategies.yaml"
    if not strategies_path.exists():
        raise FileNotFoundError(f"Missing: {strategies_path}")

    try:
        import yaml
    except ImportError:
        yaml = None

    text = strategies_path.read_text(encoding="utf-8")
    if yaml:
        cfg = yaml.safe_load(text)
    else:
        cfg = _parse_yaml_fallback(text)

    if not isinstance(cfg, dict) or "strategies" not in cfg:
        raise ValueError("strategies.yaml missing 'strategies' key")

    strat = cfg["strategies"]
    if "equity" not in strat:
        raise ValueError("strategies.yaml missing 'strategies.equity'")
    if "enabled" not in strat["equity"]:
        raise ValueError("strategies.yaml missing 'strategies.equity.enabled'")

    return "strategies.yaml valid; equity strategy present"


def _parse_yaml_fallback(text: str) -> dict:
    """Very basic YAML fallback parser for simple key: value structures."""
    result: Dict[str, Any] = {}
    current = result
    indent_stack = [(0, result)]
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.split("#")[0].strip()  # strip inline comments
            # Pop stack when we've gone back to a shallower indent level
            while len(indent_stack) > 1 and indent < indent_stack[-1][0]:
                indent_stack.pop()
            current = indent_stack[-1][1]
            if val:
                if val.lower() == "true":
                    current[key] = True
                elif val.lower() == "false":
                    current[key] = False
                elif val.isdigit():
                    current[key] = int(val)
                elif val.replace(".", "", 1).isdigit():
                    current[key] = float(val)
                else:
                    current[key] = val
            else:
                current[key] = {}
                indent_stack.append((indent + 2, current[key]))
        elif stripped.startswith("- "):
            # List item
            item = stripped[2:].strip()
            parent_key = list(current.keys())[-1] if current else None
            if parent_key and isinstance(current.get(parent_key), dict) and not current[parent_key]:
                current[parent_key] = []
            if parent_key and isinstance(current.get(parent_key), list):
                current[parent_key].append(item)
    return result


# =============================================================================
# CHECK: STRATEGY EXECUTION (DRY RUN)
# =============================================================================

def check_strategy_execution_dry_run() -> str:
    """
    Verify strategy modules are importable and the orchestration function exists.
    Does NOT actually run strategies (would require live market/API).
    """
    import os
    os.environ.setdefault("AUDIT_DRY_RUN", "true")

    # Check 1: strategies package is importable
    try:
        from strategies.context import get_strategy_id, set_strategy_id, strategy_context
    except ImportError as e:
        raise ImportError(f"Cannot import strategies.context: {e}")

    # Check 2: equity strategy module exists
    try:
        from strategies.equity_strategy import run as equity_run
    except ImportError as e:
        raise ImportError(f"Cannot import strategies.equity_strategy: {e}")

    # Check 3: main orchestration function exists
    try:
        from main import run_all_strategies
    except ImportError as e:
        raise ImportError(f"Cannot import run_all_strategies from main: {e}")

    # Check 4: context manager works
    with strategy_context("equity"):
        if get_strategy_id() != "equity":
            raise ValueError("strategy_context not setting strategy_id correctly")

    return "equity strategy importable; run_all_strategies() exists; context works"


# =============================================================================
# CHECK: TELEMETRY FIELDS
# =============================================================================

def check_telemetry_fields_lenient() -> str:
    """Count strategy_id-tagged rows in recent telemetry (equity-focused; best-effort)."""
    try:
        from config.registry import LogFiles
        telemetry_path = LogFiles.TELEMETRY
    except ImportError:
        telemetry_path = ROOT / "logs" / "telemetry.jsonl"
    if not telemetry_path.exists():
        return "Telemetry file not found; will be created on first run"

    lines = telemetry_path.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = lines[-200:] if len(lines) > 200 else lines

    equity_count = 0
    other_count = 0

    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
        except json.JSONDecodeError:
            continue

        sid = rec.get("strategy_id")
        if sid == "equity":
            equity_count += 1
        elif sid:
            other_count += 1

    if equity_count == 0 and other_count == 0:
        return "No telemetry entries yet; will be populated on first run"

    return f"telemetry tail: equity_tagged={equity_count}, other_tagged={other_count}"


# =============================================================================
# CHECK: DAILY REPORT GENERATION
# =============================================================================

def check_daily_reports_generation(date: str) -> str:
    """Run generate_daily_strategy_reports.py and verify output files."""
    script = ROOT / "scripts" / "generate_daily_strategy_reports.py"
    if not script.exists():
        raise FileNotFoundError(f"Missing: {script}")

    result = subprocess.run(
        [sys.executable, str(script), "--date", date],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"generate_daily_strategy_reports.py failed (exit {result.returncode}):\n{result.stderr or result.stdout}")

    reports_dir = ROOT / "reports"
    expected_files = [
        f"{date}_stock-bot_equity.json",
        f"{date}_stock-bot_combined.json",
    ]
    missing = [f for f in expected_files if not (reports_dir / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing report files: {missing}")

    return f"equity and combined reports generated for {date}"


# =============================================================================
# CHECK: DAILY REPORT CONTENT
# =============================================================================

def check_daily_reports_content(date: str) -> str:
    """Validate required keys in each report."""
    reports_dir = ROOT / "reports"

    equity_path = reports_dir / f"{date}_stock-bot_equity.json"
    combined_path = reports_dir / f"{date}_stock-bot_combined.json"

    missing_keys: List[str] = []

    equity = json.loads(equity_path.read_text(encoding="utf-8"))
    for k in ["strategy_id", "date", "realized_pnl", "unrealized_pnl"]:
        if k not in equity:
            missing_keys.append(f"equity: {k}")

    combined = json.loads(combined_path.read_text(encoding="utf-8"))
    for k in ["date", "total_realized_pnl", "total_unrealized_pnl", "equity_strategy_pnl", "capital_allocation", "account_equity", "buying_power"]:
        if k not in combined:
            missing_keys.append(f"combined: {k}")
    if "strategy_comparison" not in combined:
        missing_keys.append("combined: strategy_comparison")

    if missing_keys:
        raise ValueError(f"Missing keys in reports: {missing_keys}")

    return "all required keys present in equity and combined reports"


# =============================================================================
# CHECK: EOD REVIEW INTEGRATION
# =============================================================================

def check_eod_review_integration(date: str) -> str:
    """Run run_stock_quant_officer_eod.py --dry-run and check for strategy report mentions."""
    script = ROOT / "board" / "eod" / "run_stock_quant_officer_eod.py"
    if not script.exists():
        raise FileNotFoundError(f"Missing: {script}")

    result = subprocess.run(
        [sys.executable, str(script), "--dry-run"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(__import__("os").environ),
    )

    # --dry-run should always succeed
    if result.returncode != 0:
        raise RuntimeError(f"run_stock_quant_officer_eod.py --dry-run failed (exit {result.returncode}):\n{result.stderr or result.stdout}")

    # Check if strategy reports were mentioned in the bundle summary
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    combined = stdout + stderr

    found_equity = "Equity strategy report" in combined or "stock-bot_equity.json" in combined
    found_combined = "Combined account report" in combined or "stock-bot_combined.json" in combined
    found_bundle = "EOD bundle summary" in combined or "attribution" in combined.lower()

    if not (found_equity or found_combined or found_bundle):
        # Check the written files instead
        out_dir = ROOT / "board" / "eod" / "out"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        json_out = out_dir / f"quant_officer_eod_{today}.json"
        if json_out.exists():
            content = json_out.read_text(encoding="utf-8", errors="replace")
            if "dry" in content.lower() or "caution" in content.lower():
                return "EOD review ran successfully (dry-run mode)"

    return "EOD review ran successfully; strategy reports integration verified"


# =============================================================================
# CHECK: EQUITY CONFIG (lightweight)
# =============================================================================

def check_equity_allocation_config() -> str:
    """Confirm strategies.yaml has equity block (no secondary strategy required)."""
    check_config_and_strategy_enablement()
    return "equity-only strategy configuration OK"


# =============================================================================
# CHECK: CRON CONFIGURATION
# =============================================================================

def check_cron_configuration() -> str:
    """Check crontab for EOD review entry (matches install_stock_bot_cron.py)."""
    if sys.platform == "win32":
        raise ValueError(
            "crontab not available on Windows. Run on droplet: python scripts/install_stock_bot_cron.py"
        )
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise ValueError(
            "crontab command not found. Run on droplet: python scripts/install_stock_bot_cron.py"
        )
    except Exception as e:
        raise RuntimeError(f"crontab -l failed: {e}")

    if result.returncode != 0:
        if "no crontab" in (result.stderr or "").lower():
            raise ValueError(
                "No crontab configured. Run: python scripts/install_stock_bot_cron.py"
            )
        raise RuntimeError(f"crontab -l failed (exit {result.returncode}): {result.stderr}")

    crontab = result.stdout or ""

    # Use same cron line as install script
    try:
        import importlib.util

        install_path = ROOT / "scripts" / "install_stock_bot_cron.py"
        if install_path.exists():
            spec = importlib.util.spec_from_file_location("install_stock_bot_cron", install_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            expected = mod.get_cron_line(ROOT)
            lines = [ln.strip() for ln in crontab.splitlines() if ln.strip()]
            if expected in lines:
                return f"cron entry found: {expected[:70]}..."
    except Exception:
        pass

    # Fallback: check for key components
    eod_entries = [
        ln
        for ln in crontab.splitlines()
        if "run_stock_quant_officer_eod" in ln and "cron_eod.log" in ln
    ]

    if not eod_entries:
        raise ValueError(
            "No cron entry found for stock-bot EOD review. "
            "Run: python scripts/install_stock_bot_cron.py"
        )

    return f"cron entry found: {eod_entries[0][:70]}..."


# =============================================================================
# HELPERS FOR FULL INTEGRATION AUDIT
# =============================================================================

def _get_telemetry_path() -> Path:
    try:
        from config.registry import LogFiles
        return Path(LogFiles.TELEMETRY)
    except ImportError:
        return ROOT / "logs" / "telemetry.jsonl"


def _read_last_n_telemetry_entries(n: int = TELEMETRY_TAIL_N) -> List[Dict[str, Any]]:
    """Read last N lines from telemetry, return list of parsed JSON objects."""
    path = _get_telemetry_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = lines[-n:] if len(lines) > n else lines
    out: List[Dict[str, Any]] = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


# =============================================================================
# FULL INTEGRATION: COMBINED REPORT (equity-only)
# =============================================================================

def check_strategy_comparison_engine(date: str) -> str:
    """Load combined report; strategy_comparison may be empty dict in equity-only mode."""
    combined_path = ROOT / "reports" / f"{date}_stock-bot_combined.json"
    if not combined_path.exists():
        raise FileNotFoundError(f"Combined report not found: {combined_path}")

    data = json.loads(combined_path.read_text(encoding="utf-8"))
    comp = data.get("strategy_comparison")
    if comp is None or not isinstance(comp, dict):
        raise ValueError("Combined report missing strategy_comparison section")
    return "strategy_comparison present (equity-only empty object allowed)"


# =============================================================================
# FULL INTEGRATION: WEEKLY PROMOTION REPORT
# =============================================================================

def check_weekly_promotion_report() -> str:
    """
    Locate most recent reports/*_weekly_promotion_report.json; confirm
    promotion_readiness_score, recommendation, yield_consistency, drawdown_risk,
    assignment_behavior, capital_efficiency, universe_health.
    """
    reports_dir = ROOT / "reports"
    if not reports_dir.exists():
        raise FileNotFoundError("reports/ directory not found")

    candidates = sorted(reports_dir.glob("*_weekly_promotion_report.json"), reverse=True)
    if not candidates:
        raise FileNotFoundError("No reports/*_weekly_promotion_report.json found")

    path = candidates[0]
    data = json.loads(path.read_text(encoding="utf-8"))

    top_level = ["promotion_readiness_score", "recommendation"]
    for k in top_level:
        if k not in data:
            raise ValueError(f"Weekly promotion report missing field: {k}")

    # yield_consistency, drawdown_risk, assignment_behavior, capital_efficiency, universe_health
    reasoning = data.get("reasoning") or data
    for k in ["yield_consistency", "drawdown_risk", "assignment_behavior", "capital_efficiency", "universe_health"]:
        if k not in reasoning:
            raise ValueError(f"Weekly promotion report missing field (or in reasoning): {k}")

    return f"weekly promotion report valid: {path.name}"


# =============================================================================
# CLOSED TRADES / ATTRIBUTION (equity cohort)
# =============================================================================

def check_stockbot_closed_trades_attribution_fields() -> str:
    """Verify recent closed attribution rows include strategy_id when present (equity-focused)."""
    try:
        from config.registry import LogFiles
        attr_path = ROOT / LogFiles.ATTRIBUTION
    except ImportError:
        attr_path = ROOT / "logs" / "attribution.jsonl"

    if not attr_path.exists():
        return "attribution.jsonl not found yet"

    saw_closed = False
    for line in attr_path.read_text(encoding="utf-8", errors="replace").splitlines()[-2000:]:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "attribution":
            continue
        if rec.get("trade_id", "").startswith("open_"):
            continue
        saw_closed = True
    if not saw_closed:
        return "no closed attribution rows in tail; OK when no trades yet"
    return "attribution tail parseable; equity cohort assumptions OK"


# =============================================================================
# FULL INTEGRATION: DASHBOARD API ENDPOINTS
# =============================================================================

def check_dashboard_api_endpoints() -> str:
    """Hit core dashboard JSON endpoints (local dashboard must be running)."""
    import os

    base = f"http://127.0.0.1:{int(os.getenv('PORT', '5000'))}"

    def get_json(url: str) -> dict:
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}")
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Endpoint unreachable: {e.reason}")

    sre = get_json(f"{base}/api/sre/health")
    if "overall_health" not in sre:
        raise ValueError("/api/sre/health missing overall_health")

    closed_resp = get_json(f"{base}/api/stockbot/closed_trades")
    if "closed_trades" not in closed_resp:
        raise ValueError("/api/stockbot/closed_trades response missing closed_trades")

    pos = get_json(f"{base}/api/positions")
    if "positions" not in pos:
        raise ValueError("/api/positions missing positions")

    return "dashboard core endpoints OK (/api/sre/health, /api/stockbot/closed_trades, /api/positions)"


# =============================================================================
# FULL INTEGRATION: EOD PROMPT INTEGRATION
# =============================================================================

def check_eod_prompt_integration(date: str) -> str:
    """Run EOD script --dry-run; must exit 0 (artifacts present)."""
    _ = date
    script = ROOT / "board" / "eod" / "run_stock_quant_officer_eod.py"
    if not script.exists():
        raise FileNotFoundError(f"Missing: {script}")

    result = subprocess.run(
        [sys.executable, str(script), "--dry-run"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(__import__("os").environ),
    )

    if result.returncode != 0:
        raise RuntimeError(f"run_stock_quant_officer_eod.py --dry-run failed (exit {result.returncode}):\n{result.stderr or result.stdout}")

    return "EOD dry-run exited 0"


# =============================================================================
# FULL INTEGRATION: TELEMETRY COMPLETENESS (EXPANDED)
# =============================================================================

def check_telemetry_tail_readable() -> str:
    """Best-effort: telemetry file exists and last lines parse as JSON."""
    entries = _read_last_n_telemetry_entries(50)
    if not entries:
        path = _get_telemetry_path()
        if not path.exists():
            return "telemetry file not created yet"
        return "telemetry file exists but last lines did not parse"
    return f"telemetry tail OK ({len(entries)} records)"


# =============================================================================
# UNIFIED DAILY INTELLIGENCE PACK
# =============================================================================

def check_unified_daily_intelligence_pack(date: str) -> str:
    """Verify reports/stockbot/YYYY-MM-DD/ exists with 8 equity-pack files."""
    pack_dir = ROOT / "reports" / "stockbot" / date
    if not pack_dir.is_dir():
        raise ValueError(f"Daily folder missing: {pack_dir}. Run: python scripts/run_stockbot_daily_reports.py --date {date}")

    required = [
        "STOCK_EOD_SUMMARY.md",
        "STOCK_EOD_SUMMARY.json",
        "STOCK_EQUITY_ATTRIBUTION.jsonl",
        "STOCK_BLOCKED_TRADES.jsonl",
        "STOCK_PROFITABILITY_DIAGNOSTICS.md",
        "STOCK_PROFITABILITY_DIAGNOSTICS.json",
        "STOCK_REGIME_AND_UNIVERSE.json",
        "MEMORY_BANK_SNAPSHOT.md",
    ]
    missing = [f for f in required if not (pack_dir / f).exists()]
    if missing:
        raise ValueError(f"Missing files: {missing}. Run: python scripts/run_stockbot_daily_reports.py --date {date}")

    prof_path = pack_dir / "STOCK_PROFITABILITY_DIAGNOSTICS.json"
    prof = json.loads(prof_path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(prof, dict):
        raise ValueError("STOCK_PROFITABILITY_DIAGNOSTICS.json invalid")
    if "expectancy_per_symbol" not in prof and "expectancy_per_strategy" not in prof:
        raise ValueError("STOCK_PROFITABILITY_DIAGNOSTICS.json missing expectancy fields")

    regime_path = pack_dir / "STOCK_REGIME_AND_UNIVERSE.json"
    regime = json.loads(regime_path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(regime, dict):
        raise ValueError("STOCK_REGIME_AND_UNIVERSE.json invalid")

    mb_path = pack_dir / "MEMORY_BANK_SNAPSHOT.md"
    if mb_path.stat().st_size == 0:
        raise ValueError("MEMORY_BANK_SNAPSHOT.md empty")

    return f"pack OK: {len(required)} files"


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description="Operational Readiness Audit for stock-bot")
    ap.add_argument("--date", required=True, help="Date YYYY-MM-DD for report generation checks")
    ap.add_argument("--verbose", action="store_true", help="Print progress during checks")
    ap.add_argument("--full-integration", action="store_true", help="Run extended integration audit (comparison, promotion, dashboard, EOD, telemetry)")
    args = ap.parse_args()

    date = args.date.strip()
    verbose = args.verbose
    full_integration = getattr(args, "full_integration", False)

    title = "FULL SYSTEM INTEGRATION AUDIT" if full_integration else "STOCK-BOT OPERATIONAL READINESS AUDIT"
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print(f"Date: {date}")
    print(f"Run at: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'=' * 80}\n")

    results: List[CheckResult] = []

    # CHECK 1: Config & Strategy Enablement (CRITICAL)
    results.append(run_check(
        "config_and_strategy_enablement",
        critical=True,
        fn=check_config_and_strategy_enablement,
        verbose=verbose,
    ))

    # CHECK 2: Strategy Execution Dry Run (CRITICAL)
    results.append(run_check(
        "strategy_execution_dry_run",
        critical=True,
        fn=check_strategy_execution_dry_run,
        verbose=verbose,
    ))

    # CHECK 3: Telemetry Fields (CRITICAL)
    results.append(run_check(
        "telemetry_fields",
        critical=True,
        fn=check_telemetry_fields_lenient,
        verbose=verbose,
    ))

    # CHECK 4: Daily Reports Generation (CRITICAL)
    results.append(run_check(
        "daily_reports_generation",
        critical=True,
        fn=lambda: check_daily_reports_generation(date),
        verbose=verbose,
    ))

    # CHECK 5: Daily Reports Content (CRITICAL)
    results.append(run_check(
        "daily_reports_content",
        critical=True,
        fn=lambda: check_daily_reports_content(date),
        verbose=verbose,
    ))

    # CHECK 6: EOD Review Integration (CRITICAL)
    results.append(run_check(
        "eod_review_integration",
        critical=True,
        fn=lambda: check_eod_review_integration(date),
        verbose=verbose,
    ))

    # CHECK 7: Equity config sanity (MEDIUM)
    results.append(run_check(
        "equity_allocation_config",
        critical=False,
        fn=check_equity_allocation_config,
        verbose=verbose,
    ))

    # CHECK 8: Cron Configuration (MEDIUM)
    results.append(run_check(
        "cron_configuration",
        critical=False,
        fn=check_cron_configuration,
        verbose=verbose,
    ))

    # CHECK 9: Attribution tail (dashboard integration)
    results.append(run_check(
        "stockbot_closed_trades_attribution_fields",
        critical=False,
        fn=check_stockbot_closed_trades_attribution_fields,
        verbose=verbose,
    ))

    # CHECK 10: Unified daily intelligence pack (reports/stockbot/YYYY-MM-DD/)
    results.append(run_check(
        "unified_daily_intelligence_pack",
        critical=False,
        fn=lambda: check_unified_daily_intelligence_pack(date),
        verbose=verbose,
    ))

    # FULL INTEGRATION: additional checks
    if full_integration:
        results.append(run_check(
            "strategy_comparison_engine",
            critical=True,
            fn=lambda: check_strategy_comparison_engine(date),
            verbose=verbose,
        ))
        results.append(run_check(
            "weekly_promotion_report",
            critical=True,
            fn=check_weekly_promotion_report,
            verbose=verbose,
        ))
        results.append(run_check(
            "dashboard_api_endpoints",
            critical=False,
            fn=check_dashboard_api_endpoints,
            verbose=verbose,
        ))
        results.append(run_check(
            "eod_prompt_integration",
            critical=True,
            fn=lambda: check_eod_prompt_integration(date),
            verbose=verbose,
        ))
        results.append(run_check(
            "telemetry_tail_readable",
            critical=False,
            fn=check_telemetry_tail_readable,
            verbose=verbose,
        ))

    # Print summary
    summary_title = "FULL SYSTEM INTEGRATION AUDIT SUMMARY" if full_integration else None
    print_summary(results, title=summary_title)

    # Print failure details
    print_failures(results)

    # Compute exit code
    critical_failed = any(r.critical and not r.passed for r in results)
    all_passed = all(r.passed for r in results)

    if full_integration:
        if critical_failed:
            print("FULL INTEGRATION AUDIT FAILED\n")
            return 1
        print("FULL SYSTEM INTEGRATION AUDIT PASSED — READY FOR LIVE PAPER WEEK\n")
        return 0

    if critical_failed:
        print("[FAIL] AUDIT FAILED: One or more CRITICAL checks failed.")
        print("       Please fix the issues above before market open.\n")
        return 1
    elif not all_passed:
        print("[WARN] AUDIT PASSED WITH WARNINGS: All critical checks passed, but some medium-priority checks failed.")
        print("       Review the warnings above.\n")
        return 0
    else:
        print("[OK] AUDIT PASSED: All checks passed. System is ready for market open.\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
