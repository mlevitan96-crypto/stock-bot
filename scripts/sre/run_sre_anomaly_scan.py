#!/usr/bin/env python3
"""
SRE Anomaly Scanner: read-only behavioral delta detection.
Compares last N minutes vs rolling baseline (e.g. 24h). Emits structured anomaly events.
Writes: reports/audit/SRE_STATUS.json, reports/audit/SRE_EVENTS.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
try:
    from src.contracts.sre_event_schema import (
        SRE_EVENT_SCHEMA_VERSION,
        build_sre_event,
        validate_sre_event,
    )
except ImportError:
    sys.path.insert(0, str(REPO / "src"))
    from contracts.sre_event_schema import (
        SRE_EVENT_SCHEMA_VERSION,
        build_sre_event,
        validate_sre_event,
    )


def _parse_ts(r: dict) -> datetime | None:
    for key in ("ts", "timestamp", "exit_ts", "entry_ts"):
        v = r.get(key)
        if v is None:
            continue
        try:
            if isinstance(v, (int, float)):
                return datetime.fromtimestamp(float(v), tz=timezone.utc)
            s = str(v).replace("Z", "+00:00").strip()[:26]
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return None


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _count_in_window(path: Path, cutoff: datetime, key_ts: str = "timestamp") -> int:
    n = 0
    for rec in _iter_jsonl(path):
        ts = _parse_ts(rec) or _parse_ts({key_ts: rec.get(key_ts)})
        if ts and ts >= cutoff:
            n += 1
    return n


def _exits_in_window(base: Path, cutoff: datetime) -> list[dict]:
    path = base / "logs" / "exit_attribution.jsonl"
    out = []
    for rec in _iter_jsonl(path):
        ts = _parse_ts(rec)
        if ts and ts >= cutoff:
            out.append(rec)
    return out


def _blocks_in_window(base: Path, cutoff: datetime) -> list[dict]:
    path = base / "state" / "blocked_trades.jsonl"
    out = []
    for rec in _iter_jsonl(path):
        ts = _parse_ts(rec)
        if ts and ts >= cutoff:
            out.append(rec)
    return out


def _b2_suppressions_in_window(base: Path, cutoff: datetime) -> list[dict]:
    path = base / "logs" / "b2_suppressed_signal_decay.jsonl"
    out = []
    for rec in _iter_jsonl(path):
        ts = _parse_ts(rec)
        if ts and ts >= cutoff:
            out.append(rec)
    return out


def run_scan(base: Path, observed_minutes: int = 10, baseline_hours: float = 24.0) -> tuple[list[dict], str]:
    """
    Run read-only anomaly scan. Returns (list of SRE events, overall_status).
    overall_status: OK | ANOMALIES_DETECTED
    """
    now = datetime.now(timezone.utc)
    observed_end = now
    observed_start = now - timedelta(minutes=observed_minutes)
    baseline_start = now - timedelta(hours=baseline_hours)

    events: list[dict] = []
    ts_iso = now.isoformat()

    # --- Observed window counts ---
    exits_observed = _exits_in_window(base, observed_start)
    blocks_observed = _blocks_in_window(base, observed_start)
    b2_observed = _b2_suppressions_in_window(base, observed_start)

    observed_minutes_f = max(0.01, observed_minutes)
    rate_exits_obs = len(exits_observed) / observed_minutes_f
    rate_blocks_obs = len(blocks_observed) / observed_minutes_f

    # --- Baseline window counts (full baseline period) ---
    exits_baseline = _exits_in_window(base, baseline_start)
    blocks_baseline = _blocks_in_window(base, baseline_start)
    baseline_hours_f = max(0.01, baseline_hours)
    baseline_minutes_f = baseline_hours_f * 60
    rate_exits_base = len(exits_baseline) / baseline_minutes_f
    rate_blocks_base = len(blocks_baseline) / baseline_minutes_f

    # --- Rate anomaly: exit rate deviates strongly from baseline ---
    if baseline_minutes_f > 0 and rate_exits_base > 0:
        delta_rate = rate_exits_obs - rate_exits_base
        pct = (delta_rate / rate_exits_base) * 100 if rate_exits_base else 0
        if abs(pct) > 80:  # >80% change
            conf = "HIGH" if abs(pct) > 150 else "MED"
            ev = build_sre_event(
                event_type="RATE_ANOMALY",
                metric_name="exit_rate_per_min",
                baseline_window=f"last_{baseline_hours}h",
                observed_window=f"last_{observed_minutes}m",
                baseline_value=round(rate_exits_base, 4),
                observed_value=round(rate_exits_obs, 4),
                delta=round(delta_rate, 4),
                confidence=conf,
                timestamp=ts_iso,
                notes=f"Exit rate changed {pct:.1f}% vs baseline.",
            )
            ev["economic_impact"] = True
            events.append(ev)

    # --- Block rate anomaly ---
    if baseline_minutes_f > 0 and (rate_blocks_base > 0 or rate_blocks_obs > 0):
        delta_rate = rate_blocks_obs - rate_blocks_base
        if rate_blocks_base > 0:
            pct = (delta_rate / rate_blocks_base) * 100
        else:
            pct = 100.0 if rate_blocks_obs > 0 else 0.0
        if abs(pct) > 80:
            conf = "HIGH" if abs(pct) > 150 else "MED"
            ev = build_sre_event(
                event_type="RATE_ANOMALY",
                metric_name="blocked_trades_per_min",
                baseline_window=f"last_{baseline_hours}h",
                observed_window=f"last_{observed_minutes}m",
                baseline_value=round(rate_blocks_base, 4),
                observed_value=round(rate_blocks_obs, 4),
                delta=round(delta_rate, 4),
                confidence=conf,
                timestamp=ts_iso,
                notes=f"Block rate changed {pct:.1f}% vs baseline.",
            )
            ev["economic_impact"] = True
            events.append(ev)

    # --- Silence anomaly: no exits in observed window when baseline had activity ---
    if len(exits_observed) == 0 and len(exits_baseline) > 5:
        ev = build_sre_event(
            event_type="SILENCE_ANOMALY",
            metric_name="exit_count",
            baseline_window=f"last_{baseline_hours}h",
            observed_window=f"last_{observed_minutes}m",
            baseline_value=len(exits_baseline),
            observed_value=0,
            delta=-len(exits_baseline),
            confidence="MED",
            timestamp=ts_iso,
            notes="No exits in observed window; baseline had activity. Possible pipeline stall or market closed.",
        )
        ev["economic_impact"] = True
        events.append(ev)

    # --- Distribution drift: exit reason mix in observed vs baseline ---
    reasons_base: Counter = Counter()
    for r in exits_baseline:
        reason = (r.get("exit_reason") or r.get("exit_reason_code") or "unknown")
        if isinstance(reason, str) and "signal_decay" in reason.lower():
            reason = "signal_decay"
        reasons_base[reason] += 1
    reasons_obs: Counter = Counter()
    for r in exits_observed:
        reason = (r.get("exit_reason") or r.get("exit_reason_code") or "unknown")
        if isinstance(reason, str) and "signal_decay" in reason.lower():
            reason = "signal_decay"
        reasons_obs[reason] += 1

    total_base = sum(reasons_base.values()) or 1
    total_obs = sum(reasons_obs.values()) or 1
    decay_share_base = reasons_base.get("signal_decay", 0) / total_base
    decay_share_obs = reasons_obs.get("signal_decay", 0) / total_obs
    drift_pct = abs(decay_share_obs - decay_share_base) * 100
    if drift_pct > 25 and total_obs >= 3:
        ev = build_sre_event(
            event_type="DISTRIBUTION_DRIFT",
            metric_name="exit_reason_signal_decay_share",
            baseline_window=f"last_{baseline_hours}h",
            observed_window=f"last_{observed_minutes}m",
            baseline_value=round(decay_share_base, 4),
            observed_value=round(decay_share_obs, 4),
            delta=round(decay_share_obs - decay_share_base, 4),
            confidence="MED" if drift_pct > 40 else "LOW",
            timestamp=ts_iso,
            notes=f"Signal-decay share of exits drifted {drift_pct:.1f}% vs baseline.",
        )
        ev["economic_impact"] = True
        events.append(ev)

    # --- Asymmetry: loss concentration (e.g. one symbol or one reason dominates losses) ---
    pnls = []
    for r in exits_observed:
        pnl = r.get("pnl") or r.get("realized_pnl") or r.get("total_pnl_attribution_usd")
        if pnl is not None:
            try:
                pnls.append(float(pnl))
            except (TypeError, ValueError):
                pass
    if len(pnls) >= 5:
        total_pnl = sum(pnls)
        if total_pnl < 0:
            worst = min(pnls)
            if worst < 0 and abs(worst) > abs(total_pnl) * 0.5:
                ev = build_sre_event(
                    event_type="ASYMMETRY_FLAG",
                    metric_name="loss_concentration",
                    baseline_window=f"last_{baseline_hours}h",
                    observed_window=f"last_{observed_minutes}m",
                    baseline_value="N/A",
                    observed_value=round(worst, 2),
                    delta=round(total_pnl, 2),
                    confidence="MED",
                    timestamp=ts_iso,
                    notes="Single-trade or concentrated loss dominates observed window PnL.",
                )
                ev["economic_impact"] = True
                events.append(ev)

    # --- Expectation violation: B2 enabled but high early signal_decay exits (B2 should suppress) ---
    b2_path = base / "logs" / "b2_suppressed_signal_decay.jsonl"
    if b2_path.exists() and len(exits_observed) >= 3:
        signal_decay_exits = sum(1 for r in exits_observed if (r.get("exit_reason") or "").lower().startswith("signal_decay"))
        if signal_decay_exits > len(exits_observed) * 0.6 and len(b2_observed) == 0:
            ev = build_sre_event(
                event_type="EXPECTATION_VIOLATION",
                metric_name="b2_suppression_vs_signal_decay_exits",
                baseline_window=f"last_{baseline_hours}h",
                observed_window=f"last_{observed_minutes}m",
                baseline_value="B2 may suppress early signal_decay",
                observed_value=f"{signal_decay_exits} signal_decay exits, 0 B2 suppressions",
                delta="expectation_mismatch",
                confidence="LOW",
                timestamp=ts_iso,
                notes="High signal_decay exits with no B2 suppressions logged; B2 may be off or path missing.",
            )
            ev["economic_impact"] = True
            events.append(ev)

    overall = "ANOMALIES_DETECTED" if events else "OK"
    return events, overall


def _ingest_automation_anomalies(base: Path, audit_dir: Path, now_iso: str) -> bool:
    """
    Read GOVERNANCE_AUTOMATION_STATUS.json. If status is anomalies, write
    SRE_AUTOMATION_ANOMALY_<date>.md and return True (soft alert for behavioral correlation).
    SRE does not depend on automations to run; this is additive.
    """
    status_path = audit_dir / "GOVERNANCE_AUTOMATION_STATUS.json"
    if not status_path.exists():
        return False
    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    status = data.get("status") or ("anomalies" if data.get("anomalies_detected") else "ok")
    if status != "anomalies":
        return False
    checks = data.get("checks") or {}
    details = data.get("details") or data.get("anomalies") or []
    ts = data.get("run_ts_utc") or data.get("timestamp") or now_iso
    date_str = ts[:10] if len(ts) >= 10 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    failed = [k for k, v in checks.items() if v == "fail"]
    tags = []
    if "repo_structure" in failed or "no_deprecated_dirs" in failed:
        tags.append("REPO_DRIFT")
    if "governance_contracts_present" in failed or "config_drift" in failed:
        tags.append("GOVERNANCE_DRIFT")
    if "no_clawdbot_moltbot" in failed:
        tags.append("GOVERNANCE_DRIFT")
    if not tags:
        tags.append("AUTOMATION_ANOMALY")
    md_lines = [
        "# SRE Automation Anomaly Report",
        "",
        f"**Date:** {date_str}",
        f"**Governance status run (UTC):** {ts}",
        "",
        "Cursor Automations (Governance Integrity) reported anomalies. SRE ingests these as behavioral/repo signals.",
        "",
        "## Failed checks",
        "",
    ]
    for k in failed:
        md_lines.append(f"- {k}")
    md_lines.extend([
        "",
        "## Details",
        "",
    ])
    for d in details:
        md_lines.append(f"- {d}")
    md_lines.extend([
        "",
        "## Tags",
        "",
        " ".join(tags),
        "",
        "## Recommended follow-ups",
        "",
        "- Resolve failed checks (run `python scripts/automations/run_governance_integrity_once.py` to re-check).",
        "- Check for open GitHub issues created by Security Review or Governance Integrity automations.",
        "- Do not deploy on automation anomalies alone; correlate with runtime and CSA.",
        "",
    ])
    out_path = audit_dir / f"SRE_AUTOMATION_ANOMALY_{date_str}.md"
    out_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_path} (automation anomalies ingested)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="SRE anomaly scan (read-only)")
    ap.add_argument("--base-dir", default="", help="Repo root")
    ap.add_argument("--observed-minutes", type=int, default=10, help="Observed window minutes")
    ap.add_argument("--baseline-hours", type=float, default=24.0, help="Baseline window hours")
    args = ap.parse_args()

    base = Path(args.base_dir).resolve() if args.base_dir else REPO
    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    try:
        events, overall_status = run_scan(
            base,
            observed_minutes=args.observed_minutes,
            baseline_hours=args.baseline_hours,
        )
    except Exception as e:
        audit_dir.mkdir(parents=True, exist_ok=True)
        (audit_dir / "SRE_IMPLEMENTATION_BLOCKERS.md").write_text(
            f"SRE scan failed: {e}\n",
            encoding="utf-8",
        )
        print(f"SRE scan failed: {e}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc).isoformat()

    # Validate and write events
    events_valid = []
    for ev in events:
        ok, issues = validate_sre_event(ev)
        if not ok:
            continue
        events_valid.append(ev)

    automation_anomalies = _ingest_automation_anomalies(base, audit_dir, now)
    status = {
        "overall_status": overall_status,
        "scan_ts": now,
        "schema_version": SRE_EVENT_SCHEMA_VERSION,
        "observed_minutes": args.observed_minutes,
        "baseline_hours": args.baseline_hours,
        "event_count": len(events_valid),
        "automation_anomalies_present": automation_anomalies,
    }

    (audit_dir / "SRE_STATUS.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    with open(audit_dir / "SRE_EVENTS.jsonl", "w", encoding="utf-8") as f:
        for ev in events_valid:
            f.write(json.dumps(ev, default=str) + "\n")

    print(f"SRE status: {overall_status} ({len(events_valid)} events)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
