#!/usr/bin/env python3
"""
Tests for EOD confirmation: verify_eod_run, run_full_eod, push_eod_to_github, no .gz in output.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))


class TestVerifyEodRunDetectsMissingFiles(unittest.TestCase):
    """verify_eod_run reports missing required files and exists=False when dir missing."""

    def test_verify_eod_run_detects_missing_dir(self):
        from board.eod.eod_confirmation import verify_eod_run
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            result = verify_eod_run("2026-02-15", repo_root=base)
        self.assertFalse(result["exists"], "dir does not exist")
        self.assertFalse(result["valid"])
        self.assertIn("does not exist", result["reason"])

    def test_verify_eod_run_detects_missing_files(self):
        from board.eod.eod_confirmation import verify_eod_run
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            out_dir = base / "board" / "eod" / "out" / "2026-02-15"
            out_dir.mkdir(parents=True)
            # empty dir: no eod_board.json, derived_deltas.json, etc.
            result = verify_eod_run("2026-02-15", repo_root=base)
        self.assertTrue(result["exists"])
        self.assertFalse(result["valid"])
        self.assertIn("eod_board.json", result["missing_files"] or result["reason"])
        self.assertIn("derived_deltas.json", result["missing_files"] or result["reason"])


class TestVerifyEodRunDetectsInvalidJson(unittest.TestCase):
    """verify_eod_run reports invalid JSON in eod_board.json."""

    def test_verify_eod_run_detects_invalid_json(self):
        from board.eod.eod_confirmation import verify_eod_run
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            out_dir = base / "board" / "eod" / "out" / "2026-02-15"
            out_dir.mkdir(parents=True)
            (out_dir / "eod_board.json").write_text("not valid json {", encoding="utf-8")
            (out_dir / "eod_board.md").write_text("# EOD", encoding="utf-8")
            (out_dir / "eod_review.md").write_text("# Review", encoding="utf-8")
            (out_dir / "weekly_review.md").write_text("# Weekly", encoding="utf-8")
            derived = {
                "rolling_windows": {},
                "missed_money": {},
                "variant_attribution": {},
            }
            (out_dir / "derived_deltas.json").write_text(json.dumps(derived), encoding="utf-8")
            result = verify_eod_run("2026-02-15", repo_root=base)
        self.assertTrue(result["exists"])
        self.assertFalse(result["valid"])
        self.assertIn("invalid JSON", result["reason"])


class TestRunFullEodProducesAllCanonicalFiles(unittest.TestCase):
    """run_full_eod (mocked subprocess) produces canonical files; test structure only."""

    def test_run_full_eod_produces_all_canonical_files(self):
        from board.eod.eod_confirmation import run_full_eod, verify_eod_run, REQUIRED_CANONICAL_FILES
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            out_dir = base / "board" / "eod" / "out" / "2026-02-15"
            out_dir.mkdir(parents=True)
            for f in REQUIRED_CANONICAL_FILES:
                (out_dir / f).write_text("{}" if f.endswith(".json") else "# stub", encoding="utf-8")
            (out_dir / "eod_board.json").write_text('{"verdict":"OK"}', encoding="utf-8")
            derived = {"rolling_windows": {}, "missed_money": {}, "variant_attribution": {}}
            (out_dir / "derived_deltas.json").write_text(json.dumps(derived), encoding="utf-8")
            result = verify_eod_run("2026-02-15", repo_root=base)
        self.assertTrue(result["exists"], "dir exists")
        self.assertTrue(result["valid"], "all required files and valid JSON: " + result.get("reason", ""))


class TestPushEodToGithubRunsWithoutError(unittest.TestCase):
    """push_eod_to_github runs without error when git is mocked."""

    def test_push_eod_to_github_runs_without_error(self):
        from board.eod.eod_confirmation import push_eod_to_github
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            out_dir = base / "board" / "eod" / "out" / "2026-02-15"
            out_dir.mkdir(parents=True)
            (base / "state").mkdir(exist_ok=True)
            mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout="", stderr=""))
            with patch("board.eod.eod_confirmation.subprocess.run", mock_run):
                push_eod_to_github("2026-02-15", repo_root=base)
        self.assertGreaterEqual(mock_run.call_count, 1)
        cmd_lists = [c[0][0] for c in mock_run.call_args_list if c[0] and isinstance(c[0][0], list)]
        self.assertTrue(any("add" in (cmd or []) for cmd in cmd_lists), "git add should be called")


class TestNoGzFilesInOutputAfterRerun(unittest.TestCase):
    """After a proper run, no .gz files remain in the date dir (only allowed extensions)."""

    def test_no_gz_files_in_output_after_rerun(self):
        from board.eod.eod_confirmation import verify_eod_run, DISALLOWED_SUFFIXES, ALLOWED_EXTENSIONS
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            out_dir = base / "board" / "eod" / "out" / "2026-02-15"
            out_dir.mkdir(parents=True)
            (out_dir / "eod_board.json").write_text('{"verdict":"OK"}', encoding="utf-8")
            (out_dir / "eod_board.md").write_text("# EOD", encoding="utf-8")
            (out_dir / "eod_review.md").write_text("# Review", encoding="utf-8")
            (out_dir / "weekly_review.md").write_text("# Weekly", encoding="utf-8")
            derived = {"rolling_windows": {}, "missed_money": {}, "variant_attribution": {}}
            (out_dir / "derived_deltas.json").write_text(json.dumps(derived), encoding="utf-8")
            result = verify_eod_run("2026-02-15", repo_root=base)
        self.assertTrue(result["valid"], "no .gz: valid")
        with tempfile.TemporaryDirectory() as td2:
            base2 = Path(td2)
            out2 = base2 / "board" / "eod" / "out" / "2026-02-16"
            out2.mkdir(parents=True)
            for f in ["eod_board.json", "eod_board.md", "eod_review.md", "weekly_review.md", "derived_deltas.json"]:
                (out2 / f).write_text("{}" if f.endswith(".json") else "# x", encoding="utf-8")
            (out2 / "raw_attribution.jsonl.gz").write_text("", encoding="utf-8")
            result2 = verify_eod_run("2026-02-16", repo_root=base2)
        self.assertFalse(result2["valid"], "presence of .gz should make valid=False")
        self.assertTrue(
            any("disallowed" in str(m).lower() or ".gz" in str(m) for m in (result2.get("missing_files") or []) + [result2.get("reason", "")]),
            "reason or missing_files should mention disallowed/gz",
        )


if __name__ == "__main__":
    unittest.main()
