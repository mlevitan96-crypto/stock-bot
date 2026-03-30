#!/usr/bin/env python3
"""
Telegram failure pager: detect missing or failed expected Telegram / integrity outputs
for Alpaca (post-close, milestones, direction-readiness), dedupe by failure_signature,
alert via Telegram, REMEDIATED on recovery.

Runs on Linux (droplet). Idempotent state in state/telegram_failure_pager_state.json.
Does not relax strict completeness or truth gates; auto-heal hooks are read-only or
existing idempotent refresh scripts only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

STATE_FILE = "telegram_failure_pager_state.json"
AUDIT_JSONL = "alpaca_daily_close_telegram.jsonl"
SYSTEMD_POSTCLOSE = "alpaca-postclose-deepdive.service"

# States matching mission vocabulary
ST_SENT = "SENT"
ST_SEND_FAILED = "SEND_FAILED"
ST_RUNNER_NOT_RUN = "RUNNER_NOT_RUN"
ST_GATED = "GATED"
ST_PENDING = "PENDING"  # before evaluation window
ST_SKIPPED = "SKIPPED"  # weekend / outside calendar
ST_PASS = "PASS"  # direction readiness / integrity OK


@dataclass
class WindowEval:
    window_key: str
    venue: str
    kind: str
    state: str
    session_et: Optional[str]
    root_cause: str
    evidence_slug: str
    auto_heal_status: str = "not_run"
    detail: Dict[str, Any] = field(default_factory=dict)


def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", os.environ.get("DROPLET_TRADING_ROOT", "")).strip()
    return Path(r).resolve() if r else REPO


def _et_zone():
    if ZoneInfo is None:
        raise RuntimeError("zoneinfo required")
    return ZoneInfo("America/New_York")


def session_et_date(now_utc: datetime) -> date:
    return now_utc.astimezone(_et_zone()).date()


def is_weekday_et(d: date) -> bool:
    return d.weekday() < 5


def et_datetime_on(d: date, hour: int, minute: int) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=_et_zone())


def utc_iso_range_for_et_day(d: date) -> Tuple[str, str]:
    """UTC ISO strings for journalctl --since/--until covering ET calendar day d."""
    start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=_et_zone())
    end = start + timedelta(days=1)
    return (
        start.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        end.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


def failure_signature(venue: str, kind: str, session_et: Optional[str], state: str, root_cause: str) -> str:
    raw = f"{venue}|{kind}|{session_et or ''}|{state}|{root_cause}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_jsonl_tail(path: Path, max_lines: int = 500) -> List[dict]:
    if not path.is_file():
        return []
    lines: List[str] = []
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            block = 8192
            while size > 0 and len(lines) < max_lines:
                read = min(block, size)
                size -= read
                f.seek(size)
                chunk = f.read(read).decode("utf-8", errors="replace")
                lines = chunk.splitlines() + lines
        tail = lines[-max_lines:]
    except OSError:
        return []
    out: List[dict] = []
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
            if isinstance(o, dict):
                out.append(o)
        except json.JSONDecodeError:
            continue
    return out


def journalctl_range(unit: str, since: str, until: str) -> str:
    if not Path("/proc").is_dir():
        return ""
    try:
        r = subprocess.run(
            [
                "journalctl",
                "-u",
                unit,
                "--since",
                since,
                "--until",
                until,
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return (r.stdout or "") + (r.stderr or "")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def parse_postclose_journal(text: str) -> Dict[str, Any]:
    """Extract last run hints from journal text."""
    out: Dict[str, Any] = {
        "saw_start": False,
        "exit_code": None,
        "memory_bank_stop": False,
        "telegram_failed": False,
        "dedupe_skip": False,
    }
    if "Starting alpaca-postclose-deepdive.service" in text or "Starting alpaca-postclose" in text:
        out["saw_start"] = True
    m = re.search(r"status=(\d+)/", text) or re.search(
        r"Main process exited, code=\w+, status=(\d+)", text, re.I
    )
    if m:
        try:
            out["exit_code"] = int(m.group(1))
        except ValueError:
            pass
    if "Memory Bank" in text or "canonical markers" in text:
        out["memory_bank_stop"] = True
    if "Telegram send failed" in text or "STOP — Telegram" in text:
        out["telegram_failed"] = True
    if "dedupe_skip" in text:
        out["dedupe_skip"] = True
    if out["exit_code"] is None and "Failed with result" in text:
        out["exit_code"] = 1
    return out


def audit_live_sent_for_session(audit_records: List[dict], session_iso: str) -> bool:
    for o in reversed(audit_records):
        if o.get("session_date_et") != session_iso:
            continue
        if o.get("dry_run") is True:
            continue
        if o.get("dedupe_skip") is True:
            continue
        if o.get("success") is True or o.get("telegram_ok") is True:
            return True
    return False


def audit_dedupe_only_for_session(audit_records: List[dict], session_iso: str) -> bool:
    for o in reversed(audit_records):
        if o.get("session_date_et") != session_iso:
            continue
        if o.get("dedupe_skip") is True:
            return True
    return False


def evaluate_alpaca_post_close(root: Path, now_utc: datetime, journal_fn: Callable[..., str] = journalctl_range) -> WindowEval:
    d_et = session_et_date(now_utc)
    session_iso = d_et.isoformat()
    window_key = "alpaca:post_close"
    evidence = f"reports/{AUDIT_JSONL}+journal:{SYSTEMD_POSTCLOSE}"

    if not is_weekday_et(d_et):
        return WindowEval(
            window_key, "alpaca", "post_close", ST_SKIPPED, session_iso, "weekend_et", evidence
        )

    expect_after = et_datetime_on(d_et, 16, 45)
    if now_utc.astimezone(_et_zone()) < expect_after:
        return WindowEval(
            window_key, "alpaca", "post_close", ST_PENDING, session_iso, "before_expect_window", evidence
        )

    since, until = utc_iso_range_for_et_day(d_et)
    jtext = journal_fn(SYSTEMD_POSTCLOSE, since, until)
    jp = parse_postclose_journal(jtext)

    audit_path = root / "reports" / AUDIT_JSONL
    audit_recs = load_jsonl_tail(audit_path, 800)
    sent_ok = audit_live_sent_for_session(audit_recs, session_iso)

    if sent_ok or audit_dedupe_only_for_session(audit_recs, session_iso):
        return WindowEval(
            window_key,
            "alpaca",
            "post_close",
            ST_SENT,
            session_iso,
            "audit_confirms_live_or_dedupe",
            evidence,
            detail={"journal_excerpt_len": len(jtext)},
        )

    if not jp["saw_start"] and not jtext.strip():
        return WindowEval(
            window_key,
            "alpaca",
            "post_close",
            ST_RUNNER_NOT_RUN,
            session_iso,
            "no_journal_activity_et_day",
            evidence,
            detail={},
        )

    if jp["memory_bank_stop"] or jp["exit_code"] not in (None, 0):
        rc = jp["exit_code"]
        return WindowEval(
            window_key,
            "alpaca",
            "post_close",
            ST_SEND_FAILED,
            session_iso,
            "memory_bank_or_nonzero_exit" if jp["memory_bank_stop"] else f"exit_code_{rc}",
            evidence,
            detail={"parsed": jp},
        )

    if jp["telegram_failed"]:
        return WindowEval(
            window_key,
            "alpaca",
            "post_close",
            ST_SEND_FAILED,
            session_iso,
            "telegram_http_or_send_failed",
            evidence,
            detail={"parsed": jp},
        )

    # Ran but no success in audit — treat as send failed / incomplete
    return WindowEval(
        window_key,
        "alpaca",
        "post_close",
        ST_SEND_FAILED,
        session_iso,
        "runner_finished_without_live_telegram_audit",
        evidence,
        detail={"parsed": jp, "journal_len": len(jtext)},
    )


def evaluate_alpaca_milestone(root: Path, now_utc: datetime) -> WindowEval:
    d_et = session_et_date(now_utc)
    session_iso = d_et.isoformat()
    window_key = "alpaca:milestone"
    primary = root / "logs" / "alpaca_telegram_integrity.log"
    legacy = root / "logs" / "notify_milestones.log"
    log_path = primary if primary.is_file() else legacy
    evidence = (
        "logs/alpaca_telegram_integrity.log"
        if primary.is_file()
        else "logs/notify_milestones.log"
    )

    now_u = now_utc.astimezone(timezone.utc)
    if now_u.weekday() >= 5:
        return WindowEval(window_key, "alpaca", "milestone", ST_SKIPPED, session_iso, "weekend_utc", evidence)

    # Align with install_cron_alpaca_notifier.py: */10 during hours 13–21 UTC Mon–Fri (cron `13-21` is inclusive).
    if not (13 <= now_u.hour <= 21):
        return WindowEval(window_key, "alpaca", "milestone", ST_PENDING, session_iso, "outside_13_21_utc", evidence)

    if not log_path.is_file():
        return WindowEval(
            window_key, "alpaca", "milestone", ST_RUNNER_NOT_RUN, session_iso, "log_missing", evidence
        )

    try:
        mtime = datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        mtime = datetime.min.replace(tzinfo=timezone.utc)

    age_min = (now_utc - mtime).total_seconds() / 60.0
    if age_min > 45:
        return WindowEval(
            window_key,
            "alpaca",
            "milestone",
            ST_RUNNER_NOT_RUN,
            session_iso,
            "log_stale_over_45m",
            evidence,
            detail={"age_minutes": round(age_min, 1)},
        )

    try:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-8000:]
    except OSError:
        tail = ""

    if "Traceback" in tail or "Error sending Telegram" in tail:
        return WindowEval(
            window_key,
            "alpaca",
            "milestone",
            ST_SEND_FAILED,
            session_iso,
            "log_contains_traceback_or_telegram_error",
            evidence,
        )

    return WindowEval(
        window_key, "alpaca", "milestone", ST_SENT, session_iso, "log_fresh_no_error", evidence, detail={"age_minutes": round(age_min, 1)}
    )


def evaluate_alpaca_direction_readiness(root: Path, now_utc: datetime) -> WindowEval:
    """Alpaca direction-readiness integrity (state/direction_readiness.json); pages if artifact stale."""
    d_et = session_et_date(now_utc)
    session_iso = d_et.isoformat()
    window_key = "alpaca:direction_readiness"
    artifact = root / "state" / "direction_readiness.json"
    log_path = root / "logs" / "direction_readiness_cron.log"
    evidence = "state/direction_readiness.json+logs/direction_readiness_cron.log"

    if not is_weekday_et(d_et):
        return WindowEval(window_key, "alpaca", "direction_readiness", ST_SKIPPED, session_iso, "weekend_et", evidence)

    now_utc_hour = now_utc.astimezone(timezone.utc).hour
    if not (9 <= now_utc_hour < 22):
        return WindowEval(
            window_key, "alpaca", "direction_readiness", ST_PENDING, session_iso, "outside_9_21_utc", evidence
        )

    if not artifact.is_file():
        return WindowEval(
            window_key,
            "alpaca",
            "direction_readiness",
            ST_RUNNER_NOT_RUN,
            session_iso,
            "direction_readiness_missing",
            evidence,
        )

    try:
        mtime = datetime.fromtimestamp(artifact.stat().st_mtime, tz=timezone.utc)
    except OSError:
        mtime = datetime.min.replace(tzinfo=timezone.utc)

    age_min = (now_utc - mtime).total_seconds() / 60.0
    if age_min > 90:
        return WindowEval(
            window_key,
            "alpaca",
            "direction_readiness",
            ST_GATED,
            session_iso,
            "artifact_stale_over_90m",
            evidence,
            detail={"age_minutes": round(age_min, 1)},
        )

    # Primary signal is direction_readiness.json. Cron log is supplementary; auto-heal and manual
    # runs refresh the JSON without appending direction_readiness_cron.log — stale log alone must not page.
    detail: Dict[str, Any] = {"artifact_age_minutes": round(age_min, 1)}
    if log_path.is_file():
        try:
            lm = datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc)
            log_age = (now_utc - lm).total_seconds() / 60.0
            detail["log_age_minutes"] = round(log_age, 1)
            if log_age > 90:
                detail["cron_log_stale_operational_warn"] = True
        except OSError:
            detail["cron_log_stale_operational_warn"] = True

    return WindowEval(
        window_key,
        "alpaca",
        "direction_readiness",
        ST_PASS,
        session_iso,
        "freshness_ok",
        evidence,
        detail=detail,
    )


def _auto_heal_alpaca_milestone(root: Path) -> str:
    """Run milestone notifier like cron (source .alpaca_env on droplet); append output to notify_milestones.log."""
    log_path = root / "logs" / "notify_milestones.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    script = root / "scripts" / "run_alpaca_telegram_integrity_cycle.py"
    if not script.is_file():
        return "integrity_cycle_script_missing"
    stamp = datetime.now(timezone.utc).isoformat()
    header = f"\n--- telegram_failure_detector auto_heal {stamp} ---\n"
    root_q = shlex.quote(str(root))
    py_q = shlex.quote(sys.executable)
    scr_q = shlex.quote(str(script))
    alpaca_env = Path("/root/.alpaca_env")
    try:
        with open(log_path, "a", encoding="utf-8") as logf:
            logf.write(header)
            if os.name != "nt" and alpaca_env.is_file():
                inner = (
                    f"cd {root_q} && set -a && . {shlex.quote(str(alpaca_env))} && set +a 2>/dev/null; "
                    f"export PYTHONPATH={root_q} && {py_q} {scr_q} --skip-warehouse --no-self-heal"
                )
                try:
                    r = subprocess.run(
                        ["bash", "-lc", inner],
                        stdout=logf,
                        stderr=subprocess.STDOUT,
                        timeout=180,
                        text=True,
                    )
                    return f"milestone_run_exit_{r.returncode}"
                except FileNotFoundError:
                    pass
            env = {**os.environ, "PYTHONPATH": str(root)}
            r = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--skip-warehouse",
                    "--no-self-heal",
                ],
                cwd=str(root),
                stdout=logf,
                stderr=subprocess.STDOUT,
                timeout=180,
                text=True,
                env=env,
            )
            return f"milestone_run_exit_{r.returncode}"
    except (subprocess.TimeoutExpired, OSError) as e:
        return f"milestone_heal_failed:{e}"


def _auto_heal_direction_readiness(root: Path) -> str:
    script = root / "scripts" / "governance" / "check_direction_readiness_and_run.py"
    if not script.is_file():
        return "direction_readiness_script_missing"
    try:
        r = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300,
        )
        return f"direction_readiness_exit_{r.returncode}"
    except (subprocess.TimeoutExpired, OSError) as e:
        return f"direction_readiness_heal_failed:{e}"


def run_auto_heal(root: Path, venue: str, kind: str) -> str:
    """Venue-specific safe refresh; does not disable gates."""
    if venue == "alpaca" and kind == "milestone":
        return _auto_heal_alpaca_milestone(root)
    if venue == "alpaca" and kind == "direction_readiness":
        return _auto_heal_direction_readiness(root)
    if venue == "alpaca" and kind == "post_close":
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(root / "telemetry" / "alpaca_strict_completeness_gate.py"),
                    "--root",
                    str(root),
                    "--audit",
                ],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            return f"alpaca_audit_invocation_failed:{e}"
        return "alpaca_strict_audit_ran"
    return "no_heal"


def _load_state(path: Path) -> dict:
    if not path.is_file():
        return {"version": 1, "windows": {}, "signatures_alerted": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "windows": {}, "signatures_alerted": {}}


def _save_state(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _send_page(text: str, dry_run: bool) -> bool:
    if dry_run:
        print("--- PAGE (dry-run) ---\n", text, "\n---", flush=True)
        return True
    try:
        from scripts.alpaca_telegram import send_governance_telegram

        return send_governance_telegram(text, script_name="telegram_failure_detector")
    except Exception as e:
        print(f"send_failed:{e}", file=sys.stderr)
        return False


def run_cycle(
    root: Path,
    now_utc: Optional[datetime] = None,
    *,
    dry_run: bool = False,
    skip_auto_heal: bool = False,
    journal_fn: Callable[..., str] = journalctl_range,
) -> List[WindowEval]:
    if ZoneInfo is None:
        raise RuntimeError("zoneinfo required (Python 3.9+)")
    now_utc = now_utc or datetime.now(timezone.utc)

    evals = [
        evaluate_alpaca_post_close(root, now_utc, journal_fn=journal_fn),
        evaluate_alpaca_milestone(root, now_utc),
        evaluate_alpaca_direction_readiness(root, now_utc),
    ]

    state_path = root / "state" / STATE_FILE
    st = _load_state(state_path)

    for ev in evals:
        if ev.state in (ST_SKIPPED, ST_PENDING):
            continue

        ok_pass = ev.state in (ST_SENT, ST_PASS)
        sig = failure_signature(ev.venue, ev.kind, ev.session_et, ev.state, ev.root_cause)

        prev = st["windows"].get(ev.window_key, {})
        prev_state = prev.get("last_state")
        prev_sig_alerted = prev.get("last_signature_alerted")

        if not ok_pass and ev.state in (ST_SEND_FAILED, ST_RUNNER_NOT_RUN, ST_GATED):
            if not skip_auto_heal:
                ev.auto_heal_status = run_auto_heal(root, ev.venue, ev.kind)
                if ev.window_key == "alpaca:post_close":
                    ev2 = evaluate_alpaca_post_close(root, now_utc, journal_fn=journal_fn)
                    ev.state = ev2.state
                    ev.root_cause = ev2.root_cause
                    ev.detail = {**ev.detail, "post_heal": ev2.detail}
                    sig = failure_signature(ev.venue, ev.kind, ev.session_et, ev.state, ev.root_cause)
                elif ev.window_key == "alpaca:direction_readiness":
                    ev2 = evaluate_alpaca_direction_readiness(root, now_utc)
                    ev.state = ev2.state
                    ev.root_cause = ev2.root_cause
                    ev.detail = {**ev.detail, "post_heal": ev2.detail}
                    sig = failure_signature(ev.venue, ev.kind, ev.session_et, ev.state, ev.root_cause)
                elif ev.window_key == "alpaca:milestone":
                    ev2 = evaluate_alpaca_milestone(root, now_utc)
                    ev.state = ev2.state
                    ev.root_cause = ev2.root_cause
                    ev.detail = {**ev.detail, "post_heal": ev2.detail}
                    sig = failure_signature(ev.venue, ev.kind, ev.session_et, ev.state, ev.root_cause)

            ok_pass = ev.state in (ST_SENT, ST_PASS)

        if ok_pass:
            if prev_state and prev_state not in (ST_SENT, ST_PASS, ST_SKIPPED, ST_PENDING):
                remed_body = (
                    "TELEGRAM FAILURE PAGER — REMEDIATED\n"
                    f"venue={ev.venue} kind={ev.kind} session_et={ev.session_et}\n"
                    f"previous_state={prev_state} now={ev.state}\n"
                    f"evidence={ev.evidence_slug}\n"
                )
                _send_page(remed_body, dry_run)
            st["windows"][ev.window_key] = {
                "last_state": ev.state,
                "last_session_et": ev.session_et,
                "last_signature_alerted": None,
                "last_root_cause": ev.root_cause,
                "updated_utc": now_utc.isoformat(),
            }
            if prev_sig_alerted:
                st["signatures_alerted"].pop(prev_sig_alerted, None)
            continue

        alerted_sigs: Dict[str, Any] = st["signatures_alerted"]
        if sig in alerted_sigs:
            st["windows"][ev.window_key] = {
                "last_state": ev.state,
                "last_session_et": ev.session_et,
                "last_signature_alerted": sig,
                "last_root_cause": ev.root_cause,
                "updated_utc": now_utc.isoformat(),
            }
            continue

        body = (
            "TELEGRAM FAILURE PAGER — ALERT\n"
            f"venue={ev.venue}\n"
            f"expected_output={ev.kind}\n"
            f"state={ev.state}\n"
            f"session_et={ev.session_et}\n"
            f"root_cause={ev.root_cause}\n"
            f"auto_heal={ev.auto_heal_status}\n"
            f"evidence={ev.evidence_slug}\n"
            f"failure_signature={sig[:16]}…\n"
        )
        _send_page(body, dry_run)
        alerted_sigs[sig] = {
            "window_key": ev.window_key,
            "first_at_utc": now_utc.isoformat(),
            "session_et": ev.session_et,
        }
        st["windows"][ev.window_key] = {
            "last_state": ev.state,
            "last_session_et": ev.session_et,
            "last_signature_alerted": sig,
            "last_root_cause": ev.root_cause,
            "updated_utc": now_utc.isoformat(),
        }

    _save_state(state_path, st)
    return evals


def main() -> int:
    ap = argparse.ArgumentParser(description="Telegram failure detector / pager")
    ap.add_argument("--dry-run", action="store_true", help="No Telegram HTTP; print only")
    ap.add_argument("--no-auto-heal", action="store_true", help="Skip heal hooks")
    ap.add_argument("--json-out", type=Path, default=None, help="Write last eval summary JSON")
    args = ap.parse_args()
    root = _root()
    os.chdir(root)
    try:
        evals = run_cycle(root, dry_run=args.dry_run, skip_auto_heal=args.no_auto_heal)
    except Exception as e:
        print(f"detector_fatal:{e}", file=sys.stderr)
        return 1
    summary = [
        {
            "window_key": e.window_key,
            "venue": e.venue,
            "kind": e.kind,
            "state": e.state,
            "session_et": e.session_et,
            "root_cause": e.root_cause,
            "signature": failure_signature(e.venue, e.kind, e.session_et, e.state, e.root_cause),
        }
        for e in evals
    ]
    print(json.dumps(summary, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
