#!/usr/bin/env python3
"""
Tests for cron diagnosis, repair, EOD force-run, and health check.
Uses mocks to avoid SSH/crontab on Windows.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))


class TestCronEntryPresent(unittest.TestCase):
    """check_cron_installed detects EOD cron entry in crontab."""

    def test_cron_entry_present(self):
        from board.eod.cron_diagnose_and_fix import check_cron_installed

        # Mock client with crontab containing eod_confirmation
        client = MagicMock()
        client._execute.side_effect = [
            ("30 21 * * 1-5 cd /root/stock-bot && /usr/bin/python3 board/eod/eod_confirmation.py\n", "", 0),
            ("Feb 12 21:30:01 host CRON[123]: (root) CMD (...)\n", "", 0),
        ]
        result = check_cron_installed(client=client)
        self.assertTrue(result.get("cron_entry_exists"), "should detect eod_confirmation in crontab")
        self.assertTrue(result.get("schedule_ok"))
        self.assertTrue(result.get("path_ok"))


class TestCronDiagnosisJsonWritten(unittest.TestCase):
    """cron_diagnosis.json is written to board/eod/out/<date>/."""

    def test_cron_diagnosis_json_written(self):
        from board.eod.cron_diagnose_and_fix import run_on_droplet

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "scripts").mkdir()
            (base / "config").mkdir()
            (base / "board" / "eod").mkdir(parents=True)
            (base / "board" / "eod" / "eod_confirmation.py").write_text("# stub")
            (base / "board" / "eod" / "run_stock_quant_officer_eod.py").write_text("# stub")

            with (
                patch("board.eod.cron_diagnose_and_fix._detect_stockbot_root", return_value=str(base)),
                patch("board.eod.cron_diagnose_and_fix.check_cron_installed", return_value={"cron_entry_exists": True, "errors": []}),
                patch("board.eod.cron_diagnose_and_fix.check_cron_execution", return_value={}),
                patch("board.eod.cron_diagnose_and_fix.check_script_health", return_value={"errors": []}),
                patch("board.eod.cron_diagnose_and_fix.check_logging", return_value={}),
                patch("board.eod.cron_diagnose_and_fix.force_run_eod", return_value=(1, "", "EOD pipeline mock fail")),
            ):
                rc = run_on_droplet("2026-02-12")
            diag_path = base / "board" / "eod" / "out" / "2026-02-12" / "cron_diagnosis.json"
            self.assertTrue(diag_path.exists(), f"cron_diagnosis.json should exist at {diag_path}")
            data = json.loads(diag_path.read_text())
            self.assertIn("date", data)
            self.assertEqual(data["date"], "2026-02-12")
            self.assertIn("cron_installed", data)


class TestCronRepairReinstallsCorrectEntry(unittest.TestCase):
    """repair_cron reinstalls EOD confirmation entry."""

    def test_cron_repair_reinstalls_correct_entry(self):
        from board.eod.cron_diagnose_and_fix import repair_cron

        client = MagicMock()
        client._execute.return_value = ("", "", 0)
        with patch("board.eod.cron_diagnose_and_fix._detect_stockbot_root", return_value="/root/stock-bot"):
            ok, msg = repair_cron(client=client)
        self.assertTrue(ok, msg)
        calls = [c[0][0] for c in client._execute.call_args_list]
        install_cmd = next((c for c in calls if "crontab" in c), None)
        self.assertIsNotNone(install_cmd)
        self.assertIn("eod_confirmation", install_cmd)
        self.assertIn("30 21", install_cmd)


class TestEodConfirmationRunsAfterCronFix(unittest.TestCase):
    """force_run_eod invokes eod_confirmation.py --date."""

    def test_eod_confirmation_runs_after_cron_fix(self):
        from board.eod.cron_diagnose_and_fix import force_run_eod

        client = MagicMock()
        client._execute.return_value = ("", "", 0)
        with patch("board.eod.cron_diagnose_and_fix._detect_stockbot_root", return_value="/root/stock-bot"):
            rc, out, err = force_run_eod("2026-02-12", client=client)
        self.assertEqual(rc, 0)
        call_cmd = client._execute.call_args[0][0]
        self.assertIn("eod_confirmation.py", call_cmd)
        self.assertIn("--date 2026-02-12", call_cmd)


class TestGithubPushAfterRecovery(unittest.TestCase):
    """push_to_github runs git add, commit, push."""

    def test_github_push_after_recovery(self):
        from board.eod.cron_diagnose_and_fix import push_to_github

        client = MagicMock()
        client._execute.return_value = ("", "", 0)
        with patch("board.eod.cron_diagnose_and_fix._detect_stockbot_root", return_value="/root/stock-bot"):
            rc, out, err = push_to_github("2026-02-12", client=client)
        self.assertEqual(rc, 0)
        call_cmd = client._execute.call_args[0][0]
        self.assertIn("git add", call_cmd)
        self.assertIn("board/eod/out/2026-02-12", call_cmd)
        self.assertIn("git push", call_cmd)
        self.assertIn("cron recovery", call_cmd)


class TestCronHealthCheckDetectsAndRepairs(unittest.TestCase):
    """cron_health_check detects missing cron and repairs."""

    def test_cron_health_check_detects_and_repairs(self):
        from board.eod.cron_health_check import (
            check_cron_entry_exists,
            check_eod_executable,
            check_python_path,
            repair_cron,
        )

        with patch("subprocess.run") as mock_run:
            # crontab -l returns empty (no EOD entry)
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            ok, msg = check_cron_entry_exists()
            self.assertFalse(ok, "empty crontab should fail")

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "board" / "eod").mkdir(parents=True)
            (base / "board" / "eod" / "eod_confirmation.py").write_text("# stub")
            with patch("board.eod.cron_health_check._detect_root", return_value=str(base)):
                ok, _ = check_eod_executable(str(base))
                self.assertTrue(ok)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Python 3.10\n", stderr="")
            ok, _ = check_python_path()
            self.assertTrue(ok)

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "logs").mkdir()
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                ok, msg = repair_cron(str(base))
                self.assertTrue(ok, msg)
                mock_run.assert_called()
                call_args = mock_run.call_args[0][0]
                self.assertIn("crontab", " ".join(call_args) if isinstance(call_args, list) else call_args)


if __name__ == "__main__":
    unittest.main()
