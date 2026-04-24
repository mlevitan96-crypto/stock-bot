#!/usr/bin/env python3
"""
Remove exit_attribution.jsonl lines whose trade_id appears in strict gate
`incomplete_trade_ids_by_reason` (audit). Preserves **raw lines** (no json round-trip).

If the gate reports zero incomplete trades, exits without touching the ledger.

Usage:
  sudo systemctl stop stock-bot.service
  PYTHONPATH=/root/stock-bot python3 scripts/_tmp_auto_amputate.py --root /root/stock-bot --apply --i-know-writers-stopped
  sudo systemctl start stock-bot.service
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set


def _incomplete_trade_ids(gate: Dict[str, Any]) -> Set[str]:
    full = gate.get("incomplete_trade_ids_all")
    if isinstance(full, list) and full:
        return {str(t) for t in full if t}
    out: Set[str] = set()
    for ids in (gate.get("incomplete_trade_ids_by_reason") or {}).values():
        for tid in ids or []:
            if tid:
                out.add(str(tid))
    if not out:
        for ex in gate.get("incomplete_examples") or []:
            tid = ex.get("trade_id")
            if tid:
                out.add(str(tid))
    return out


def _run_gate(root: Path) -> Dict[str, Any]:
    gate_py = root / "telemetry" / "alpaca_strict_completeness_gate.py"
    env = {**dict(os.environ), "PYTHONPATH": str(root)}
    p = subprocess.run(
        [sys.executable, str(gate_py), "--root", str(root), "--audit"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
    )
    raw = (p.stdout or "").strip()
    if not raw:
        err = (p.stderr or "")[:800]
        raise RuntimeError(f"strict gate empty stdout stderr={err!r}")
    return json.loads(raw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--i-know-writers-stopped", action="store_true", dest="writers_ok")
    args = ap.parse_args()
    root = args.root.resolve()
    exit_path = root / "logs" / "exit_attribution.jsonl"

    gate = _run_gate(root)
    blockers = _incomplete_trade_ids(gate)
    print("strict_gate trades_seen:", gate.get("trades_seen"))
    print("strict_gate trades_incomplete:", gate.get("trades_incomplete"))
    print("strict_gate LEARNING_STATUS:", gate.get("LEARNING_STATUS"))
    print("incomplete_trade_ids_to_remove:", len(blockers))
    for tid in sorted(blockers)[:30]:
        print(" ", tid)
    if len(blockers) > 30:
        print(" ...", len(blockers) - 30, "more")

    if not blockers:
        print("nothing_to_do: ledger unchanged")
        return 0

    if not exit_path.is_file():
        print("missing", exit_path)
        return 2

    kept: List[str] = []
    removed = 0
    total = 0
    with exit_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            raw = line if line.endswith("\n") else line + "\n"
            body = line.strip()
            try:
                rec = json.loads(body)
            except json.JSONDecodeError:
                kept.append(raw)
                continue
            tid = str(rec.get("trade_id") or "").strip()
            if tid in blockers:
                removed += 1
                continue
            kept.append(raw)

    print("ledger_lines_read:", total)
    print("rows_removed:", removed)
    print("rows_kept:", len(kept))

    if not args.apply:
        print("dry_run: pass --apply --i-know-writers-stopped")
        return 0
    if not args.writers_ok:
        print("refusing without --i-know-writers-stopped")
        return 1

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = exit_path.with_name(f"exit_attribution.pre_auto_amputate_{stamp}.jsonl")
    backup.write_bytes(exit_path.read_bytes())
    print("backup:", backup)
    exit_path.write_text("".join(kept), encoding="utf-8")
    print("wrote:", exit_path)

    gate2 = _run_gate(root)
    print("post_amputation trades_incomplete:", gate2.get("trades_incomplete"))
    print("post_amputation LEARNING_STATUS:", gate2.get("LEARNING_STATUS"))
    ok = gate2.get("LEARNING_STATUS") == "ARMED" and gate2.get("trades_incomplete") == 0
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
