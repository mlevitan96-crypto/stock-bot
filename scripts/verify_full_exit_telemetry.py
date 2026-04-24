#!/usr/bin/env python3
"""
Phase 7 — Full exit telemetry verification.
Checks exit_event.jsonl (and exit_attribution.jsonl) for required fields:
- All fields present in exit_event.jsonl
- No missing exit components (full vector)
- No missing high_water / MFE / MAE
- No missing entry→exit deltas
- No missing composite_at_exit
- No missing regime or UW conviction
- No missing enriched signals
- No missing exit_reason_code
- No missing exit_quality_metrics
Writes: reports/telemetry/EXIT_TELEMETRY_VERIFICATION.md
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# Required keys on each EXIT_EVENT record
EXIT_EVENT_REQUIRED = [
    "event_type", "trade_id", "symbol", "entry_ts", "exit_ts",
    "entry_price", "exit_price", "exit_reason_code", "exit_components",
    "entry_signal_snapshot", "exit_signal_snapshot", "entry_exit_deltas",
    "exit_quality_metrics", "regime_at_entry", "regime_at_exit",
    "uw_conviction_entry", "uw_conviction_exit", "composite_at_entry", "composite_at_exit",
    "composite_components_entry", "composite_components_exit",
]
EXIT_QUALITY_KEYS = ["mfe", "mae", "high_water", "low_water", "time_in_trade_sec", "giveback", "saved_loss", "left_money"]
DELTA_KEYS = [
    "delta_composite", "delta_flow_conviction", "delta_dark_pool_notional",
    "delta_sentiment", "delta_regime", "delta_gamma", "delta_vol",
    "delta_iv_rank", "delta_squeeze_score", "delta_sector_strength",
]
CANONICAL_COMPONENTS = [
    "exit_flow_deterioration", "exit_volatility_spike", "exit_regime_shift",
    "exit_sentiment_reversal", "exit_gamma_collapse", "exit_dark_pool_reversal",
    "exit_insider_shift", "exit_sector_rotation", "exit_time_decay",
    "exit_microstructure_noise", "exit_score_deterioration",
]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def check_record(rec: Dict[str, Any], index: int) -> List[str]:
    issues: List[str] = []
    for k in EXIT_EVENT_REQUIRED:
        if k not in rec:
            issues.append(f"missing_key:{k}")
    if rec.get("event_type") != "EXIT_EVENT":
        issues.append("event_type_not_EXIT_EVENT")
    exit_components = rec.get("exit_components") or {}
    for c in CANONICAL_COMPONENTS:
        if c not in exit_components:
            issues.append(f"missing_component:{c}")
        else:
            comp = exit_components[c]
            if not isinstance(comp, dict):
                issues.append(f"component_not_dict:{c}")
            else:
                for sub in ("raw_value", "normalized_value", "contribution_to_exit_score"):
                    if sub not in comp:
                        issues.append(f"component_missing_sub:{c}.{sub}")
    eq = rec.get("exit_quality_metrics") or {}
    for q in EXIT_QUALITY_KEYS:
        if q not in eq:
            issues.append(f"exit_quality_missing:{q}")
    deltas = rec.get("entry_exit_deltas") or {}
    for d in DELTA_KEYS:
        if d not in deltas:
            issues.append(f"delta_missing:{d}")
    if "composite_at_exit" not in rec:
        issues.append("missing_composite_at_exit")
    if "regime_at_exit" not in rec:
        issues.append("missing_regime_at_exit")
    if "uw_conviction_exit" not in rec:
        issues.append("missing_uw_conviction_exit")
    if not rec.get("exit_signal_snapshot"):
        issues.append("missing_exit_signal_snapshot")
    if not str(rec.get("exit_reason_code", "")).strip():
        issues.append("missing_exit_reason_code")
    return issues


def main() -> int:
    base = Path(os.environ.get("REPO", REPO))
    exit_event_path = base / "logs" / "exit_event.jsonl"
    exit_attr_path = base / "logs" / "exit_attribution.jsonl"
    report_path = base / "reports" / "telemetry" / "EXIT_TELEMETRY_VERIFICATION.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    events = load_jsonl(exit_event_path)
    exit_attr = load_jsonl(exit_attr_path)

    all_issues: List[str] = []
    record_issues: List[Dict[str, Any]] = []
    for i, rec in enumerate(events):
        issues = check_record(rec, i)
        if issues:
            all_issues.extend(issues)
            record_issues.append({"index": i, "trade_id": rec.get("trade_id"), "issues": issues})

    total = len(events)
    ok = total - len(record_issues)
    pct = (ok / total * 100) if total else 0

    lines = [
        "# Exit Telemetry Verification",
        "",
        f"**Source:** `logs/exit_event.jsonl`",
        f"**Records checked:** {total}",
        f"**Records with all required fields:** {ok} ({pct:.1f}%)",
        "",
        "## Required fields (exit_event)",
        "",
        "| Field | Present |",
        "|-------|--------|",
    ]
    for k in EXIT_EVENT_REQUIRED:
        present = sum(1 for r in events if k in r)
        lines.append(f"| {k} | {present}/{total} |")
    lines.extend([
        "",
        "## Exit quality metrics (must be present)",
        "",
        "| Key | Present |",
        "|-----|--------|",
    ])
    for q in EXIT_QUALITY_KEYS:
        present = sum(1 for r in events if q in (r.get("exit_quality_metrics") or {}))
        lines.append(f"| {q} | {present}/{total} |")
    lines.extend([
        "",
        "## Entry→exit deltas",
        "",
        "| Delta | Present |",
        "|-------|--------|",
    ])
    for d in DELTA_KEYS:
        present = sum(1 for r in events if d in (r.get("entry_exit_deltas") or {}))
        lines.append(f"| {d} | {present}/{total} |")
    lines.extend([
        "",
        "## Exit components (canonical vector)",
        "",
        "| Component | Present |",
        "|-----------|--------|",
    ])
    for c in CANONICAL_COMPONENTS:
        present = sum(1 for r in events if (r.get("exit_components") or {}).get(c) is not None)
        lines.append(f"| {c} | {present}/{total} |")
    lines.append("")
    if record_issues:
        lines.append("## Records with issues (sample)")
        lines.append("")
        for item in record_issues[:20]:
            lines.append(f"- Index {item['index']} trade_id={item.get('trade_id')}: {item['issues']}")
        lines.append("")
    lines.append(f"**exit_attribution.jsonl lines:** {len(exit_attr)}")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report_path}")
    return 0 if not record_issues else 1


if __name__ == "__main__":
    sys.exit(main())
