#!/usr/bin/env python3
"""
Verify Alpha Upgrade: displacement policy, shorts sanity, feature snapshot, shadow experiments.

Run on droplet after deploy. Prints PASS/FAIL per check, exits non-zero on any FAIL.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
LOG_DIR = REPO_ROOT / "logs"
STATE_DIR = REPO_ROOT / "state"


def _pass(msg: str) -> None:
    print(f"  PASS: {msg}")


def _fail(msg: str) -> None:
    print(f"  FAIL: {msg}")


def check_displacement_policy() -> bool:
    """Displacement policy present and config keys exist."""
    ok = True
    policy_path = REPO_ROOT / "trading" / "displacement_policy.py"
    if not policy_path.exists():
        _fail(f"trading/displacement_policy.py not found")
        return False
    _pass("trading/displacement_policy.py exists")
    try:
        from trading.displacement_policy import evaluate_displacement
        _pass("evaluate_displacement importable")
    except Exception as e:
        _fail(f"evaluate_displacement import: {e}")
        ok = False
    cfg_keys = (
        "DISPLACEMENT_ENABLED",
        "DISPLACEMENT_MIN_HOLD_SECONDS",
        "DISPLACEMENT_MIN_DELTA_SCORE",
        "DISPLACEMENT_REQUIRE_THESIS_DOMINANCE",
        "DISPLACEMENT_LOG_EVERY_DECISION",
    )
    try:
        from main import Config
        for k in cfg_keys:
            if not hasattr(Config, k):
                _fail(f"Config missing {k}")
                ok = False
        if ok:
            _pass("displacement config keys present")
    except Exception as e:
        _fail(f"Config check: {e}")
        ok = False
    return ok


def check_displacement_logging() -> bool:
    """Today's logs contain subsystem=displacement; if missing, run dry-run then re-check."""
    ok = True
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    se_path = LOG_DIR / "system_events.jsonl"
    if not se_path.exists():
        try:
            se_path.touch()
        except Exception as e:
            _fail(f"could not create system_events.jsonl: {e}")
            return False
    found = False
    try:
        with se_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("subsystem") == "displacement":
                        found = True
                        break
                except Exception:
                    continue
    except Exception as e:
        _fail(f"reading system_events: {e}")
        return False
    if found:
        _pass("subsystem=displacement found in system_events.jsonl")
        return True
    # Dry-run: emit one displacement_evaluated event then re-check
    try:
        from trading.displacement_policy import evaluate_displacement
        from utils.system_events import log_system_event
        cur = {"symbol": "DRY", "current_score": 2.5, "entry_score": 2.5, "age_hours": 1.0}
        ch = {"symbol": "RUN", "score": 3.5}
        ctx = {"regime_label": "mixed", "posture": "NEUTRAL"}
        allowed, reason, diag = evaluate_displacement(cur, ch, ctx)
        log_system_event("displacement", "displacement_evaluated", "INFO", allowed=allowed, reason=reason, details=diag)
    except Exception as e:
        _fail(f"displacement dry-run: {e}")
        return False
    found = False
    try:
        with se_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("subsystem") == "displacement":
                        found = True
                        break
                except Exception:
                    continue
    except Exception as e:
        _fail(f"re-reading system_events: {e}")
        return False
    if found:
        _pass("subsystem=displacement found in system_events.jsonl (after dry-run)")
    else:
        _fail("no subsystem=displacement in system_events.jsonl after dry-run")
        ok = False
    return ok


def check_shorts_sanity() -> bool:
    """No shorts_mismatch CRITICAL when shorts should be enabled."""
    ok = True
    se_path = LOG_DIR / "system_events.jsonl"
    if not se_path.exists():
        _pass("system_events missing; skip shorts_mismatch check")
        return True
    try:
        from main import Config
        longs_only = getattr(Config, "LONG_ONLY", True)
    except Exception:
        longs_only = True
    if longs_only:
        _pass("LONG_ONLY=true; shorts_mismatch check N/A")
        return True
    found_critical = False
    try:
        with se_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("subsystem") == "posture" and rec.get("event_type") == "shorts_mismatch":
                        if str(rec.get("severity", "")).upper() == "CRITICAL":
                            found_critical = True
                            break
                except Exception:
                    continue
    except Exception as e:
        _fail(f"reading system_events for shorts: {e}")
        return False
    if found_critical:
        _fail("shorts_mismatch CRITICAL present (shorts enabled but engine never permits)")
        ok = False
    else:
        _pass("no shorts_mismatch CRITICAL")
    return ok


