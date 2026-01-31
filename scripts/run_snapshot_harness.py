#!/usr/bin/env python3
"""
Snapshot dry-run harness — produces snapshots from master_trade_log without trading.
NO ORDERS PLACED. Consumes artifacts only (no live UW calls).
Output: logs/signal_snapshots_harness_<DATE>.jsonl, reports/SNAPSHOT_HARNESS_VERIFICATION_<DATE>.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _artifact_ts(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        stat = path.stat()
        return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--symbols", default="AAPL")
    ap.add_argument("--max-events", type=int, default=25)
    ap.add_argument("--mode", default="PAPER", choices=["LIVE", "PAPER"])
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()

    base = Path(args.base_dir) if args.base_dir else REPO
    target_date = args.date
    symbols_set = {s.strip().upper() for s in args.symbols.split(",") if s.strip()}
    max_events = max(1, args.max_events)
    mode = args.mode

    from telemetry.signal_snapshot_writer import (
        build_snapshot_record,
        write_snapshot,
        validate_snapshot_record,
        REQUIRED_KEYS,
    )

    mtl_path = base / "logs" / "master_trade_log.jsonl"
    records = []
    if mtl_path.exists():
        with mtl_path.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        # Prefer date-filtered; fallback to last N
        for line in reversed(lines[-max_events * 3:]):  # buffer for filtering
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = rec.get("entry_ts") or rec.get("exit_ts") or rec.get("timestamp") or ""
            if target_date and not str(ts).startswith(target_date):
                continue
            sym = str(rec.get("symbol", "")).upper()
            if symbols_set and sym not in symbols_set:
                continue
            records.append(rec)
            if len(records) >= max_events:
                break
        records.reverse()
        if not records and lines:
            # Fallback: last N lines, warn
            for line in lines[-max_events:]:
                try:
                    rec = json.loads(line.strip())
                    records.append(rec)
                except Exception:
                    pass

    if not records:
        sys.stderr.write(
            f"WARN: No master_trade_log records for {target_date} symbols {symbols_set}; "
            "using synthetic AAPL entry.\n"
        )
        records = [{
            "symbol": "AAPL",
            "trade_id": f"harness:{target_date}:AAPL",
            "entry_ts": f"{target_date}T15:30:00.000000+00:00",
            "exit_ts": None,
            "v2_score": 2.5,
            "entry_v2_score": 2.5,
            "feature_snapshot": {},
            "regime_snapshot": {"regime": "NEUTRAL"},
        }]

    # Artifact timestamps
    premarket_ts = _artifact_ts(base / "state" / "premarket_intel.json")
    postmarket_ts = _artifact_ts(base / "state" / "postmarket_intel.json")
    expanded_ts = _artifact_ts(base / "data" / "uw_expanded_intel.json")
    uw_artifacts_used = {
        "premarket_intel_ts": premarket_ts,
        "postmarket_intel_ts": postmarket_ts,
        "expanded_intel_ts": expanded_ts,
    }

    harness_path = base / "logs" / f"signal_snapshots_harness_{target_date}.jsonl"
    harness_path.parent.mkdir(parents=True, exist_ok=True)
    if harness_path.exists():
        harness_path.write_text("")  # overwrite for idempotent run

    written = 0
    schema_ok = 0
    schema_fail = 0
    comp_present = {}
    comp_defaulted = {}
    comp_missing = {}

    for rec in records:
        sym = str(rec.get("symbol", "")).upper()
        ts = rec.get("entry_ts") or rec.get("exit_ts") or rec.get("timestamp") or datetime.now(timezone.utc).isoformat()
        trade_id = rec.get("trade_id") or f"harness:{target_date}:{sym}"
        feats = rec.get("feature_snapshot") or {}
        regime_snap = rec.get("regime_snapshot") or {}
        regime_label = regime_snap.get("regime") if isinstance(regime_snap, dict) else None
        score = rec.get("v2_score") or rec.get("entry_v2_score") or rec.get("entry_v2_score")
        if score is None:
            score = 2.0
        composite_meta = {"components": feats, "component_contributions": feats, "component_sources": {}}

        # ENTRY_DECISION
        entry_rec = build_snapshot_record(
            symbol=sym,
            lifecycle_event="ENTRY_DECISION",
            mode=mode,
            composite_score_v2=float(score),
            freshness_factor=1.0,
            composite_meta=composite_meta,
            regime_label=regime_label,
            trade_id=trade_id,
            uw_artifacts_used=uw_artifacts_used,
            notes=["harness", "NO_ORDERS_PLACED"],
            timestamp_utc=ts,
        )
        ok, missing = validate_snapshot_record(entry_rec)
        if ok:
            schema_ok += 1
        else:
            schema_fail += 1
        if write_snapshot(base, entry_rec, harness_path):
            written += 1
        for c, v in (entry_rec.get("components") or {}).items():
            if isinstance(v, dict):
                if v.get("present"):
                    comp_present[c] = comp_present.get(c, 0) + 1
                elif v.get("defaulted"):
                    comp_defaulted[c] = comp_defaulted.get(c, 0) + 1
                else:
                    comp_missing[c] = comp_missing.get(c, 0) + 1

        # EXIT_DECISION if exit context exists
        if rec.get("exit_ts"):
            exit_score = rec.get("exit_v2_score") or rec.get("v2_score") or score
            entry_ts_iso = rec.get("entry_ts") or ts
            stable_tid = f"live:{sym}:{entry_ts_iso}" if entry_ts_iso else trade_id
            pos_side = (rec.get("side") or "long").lower()[:4]
            exit_rec = build_snapshot_record(
                symbol=sym,
                lifecycle_event="EXIT_DECISION",
                mode=mode,
                composite_score_v2=float(exit_score),
                freshness_factor=1.0,
                composite_meta=composite_meta,
                regime_label=regime_label,
                trade_id=stable_tid,
                entry_timestamp_utc=entry_ts_iso,
                side=pos_side,
                uw_artifacts_used=uw_artifacts_used,
                notes=["harness", "NO_ORDERS_PLACED", f"exit:{rec.get('exit_reason', '')}"],
                timestamp_utc=rec.get("exit_ts"),
            )
            ok, _ = validate_snapshot_record(exit_rec)
            if ok:
                schema_ok += 1
            else:
                schema_fail += 1
            if write_snapshot(base, exit_rec, harness_path):
                written += 1
            for c, v in (exit_rec.get("components") or {}).items():
                if isinstance(v, dict):
                    if v.get("present"):
                        comp_present[c] = comp_present.get(c, 0) + 1
                    elif v.get("defaulted"):
                        comp_defaulted[c] = comp_defaulted.get(c, 0) + 1
                    else:
                        comp_missing[c] = comp_missing.get(c, 0) + 1

    # Verification report
    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"SNAPSHOT_HARNESS_VERIFICATION_{target_date}.md"
    lines = [
        f"# Snapshot Harness Verification — {target_date}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
        f"- Snapshots written: {written}",
        f"- Schema validation passed: {schema_ok}",
        f"- Schema validation failed: {schema_fail}",
        f"- Required keys missing: {0 if schema_fail == 0 else 'see validation'}",
        "",
        "## Component tallies",
        "",
        "| Component | Present | Defaulted | Missing |",
        "|-----------|---------|-----------|---------|",
    ]
    all_comp = sorted(set(comp_present) | set(comp_defaulted) | set(comp_missing))
    for c in all_comp[:30]:
        p = comp_present.get(c, 0)
        d = comp_defaulted.get(c, 0)
        m = comp_missing.get(c, 0)
        lines.append(f"| {c} | {p} | {d} | {m} |")
    lines.extend([
        "",
        "## Artifact timestamps",
        "",
        f"- premarket_intel: {premarket_ts or 'N/A'}",
        f"- postmarket_intel: {postmarket_ts or 'N/A'}",
        f"- expanded_intel: {expanded_ts or 'N/A'}",
        "",
        "## NO ORDERS PLACED",
        "",
        "This harness produces snapshots from existing master_trade_log data. No orders were placed.",
        "",
        "---",
        "",
        "*Generated by scripts/run_snapshot_harness.py*",
        "",
    ])
    report_path.write_text("\n".join(lines), encoding="utf-8")

    if schema_fail > 0:
        sys.stderr.write(f"ERROR: {schema_fail} snapshot(s) failed schema validation\n")
        return 1
    print(f"Wrote {written} snapshots to {harness_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
