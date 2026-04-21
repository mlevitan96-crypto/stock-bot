#!/usr/bin/env python3
"""
Forensic scan: find UTC instant when entry OFI + exit slippage/fee telemetry became present
in production JSONL (data-proof anchor for STRICT_EPOCH_START).

Scans (append order):
  logs/entry_snapshots.jsonl — first row with finite ofi_l1_roll_60s_sum (+ optional 300s)
  logs/exit_attribution.jsonl — first row with finite exit_slippage_bps AND fees_usd present

Proposed anchor = max(entry_ts, exit_ts) so both subsystems are live.

Usage:
  PYTHONPATH=. python3 scripts/_tmp_schema_audit.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _parse_ts(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        s = str(v).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (TypeError, ValueError):
        return None


def _finite(x: Any) -> bool:
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def _scan_entry_snapshots(path: Path) -> Tuple[Optional[Dict[str, Any]], int]:
    """First entry_snapshot row with OFI L1 60s sum present and finite."""
    first: Optional[Dict[str, Any]] = None
    n = 0
    if not path.is_file():
        return None, 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            n += 1
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            if rec.get("msg") != "entry_snapshot":
                continue
            if "ofi_l1_roll_60s_sum" not in rec:
                continue
            if not _finite(rec.get("ofi_l1_roll_60s_sum")):
                continue
            ts = _parse_ts(rec.get("timestamp_utc"))
            if ts is None:
                continue
            first = {
                "line_number": n,
                "timestamp_utc": rec.get("timestamp_utc"),
                "epoch_utc": ts,
                "symbol": rec.get("symbol"),
                "order_id": rec.get("order_id"),
                "ofi_l1_roll_60s_sum": rec.get("ofi_l1_roll_60s_sum"),
                "ofi_l1_roll_300s_sum": rec.get("ofi_l1_roll_300s_sum"),
            }
            break
    return first, n


def _entry_uw_dense(eu: Any) -> bool:
    """Alpha 11 / ML tripwire style: persisted UW blob with finite sentiment or earnings proximity."""
    if not isinstance(eu, dict) or not eu:
        return False
    for k in ("sentiment_score", "earnings_proximity"):
        if k in eu and _finite(eu.get(k)):
            return True
    comp = eu.get("components")
    if isinstance(comp, dict) and comp:
        return True
    return False


def _scan_exit_dense(path: Path) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    First exit row where broker economics + UW density are present.
    Note: some hosts never emitted ``exit_slippage_bps`` in JSONL; we require ``fees_usd`` and dense ``entry_uw``.
    If ``exit_slippage_bps`` exists, it is preferred as an additional signal on the same row.
    """
    first: Optional[Dict[str, Any]] = None
    n = 0
    if not path.is_file():
        return None, 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            n += 1
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            if "fees_usd" not in rec:
                continue
            if not _entry_uw_dense(rec.get("entry_uw")):
                continue
            ex = _parse_ts(rec.get("exit_ts") or rec.get("timestamp") or rec.get("ts"))
            if ex is None:
                continue
            slip = rec.get("exit_slippage_bps")
            first = {
                "line_number": n,
                "exit_ts": rec.get("exit_ts"),
                "epoch_utc": ex,
                "symbol": rec.get("symbol"),
                "trade_id": rec.get("trade_id"),
                "fees_usd": rec.get("fees_usd"),
                "exit_slippage_bps": slip if slip is not None else None,
                "entry_uw_keys_sample": list(rec["entry_uw"].keys())[:16] if isinstance(rec.get("entry_uw"), dict) else [],
            }
            break
    return first, n


def _sustained_density(
    path: Path,
    *,
    is_entry: bool,
    anchor_epoch: float,
    sample_lines: int = 800,
) -> Tuple[int, int, float]:
    """After anchor: count rows in file tail that still satisfy schema (same criteria as first hit)."""
    ok = 0
    tot = 0
    if not path.is_file():
        return 0, 0, 0.0
    buf: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            buf.append(line)
            if len(buf) > sample_lines * 2:
                buf = buf[-sample_lines * 2 :]
    for line in buf[-sample_lines:]:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        ts_raw = (
            rec.get("timestamp_utc")
            if is_entry
            else (rec.get("exit_ts") or rec.get("timestamp") or rec.get("ts"))
        )
        ts = _parse_ts(ts_raw)
        if ts is None or ts < anchor_epoch:
            continue
        tot += 1
        if is_entry:
            if rec.get("msg") == "entry_snapshot" and _finite(rec.get("ofi_l1_roll_60s_sum")):
                ok += 1
        else:
            if "fees_usd" in rec and _entry_uw_dense(rec.get("entry_uw")):
                ok += 1
    pct = (100.0 * ok / tot) if tot else 0.0
    return ok, tot, pct


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--sample-lines", type=int, default=800)
    args = ap.parse_args()
    root = args.root.resolve()
    ent_path = root / "logs" / "entry_snapshots.jsonl"
    ex_path = root / "logs" / "exit_attribution.jsonl"

    ent_first, ent_lines = _scan_entry_snapshots(ent_path)
    ex_first, ex_lines = _scan_exit_dense(ex_path)

    out: Dict[str, Any] = {
        "root": str(root),
        "fields_scanned": {
            "entry_snapshots": [
                "msg==entry_snapshot",
                "finite ofi_l1_roll_60s_sum",
                "timestamp_utc",
            ],
            "exit_attribution": [
                "fees_usd key present (broker economics)",
                "entry_uw with finite sentiment_score or earnings_proximity OR nonempty components",
                "exit_ts",
                "exit_slippage_bps when present (optional; many logs omit this key)",
            ],
        },
        "entry_snapshots_path": str(ent_path),
        "exit_attribution_path": str(ex_path),
        "total_lines_seen_entry_file": ent_lines,
        "total_lines_seen_exit_file": ex_lines,
        "first_dense_entry": ent_first,
        "first_dense_exit_fees_uw": ex_first,
    }

    epochs: List[float] = []
    if ent_first and ent_first.get("epoch_utc") is not None:
        epochs.append(float(ent_first["epoch_utc"]))
    if ex_first and ex_first.get("epoch_utc") is not None:
        epochs.append(float(ex_first["epoch_utc"]))

    if not epochs:
        out["error"] = "Could not find schema hits; check log paths and content."
        print(json.dumps(out, indent=2))
        return 2

    anchor = max(epochs)
    out["proposed_STRICT_EPOCH_START"] = anchor
    out["proposed_STRICT_EPOCH_START_iso_utc"] = datetime.fromtimestamp(anchor, tz=timezone.utc).isoformat()

    out["post_anchor_sustained"] = {
        "entry_snapshots": _sustained_density(
            ent_path, is_entry=True, anchor_epoch=anchor, sample_lines=args.sample_lines
        ),
        "exit_attribution": _sustained_density(
            ex_path, is_entry=False, anchor_epoch=anchor, sample_lines=args.sample_lines
        ),
    }
    # tuple -> list for JSON
    ps = out["post_anchor_sustained"]
    for k, v in ps.items():
        ps[k] = {"ok": v[0], "eligible_tail_rows": v[1], "density_pct": round(v[2], 2)}

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