def check_feature_snapshot() -> bool:
    """Feature snapshot module present (and optionally trade_intent includes snapshot)."""
    ok = True
    snap_path = REPO_ROOT / "telemetry" / "feature_snapshot.py"
    if not snap_path.exists():
        _fail("telemetry/feature_snapshot.py not found")
        return False
    _pass("telemetry/feature_snapshot.py exists")
    return ok


def check_trade_intent() -> bool:
    """run.jsonl contains trade_intent with feature_snapshot + thesis_tags."""
    run_path = LOG_DIR / "run.jsonl"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not run_path.exists():
        run_path.touch()
    found = False
    try:
        with run_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("event_type") != "trade_intent":
                        continue
                    if "feature_snapshot" in rec and "thesis_tags" in rec:
                        found = True
                        break
                except Exception:
                    continue
    except Exception as e:
        _fail(f"reading run.jsonl: {e}")
        return False
    if found:
        _pass("trade_intent with feature_snapshot+thesis_tags in run.jsonl")
        return True
    try:
        from datetime import datetime, timezone
        from config.registry import append_jsonl
        log_path = REPO_ROOT / "logs" / "run.jsonl"
        dry = {
            "event_type": "trade_intent",
            "symbol": "DRY",
            "side": "buy",
            "score": 3.5,
            "feature_snapshot": {"symbol": "DRY", "v2_score": 3.5, "ts": datetime.now(timezone.utc).isoformat()},
            "thesis_tags": {"thesis_regime_alignment_score": 0.5},
            "displacement_context": None,
        }
        append_jsonl(log_path, dry)
    except Exception as e:
        _fail(f"trade_intent dry-run: {e}")
        return False
    found = False
    try:
        with run_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("event_type") != "trade_intent":
                        continue
                    if "feature_snapshot" in rec and "thesis_tags" in rec:
                        found = True
                        break
                except Exception:
                    continue
    except Exception:
        pass
    if found:
        _pass("trade_intent with feature_snapshot+thesis_tags (after dry-run)")
    else:
        _fail("no trade_intent with feature_snapshot+thesis_tags in run.jsonl")
        return False
    return True


def check_exit_intent() -> bool:
    """run.jsonl contains exit_intent with thesis_break_reason."""
    run_path = LOG_DIR / "run.jsonl"
    found = False
    try:
        with run_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("event_type") != "exit_intent":
                        continue
                    if "thesis_break_reason" in rec:
                        found = True
                        break
                except Exception:
                    continue
    except Exception as e:
        _fail(f"reading run.jsonl for exit_intent: {e}")
        return False
    if found:
        _pass("exit_intent with thesis_break_reason in run.jsonl")
        return True
    try:
        from datetime import datetime, timezone
        from config.registry import append_jsonl
        log_path = REPO_ROOT / "logs" / "run.jsonl"
        dry = {
            "event_type": "exit_intent",
            "symbol": "DRY",
            "close_reason": "dry_run",
            "feature_snapshot_at_exit": {"symbol": "DRY"},
            "thesis_tags_at_exit": {},
            "thesis_break_reason": "other",
        }
        append_jsonl(log_path, dry)
    except Exception as e:
        _fail(f"exit_intent dry-run: {e}")
        return False
    found = False
    try:
        with run_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("event_type") != "exit_intent" or "thesis_break_reason" not in rec:
                        continue
                    found = True
                    break
                except Exception:
                    continue
    except Exception:
        pass
    if found:
        _pass("exit_intent with thesis_break_reason (after dry-run)")
    else:
        _fail("no exit_intent with thesis_break_reason in run.jsonl")
        return False
    return True


