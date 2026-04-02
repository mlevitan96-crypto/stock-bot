"""Post-close Telegram behavior under TELEGRAM_GOVERNANCE_INTEGRITY_ONLY (droplet unit)."""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def repo_root(monkeypatch):
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root)
    if str(root) not in sys.path:
        monkeypatch.syspath_prepend(str(root))


def test_send_telegram_skips_when_integrity_only(repo_root, monkeypatch):
    monkeypatch.setenv("TELEGRAM_GOVERNANCE_INTEGRITY_ONLY", "1")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    from scripts.alpaca_postclose_deepdive import _send_telegram

    ok, suppressed = _send_telegram("body", dry_run=False)
    assert ok is True
    assert suppressed is True


def test_send_telegram_dry_run_not_suppressed(repo_root, monkeypatch):
    monkeypatch.setenv("TELEGRAM_GOVERNANCE_INTEGRITY_ONLY", "1")
    from scripts.alpaca_postclose_deepdive import _send_telegram

    ok, suppressed = _send_telegram("body", dry_run=True)
    assert ok is True
    assert suppressed is False
