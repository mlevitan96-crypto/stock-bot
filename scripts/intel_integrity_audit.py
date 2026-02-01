#!/usr/bin/env python3
"""
Full Intelligence Integrity Audit (READ-ONLY)
=============================================
Produces 9 reports under reports/:
  INTEL_EXPECTED_INVENTORY.md
  INTEL_DATA_PRESENCE.md
  INTEL_SIGNAL_FEATURES.md
  INTEL_SCORE_COMPONENTS.md
  INTEL_GATES.md
  INTEL_DECISION_TRACE.md
  INTEL_ARTIFACT_HEALTH.md
  INTEL_SILENT_FAILURES.md
  INTEL_SYSTEM_VERDICT.md

Uses config.registry for all paths. No code changes, no restarts.
Run from repo root: python scripts/intel_integrity_audit.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.registry import (
    CacheFiles,
    Directories,
    LogFiles,
    StateFiles,
    SignalComponents,
)

WINDOW_MIN = 30
REPORTS_DIR = ROOT / "reports"
TELEMETRY_ROOT = ROOT / "telemetry"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _since_minutes(minutes: int) -> datetime:
    return _now() - timedelta(minutes=minutes)


def _parse_ts(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        s = str(s).replace("Z", "+00:00").strip()
        if "T" not in s and " " in s:
            s = s.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _read_jsonl(path: Path, since_min: int | None = None, ts_key: str | None = None) -> list[dict]:
    out = []
    if not path.exists():
        return out
    since = _since_minutes(since_min) if since_min else None
    key = ts_key or "ts"
    if "system_events" in str(path):
        key = "timestamp"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            ts = _parse_ts(rec.get(key) or rec.get("ts") or rec.get("_dt") or rec.get("_ts") or rec.get("timestamp"))
            if since and ts and ts < since:
                continue
            out.append(rec)
        except Exception:
            continue
    return out


def _read_json(path: Path, default: dict | None = None) -> dict | list:
    if default is None:
        default = {}
    try:
        if path.exists() and path.stat().st_size > 0:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        pass
    return default


# ---------------------------------------------------------------------------
# 1) CANONICAL INTELLIGENCE INVENTORY
# ---------------------------------------------------------------------------
def build_expected_inventory() -> str:
    lines = [
        "# Canonical Intelligence Inventory",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        "**Scope:** Expected intelligence outputs the system is designed to produce.",
        "",
        "---",
        "",
        "## 1. Data sources",
        "",
        "| Source | Path / origin |",
        "|--------|----------------|",
    ]
    # From config.registry and main/dashboard usage
    data_sources = [
        ("Market (Alpaca)", "APIConfig.ALPACA_*; paper trades"),
        ("UW API (Unusual Whales)", "APIConfig.UW_BASE_URL; flow, dark pool, sentiment"),
        ("UW flow cache", str(CacheFiles.UW_FLOW_CACHE)),
        ("UW flow cache log", str(CacheFiles.UW_FLOW_CACHE_LOG)),
        ("Composite cache", str(CacheFiles.COMPOSITE_CACHE)),
        ("State: regime", str(StateFiles.REGIME_DETECTOR_STATE)),
        ("State: market context", str(StateFiles.MARKET_CONTEXT_V2)),
        ("State: regime posture", str(StateFiles.REGIME_POSTURE_STATE)),
        ("State: signal weights", str(StateFiles.SIGNAL_WEIGHTS)),
        ("State: internal positions", str(StateFiles.INTERNAL_POSITIONS)),
    ]
    for name, path in data_sources:
        lines.append(f"| {name} | `{path}` |")
    lines.extend([
        "",
        "## 2. Signal layers (Decision Intelligence Trace)",
        "",
        "From `telemetry/decision_intelligence_trace._comps_to_signal_layers`:",
        "",
        "- **alpha_signals**",
        "- **flow_signals**",
        "- **regime_signals**",
        "- **volatility_signals**",
        "- **dark_pool_signals**",
        "",
        "## 3. Feature / score component families",
        "",
        "From `config.registry.SignalComponents.ALL_COMPONENTS`:",
        "",
    ])
    for c in SignalComponents.ALL_COMPONENTS:
        lines.append(f"- `{c}`")
    lines.extend([
        "",
        "## 4. Score components (aggregation)",
        "",
        "Trace `aggregation.score_components` is built from the same component dict as signal layers (per-cluster scoring).",
        "",
        "## 5. Gates",
        "",
        "From `main.py` (append_gate_result):",
        "",
        "- **score_gate**",
        "- **capacity_gate**",
        "- **risk_gate**",
        "- **momentum_gate**",
        "- **directional_gate**",
        "- **displacement_gate**",
        "",
        "## 6. Trade intents",
        "",
        "- **trade_intent** — emitted to `logs/run.jsonl` (entry decisions: entered or blocked)",
        "- **exit_intent** — emitted to `logs/run.jsonl` (exit decisions)",
        "- **cycle / complete** — cycle summaries to `logs/run.jsonl`",
        "",
        "## 7. Post-trade / computed artifacts",
        "",
        "| Artifact | Path (under telemetry/<date>/computed/) |",
        "|----------|------------------------------------------|",
    ])
    artifacts = [
        ("entry_parity_details", "entry_parity_details.json"),
        ("live_vs_shadow_pnl", "live_vs_shadow_pnl.json"),
        ("shadow_vs_live_parity", "shadow_vs_live_parity.json"),
        ("feature_family_summary", "feature_family_summary.json"),
        ("exit_intel_completeness", "exit_intel_completeness.json"),
        ("score_distribution_curves", "score_distribution_curves.json"),
        ("signal_performance", "signal_performance.json"),
        ("signal_weight_recommendations", "signal_weight_recommendations.json"),
        ("feature_equalizer_builder", "feature_equalizer_builder.json"),
        ("feature_value_curves", "feature_value_curves.json"),
        ("long_short_analysis", "long_short_analysis.json"),
        ("regime_sector_feature_matrix", "regime_sector_feature_matrix.json"),
        ("regime_timeline", "regime_timeline.json"),
        ("replacement_telemetry_expanded", "replacement_telemetry_expanded.json"),
        ("pnl_windows", "pnl_windows.json"),
    ]
    for name, fname in artifacts:
        lines.append(f"| {name} | `{fname}` |")
    lines.extend([
        "",
        "## 8. Shadow artifacts",
        "",
        "Same as post-trade; shadow vs live parity is in `shadow_vs_live_parity`, `entry_parity_details`, `live_vs_shadow_pnl`.",
        "",
        "## 9. Dashboard-visible intelligence",
        "",
        "From `dashboard.py` computed API: live_vs_shadow_pnl, signal_performance, signal_weight_recommendations, score_distribution_curves, shadow_vs_live_parity, entry_parity_details, feature_family_summary, exit_intel_completeness.",
        "",
    ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 2) INGESTION & DATA PRESENCE
# ---------------------------------------------------------------------------
def build_data_presence() -> str:
    lines = [
        "# Ingestion & Data Presence Audit",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        "**Window:** N/A (file existence and non-empty payloads).",
        "",
        "---",
        "",
    ]
    checks = [
        ("UW flow cache", CacheFiles.UW_FLOW_CACHE, "json", "non-empty dict with flow/cluster data"),
        ("UW flow cache log", CacheFiles.UW_FLOW_CACHE_LOG, "jsonl", "lines with _ts"),
        ("Composite cache", CacheFiles.COMPOSITE_CACHE, "json", "composite clusters"),
        ("Run log", LogFiles.RUN, "jsonl", "event_type trade_intent/exit_intent/complete"),
        ("System events", LogFiles.SYSTEM_EVENTS, "jsonl", "event_type, timestamp"),
        ("Regime state", StateFiles.REGIME_DETECTOR_STATE, "json", "regime_label or equivalent"),
        ("Market context v2", StateFiles.MARKET_CONTEXT_V2, "json", "optional"),
        ("Signal weights", StateFiles.SIGNAL_WEIGHTS, "json", "optional"),
    ]
    for name, path, kind, note in checks:
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        empty = size == 0
        if kind == "json" and exists and size > 0:
            data = _read_json(path, default={})
            empty = (isinstance(data, dict) and len(data) == 0) or (isinstance(data, list) and len(data) == 0)
        status = "OK" if (exists and not empty) else ("EMPTY" if exists else "MISSING")
        lines.append(f"- **{name}** (`{path}`): exists={exists}, size={size}, status={status} — {note}")
    # Raw excerpts: last 3 timestamps from run.jsonl and system_events
    lines.append("")
    lines.append("## Evidence (timestamps)")
    for label, path, key in [
        ("Run log (last 3 _dt)", LogFiles.RUN, "_dt"),
        ("System events (last 3 timestamp)", LogFiles.SYSTEM_EVENTS, "timestamp"),
    ]:
        if path.exists():
            recs = _read_jsonl(path, since_min=None)[-3:]
            timestamps = [str(r.get(key) or r.get("ts") or r.get("_ts") or "?")[:22] for r in recs]
            lines.append(f"- **{label}:** {timestamps}")
        else:
            lines.append(f"- **{label}:** file missing")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3) SIGNAL & FEATURE COMPLETENESS (from run.jsonl last 30 min)
# ---------------------------------------------------------------------------
def build_signal_features(run_recs: list[dict]) -> str:
    lines = [
        "# Signal & Feature Completeness Audit",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        f"**Window:** last {WINDOW_MIN} minutes.",
        f"**trade_intent count in window:** {len([r for r in run_recs if r.get('event_type') == 'trade_intent'])}",
        "",
        "---",
        "",
    ]
    trade_intents = [r for r in run_recs if r.get("event_type") == "trade_intent"]
    if not trade_intents:
        lines.append("No trade_intent events in window. Cannot verify signal layers or features.")
        return "\n".join(lines)
    layer_counts: dict[str, int] = defaultdict(int)
    feature_names: set[str] = set()
    default_like = 0
    for r in trade_intents:
        trace = r.get("intelligence_trace") or {}
        layers = trace.get("signal_layers") or {}
        for layer_name, arr in layers.items():
            if arr:
                layer_counts[layer_name] += 1
            for s in arr or []:
                name = s.get("name")
                if name:
                    feature_names.add(str(name))
                v = s.get("value") if s.get("value") is not None else s.get("score")
                if v is not None and float(v) == 0.0 and len(arr or []) == 1:
                    default_like += 1
    expected_layers = ["alpha_signals", "flow_signals", "regime_signals", "volatility_signals", "dark_pool_signals"]
    lines.append("## Signal layers emitted (at least one event with non-empty layer)")
    for layer in expected_layers:
        count = layer_counts.get(layer, 0)
        lines.append(f"- **{layer}:** {count} events")
    lines.append("")
    lines.append("## Feature names seen in window (sample)")
    for n in sorted(feature_names)[:50]:
        lines.append(f"- `{n}`")
    if len(feature_names) > 50:
        lines.append(f"- ... and {len(feature_names) - 50} more")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4) SCORE COMPONENT INTEGRITY
# ---------------------------------------------------------------------------
def build_score_components(run_recs: list[dict]) -> str:
    lines = [
        "# Score Component Integrity Audit",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        f"**Window:** last {WINDOW_MIN} minutes.",
        "",
        "---",
        "",
    ]
    trade_intents = [r for r in run_recs if r.get("event_type") == "trade_intent"]
    if not trade_intents:
        lines.append("No trade_intent in window.")
        return "\n".join(lines)
    all_comps: Counter = Counter()
    neutral_comps: Counter = Counter()
    raw_scores: list[float] = []
    for r in trade_intents:
        trace = r.get("intelligence_trace") or {}
        agg = trace.get("aggregation") or {}
        comps = agg.get("score_components") or {}
        raw_scores.append(agg.get("raw_score"))
        for k, v in comps.items():
            all_comps[k] += 1
            try:
                if v is not None and float(v) == 0.0:
                    neutral_comps[k] += 1
            except (TypeError, ValueError):
                pass
    lines.append("## Score components observed")
    for comp, count in all_comps.most_common():
        neutral = neutral_comps.get(comp, 0)
        lines.append(f"- **{comp}:** present in {count} events, neutral/zero in {neutral}")
    lines.append("")
    lines.append("## Raw scores (sample)")
    for s in raw_scores[:20]:
        lines.append(f"- {s}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5) GATE EVALUATION COMPLETENESS
# ---------------------------------------------------------------------------
def build_gates(run_recs: list[dict]) -> str:
    lines = [
        "# Gate Evaluation Completeness Audit",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        f"**Window:** last {WINDOW_MIN} minutes.",
        "",
        "---",
        "",
    ]
    trade_intents = [r for r in run_recs if r.get("event_type") == "trade_intent"]
    gate_counts: dict[str, int] = defaultdict(int)
    gate_failures: dict[str, list[str]] = defaultdict(list)
    for r in trade_intents:
        trace = r.get("intelligence_trace") or {}
        gates = trace.get("gates") or {}
        for gname, gval in gates.items():
            if isinstance(gval, dict):
                gate_counts[gname] += 1
                if not gval.get("passed"):
                    reason = gval.get("reason") or "no_reason"
                    gate_failures[gname].append(reason)
    expected_gates = ["score_gate", "capacity_gate", "risk_gate", "momentum_gate", "directional_gate", "displacement_gate"]
    lines.append("## Gates evaluated (at least once in window)")
    for g in expected_gates:
        count = gate_counts.get(g, 0)
        failures = gate_failures.get(g, [])
        lines.append(f"- **{g}:** evaluated in {count} events; failures with reason: {len(failures)}")
        for reason in failures[:5]:
            lines.append(f"  - `{reason}`")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6) DECISION TRACE & SENTINEL
# ---------------------------------------------------------------------------
def build_decision_trace(run_recs: list[dict], sys_recs: list[dict]) -> str:
    lines = [
        "# Decision Trace & Sentinel Audit",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        f"**Window:** last {WINDOW_MIN} minutes.",
        "",
        "---",
        "",
    ]
    trade_intents = [r for r in run_recs if r.get("event_type") == "trade_intent"]
    with_trace = [r for r in trade_intents if r.get("intelligence_trace")]
    missing_trace = [r for r in trade_intents if not r.get("intelligence_trace")]
    total = len(trade_intents)
    pct = (100.0 * len(with_trace) / total) if total else 100.0
    lines.append(f"## trade_intent with intelligence_trace")
    lines.append(f"- Total trade_intent: {total}")
    lines.append(f"- With intelligence_trace: {len(with_trace)} ({pct:.1f}%)")
    lines.append(f"- Missing intelligence_trace: {len(missing_trace)}")
    if missing_trace:
        lines.append("")
        lines.append("Sample missing (intent_id / _dt):")
        for r in missing_trace[:5]:
            lines.append(f"- {r.get('intent_id', r.get('_dt', '?'))}")
    sentinel = [r for r in sys_recs if (r.get("event_type") or "") == "missing_intelligence_trace"]
    lines.append("")
    lines.append("## missing_intelligence_trace sentinel events (system_events.jsonl)")
    lines.append(f"- Count in window: {len(sentinel)}")
    if sentinel:
        lines.append("Sample:")
        for r in sentinel[:3]:
            lines.append(f"- {r.get('timestamp')} {r.get('event_type')}")
    partial = 0
    for r in with_trace:
        t = r.get("intelligence_trace") or {}
        if not t.get("final_decision") or not t.get("gates"):
            partial += 1
    lines.append("")
    lines.append("## Partial traces (have trace but missing final_decision or gates)")
    lines.append(f"- Count: {partial}")
    # Raw excerpt: one trade_intent with trace (keys only) and one without if any
    lines.append("")
    lines.append("## Evidence (raw excerpt)")
    if with_trace:
        r = with_trace[0]
        lines.append("- **Sample trade_intent WITH intelligence_trace:**")
        lines.append(f"  - _dt: {r.get('_dt')}, event_type: {r.get('event_type')}, symbol: {r.get('symbol')}")
        lines.append(f"  - trace keys: {list((r.get('intelligence_trace') or {}).keys())}")
    if missing_trace:
        r = missing_trace[0]
        lines.append("- **Sample trade_intent WITHOUT intelligence_trace:**")
        lines.append(f"  - _dt: {r.get('_dt')}, event_type: {r.get('event_type')}, symbol: {r.get('symbol')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 7) POST-TRADE & SHADOW ARTIFACT HEALTH
# ---------------------------------------------------------------------------
def build_artifact_health() -> str:
    lines = [
        "# Post-Trade & Shadow Artifact Health",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        "",
        "---",
        "",
    ]
    today = _now().strftime("%Y-%m-%d")
    computed_dir = TELEMETRY_ROOT / today / "computed"
    # Also check latest date dir if today is empty
    date_dirs = sorted([d for d in TELEMETRY_ROOT.iterdir() if d.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", d.name)], reverse=True)
    if not computed_dir.exists() and date_dirs:
        computed_dir = date_dirs[0] / "computed"
    artifacts = [
        "entry_parity_details.json", "live_vs_shadow_pnl.json", "shadow_vs_live_parity.json",
        "feature_family_summary.json", "exit_intel_completeness.json", "score_distribution_curves.json",
        "signal_performance.json", "signal_weight_recommendations.json",
        "feature_equalizer_builder.json", "feature_value_curves.json", "long_short_analysis.json",
        "regime_sector_feature_matrix.json", "regime_timeline.json", "replacement_telemetry_expanded.json", "pnl_windows.json",
    ]
    lines.append("## Artifact presence, freshness, size")
    for name in artifacts:
        path = computed_dir / name
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        mtime = path.stat().st_mtime if exists else 0
        from_epoch = datetime.fromtimestamp(mtime, tz=timezone.utc) if mtime else None
        fresh = (from_epoch and (_now() - from_epoch).total_seconds() < 86400 * 2) if from_epoch else False
        status = "OK" if (exists and size > 0) else ("STALE/EMPTY" if exists else "MISSING")
        lines.append(f"- **{name}:** exists={exists}, size={size}, mtime={from_epoch}, status={status}")
    lines.append("")
    lines.append("## Generation logic (code references)")
    lines.append("- entry_parity_details, feature_family_summary, live_vs_shadow_pnl, shadow_vs_live_parity: `generate_missing_shadow_artifacts.py`")
    lines.append("- exit_intel_completeness, score_distribution_curves, signal_performance, signal_weight_recommendations: `scripts/run_full_telemetry_extract.py` + telemetry/*.py")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 8) SILENT FAILURE DETECTION (code scan)
# ---------------------------------------------------------------------------
def build_silent_failures() -> str:
    lines = [
        "# Silent Failure Detection",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        "**Method:** grep/code scan for try/except swallow, default fallbacks, feature flags, TODO/deprecated.",
        "",
        "---",
        "",
    ]
    # Search for patterns
    patterns = [
        (r"except\s*.*:\s*\n\s*(?:pass|continue)\s*(?:\n|$)", "try/except pass|continue"),
        (r"read_json\s*\([^)]+,\s*default\s*=\s*\{\}", "read_json(..., default={}"),
        (r"\.get\s*\([^)]+,\s*\{\}\s*\)", ".get(..., {})"),
        (r"missing_intelligence_trace", "missing_intelligence_trace sentinel"),
        (r"TODO|FIXME|deprecated", "TODO/FIXME/deprecated"),
    ]
    found: list[tuple[str, str, str]] = []
    for py_path in ROOT.rglob("*.py"):
        if "archive" in str(py_path) or "venv" in str(py_path) or "__pycache__" in str(py_path):
            continue
        try:
            text = py_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = py_path.relative_to(ROOT)
        for pattern, label in patterns:
            for m in re.finditer(pattern, text, re.MULTILINE):
                found.append((str(rel), label, m.group(0).strip()[:80]))
    # Dedupe by (file, label, snippet)
    seen = set()
    for rel, label, snip in found[:100]:
        key = (rel, label, snip[:60])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- **{rel}** ({label}): `{snip}`")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 9) FINAL VERDICT
# ---------------------------------------------------------------------------
def build_verdict(
    run_recs: list[dict],
    sys_recs: list[dict],
    data_presence_ok: bool,
    silent_failures_count: int,
) -> str:
    trade_intents = [r for r in run_recs if r.get("event_type") == "trade_intent"]
    missing_trace = len([r for r in trade_intents if not r.get("intelligence_trace")])
    sentinel_count = len([r for r in sys_recs if (r.get("event_type") or "") == "missing_intelligence_trace"])
    pass_trace = missing_trace == 0 and sentinel_count == 0
    pass_silent = silent_failures_count == 0
    lines = [
        "# Final Intelligence Verdict",
        "",
        "**Generated:** " + _now().isoformat() + " (UTC)",
        "",
        "---",
        "",
        "## Subsystem verdicts",
        "",
        "| Subsystem | Verdict | Notes |",
        "|-----------|---------|-------|",
    ]
    lines.append(f"| Data presence | {'PASS' if data_presence_ok else 'WARN'} | See INTEL_DATA_PRESENCE.md |")
    lines.append(f"| Signal/features | {'WARN' if not trade_intents else 'PASS'} | PASS when trade_intent in window; WARN when none |")
    lines.append(f"| Score components | {'WARN' if not trade_intents else 'PASS'} | See INTEL_SCORE_COMPONENTS.md |")
    lines.append(f"| Gates | {'WARN' if not trade_intents else 'PASS'} | See INTEL_GATES.md |")
    lines.append(f"| Decision trace | {'FAIL' if not pass_trace else 'PASS'} | missing_trace={missing_trace}, sentinel_events={sentinel_count} |")
    lines.append(f"| Artifacts | WARN | See INTEL_ARTIFACT_HEALTH.md |")
    lines.append(f"| Silent failures | {'FAIL' if not pass_silent else 'PASS'} | {silent_failures_count} patterns found; do not PASS if any remain |")
    lines.append("")
    lines.append("## Missing / stale / disabled intelligence")
    if missing_trace:
        lines.append(f"- trade_intent missing intelligence_trace: {missing_trace}")
    if sentinel_count:
        lines.append(f"- missing_intelligence_trace sentinel events: {sentinel_count}")
    if silent_failures_count:
        lines.append(f"- Code patterns indicating silent fallbacks / swallowed errors: {silent_failures_count}")
    lines.append("")
    verdict = "complete, coherent, and free of silent degradation" if (pass_trace and pass_silent) else "NOT complete, coherent, or free of silent degradation"
    lines.append("## Statement")
    lines.append("")
    lines.append(f"**The STOCK-BOT intelligence pipeline is {verdict}.**")
    lines.append("")
    lines.append("(Do not declare PASS unless zero silent failures and zero missing traces.)")
    return "\n".join(lines)


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    run_path = LogFiles.RUN
    sys_path = LogFiles.SYSTEM_EVENTS
    run_recs = _read_jsonl(run_path, since_min=WINDOW_MIN)
    sys_recs = _read_jsonl(sys_path, since_min=WINDOW_MIN)

    # 1
    (REPORTS_DIR / "INTEL_EXPECTED_INVENTORY.md").write_text(build_expected_inventory(), encoding="utf-8")
    # 2
    (REPORTS_DIR / "INTEL_DATA_PRESENCE.md").write_text(build_data_presence(), encoding="utf-8")
    data_presence_ok = run_path.exists() and run_path.stat().st_size > 0
    # 3
    (REPORTS_DIR / "INTEL_SIGNAL_FEATURES.md").write_text(build_signal_features(run_recs), encoding="utf-8")
    # 4
    (REPORTS_DIR / "INTEL_SCORE_COMPONENTS.md").write_text(build_score_components(run_recs), encoding="utf-8")
    # 5
    (REPORTS_DIR / "INTEL_GATES.md").write_text(build_gates(run_recs), encoding="utf-8")
    # 6
    (REPORTS_DIR / "INTEL_DECISION_TRACE.md").write_text(build_decision_trace(run_recs, sys_recs), encoding="utf-8")
    # 7
    (REPORTS_DIR / "INTEL_ARTIFACT_HEALTH.md").write_text(build_artifact_health(), encoding="utf-8")
    # 8
    silent_text = build_silent_failures()
    (REPORTS_DIR / "INTEL_SILENT_FAILURES.md").write_text(silent_text, encoding="utf-8")
    silent_count = silent_text.count("\n- **")
    # 9
    (REPORTS_DIR / "INTEL_SYSTEM_VERDICT.md").write_text(
        build_verdict(run_recs, sys_recs, data_presence_ok, silent_count), encoding="utf-8"
    )
    print("Reports written to reports/:")
    for name in [
        "INTEL_EXPECTED_INVENTORY.md", "INTEL_DATA_PRESENCE.md", "INTEL_SIGNAL_FEATURES.md",
        "INTEL_SCORE_COMPONENTS.md", "INTEL_GATES.md", "INTEL_DECISION_TRACE.md",
        "INTEL_ARTIFACT_HEALTH.md", "INTEL_SILENT_FAILURES.md", "INTEL_SYSTEM_VERDICT.md",
    ]:
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