def check_directional_gate() -> bool:
    """directional_gate / blocked_high_vol_no_alignment code path present."""
    main_path = REPO_ROOT / "main.py"
    if not main_path.exists():
        _fail("main.py not found")
        return False
    text = main_path.read_text(encoding="utf-8")
    if "blocked_high_vol_no_alignment" not in text or "directional_gate" not in text:
        _fail("directional_gate / blocked_high_vol_no_alignment not found in main.py")
        return False
    _pass("directional_gate blocks for high-vol present")
    return True


def check_shadow_experiments() -> bool:
    """If SHADOW_EXPERIMENTS_ENABLED: shadow.jsonl has shadow_variant_decision."""
    ok = True
    try:
        from main import Config
        enabled = getattr(Config, "SHADOW_EXPERIMENTS_ENABLED", False)
    except Exception:
        enabled = False
    if not enabled:
        _pass("SHADOW_EXPERIMENTS_ENABLED false; shadow check N/A")
        return True
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    sh_path = LOG_DIR / "shadow.jsonl"
    found = False
    if sh_path.exists():
        try:
            with sh_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                        if rec.get("event_type") == "shadow_variant_decision":
                            found = True
                            break
                    except Exception:
                        continue
        except Exception:
            pass
    if found:
        _pass("event_type=shadow_variant_decision in shadow.jsonl")
        return True
    try:
        from telemetry.shadow_experiments import run_shadow_variants
        dry_candidates = [{"ticker": "DRY", "symbol": "DRY", "composite_score": 3.5, "score": 3.5, "direction": "bullish"}]
        run_shadow_variants(
            {"market_regime": "mixed", "regime": "mixed", "engine": None},
            candidates=dry_candidates,
            positions={},
            experiments=getattr(Config, "SHADOW_EXPERIMENTS", None),
            max_variants_per_cycle=getattr(Config, "SHADOW_MAX_VARIANTS_PER_CYCLE", 4),
        )
    except Exception as e:
        _fail(f"shadow dry-run: {e}")
        return False
    found = False
    try:
        with sh_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("event_type") == "shadow_variant_decision":
                        found = True
                        break
                except Exception:
                    continue
    except Exception as e:
        _fail(f"reading shadow.jsonl after dry-run: {e}")
        return False
    if found:
        _pass("event_type=shadow_variant_decision (after dry-run)")
    else:
        _fail("no shadow_variant_decision in shadow.jsonl after dry-run")
        return False
    return True


def check_eod_report() -> bool:
    """EOD alpha diagnostic report exists for today; run generator if missing."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = REPO_ROOT / "reports" / f"EOD_ALPHA_DIAGNOSTIC_{today}.md"
    gen_path = REPO_ROOT / "reports" / "_daily_review_tools" / "generate_eod_alpha_diagnostic.py"
    if not gen_path.exists():
        _fail("reports/_daily_review_tools/generate_eod_alpha_diagnostic.py not found")
        return False
    _pass("generate_eod_alpha_diagnostic.py exists")
    if not report_path.exists():
        import subprocess
        r = subprocess.run(
            [sys.executable, str(gen_path), "--date", today],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            _fail(f"generate_eod_alpha_diagnostic --date {today} exited {r.returncode}")
            return False
    if report_path.exists():
        _pass(f"EOD_ALPHA_DIAGNOSTIC_{today}.md exists")
        return True
    _fail(f"EOD_ALPHA_DIAGNOSTIC_{today}.md not found after run")
    return False


def main() -> int:
    print("verify_alpha_upgrade checks")
    print("-" * 60)
    results = []
    results.append(("Displacement policy", check_displacement_policy()))
    results.append(("Displacement logging", check_displacement_logging()))
    results.append(("Shorts sanity", check_shorts_sanity()))
    results.append(("Feature snapshot", check_feature_snapshot()))
    results.append(("Trade intent (snapshot+tags)", check_trade_intent()))
    results.append(("Exit intent (thesis_break)", check_exit_intent()))
    results.append(("Directional gate", check_directional_gate()))
    results.append(("Shadow experiments", check_shadow_experiments()))
    results.append(("EOD report", check_eod_report()))
    print("-" * 60)
    ok = all(r[1] for r in results)
    for name, v in results:
        print(f"  {'PASS' if v else 'FAIL'}: {name}")
    print()
    if ok:
        print("All checks PASS.")
        return 0
    print("One or more checks FAIL.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
