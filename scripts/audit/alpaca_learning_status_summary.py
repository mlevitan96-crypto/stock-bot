#!/usr/bin/env python3
"""
Canonical Alpaca learning status summary (synthesis only). Overwrites rolling reports/ALPACA_LEARNING_STATUS_SUMMARY.{json,md}.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]


def git_head_sha(root: Path) -> str:
    try:
        p = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=8,
        )
        if p.returncode == 0 and (p.stdout or "").strip():
            return (p.stdout or "").strip()[:40]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def _rel(root: Path, p: Path) -> str:
    try:
        return str(p.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def compute_verdict(exit_code: int, trades_seen: int, trades_incomplete: int) -> str:
    if exit_code in (1, 2):
        return "LEARNING_NOT_SAFE"
    if trades_incomplete > 0:
        return "LEARNING_NOT_SAFE"
    if exit_code == 0 and trades_seen == 0:
        return "NO_ACTIVITY"
    if exit_code == 0:
        return "LEARNING_SAFE"
    return "LEARNING_NOT_SAFE"


def build_summary_dict(
    root: Path,
    truth_json_path: Path,
    exit_code: int,
    commit_sha: str,
    *,
    incident_json_path: Optional[Path] = None,
    window_hours_override: Optional[int] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    truth_json_path = Path(truth_json_path)
    data: Dict[str, Any] = {}
    if truth_json_path.is_file():
        try:
            data = json.loads(truth_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"_truth_json_parse_error": True}

    fg = data.get("final_gate") or data.get("initial_gate") or {}
    window_hours = int(window_hours_override if window_hours_override is not None else data.get("window_hours") or 0)
    window_start = fg.get("OPEN_TS_UTC_EPOCH")
    if window_start is None:
        window_start = data.get("open_ts_epoch")
    window_end = fg.get("EXIT_TS_UTC_EPOCH_MAX")
    if window_end is None:
        window_end = data.get("window_end_epoch")

    trades_seen = int(fg.get("trades_seen") or 0)
    trades_incomplete = int(fg.get("trades_incomplete") or 0)
    verdict = compute_verdict(exit_code, trades_seen, trades_incomplete)

    actions = data.get("sre_repair_actions_applied") or []
    meta = data.get("sre_engine_meta") or {}
    rounds = int(meta.get("rounds_executed") or 0)
    actions_applied = len(actions)
    sre_ran = actions_applied > 0 or rounds > 0

    contract = str(data.get("contract") or "alpaca_forward_truth")
    runner = f"{contract}_runner"

    notes: List[str] = []
    if data.get("_truth_json_parse_error"):
        notes.append("truth_json_parse_error")
    if data.get("error"):
        notes.append(f"run_error:{data.get('error')}")
    if data.get("precheck"):
        notes.append(f"precheck:{data.get('precheck')}")
    lfr = fg.get("learning_fail_closed_reason")
    if lfr and verdict != "LEARNING_SAFE":
        notes.append(f"learning_fail_closed_reason:{lfr}")
    if not notes:
        notes.append("synthesis_from_truth_json_and_exit_code")

    proof_links: List[str] = [_rel(root, truth_json_path.resolve())]
    if incident_json_path:
        ip = Path(incident_json_path)
        if ip.is_file():
            proof_links.append(_rel(root, ip.resolve()))

    ts = data.get("run_utc") or datetime.now(timezone.utc).isoformat()

    return {
        "timestamp_utc": ts,
        "window_hours": window_hours,
        "window_start_epoch": window_start,
        "window_end_epoch": window_end,
        "verdict": verdict,
        "trades_seen": trades_seen,
        "trades_incomplete": trades_incomplete,
        "sre_auto_repair": {
            "ran": sre_ran,
            "actions_applied": actions_applied,
            "residual_incompletes": trades_incomplete,
        },
        "exit_code": exit_code,
        "commit_sha": commit_sha,
        "runner": runner,
        "notes": notes,
        "proof_links": proof_links,
    }


def render_markdown(summary: Dict[str, Any]) -> str:
    v = summary["verdict"]
    banner = {
        "LEARNING_SAFE": "LEARNING SAFE — strict cohort complete; safe to treat as learning-greenlight input.",
        "LEARNING_NOT_SAFE": "NOT LEARNING SAFE — do not consume this window for learning until resolved.",
        "NO_ACTIVITY": "NO ACTIVITY — no exits in window; vacuous from a learning-input perspective.",
    }.get(v, v)

    sar = summary.get("sre_auto_repair") or {}
    lines = [
        f"# Alpaca learning status summary\n\n## {banner}\n\n",
        "| Field | Value |\n|---|---|\n",
        f"| timestamp_utc | `{summary.get('timestamp_utc')}` |\n",
        f"| window_hours | {summary.get('window_hours')} |\n",
        f"| window_start_epoch | {summary.get('window_start_epoch')} |\n",
        f"| window_end_epoch | {summary.get('window_end_epoch')} |\n",
        f"| verdict | **{v}** |\n",
        f"| trades_seen | {summary.get('trades_seen')} |\n",
        f"| trades_incomplete | {summary.get('trades_incomplete')} |\n",
        f"| sre_auto_repair.ran | {sar.get('ran')} |\n",
        f"| sre_auto_repair.actions_applied | {sar.get('actions_applied')} |\n",
        f"| sre_auto_repair.residual_incompletes | {sar.get('residual_incompletes')} |\n",
        f"| exit_code | {summary.get('exit_code')} |\n",
        f"| commit_sha | `{summary.get('commit_sha')}` |\n",
        f"| runner | `{summary.get('runner')}` |\n",
        "\n## Why this verdict\n\n",
    ]
    if v == "LEARNING_SAFE":
        lines.append(
            "Process exited **0** (CERT_OK) with **trades_incomplete == 0** and at least one exit in the evaluated cohort. "
            "Forward truth contract + SRE engine completed; see `proof_links` for JSON evidence.\n\n"
        )
    elif v == "NO_ACTIVITY":
        lines.append(
            "Process exited **0** but **trades_seen == 0** for the bounded gate: no economic exits in scope, so no learning rows to consume.\n\n"
        )
    else:
        lines.append(
            "Exit code **1** (precheck/structural/runtime) or **2** (INCIDENT), or **trades_incomplete > 0** after evaluation. "
            "Treat as blocked for learning consumption until proof shows `trades_incomplete == 0` and exit **0**.\n\n"
        )
    lines.append("## Proof artifacts\n\n")
    for pl in summary.get("proof_links") or []:
        lines.append(f"- `{pl}`\n")
    lines.append("\n## Notes\n\n")
    for n in summary.get("notes") or []:
        lines.append(f"- {n}\n")
    return "".join(lines)


def emit_learning_status_summary(
    root: Path,
    truth_json_path: Path,
    exit_code: int,
    commit_sha: str,
    *,
    incident_json_path: Optional[Path] = None,
    window_hours_override: Optional[int] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    summary = build_summary_dict(
        root,
        truth_json_path,
        exit_code,
        commit_sha,
        incident_json_path=incident_json_path,
        window_hours_override=window_hours_override,
    )
    out_json = root / "reports" / "ALPACA_LEARNING_STATUS_SUMMARY.json"
    out_md = root / "reports" / "audit" / "ALPACA_LEARNING_STATUS_SUMMARY.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--truth-json", type=Path, required=True)
    ap.add_argument("--incident-json", type=Path, default=None)
    ap.add_argument("--window-hours", type=int, default=None)
    ap.add_argument("--exit-code", type=int, required=True)
    ap.add_argument("--commit-sha", type=str, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    sha = args.commit_sha if args.commit_sha else git_head_sha(root)
    emit_learning_status_summary(
        root,
        args.truth_json,
        args.exit_code,
        sha,
        incident_json_path=args.incident_json,
        window_hours_override=args.window_hours,
    )
    print(json.dumps({"written": ["reports/ALPACA_LEARNING_STATUS_SUMMARY.json", "reports/audit/ALPACA_LEARNING_STATUS_SUMMARY.md"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
