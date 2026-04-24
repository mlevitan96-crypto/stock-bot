#!/usr/bin/env python3
"""
Verify long vs short trade logic on droplet (or locally with same log layout).

Reports:
- LONG_ONLY env (true => shorts blocked)
- Recent signal direction mix (from signal_history if present)
- Last N trades direction from attribution / exit_attribution
- Count of long_only_blocked_short_entry in blocked_trades

Usage (on droplet):
  cd /root/stock-bot && python3 scripts/verify_long_short_on_droplet.py [--base-dir .] [--last 100]

Local:
  python scripts/verify_long_short_on_droplet.py --base-dir . --last 200
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _day_utc(ts) -> str:
    """Extract YYYY-MM-DD from ts (iso string or unix int)."""
    if ts is None:
        return ""
    s = str(ts)
    if s.isdigit():
        try:
            return datetime.fromtimestamp(int(s), tz=timezone.utc).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return ""
    if "T" in s:
        return s.split("T")[0][:10]
    return s[:10] if len(s) >= 10 else ""


def _iter_jsonl(path: Path, limit: int | None = None):
    if not path.exists():
        return
    n = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
            n += 1
            if limit is not None and n >= limit:
                return
        except json.JSONDecodeError:
            continue


def _iter_jsonl_today(path: Path, today: str):
    """Yield records whose timestamp falls on today (UTC)."""
    if not path.exists() or not today:
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            ts = rec.get("ts") or rec.get("timestamp") or rec.get("exit_ts") or rec.get("evaluated_at") or ""
            if _day_utc(ts) == today:
                yield rec
        except json.JSONDecodeError:
            continue


def _normalize_direction(d: str | None) -> str:
    if not d:
        return "unknown"
    d = str(d).strip().lower()
    if d in ("bullish", "long", "buy"):
        return "long"
    if d in ("bearish", "short", "sell"):
        return "short"
    if d in ("neutral", ""):
        return "neutral"
    return d if d in ("long", "short", "neutral") else "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify long/short logic and direction mix on droplet")
    ap.add_argument("--base-dir", default="", help="Repo root (default: script parent)")
    ap.add_argument("--last", type=int, default=200, help="Last N trades/signals to consider")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    last_n = max(1, args.last)

    lines: list[str] = []
    lines.append("## Long/Short verification")
    lines.append("")

    # 1) LONG_ONLY
    long_only_raw = os.environ.get("LONG_ONLY", "").strip().lower()
    long_only = long_only_raw in ("1", "true", "yes", "on")
    lines.append(f"- **LONG_ONLY env:** `{os.environ.get('LONG_ONLY', '(unset)')}` -> shorts **{'BLOCKED' if long_only else 'ALLOWED'}**")
    lines.append("")

    # 2) Signal history direction mix (if present)
    sig_path = base / "logs" / "signal_history.jsonl"
    if sig_path.exists():
        dir_counts: dict[str, int] = {}
        for rec in _iter_jsonl(sig_path, limit=last_n):
            d = _normalize_direction(rec.get("direction") or rec.get("direction_normalized"))
            dir_counts[d] = dir_counts.get(d, 0) + 1
        lines.append("### Signal history (direction mix, last N)")
        for k in ("long", "short", "neutral", "unknown"):
            if k in dir_counts:
                lines.append(f"- {k}: {dir_counts[k]}")
        lines.append("")
    else:
        lines.append("### Signal history: file not found (skip direction mix)")
        lines.append("")

    # 3) Attribution / exit_attribution — last N trades by direction
    attr_path = base / "logs" / "attribution.jsonl"
    exit_path = base / "logs" / "exit_attribution.jsonl"
    # Prefer exit_attribution for closed trades; fallback attribution
    trade_recs: list[dict] = []
    if exit_path.exists():
        for rec in _iter_jsonl(exit_path, limit=last_n):
            trade_recs.append(rec)
    if len(trade_recs) < last_n and attr_path.exists():
        for rec in _iter_jsonl(attr_path, limit=last_n):
            trade_recs.append(rec)
    # Dedupe by taking most recent by ts; for simplicity just use order (last N lines = recent)
    trade_recs = trade_recs[:last_n]
    by_dir: dict[str, list[float]] = {}
    for rec in trade_recs:
        d = _normalize_direction(rec.get("direction") or rec.get("position_side") or rec.get("side"))
        pnl = float(rec.get("pnl_usd") or rec.get("pnl") or rec.get("realized_pnl_usd") or 0)
        by_dir.setdefault(d, []).append(pnl)
    lines.append("### Executed trades (last N) by direction")
    for k in ("long", "short", "neutral", "unknown"):
        if k not in by_dir:
            continue
        pnls = by_dir[k]
        total_pnl = sum(pnls)
        lines.append(f"- **{k}:** count={len(pnls)}, total_pnl_usd={total_pnl:.2f}")
    lines.append("")

    # 4) Blocked: long_only_blocked_short_entry
    blocked_path = base / "state" / "blocked_trades.jsonl"
    long_only_blocked = 0
    if blocked_path.exists():
        for rec in _iter_jsonl(blocked_path, limit=5000):
            reason = str(rec.get("reason") or rec.get("block_reason") or "").strip()
            if "long_only_blocked" in reason or "long_only_mode" in reason:
                long_only_blocked += 1
    lines.append("### Blocked (short entry by LONG_ONLY)")
    lines.append(f"- Count (last 5000 blocked): **{long_only_blocked}**")
    lines.append("")

    # 5) Today only: signals and trades, then root-cause reason all long
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines.append("---")
    lines.append("## Today only (UTC date " + today + ")")
    lines.append("")

    today_sig_long = 0
    today_sig_short = 0
    today_sig_other = 0
    if sig_path.exists():
        for rec in _iter_jsonl_today(sig_path, today):
            d = _normalize_direction(rec.get("direction") or rec.get("direction_normalized"))
            if d == "long":
                today_sig_long += 1
            elif d == "short":
                today_sig_short += 1
            else:
                today_sig_other += 1
    lines.append("### Signals today (by direction)")
    lines.append(f"- long: {today_sig_long}, short: {today_sig_short}, other: {today_sig_other}")
    lines.append("")

    today_trades: list[dict] = []
    for path in (exit_path, attr_path):
        if path.exists():
            for rec in _iter_jsonl_today(path, today):
                today_trades.append(rec)
    today_by_dir: dict[str, int] = {}
    for rec in today_trades:
        d = _normalize_direction(rec.get("direction") or rec.get("position_side") or rec.get("side"))
        today_by_dir[d] = today_by_dir.get(d, 0) + 1
    lines.append("### Executed trades today (by direction)")
    if today_by_dir:
        for k in ("long", "short", "neutral", "unknown"):
            if k in today_by_dir:
                lines.append(f"- **{k}:** {today_by_dir[k]}")
    else:
        lines.append("- No trades today in attribution/exit_attribution.")
    lines.append("")

    # Reason all long
    lines.append("## Why all of today's positions are long (root cause)")
    lines.append("")
    total_today_trades = sum(today_by_dir.values())
    all_long = (
        total_today_trades > 0
        and today_by_dir.get("short", 0) == 0
        and today_by_dir.get("bearish", 0) == 0
    )
    all_long_signals = (today_sig_long + today_sig_short + today_sig_other) > 0 and today_sig_short == 0

    if long_only:
        lines.append("1. **LONG_ONLY is enabled** on this host. Short entries are **blocked** by design (env LONG_ONLY=true). So every executed position today is long.")
    elif all_long or all_long_signals:
        lines.append("1. **LONG_ONLY is NOT set** (shorts are allowed).")
        lines.append("2. **Direction comes from flow sentiment**, not from score. Each cluster gets direction from UW cache/enriched sentiment (BULLISH -> long, BEARISH -> short).")
        lines.append("3. **All of today's signals/trades are long** because every accepted signal had **direction=bullish** (flow sentiment BULLISH). That typically means:")
        lines.append("   - **Net call premium > put premium** in options flow (call buying or put selling dominates), so derived sentiment is BULLISH.")
        lines.append("   - UW cache may be writing BULLISH for the symbols that passed the composite gate, or flow data today is skewed bullish (e.g. heavy call buying even in a down market).")
        lines.append("4. To get shorts: ensure bearish flow (put buying / call selling) is present and that UW cache/enrichment sets sentiment to BEARISH for some symbols; then those clusters will get direction=bearish and side=sell.")
    else:
        lines.append("Today's mix includes both long and short; no single root cause.")
    lines.append("")

    out = "\n".join(lines)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
