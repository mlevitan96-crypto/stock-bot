#!/usr/bin/env python3
"""
Daily classification contradictions report. Fails governance if any violation.
Reads last 24h of reports/uw_health/uw_failure_events.jsonl, writes
reports/uw_health/uw_classification_contradictions.md.
Exit code: non-zero if contradictions > 0 (cron/systemd FAIL).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
UW_FAILURE_EVENTS = REPO / "reports" / "uw_health" / "uw_failure_events.jsonl"
OUT_MD = REPO / "reports" / "uw_health" / "uw_classification_contradictions.md"

UW_MISSING_DATA = "UW_MISSING_DATA"
UW_STALE_DATA = "UW_STALE_DATA"
UW_LOW_QUALITY_SIGNAL = "UW_LOW_QUALITY_SIGNAL"


def _any_indicator_true(indicators: dict) -> bool:
    if not indicators or not isinstance(indicators, dict):
        return False
    if indicators.get("no_bars") or indicators.get("bars_empty") or indicators.get("bars_stale"):
        return True
    if indicators.get("uw_root_cause_missing") or indicators.get("uw_root_cause_stale"):
        return True
    if (indicators.get("required_fields_missing") or []) or indicators.get("lookback_insufficient"):
        return True
    return False


def load_events_24h(limit: int = 100000) -> list[dict]:
    if not UW_FAILURE_EVENTS.exists():
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).timestamp()
    out = []
    for line in UW_FAILURE_EVENTS.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            ts = float(r.get("ts") or r.get("event_ts") or 0)
            if ts >= cutoff:
                out.append(r)
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def main() -> int:
    events = load_events_24h()
    contradictions: list[dict] = []
    for r in events:
        indicators = r.get("missing_data_indicators") or {}
        failure_class = r.get("failure_class") or ""
        decision = r.get("decision_taken") or ""
        any_ind = _any_indicator_true(indicators)
        # Rule 1: any indicator true AND failure_class == UW_LOW_QUALITY_SIGNAL → CONTRADICTION
        if any_ind and failure_class == UW_LOW_QUALITY_SIGNAL:
            contradictions.append({**r, "rule": "indicator_true_but_low_quality_class"})
        # Rule 2: decision_taken == "reject" AND any indicator true → CONTRADICTION
        elif decision == "reject" and any_ind:
            contradictions.append({**r, "rule": "reject_with_missing_data_indicator"})
        # Rule 3: failure_class in {UW_MISSING_DATA, UW_STALE_DATA} AND decision_taken == "reject" → CONTRADICTION
        elif failure_class in (UW_MISSING_DATA, UW_STALE_DATA) and decision == "reject":
            contradictions.append({**r, "rule": "data_failure_class_but_reject_decision"})

    by_symbol = Counter(c.get("symbol") or "?" for c in contradictions)
    top_symbols = by_symbol.most_common(20)
    examples = contradictions[:20]

    lines = [
        "# UW classification contradictions (last 24h)",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Events scanned: **{len(events)}**",
        f"**Contradiction count: {len(contradictions)}**",
        "",
        "## Verdict",
        "",
        f"**{'FAIL' if contradictions else 'PASS'}** — contradictions must be 0 for governance pass.",
        "",
        "## Top symbols (contradictions)",
        "",
    ]
    for sym, count in top_symbols:
        lines.append(f"- {sym}: {count}")
    lines.extend([
        "",
        "## 20 example rows (symbol, ts, failure_class, indicators, decision_taken)",
        "",
    ])
    for i, c in enumerate(examples, 1):
        ind = c.get("missing_data_indicators") or {}
        lines.append(f"{i}. **{c.get('symbol')}** ts={c.get('ts')} class={c.get('failure_class')} decision={c.get('decision_taken')} rule={c.get('rule')}")
        lines.append(f"   indicators: no_bars={ind.get('no_bars')} bars_empty={ind.get('bars_empty')} uw_root_cause_missing={ind.get('uw_root_cause_missing')} uw_root_cause_stale={ind.get('uw_root_cause_stale')}")
        lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}; contradictions={len(contradictions)}")
    return 1 if contradictions else 0


if __name__ == "__main__":
    sys.exit(main())
