#!/usr/bin/env python3
"""
Read-only: count Alpaca opens (from open_<SYM>_<ISO> trade_id) and terminal closes after STRICT_EPOCH_START.
Run on droplet: python3 scripts/alpaca_post_era_trade_activity_check.py [--root /root/stock-bot]
Does not modify trading, learning, or telemetry.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_iso_epoch(s: object) -> float | None:
    if not s or not isinstance(s, str):
        return None
    try:
        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")


def open_epoch_from_trade_id(tid: object) -> tuple[float | None, str | None, str | None]:
    m = TID_RE.match(str(tid or "").strip())
    if not m:
        return None, None, None
    sym = m.group(1)
    ep = parse_iso_epoch(m.group(2))
    return ep, str(tid), sym


def read_strict_epoch_from_latest_summary(reports: Path) -> tuple[float, Path | None]:
    """Prefer strict-era entry-filter summary; else newest ALPACA_STRICT*SUMMARY*.md."""
    strict_epoch = 1775581260.0
    chosen: Path | None = None
    entry_summaries = sorted(
        reports.glob("ALPACA_STRICT*ENTRY*SUMMARY*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    candidates = entry_summaries or sorted(
        reports.glob("ALPACA_STRICT*SUMMARY*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return strict_epoch, None
    chosen = candidates[0]
    try:
        txt = chosen.read_text(encoding="utf-8", errors="replace")
        mm = re.search(r"STRICT_EPOCH_START[^0-9]*`([0-9.]+)`", txt)
        if mm:
            strict_epoch = float(mm.group(1))
    except Exception:
        pass
    return strict_epoch, chosen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("/root/stock-bot"))
    args = ap.parse_args()
    root = args.root.resolve()
    reports = root / "reports"
    strict_epoch, proof_path = read_strict_epoch_from_latest_summary(reports)
    strict_iso = datetime.fromtimestamp(strict_epoch, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    print("=== PHASE 0 ===")
    print("proof_summary_file", str(proof_path) if proof_path else "none")
    print("strict_epoch_start", strict_epoch)
    print("strict_epoch_start_iso", strict_iso)

    post_opens: dict[str, dict] = {}

    def add_open(tid: object, src: str) -> None:
        ep, tid_s, sym = open_epoch_from_trade_id(tid)
        if ep is None or ep < strict_epoch or not tid_s:
            return
        if tid_s not in post_opens:
            post_opens[tid_s] = {
                "symbol": sym,
                "open_iso": datetime.fromtimestamp(ep, tz=timezone.utc).isoformat(),
                "source": src,
            }

    apath = root / "logs" / "attribution.jsonl"
    if apath.exists():
        for line in apath.open(encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            tid = rec.get("trade_id")
            if tid and str(tid).startswith("open_"):
                add_open(tid, "attribution.jsonl")

    rpath = root / "logs" / "run.jsonl"
    if rpath.exists():
        for line in rpath.open(encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event_type") != "trade_intent":
                continue
            if str(rec.get("decision_outcome", "")).lower() != "entered":
                continue
            for k in ("trade_id", "canonical_trade_id", "pending_trade_id"):
                tid = rec.get(k)
                if tid and str(tid).startswith("open_"):
                    add_open(tid, "run.jsonl")

    unified = root / "logs" / "alpaca_unified_events.jsonl"
    if unified.exists():
        for line in unified.open(encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            et = rec.get("event_type") or rec.get("type")
            if et != "alpaca_entry_attribution":
                continue
            tid = rec.get("trade_id") or rec.get("trade_key")
            if tid and str(tid).startswith("open_"):
                add_open(tid, "alpaca_unified_events.jsonl")

    epath = root / "logs" / "exit_attribution.jsonl"
    if epath.exists():
        for line in epath.open(encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            tid = rec.get("trade_id")
            if tid and str(tid).startswith("open_"):
                add_open(tid, "exit_attribution.jsonl")

    print("=== PHASE 1 ===")
    print("count_post_era_opens", len(post_opens))
    for i, (tid, info) in enumerate(list(post_opens.items())[:5]):
        print(
            "sample_open",
            i + 1,
            info["symbol"],
            tid,
            info["open_iso"],
            info["source"],
        )

    post_closes: list[dict] = []
    unified_keys: set[tuple[str, float]] = set()

    if unified.exists():
        for line in unified.open(encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            et = rec.get("event_type") or rec.get("type")
            if et != "alpaca_exit_attribution" or not rec.get("terminal_close"):
                continue
            ts = rec.get("timestamp") or rec.get("ts") or rec.get("exit_timestamp")
            cep = parse_iso_epoch(ts)
            if cep is None or cep < strict_epoch:
                continue
            tid = str(rec.get("trade_id") or "")
            sym = str(rec.get("symbol") or "").upper()
            iso = datetime.fromtimestamp(cep, tz=timezone.utc).isoformat()
            unified_keys.add((tid, round(cep, 3)))
            post_closes.append(
                {
                    "trade_id": tid,
                    "symbol": sym,
                    "close_iso": iso,
                    "source": "alpaca_unified_events.jsonl",
                }
            )

    if epath.exists():
        for line in epath.open(encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = rec.get("timestamp") or rec.get("exit_timestamp")
            cep = parse_iso_epoch(ts)
            if cep is None or cep < strict_epoch:
                continue
            tid = str(rec.get("trade_id") or "")
            sym = str(rec.get("symbol") or "").upper()
            key = (tid, round(cep, 3))
            if key in unified_keys:
                continue
            iso = datetime.fromtimestamp(cep, tz=timezone.utc).isoformat()
            post_closes.append(
                {
                    "trade_id": tid,
                    "symbol": sym,
                    "close_iso": iso,
                    "source": "exit_attribution.jsonl",
                }
            )

    print("=== PHASE 2 ===")
    print("count_post_era_closes", len(post_closes))
    for i, c in enumerate(post_closes[:5]):
        print(
            "sample_close",
            i + 1,
            c["symbol"],
            c["trade_id"],
            c["close_iso"],
            c["source"],
        )

    print("=== PHASE 3 ===")
    n_o = len(post_opens)
    n_c = len(post_closes)
    if n_o == 0:
        status = "STATUS_C"
        note = "No opens post-era (execution/signal issue — escalate)"
    elif n_c == 0:
        status = "STATUS_A"
        note = "Opens exist, closes pending (expected — wait)"
    else:
        status = "STATUS_B"
        note = "Opens and closes exist (learning should arm on next strict run)"
    print(status, "-", note)
    print("=== EXECUTION NOTE ===")
    print(
        "LEARNING_STATUS does not disable stock-bot execution; this check is log-only."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
