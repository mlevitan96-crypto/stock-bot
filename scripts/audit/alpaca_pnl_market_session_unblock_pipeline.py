#!/usr/bin/env python3
"""
Pin ET market session, build demo fixture (or use droplet root), run forward truth, alignment, bundle exports.
All report artifacts → reports/daily/<session-date-et>/evidence/; canonical DAILY_* via assembler.
Signal Path Intelligence (SPI) is emitted when `alpaca_pnl_massive_final_review.py` runs on the same cohort (see MEMORY_BANK.md).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], cwd: Path | None = None) -> int:
    p = subprocess.run(cmd, cwd=cwd or REPO)
    return int(p.returncode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ts", type=str, default="20260327_MKTS_FINAL")
    ap.add_argument("--session-date-et", type=str, default="2026-03-26")
    ap.add_argument(
        "--fixture-root",
        type=Path,
        default=REPO / "artifacts" / "alpaca_pnl_session_et_20260326",
        help="TRADING_BOT_ROOT for synthetic session demo",
    )
    ap.add_argument("--skip-fixture", action="store_true")
    args = ap.parse_args()
    ts = args.ts
    sys.path.insert(0, str(REPO))
    from src.report_output.paths import evidence_dir
    from telemetry.alpaca_market_session_window import market_session_bounds_utc

    bounds = market_session_bounds_utc(args.session_date_et)
    w0, w1 = float(bounds["window_start_epoch_utc"]), float(bounds["window_end_epoch_utc"])
    evd = evidence_dir(REPO, args.session_date_et)
    evd.mkdir(parents=True, exist_ok=True)

    scope = evd / f"ALPACA_PNL_MARKET_SESSION_SCOPE_{ts}.md"
    scope.write_text(
        "\n".join(
            [
                f"# Alpaca PnL — market session scope ({ts})",
                "",
                "## Canonical TODAY (ET session)",
                "",
                f"- **session_date_et:** `{bounds['session_date_et']}`",
                f"- **session_open_et:** `{bounds['session_open_et']}`",
                f"- **session_close_et:** `{bounds['session_close_et']}`",
                f"- **window_start_utc:** `{bounds['window_start_utc']}` → epoch `{w0}`",
                f"- **window_end_utc:** `{bounds['window_end_utc']}` → epoch `{w1}`",
                "",
                "## Strict gate parameters",
                "",
                f"- `OPEN_TS_UTC_EPOCH` = max(STRICT_EPOCH_START, window_start_epoch) (runner)",
                f"- `EXIT_TS_UTC_EPOCH_MAX` = `{w1}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    contract = evd / f"ALPACA_PNL_TRUTH_JSON_CONTRACT_{ts}.md"
    contract.write_text(
        "\n".join(
            [
                f"# Truth JSON contract ({ts})",
                "",
                "## Rules",
                "",
                "1. `telemetry/alpaca_strict_completeness_gate.py` — `complete_trade_ids` cap ≥ 50k.",
                "2. `scripts/audit/alpaca_forward_truth_contract_runner.py` — `collect_complete_trade_ids=True` on `_gate` and SRE `_gate`.",
                "3. **Assertion:** if `trades_complete > 0` then `len(complete_trade_ids) > 0`; else runner exits **2** and writes INCIDENT.",
                "",
                "## References",
                "",
                "- `alpaca_forward_truth_contract_runner.py` (post-SRE enumeration check)",
                "- `alpaca_sre_auto_repair_engine.py` (`collect_complete_trade_ids=True`)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    fx = args.fixture_root.resolve()
    if not args.skip_fixture:
        rc = _run([sys.executable, str(REPO / "scripts" / "audit" / "alpaca_pnl_session_demo_fixture.py"), str(fx)])
        if rc != 0:
            return rc

    truth_json = evd / f"ALPACA_MARKET_SESSION_TRUTH_{ts}.json"
    truth_md = evd / f"ALPACA_MARKET_SESSION_TRUTH_{ts}.md"
    inc_md = evd / f"_incident_ms_{ts}.md"
    inc_json = evd / f"_incident_ms_{ts}.json"
    rc = _run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit" / "alpaca_forward_truth_contract_runner.py"),
            "--root",
            str(fx),
            "--window-start-epoch",
            str(w0),
            "--window-end-epoch",
            str(w1),
            "--repair-max-rounds",
            "2",
            "--json-out",
            str(truth_json),
            "--md-out",
            str(truth_md),
            "--incident-md",
            str(inc_md),
            "--incident-json",
            str(inc_json),
        ]
    )
    if rc != 0:
        return rc

    tdata = json.loads(truth_json.read_text(encoding="utf-8"))
    fg = tdata.get("final_gate") or {}
    cids = list(fg.get("complete_trade_ids") or [])
    rel_ev = evd.relative_to(REPO).as_posix()
    bundle_doc: dict = {
        "ts": ts,
        "session_date_et": bounds["session_date_et"],
        "window_start_epoch_utc": w0,
        "window_end_epoch_utc": w1,
        "droplet_command": (
            "python scripts/audit/alpaca_forward_truth_contract_runner.py --root /root/stock-bot "
            f"--window-start-epoch {w0} --window-end-epoch {w1} "
            f"--json-out {rel_ev}/ALPACA_MARKET_SESSION_TRUTH_{ts}.json "
            f"--md-out {rel_ev}/ALPACA_MARKET_SESSION_TRUTH_{ts}.md "
            f"--incident-md {rel_ev}/_incident_ms.md --incident-json {rel_ev}/_incident_ms.json"
        ),
        "workspace_demo_fixture_root": str(fx),
        "note": "Droplet must scp the same logs slice to workspace for production parity; demo uses synthetic MKT1/MKT2.",
        "trades_seen": fg.get("trades_seen"),
        "trades_complete": fg.get("trades_complete"),
        "trades_incomplete": fg.get("trades_incomplete"),
    }
    (evd / f"ALPACA_MARKET_SESSION_DROPLET_BUNDLE_{ts}.json").write_text(json.dumps(bundle_doc, indent=2), encoding="utf-8")

    ct_payload = {
        "session_date_et": bounds["session_date_et"],
        "window_start_epoch_utc": w0,
        "window_end_epoch_utc": w1,
        "trades_seen": fg.get("trades_seen"),
        "trades_complete": fg.get("trades_complete"),
        "complete_trade_ids": cids,
        "source": "workspace_session_demo_fixture",
    }
    ct_path = evd / f"ALPACA_MARKET_SESSION_COMPLETE_TRADE_IDS_{ts}.json"
    ct_path.write_text(json.dumps(ct_payload, indent=2), encoding="utf-8")

    proof = evd / f"ALPACA_PNL_DROPLET_CERT_PROOF_{ts}.md"
    proof.write_text(
        "\n".join(
            [
                f"# Droplet cert proof ({ts})",
                "",
                "## Command (authoritative on Alpaca host)",
                "",
                "```bash",
                bundle_doc["droplet_command"],
                "```",
                "",
                "## Workspace demo",
                "",
                f"- Fixture root: `{fx}`",
                f"- Truth JSON: `{truth_json.relative_to(REPO)}`",
                f"- `complete_trade_ids` count: **{len(cids)}**",
                "",
            ]
        ),
        encoding="utf-8",
    )

    align_report = evd / f"ALPACA_PNL_COHORT_ALIGNMENT_{ts}.json"
    rc = _run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit" / "alpaca_pnl_cohort_alignment_check.py"),
            "--complete-trade-ids",
            str(ct_path),
            "--window-start-epoch",
            str(w0),
            "--window-end-epoch",
            str(w1),
            "--root",
            str(fx),
            "--json-out",
            str(align_report),
        ]
    )
    align_md = evd / f"ALPACA_PNL_COHORT_ALIGNMENT_{ts}.md"
    ar = json.loads(align_report.read_text(encoding="utf-8")) if align_report.is_file() else {}
    align_md.write_text(
        f"# Cohort alignment ({ts})\n\n```json\n{json.dumps(ar, indent=2)}\n```\n",
        encoding="utf-8",
    )
    if rc != 0:
        return rc

    rc = _run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit" / "alpaca_pnl_massive_final_review.py"),
            "--ts",
            ts,
            "--cohort-ids",
            str(ct_path),
            "--truth-json",
            str(truth_json),
            "--window-start-epoch",
            str(w0),
            "--window-end-epoch",
            str(w1),
            "--root",
            str(fx),
            "--output-dir",
            str(evd),
        ]
    )
    if rc != 0:
        return rc

    (evd / "EVIDENCE_RUN_META.json").write_text(
        json.dumps({"ts": ts, "session_date_et": args.session_date_et}, indent=2),
        encoding="utf-8",
    )

    rc = _run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit" / "assemble_daily_market_session_report.py"),
            "--session-date-et",
            args.session_date_et,
            "--repo",
            str(REPO),
        ]
    )
    if rc != 0:
        return rc

    summary = evd / f"ALPACA_PNL_RERUN_SUMMARY_{ts}.md"
    summary.write_text(
        "\n".join(
            [
                f"# Massive PnL review rerun ({ts})",
                "",
                "## Pipeline",
                "",
                "1. `alpaca_pnl_market_session_unblock_pipeline.py`",
                "2. `alpaca_pnl_session_demo_fixture.py`",
                "3. `alpaca_forward_truth_contract_runner.py` (market session epochs)",
                "4. `alpaca_pnl_cohort_alignment_check.py`",
                "5. `alpaca_pnl_massive_final_review.py --output-dir evidence/`",
                "6. `assemble_daily_market_session_report.py`",
                "",
                "## Canonical (operator)",
                "",
                f"- `reports/daily/{args.session_date_et}/DAILY_MARKET_SESSION_REPORT.md`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    test_fix = evd / f"ALPACA_PNL_TEST_DETERMINISM_FIX_{ts}.md"
    test_fix.write_text(
        "\n".join(
            [
                f"# Test determinism ({ts})",
                "",
                "- `tests/test_alpaca_entry_ts_normalization.py` strict gate tests use fixed `open_ts_epoch=0.0`.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
