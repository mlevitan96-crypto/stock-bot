#!/usr/bin/env python3
"""
Replay lab (additive): snapshot logs → isolated workspace → strict gate with explicit era (POLICY C).

Supports:
  --strict-epoch-start E   explicit UTC epoch (required unless computed below)
  --slice-hours N         with --strict-epoch-start omitted: epoch = now_utc - N*3600
  --replay-era-auto       with --slice-hours: set epoch = min(open_epoch) among last 50 exits
                            with exit_ts in [now - slice_hours, now] (labeled CODE_COMPLETE_REPLAY_ERA_AUTO)

Outputs --json-out path (default reports/ALPACA_REPLAY_GATE_<ts>.json under repo).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]

TID_RE = __import__("re").compile(r"^open_([A-Z0-9]+)_(.+)$")


def _parse_iso_ts(s: Any) -> Optional[float]:
    if not s or not isinstance(s, str):
        return None
    try:
        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def _open_epoch_from_tid(tid: str) -> Optional[float]:
    m = TID_RE.match(str(tid).strip())
    if not m:
        return None
    return _parse_iso_ts(m.group(2))


def _iter_jsonl(path: Path):
    if not path.is_file():
        return
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def compute_auto_replay_era(exit_path: Path, slice_hours: float, tail_n: int = 50) -> Tuple[float, Dict[str, Any]]:
    """Min open_epoch among last `tail_n` exits with exit_ts >= now - slice_hours."""
    now = time.time()
    lo = now - float(slice_hours) * 3600.0
    rows: List[Tuple[float, float, str]] = []
    for rec in _iter_jsonl(exit_path):
        ex_ts = _parse_iso_ts(rec.get("timestamp"))
        if ex_ts is None or ex_ts < lo:
            continue
        tid = rec.get("trade_id")
        if not tid:
            continue
        oep = _open_epoch_from_tid(str(tid))
        if oep is None:
            continue
        rows.append((ex_ts, oep, str(tid)))
    rows.sort(key=lambda x: x[0])
    tail = rows[-tail_n:] if len(rows) > tail_n else rows
    meta = {
        "candidates_in_exit_window": len(rows),
        "tail_n_used": len(tail),
        "now_utc_epoch": now,
        "slice_hours": slice_hours,
        "window_floor_epoch": lo,
    }
    if not tail:
        return lo, {**meta, "fallback": "window_floor_only_vacuous_tail"}
    mopen = min(x[1] for x in tail)
    return mopen, {**meta, "fallback": None, "auto_strict_epoch_from_min_open_in_tail": mopen}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, default=REPO / "artifacts" / "alpaca_replay_lab_default")
    ap.add_argument("--source-root", type=Path, default=REPO, help="Repo root to copy logs from")
    ap.add_argument("--init-snapshot", action="store_true")
    ap.add_argument("--strict-epoch-start", type=float, default=None)
    ap.add_argument("--slice-hours", type=float, default=None)
    ap.add_argument("--replay-era-auto", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--ts", default=None, help="Suffix for default json-out filename")
    ap.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write full result JSON here (default: reports/ALPACA_REPLAY_GATE_<ts>.json)",
    )
    args = ap.parse_args()

    sys.path.insert(0, str(REPO))
    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    src_root = args.source_root.resolve()
    exit_path = src_root / "logs" / "exit_attribution.jsonl"

    era_meta: Dict[str, Any] = {}
    strict_epoch: float
    if args.strict_epoch_start is not None:
        strict_epoch = float(args.strict_epoch_start)
        era_meta = {"policy": "explicit_strict_epoch_start", "value": strict_epoch}
    elif args.slice_hours is not None:
        sh = float(args.slice_hours)
        if args.replay_era_auto:
            strict_epoch, era_meta = compute_auto_replay_era(exit_path, sh)
            era_meta["policy"] = "CODE_COMPLETE_REPLAY_ERA_AUTO"
            era_meta["label"] = "CODE_COMPLETE_CERTIFIED_REPLAY_ERA_NOT_LIVE_FORWARD"
        else:
            strict_epoch = time.time() - sh * 3600.0
            era_meta = {
                "policy": "rolling_window_slice_hours",
                "slice_hours": sh,
                "strict_epoch_start": strict_epoch,
            }
    else:
        print("Provide --strict-epoch-start and/or --slice-hours", file=sys.stderr)
        return 2

    ws: Path = args.workspace.resolve()
    if args.init_snapshot:
        src_logs = src_root / "logs"
        dst_logs = ws / "logs"
        dst_logs.mkdir(parents=True, exist_ok=True)
        for name in (
            "exit_attribution.jsonl",
            "run.jsonl",
            "alpaca_unified_events.jsonl",
            "orders.jsonl",
            "alpaca_entry_attribution.jsonl",
            "alpaca_exit_attribution.jsonl",
            "alpaca_emit_failures.jsonl",
        ):
            p = src_logs / name
            if p.is_file():
                shutil.copy2(p, dst_logs / name)

    r = evaluate_completeness(ws, open_ts_epoch=strict_epoch, audit=args.audit)
    ts = args.ts or datetime.now(timezone.utc).strftime("%Y%m%d_%H%MZ")
    out_path = args.json_out or (REPO / "reports" / f"ALPACA_REPLAY_GATE_{ts}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "workspace": str(ws),
        "strict_epoch_start": strict_epoch,
        "init_snapshot": args.init_snapshot,
        "slice_hours": args.slice_hours,
        "replay_era_auto": args.replay_era_auto,
        "era_selection_meta": era_meta,
        "gate": r,
        "non_vacuous": (r.get("trades_seen") or 0) > 0,
        "cert_label": (
            "CODE_COMPLETE_REPLAY"
            if era_meta.get("policy") in ("CODE_COMPLETE_REPLAY_ERA_AUTO", "rolling_window_slice_hours")
            else "EXPLICIT_EPOCH_REPLAY"
        ),
    }
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(out_path), "trades_seen": r.get("trades_seen"), "LEARNING_STATUS": r.get("LEARNING_STATUS")}, indent=2))
    ok = (r.get("trades_incomplete") or 1) == 0 and (r.get("trades_seen") or 0) > 0 and r.get("LEARNING_STATUS") == "ARMED"
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
