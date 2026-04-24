#!/usr/bin/env python3
"""
Phase 8 — Replay readiness check.
Checks: exit_event.jsonl exists; ≥90% of exits have full component vectors,
entry→exit deltas, high_water/MFE/MAE, composite_at_exit, enriched signals.
Writes: reports/telemetry/REPLAY_READINESS.md
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

COMPONENT_KEYS = [
    "exit_flow_deterioration", "exit_volatility_spike", "exit_regime_shift",
    "exit_sentiment_reversal", "exit_gamma_collapse", "exit_dark_pool_reversal",
    "exit_insider_shift", "exit_sector_rotation", "exit_time_decay",
    "exit_microstructure_noise", "exit_score_deterioration",
]
DELTA_KEYS = [
    "delta_composite", "delta_flow_conviction", "delta_dark_pool_notional",
    "delta_sentiment", "delta_regime", "delta_gamma", "delta_vol",
    "delta_iv_rank", "delta_squeeze_score", "delta_sector_strength",
]
QUALITY_KEYS = ["high_water", "mfe", "mae"]


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


def main() -> int:
    base = Path(os.environ.get("REPO", REPO))
    exit_event_path = base / "logs" / "exit_event.jsonl"
    report_path = base / "reports" / "telemetry" / "REPLAY_READINESS.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    events = load_jsonl(exit_event_path)
    total = len(events)

    def pct(n: int) -> float:
        return (n / total * 100) if total else 0.0

    full_components = sum(
        1 for r in events
        if all((r.get("exit_components") or {}).get(c) is not None for c in COMPONENT_KEYS)
    )
    full_deltas = sum(
        1 for r in events
        if all((r.get("entry_exit_deltas") or {}).get(d) is not None for d in DELTA_KEYS)
    )
    has_quality = sum(
        1 for r in events
        if all((r.get("exit_quality_metrics") or {}).get(q) is not None for q in QUALITY_KEYS)
    )
    has_composite_exit = sum(1 for r in events if r.get("composite_at_exit") is not None)
    has_enriched = sum(
        1 for r in events
        if (r.get("exit_signal_snapshot") and isinstance(r.get("exit_signal_snapshot"), dict))
    )

    threshold_pct = 90.0
    ready_components = pct(full_components) >= threshold_pct
    ready_deltas = pct(full_deltas) >= threshold_pct
    ready_quality = pct(has_quality) >= threshold_pct
    ready_composite = pct(has_composite_exit) >= threshold_pct
    ready_enriched = pct(has_enriched) >= threshold_pct
    file_ok = exit_event_path.exists()
    all_ready = file_ok and ready_components and ready_deltas and ready_quality and ready_composite and ready_enriched

    lines = [
        "# Replay Readiness",
        "",
        f"**Source:** `logs/exit_event.jsonl`",
        f"**Total exit events:** {total}",
        "",
        "## Checks (≥90% required)",
        "",
        "| Check | Count | % | Pass |",
        "|-------|-------|---|------|",
        f"| exit_event.jsonl exists | {1 if file_ok else 0} | — | {'Yes' if file_ok else 'No'} |",
        f"| Full exit component vectors | {full_components}/{total} | {pct(full_components):.1f}% | {'Yes' if ready_components else 'No'} |",
        f"| Entry→exit deltas | {full_deltas}/{total} | {pct(full_deltas):.1f}% | {'Yes' if ready_deltas else 'No'} |",
        f"| high_water / MFE / MAE | {has_quality}/{total} | {pct(has_quality):.1f}% | {'Yes' if ready_quality else 'No'} |",
        f"| composite_at_exit | {has_composite_exit}/{total} | {pct(has_composite_exit):.1f}% | {'Yes' if ready_composite else 'No'} |",
        f"| Enriched signals at exit | {has_enriched}/{total} | {pct(has_enriched):.1f}% | {'Yes' if ready_enriched else 'No'} |",
        "",
        f"**Replay ready:** {'Yes' if all_ready else 'No'}",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report_path}")
    return 0 if all_ready else 1


if __name__ == "__main__":
    sys.exit(main())
