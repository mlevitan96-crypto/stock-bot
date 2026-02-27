#!/usr/bin/env python3
"""
Blocked-trade expectancy analysis: extract candidates, replay with exit logic, bucket by score.
Outputs: extracted_candidates.jsonl, replay_results.jsonl, bucket_analysis.md.
Run from repo root. Requires state/blocked_trades.jsonl; bars from data/bars or Alpaca for replay.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "reports" / "blocked_expectancy"
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"
SNAPSHOT_PATH = REPO / "logs" / "score_snapshot.jsonl"
TRAILING_STOP_PCT = 0.015
TIME_EXIT_MINUTES = 240


def _parse_ts(v) -> datetime | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _score_bucket(score: float) -> str:
    """0.5-width buckets: 1.0-1.5, 1.5-2.0, ..."""
    if score is None:
        return "unknown"
    try:
        s = float(score)
        lo = int(s * 2) / 2.0
        hi = lo + 0.5
        return f"{lo:.1f}-{hi:.1f}"
    except Exception:
        return "unknown"


def extract_candidates() -> list[dict]:
    """Load blocked_trades; keep score_below_min and expectancy_blocked:score_floor_breach."""
    candidates = []
    if not BLOCKED_PATH.exists():
        return candidates
    for line in BLOCKED_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        reason = (r.get("reason") or r.get("block_reason") or "").strip()
        if reason == "score_below_min" or reason == "expectancy_blocked:score_floor_breach":
            ts = r.get("timestamp") or r.get("ts")
            score = r.get("score") or r.get("candidate_score")
            try:
                score = float(score) if score is not None else None
            except (TypeError, ValueError):
                score = None
            entry_price = r.get("would_have_entered_price") or r.get("decision_price")
            try:
                entry_price = float(entry_price) if entry_price is not None else None
            except (TypeError, ValueError):
                entry_price = None
            direction = (r.get("direction") or "bullish").lower()
            side = "long" if direction == "bullish" else "short"
            candidates.append({
                "symbol": r.get("symbol") or "?",
                "score": score,
                "reason": reason,
                "timestamp": ts,
                "entry_price": entry_price,
                "side": side,
                "bucket": _score_bucket(score),
            })
    return candidates


def load_bars_for_candidate(symbol: str, entry_dt: datetime, max_minutes: int = 300) -> list[dict]:
    """Load bars from entry_dt. Prefer data/bars/alpaca_daily.parquet (daily) then 1Min/5Min/15Min."""
    if symbol in (None, "", "?"):
        return []
    try:
        from data.bars_loader import load_bars, load_bars_from_daily_parquet
        parquet = REPO / "data" / "bars" / "alpaca_daily.parquet"
    except ImportError:
        return []
    date_str = entry_dt.strftime("%Y-%m-%d")
    end_ts = entry_dt + timedelta(minutes=max_minutes)
    # Prefer daily parquet when present (real PNL from Alpaca daily bars)
    if parquet.exists():
        end_date = (entry_dt + timedelta(days=14)).strftime("%Y-%m-%d")
        bars = load_bars_from_daily_parquet(symbol, date_str, end_date)
        if bars:
            return bars
    bars = load_bars(symbol, date_str, timeframe="1Min", start_ts=entry_dt, end_ts=end_ts, use_cache=True, fetch_if_missing=True)
    if not bars:
        for tf in ("5Min", "15Min"):
            bars = load_bars(symbol, date_str, timeframe=tf, start_ts=entry_dt, end_ts=end_ts, use_cache=True, fetch_if_missing=True)
            if bars:
                break
    return bars


def replay_one(candidate: dict) -> dict | None:
    """Simulate entry at entry_price, exit by trailing stop or time. Return pnl_pct, mfe_pct, mae_pct, exit_reason."""
    symbol = candidate.get("symbol")
    entry_price = candidate.get("entry_price")
    side = candidate.get("side", "long")
    ts = candidate.get("timestamp")
    entry_dt = _parse_ts(ts)
    if not entry_dt or not symbol or symbol == "?" or not entry_price or entry_price <= 0:
        return None
    bars = load_bars_for_candidate(symbol, entry_dt, max_minutes=TIME_EXIT_MINUTES + 30)
    if not bars:
        return None
    # Build list of (dt, o, h, l, c)
    bar_list = []
    for b in bars:
        t = b.get("t") or b.get("timestamp")
        dt = _parse_ts(t)
        if dt is None:
            continue
        if dt < entry_dt:
            if getattr(dt, "date", None) and getattr(entry_dt, "date", None) and dt.date() == entry_dt.date():
                pass
            else:
                continue
        o = float(b.get("o", b.get("open", 0)))
        h = float(b.get("h", b.get("high", 0)))
        l = float(b.get("l", b.get("low", 0)))
        c = float(b.get("c", b.get("close", 0)))
        bar_list.append((dt, o, h, l, c))
    if not bar_list:
        return None
    exit_time = entry_dt + timedelta(minutes=TIME_EXIT_MINUTES)
    mfe_pct = 0.0
    mae_pct = 0.0
    exit_price = entry_price
    exit_reason = "session_end"
    hold_bars = 0
    for i, (dt, o, h, l, c) in enumerate(bar_list):
        hold_bars = i + 1
        if side == "long":
            ret = (c - entry_price) / entry_price if entry_price else 0
            high_ret = (h - entry_price) / entry_price if entry_price else 0
            low_ret = (l - entry_price) / entry_price if entry_price else 0
        else:
            ret = (entry_price - c) / entry_price if entry_price else 0
            high_ret = (entry_price - l) / entry_price if entry_price else 0
            low_ret = (entry_price - h) / entry_price if entry_price else 0
        mfe_pct = max(mfe_pct, high_ret * 100)
        mae_pct = min(mae_pct, low_ret * 100)
        # Trailing stop: exit if drawdown from running max exceeds TRAILING_STOP_PCT
        if side == "long" and low_ret <= -TRAILING_STOP_PCT:
            exit_price = c
            exit_reason = "trailing_stop"
            break
        if side == "short" and high_ret <= -TRAILING_STOP_PCT:
            exit_price = c
            exit_reason = "trailing_stop"
            break
        if dt >= exit_time:
            exit_price = c
            exit_reason = "time_exit"
            break
    if exit_reason == "session_end" and bar_list:
        exit_price = bar_list[-1][4]
    if side == "long":
        pnl_pct = (exit_price - entry_price) / entry_price * 100 if entry_price else 0
    else:
        pnl_pct = (entry_price - exit_price) / entry_price * 100 if entry_price else 0
    return {
        "symbol": symbol,
        "score": candidate.get("score"),
        "bucket": candidate.get("bucket"),
        "reason": candidate.get("reason"),
        "pnl_pct": round(pnl_pct, 4),
        "mfe_pct": round(mfe_pct, 4),
        "mae_pct": round(mae_pct, 4),
        "exit_reason": exit_reason,
        "hold_bars": hold_bars,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = extract_candidates()
    # Write extracted
    extracted_path = OUT_DIR / "extracted_candidates.jsonl"
    with extracted_path.open("w", encoding="utf-8") as f:
        for c in candidates:
            f.write(json.dumps(c, default=str) + "\n")
    print(f"Extracted {len(candidates)} candidates -> {extracted_path}")

    # Replay (best-effort; bars may be missing locally)
    replay_path = OUT_DIR / "replay_results.jsonl"
    replay_results = []
    for c in candidates:
        res = replay_one(c)
        if res is not None:
            replay_results.append(res)
    with replay_path.open("w", encoding="utf-8") as f:
        for r in replay_results:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"Replayed {len(replay_results)} -> {replay_path}")

    # Bucket analysis
    by_bucket = defaultdict(lambda: {"pnl_pcts": [], "n": 0})
    for r in replay_results:
        b = r.get("bucket") or "unknown"
        by_bucket[b]["pnl_pcts"].append(r.get("pnl_pct", 0))
        by_bucket[b]["n"] += 1
    buckets_sorted = sorted(by_bucket.keys(), key=lambda x: (float(x.split("-")[0]) if "-" in x and x != "unknown" else -1))
    lines = [
        "# Blocked-trade score bucket analysis",
        "",
        "| bucket | n | mean_pnl_pct | win_rate | median_pnl_pct |",
        "|--------|---|--------------|----------|----------------|",
    ]
    for b in buckets_sorted:
        vals = by_bucket[b]["pnl_pcts"]
        n = len(vals)
        if n == 0:
            continue
        mean_pnl = sum(vals) / n
        wins = sum(1 for v in vals if v > 0)
        win_rate = wins / n * 100
        vals_sorted = sorted(vals)
        median_pnl = vals_sorted[n // 2] if n else 0
        lines.append(f"| {b} | {n} | {mean_pnl:.3f} | {win_rate:.1f}% | {median_pnl:.3f} |")
    bucket_md = OUT_DIR / "bucket_analysis.md"
    bucket_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Bucket analysis -> {bucket_md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
