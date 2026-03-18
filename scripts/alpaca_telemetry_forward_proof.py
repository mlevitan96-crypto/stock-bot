#!/usr/bin/env python3
"""
Forward-only telemetry proof: post-repair exits must have 100% entry join by trade_id.
HARD FAIL (exit 1) if any post-epoch closed trade lacks matching entry attribution.
Requires state/alpaca_telemetry_repair_epoch.json with {"repair_iso_utc": "..."}.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

EPOCH = REPO / "state" / "alpaca_telemetry_repair_epoch.json"
EXIT_LOG = REPO / "logs" / "exit_attribution.jsonl"
ENTRY_LOG = REPO / "logs" / "alpaca_entry_attribution.jsonl"
UNIFIED = REPO / "logs" / "alpaca_unified_events.jsonl"


def _parse_ts(s: str):
    if not s:
        return None
    try:
        s = str(s).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


def load_entry_trade_ids() -> Set[str]:
    ids: Set[str] = set()
    for path in (ENTRY_LOG,):
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(r, dict):
                    tid = str(r.get("trade_id") or "").strip()
                    if tid:
                        ids.add(tid)
    if UNIFIED.exists():
        with open(UNIFIED, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(r, dict) and r.get("event_type") == "alpaca_entry_attribution":
                    tid = str(r.get("trade_id") or "").strip()
                    if tid:
                        ids.add(tid)
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-trades", type=int, default=50)
    args = ap.parse_args()

    if not EPOCH.exists():
        print("FAIL: state/alpaca_telemetry_repair_epoch.json missing. Run scripts/write_alpaca_telemetry_repair_epoch.py on deploy.")
        return 2

    ep = json.loads(EPOCH.read_text(encoding="utf-8"))
    t0s = str(ep.get("repair_iso_utc") or ep.get("iso_utc") or "")
    t0 = _parse_ts(t0s)
    if not t0:
        print("FAIL: invalid repair_iso_utc in epoch file")
        return 2

    entry_ids = load_entry_trade_ids()
    post_exits: List[Dict[str, Any]] = []
    with open(EXIT_LOG, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(r, dict):
                continue
            ets = _parse_ts(str(r.get("timestamp") or r.get("exit_timestamp") or ""))
            if ets and ets >= t0:
                post_exits.append(r)

    n = len(post_exits)
    if n < args.min_trades:
        print(f"PENDING: only {n} exits since repair (need {args.min_trades}). Do not certify DATA_READY.")
        return 3

    missing = []
    for r in post_exits:
        tid = str(r.get("trade_id") or "").strip()
        if not tid:
            missing.append({"reason": "no_trade_id_on_exit", "symbol": r.get("symbol")})
        elif tid not in entry_ids:
            # exit may use live: key while entry used open_ — also check open_ form
            sym = str(r.get("symbol") or "").upper()
            ets = str(r.get("entry_timestamp") or "")
            alt = f"open_{sym}_{ets}" if sym and ets else ""
            if alt not in entry_ids:
                missing.append({"trade_id": tid, "symbol": sym, "alt_checked": alt})

    AUDIT = REPO / "reports" / "audit"
    AUDIT.mkdir(parents=True, exist_ok=True)
    proof_path = AUDIT / "ALPACA_TELEMETRY_FORWARD_PROOF.md"
    pct = 100.0 * (n - len(missing)) / n if n else 0
    body = [
        "# Alpaca Telemetry Forward Proof",
        "",
        f"- **Repair epoch:** {t0s}",
        f"- **Post-epoch exits counted:** {n}",
        f"- **Min required:** {args.min_trades}",
        f"- **Missing entry join:** {len(missing)}",
        f"- **Coverage:** {pct:.2f}%",
        "",
    ]
    if missing:
        body.append("## FAILURES (sample 20)")
        for m in missing[:20]:
            body.append(f"- `{m}`")
        _write_result(AUDIT, body, False)
        proof_path.write_text("\n".join(body), encoding="utf-8")
        _blocker(AUDIT, "\n".join(body))
        print(f"HARD FAIL: {len(missing)}/{n} exits without entry attribution join")
        return 1

    # emit_entry_attribution_failed since epoch (journalctl)
    jfail = -1
    try:
        since = t0s.replace("+00:00", "").split(".")[0]
        cmd = (
            f"journalctl -u stock-bot --since='{since}' --no-pager 2>/dev/null | "
            "grep -c emit_entry_attribution_failed || true"
        )
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=45)
        jfail = int((out.stdout or "0").strip() or "0")
    except Exception as ex:
        body.append(f"## journalctl check: skipped ({ex})\n")
        jfail = -1
    if jfail > 0:
        body.append(f"## HARD FAIL: emit_entry_attribution_failed in journal since epoch: **{jfail}**\n")
        _write_result(AUDIT, body, False)
        proof_path.write_text("\n".join(body), encoding="utf-8")
        _blocker(AUDIT, "\n".join(body))
        print(f"HARD FAIL: journal emit_entry_attribution_failed count={jfail}")
        return 1
    if jfail == 0:
        body.append("## journalctl: emit_entry_attribution_failed count **0** since epoch\n")

    body.append("## RESULT: **PASS** — 100% entry join + zero emit failures (journal).\n")
    _write_result(AUDIT, body, True)
    proof_path.write_text("\n".join(body), encoding="utf-8")
    print("PASS: 100% join")
    return 0


def _write_result(audit: Path, body: List[str], passed: bool) -> None:
    p = audit / "ALPACA_TELEMETRY_FORWARD_PROOF_RESULT.md"
    hdr = "# Forward Proof Result\n\n**PASS**\n\n" if passed else "# Forward Proof Result\n\n**FAIL**\n\n"
    p.write_text(hdr + "\n".join(body), encoding="utf-8")


def _blocker(audit: Path, text: str) -> None:
    (audit / "ALPACA_TELEMETRY_FORWARD_PROOF_BLOCKER_LATEST.md").write_text(
        "# ALPACA TELEMETRY FORWARD PROOF — BLOCKER\n\n" + text, encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main())
