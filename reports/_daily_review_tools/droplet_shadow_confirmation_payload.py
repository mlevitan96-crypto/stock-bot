#!/usr/bin/env python3
"""
Droplet-native shadow confirmation report generator.

This file is intended to be executed ON the droplet (where local logs are production truth):
- reads /root/stock-bot/logs/attribution.jsonl
- reads /root/stock-bot/logs/shadow.jsonl
- writes reports/SHADOW_TRADING_CONFIRMATION_YYYY-MM-DD.md

Date is taken from REPORT_DATE env var (YYYY-MM-DD), defaulting to today UTC.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _dt(x: Any) -> Optional[datetime]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        try:
            return datetime.fromtimestamp(float(x), tz=timezone.utc)
        except Exception:
            return None
    try:
        s = str(x).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _in_date(rec: Dict[str, Any], date_str: str) -> bool:
    dt = _dt(rec.get("ts") or rec.get("timestamp"))
    return bool(dt and dt.date().isoformat() == date_str)


def _read_jsonl(path: Path, date_str: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict) and _in_date(r, date_str):
                    out.append(r)
    except FileNotFoundError:
        return []
    except Exception:
        return []
    return out


def main() -> int:
    date = os.getenv("REPORT_DATE") or _now_utc().strftime("%Y-%m-%d")
    now = _now_utc().isoformat()

    root = Path("/root/stock-bot")
    trades = _read_jsonl(root / "logs/attribution.jsonl", date)
    shadow = _read_jsonl(root / "logs/shadow.jsonl", date)

    # real symbols
    real_syms = set()
    for t in trades:
        sym = t.get("symbol") or (t.get("context") or {}).get("symbol")
        if sym:
            real_syms.add(str(sym).upper())

    # shadow summaries
    by_type: Dict[str, int] = {}
    score_deltas: List[float] = []
    shadow_exec: List[Dict[str, Any]] = []
    divergences = 0

    for r in shadow:
        et = str(r.get("event_type", "") or "")
        by_type[et] = by_type.get(et, 0) + 1
        if et == "divergence":
            divergences += 1
        if et == "score_compare":
            try:
                score_deltas.append(float(r.get("v2_score", 0.0)) - float(r.get("v1_score", 0.0)))
            except Exception:
                pass
        if et == "shadow_executed":
            shadow_exec.append(r)

    shadow_exec_syms = set()
    with_entry = 0
    for r in shadow_exec:
        sym = r.get("symbol")
        if sym:
            shadow_exec_syms.add(str(sym).upper())
        if r.get("entry_price") is not None:
            with_entry += 1

    overlap = sorted(real_syms & shadow_exec_syms)
    real_only = sorted(real_syms - shadow_exec_syms)
    shadow_only = sorted(shadow_exec_syms - real_syms)
    avg_delta = (sum(score_deltas) / len(score_deltas)) if score_deltas else 0.0

    lines: List[str] = []
    lines.append(f"# SHADOW_TRADING_CONFIRMATION_{date}")
    lines.append("")
    lines.append("## Data source")
    lines.append("- **source**: `Droplet local logs (/root/stock-bot/logs)`")
    lines.append(f"- **generated_utc**: `{now}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- **real_trades(attribution)**: `{len(trades)}`")
    lines.append(f"- **shadow_events**: `{len(shadow)}`")
    lines.append(f"- **divergences**: `{divergences}`")
    lines.append(f"- **shadow_executed**: `{len(shadow_exec)}`")
    lines.append(f"- **shadow_executed_with_entry_price**: `{with_entry}`")
    lines.append(f"- **avg(v2_score - v1_score)** (score_compare): `{avg_delta:.4f}`")
    lines.append("")
    lines.append("## Real vs shadow (symbol overlap)")
    lines.append(f"- **real_symbols**: `{len(real_syms)}`")
    lines.append(f"- **shadow_executed_symbols**: `{len(shadow_exec_syms)}`")
    lines.append(f"- **overlap_symbols**: `{len(overlap)}`")
    lines.append(f"- **real_only_symbols**: `{len(real_only)}`")
    lines.append(f"- **shadow_only_symbols**: `{len(shadow_only)}`")
    if overlap:
        lines.append("")
        lines.append("### Overlap (up to 25)")
        lines.append("- " + ", ".join(overlap[:25]))
    lines.append("")
    lines.append("## Shadow executed samples (up to 5)")
    if shadow_exec:
        for r in shadow_exec[:5]:
            lines.append(
                f"- {r.get('symbol')} {r.get('side')} qty={r.get('qty')} "
                f"entry_price={r.get('entry_price')} v2_score={r.get('v2_score')} ts={r.get('ts')}"
            )
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Shadow event types")
    for k, v in sorted(by_type.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("- Presence of `shadow_executed` confirms the v2 hypothetical order-intent path is active.")
    lines.append("- Presence of non-null `entry_price` confirms the new shadow trade enrichment is active.")
    lines.append("")

    out_path = root / "reports" / f"SHADOW_TRADING_CONFIRMATION_{date}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

