"""Tests for scripts/governance/telegram_failure_detector.py"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.governance.telegram_failure_detector import (
    ST_GATED,
    ST_PASS,
    ST_PENDING,
    ST_RUNNER_NOT_RUN,
    ST_SEND_FAILED,
    ST_SENT,
    ST_SKIPPED,
    audit_live_sent_for_session,
    evaluate_alpaca_milestone,
    evaluate_alpaca_post_close,
    evaluate_alpaca_direction_readiness,
    failure_signature,
    parse_postclose_journal,
    run_cycle,
)


def test_parse_postclose_journal_status():
    text = """
Mar 27 20:30:06 host systemd[1]: Starting alpaca-postclose-deepdive.service
Mar 27 20:30:06 host python3[1]: STOP — Memory Bank: canonical markers missing
Mar 27 20:30:06 host systemd[1]: alpaca-postclose-deepdive.service: Main process exited, code=exited, status=4/NOPERMISSION
Mar 27 20:30:06 host systemd[1]: Failed to start alpaca-postclose-deepdive.service
"""
    p = parse_postclose_journal(text)
    assert p["saw_start"]
    assert p["exit_code"] == 4
    assert p["memory_bank_stop"]


def test_failure_signature_stable():
    a = failure_signature("alpaca", "post_close", "2026-03-27", ST_SEND_FAILED, "memory_bank")
    b = failure_signature("alpaca", "post_close", "2026-03-27", ST_SEND_FAILED, "memory_bank")
    assert a == b
    c = failure_signature("alpaca", "post_close", "2026-03-27", ST_RUNNER_NOT_RUN, "memory_bank")
    assert a != c


def test_audit_live_sent_for_session():
    recs = [
        {"session_date_et": "2026-03-27", "dry_run": True, "telegram_ok": False},
        {"session_date_et": "2026-03-27", "dry_run": False, "telegram_ok": True, "success": True},
    ]
    assert audit_live_sent_for_session(recs, "2026-03-27") is True


def test_evaluate_alpaca_post_close_weekend():
    root = Path("/tmp")
    sat = datetime(2026, 3, 28, 18, 0, tzinfo=timezone.utc)  # Saturday ET
    ev = evaluate_alpaca_post_close(root, sat, journal_fn=lambda *a, **k: "")
    assert ev.state == ST_SKIPPED


def test_evaluate_alpaca_post_close_runner_not_run(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / "reports").mkdir()
    # Monday 2026-03-30 17:00 ET = 21:00 UTC
    now = datetime(2026, 3, 30, 21, 0, tzinfo=timezone.utc)
    ev = evaluate_alpaca_post_close(root, now, journal_fn=lambda *a, **k: "")
    assert ev.state == ST_RUNNER_NOT_RUN


def test_evaluate_alpaca_post_close_sent_via_audit(tmp_path: Path):
    root = tmp_path
    rep = root / "reports"
    rep.mkdir()
    audit = rep / "alpaca_daily_close_telegram.jsonl"
    audit.write_text(
        json.dumps(
            {
                "session_date_et": "2026-03-30",
                "dry_run": False,
                "telegram_ok": True,
                "success": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    now = datetime(2026, 3, 30, 21, 0, tzinfo=timezone.utc)
    ev = evaluate_alpaca_post_close(root, now, journal_fn=lambda *a, **k: "noise")
    assert ev.state == ST_SENT


def test_evaluate_direction_readiness_pending_utc_hour(tmp_path: Path):
    root = tmp_path
    (root / "state").mkdir()
    # Weekday but 04 UTC -> outside 9-21
    now = datetime(2026, 3, 30, 4, 0, tzinfo=timezone.utc)
    ev = evaluate_alpaca_direction_readiness(root, now)
    assert ev.state == ST_PENDING


def test_run_cycle_send_failed_then_remediate(tmp_path: Path, monkeypatch):
    import scripts.governance.telegram_failure_detector as det

    root = tmp_path
    (root / "reports").mkdir()
    (root / "state").mkdir()
    (root / "logs").mkdir()
    pages: list[str] = []

    def fake_send(text: str, dry_run: bool) -> bool:
        pages.append(text)
        return True

    monkeypatch.setattr(det, "_send_page", fake_send)

    journal = ""
    now = datetime(2026, 3, 30, 21, 0, tzinfo=timezone.utc)

    run_cycle(
        root,
        now,
        dry_run=True,
        skip_auto_heal=True,
        journal_fn=lambda *a, **k: journal,
    )
    assert any("ALERT" in p for p in pages)

    pages.clear()
    audit = root / "reports" / "alpaca_daily_close_telegram.jsonl"
    audit.write_text(
        json.dumps(
            {
                "session_date_et": "2026-03-30",
                "telegram_ok": True,
                "success": True,
                "dry_run": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    # Satisfy other windows so remediation is attributable to alpaca post_close.
    (root / "logs" / "notify_milestones.log").write_text("ok\n", encoding="utf-8")
    (root / "state" / "direction_readiness.json").write_text("{}", encoding="utf-8")
    run_cycle(
        root,
        now,
        dry_run=True,
        skip_auto_heal=True,
        journal_fn=lambda *a, **k: "start",
    )
    assert any("REMEDIATED" in p for p in pages)


def test_run_cycle_dedup_same_signature(tmp_path: Path, monkeypatch):
    import scripts.governance.telegram_failure_detector as det

    root = tmp_path
    (root / "reports").mkdir()
    (root / "state").mkdir()
    (root / "logs").mkdir()
    calls: list[str] = []

    def fake_send(text: str, dry_run: bool) -> bool:
        calls.append(text)
        return True

    monkeypatch.setattr(det, "_send_page", fake_send)
    now = datetime(2026, 3, 30, 21, 0, tzinfo=timezone.utc)
    run_cycle(root, now, dry_run=True, skip_auto_heal=True, journal_fn=lambda *a, **k: "")
    first = len(calls)
    run_cycle(root, now, dry_run=True, skip_auto_heal=True, journal_fn=lambda *a, **k: "")
    assert len(calls) == first


def test_evaluate_alpaca_milestone_gated_stale_log(tmp_path: Path):
    if sys.platform == "win32":
        pytest.skip("mtime backdating unreliable on Windows tmp for this assertion")
    root = tmp_path
    logd = root / "logs"
    logd.mkdir(parents=True)
    log = logd / "alpaca_telegram_integrity.log"
    log.write_text("ok\n", encoding="utf-8")
    old = time.time() - 5000
    os.utime(log, (old, old))
    now = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc)  # Mon, 15 UTC in 13-21
    ev = evaluate_alpaca_milestone(root, now)
    assert ev.state == ST_RUNNER_NOT_RUN
    assert "stale" in ev.root_cause


def test_evaluate_direction_readiness_gated_stale(tmp_path: Path):
    if sys.platform == "win32":
        pytest.skip("mtime backdating unreliable on Windows tmp for this assertion")
    root = tmp_path
    st = root / "state"
    st.mkdir(parents=True)
    p = st / "direction_readiness.json"
    p.write_text("{}", encoding="utf-8")
    old = time.time() - 8000
    os.utime(p, (old, old))
    now = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc)
    ev = evaluate_alpaca_direction_readiness(root, now)
    assert ev.state == ST_GATED


def test_evaluate_direction_readiness_pass_fresh(tmp_path: Path):
    root = tmp_path
    st = root / "state"
    st.mkdir(parents=True)
    p = st / "direction_readiness.json"
    p.write_text('{"ready":false}', encoding="utf-8")
    (root / "logs").mkdir(exist_ok=True)
    lp = root / "logs" / "direction_readiness_cron.log"
    lp.write_text("tick\n", encoding="utf-8")
    now = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc)
    ts = now.timestamp()
    os.utime(p, (ts, ts))
    os.utime(lp, (ts, ts))
    ev = evaluate_alpaca_direction_readiness(root, now)
    assert ev.state == ST_PASS


def test_evaluate_direction_readiness_pass_artifact_fresh_cron_log_stale(tmp_path: Path):
    """JSON is source of truth; stale direction_readiness_cron.log must not fail (auto-heal updates JSON only)."""
    if sys.platform == "win32":
        pytest.skip("mtime backdating unreliable on Windows tmp for this assertion")
    root = tmp_path
    st = root / "state"
    st.mkdir(parents=True)
    p = st / "direction_readiness.json"
    p.write_text('{"ready":false}', encoding="utf-8")
    (root / "logs").mkdir(exist_ok=True)
    lp = root / "logs" / "direction_readiness_cron.log"
    lp.write_text("old cron\n", encoding="utf-8")
    now = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc)
    os.utime(p, (now.timestamp(), now.timestamp()))
    os.utime(lp, (time.time() - 8000, time.time() - 8000))
    ev = evaluate_alpaca_direction_readiness(root, now)
    assert ev.state == ST_PASS
    assert ev.detail.get("cron_log_stale_operational_warn") is True


def test_evaluate_alpaca_milestone_active_hour_21_utc(tmp_path: Path):
    root = tmp_path
    logd = root / "logs"
    logd.mkdir(parents=True)
    log = logd / "alpaca_telegram_integrity.log"
    log.write_text("ok\n", encoding="utf-8")
    now = datetime(2026, 3, 30, 21, 15, tzinfo=timezone.utc)
    os.utime(log, (now.timestamp(), now.timestamp()))
    ev = evaluate_alpaca_milestone(root, now)
    assert ev.state == ST_SENT
