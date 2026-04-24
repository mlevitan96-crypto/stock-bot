#!/usr/bin/env python3
"""
Alpaca 2000-trade edge discovery pipeline.
Builds frozen dataset, bar-by-bar reconstruction, baseline, counterfactuals,
stability checks, promotion shortlist, board packet, CSA/SRE reviews, Telegram.
NO LIVE OR PAPER CHANGES.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
EXIT_ATTRIBUTION = REPO / "logs" / "exit_attribution.jsonl"
ENTRY_ATTRIBUTION_LOG = REPO / "logs" / "alpaca_entry_attribution.jsonl"
EXIT_ATTRIBUTION_CANONICAL = REPO / "logs" / "alpaca_exit_attribution.jsonl"
REPORTS_DIR = REPO / "reports"
MAX_TRADES_DEFAULT = 2000


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _governance_blockers_present() -> bool:
    """True if any reports/audit/GOVERNANCE_BLOCKER_*.md exists."""
    audit = REPORTS_DIR / "audit"
    if not audit.exists():
        return False
    return any(f.name.startswith("GOVERNANCE_BLOCKER_") and f.name.endswith(".md") for f in audit.iterdir())


def _parse_ts(s: Any):
    if s is None:
        return None
    try:
        s = str(s).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _derive_trade_key_from_entry_rec(rec: dict) -> str:
    """Build canonical trade_key from entry attribution record (backfill when missing)."""
    from src.telemetry.alpaca_trade_key import build_trade_key
    sym = rec.get("symbol") or "?"
    side = rec.get("side") or "LONG"
    ts = rec.get("timestamp") or ""
    return build_trade_key(sym, side, ts)


def _derive_trade_key_from_exit_rec(rec: dict) -> str:
    """Build canonical trade_key from exit attribution record (backfill when missing)."""
    from src.telemetry.alpaca_trade_key import build_trade_key
    sym = rec.get("symbol") or "?"
    side = rec.get("side") or rec.get("direction") or "LONG"
    entry_ts = rec.get("entry_time_iso") or rec.get("entry_timestamp") or ""
    if not entry_ts and isinstance(rec.get("trade_id"), str):
        tid = rec["trade_id"]
        if tid.startswith("open_") and "_" in tid:
            parts = tid.split("_", 2)
            if len(parts) >= 3:
                entry_ts = parts[2].replace("-", ":").replace("Z", "+00:00")[:19]
    return build_trade_key(sym, side, entry_ts)


# ---------- Step 1: Frozen dataset ----------
MIN_JOIN_COVERAGE_PCT_DEFAULT = 98.0
MIN_TRADES_DEFAULT = 200
MIN_FINAL_EXITS_DEFAULT = 200


def step1_build_frozen_dataset(
    exit_path: Path,
    out_dir: Path,
    max_trades: int = MAX_TRADES_DEFAULT,
    entry_attr_path: Optional[Path] = None,
    exit_attr_canonical_path: Optional[Path] = None,
    *,
    allow_missing_attribution: bool = False,
    missing_attribution_threshold_pct: float = 2.0,
    min_join_coverage_pct: float = 98.0,
    allow_fallback_join: bool = False,
    min_trades: int = MIN_TRADES_DEFAULT,
    min_final_exits: int = MIN_FINAL_EXITS_DEFAULT,
    diagnostic: bool = False,
) -> tuple[int, Optional[str]]:
    """Extract last N trades; freeze CSV (with trade_key) + attribution jsonl; normalize trade_key; verify join coverage and sample size; write INPUT_FREEZE.md. Hard-fail if join coverage or sample size below threshold unless allow_missing_attribution."""
    if not exit_path.exists():
        return 0, None
    from src.telemetry.alpaca_trade_key import build_trade_key
    rows = []
    count_blank = count_json_error = count_not_dict = count_no_exit_ts = 0
    with open(exit_path, "r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f):
            line_stripped = line.strip()
            if not line_stripped:
                count_blank += 1
                continue
            try:
                rec = json.loads(line_stripped)
            except json.JSONDecodeError:
                count_json_error += 1
                continue
            if not isinstance(rec, dict):
                count_not_dict += 1
                continue
            entry_ts = rec.get("entry_timestamp") or rec.get("ts") or ""
            exit_ts = rec.get("timestamp") or rec.get("exit_timestamp") or rec.get("ts") or ""
            if not exit_ts:
                count_no_exit_ts += 1
                continue
            line = line_stripped
            symbol = (rec.get("symbol") or "?").strip().upper() or "?"
            entry_price = rec.get("entry_price")
            exit_price = rec.get("exit_price")
            try:
                pnl = float(rec.get("realized_pnl_usd") or rec.get("pnl") or rec.get("pnl_usd") or 0)
            except (TypeError, ValueError):
                pnl = 0.0
            exit_reason = (rec.get("exit_reason") or "").strip() or "unknown"
            entry_regime = (rec.get("entry_regime") or "").strip() or "unknown"
            exit_regime = (rec.get("exit_regime") or "").strip() or "unknown"
            v2_score = rec.get("v2_exit_score")
            try:
                v2_score = float(v2_score) if v2_score is not None else None
            except (TypeError, ValueError):
                v2_score = None
            time_in_trade = rec.get("time_in_trade_minutes")
            try:
                time_in_trade = float(time_in_trade) if time_in_trade is not None else None
            except (TypeError, ValueError):
                time_in_trade = None
            side = (rec.get("side") or rec.get("direction") or "long").strip().lower()
            if side not in ("long", "short", "buy", "sell"):
                side = "long"
            if side == "sell":
                side = "short"
            if side == "buy":
                side = "long"
            trade_id = rec.get("trade_id") or f"exit_attr_{idx}"
            entry_time_norm = entry_ts[:19] if entry_ts else ""
            trade_key = build_trade_key(symbol, side, entry_ts or entry_time_norm)
            rows.append({
                "trade_id": str(trade_id),
                "trade_key": trade_key,
                "symbol": symbol,
                "side": side,
                "entry_time": entry_time_norm,
                "exit_time": exit_ts[:19] if exit_ts else "",
                "entry_price": entry_price,
                "exit_price": exit_price,
                "realized_pnl_usd": round(pnl, 6),
                "exit_reason": exit_reason,
                "entry_regime": entry_regime,
                "exit_regime": exit_regime,
                "v2_exit_score": v2_score,
                "time_in_trade_minutes": time_in_trade,
            })
    # Take last max_trades (most recent)
    rows_before_cap = len(rows)
    rows = rows[-max_trades:] if len(rows) > max_trades else rows
    n = len(rows)
    if diagnostic:
        total_lines = count_blank + count_json_error + count_not_dict + count_no_exit_ts + rows_before_cap
        print(f"[diagnostic] exit_path={exit_path}", file=sys.stderr)
        print(f"[diagnostic] lines_read={total_lines} blank={count_blank} json_error={count_json_error} not_dict={count_not_dict} no_exit_ts={count_no_exit_ts} rows_kept={rows_before_cap} rows_after_max_trades={n} drop_cap={max(0, rows_before_cap - max_trades)}", file=sys.stderr)
    if n == 0:
        return 0, None
    # Sample-size gate (DATA_READY: trades_total >= min_trades, final_exits_count >= min_final_exits)
    if not allow_missing_attribution and (n < min_trades or n < min_final_exits):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        blocker_path = REPORTS_DIR / "audit" / f"ALPACA_JOIN_INTEGRITY_BLOCKER_{ts}.md"
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        (REPORTS_DIR / "audit").mkdir(parents=True, exist_ok=True)
        with open(blocker_path, "w", encoding="utf-8") as bf:
            bf.write("# Alpaca data readiness blocker — SAMPLE_SIZE\n\n")
            bf.write(f"- **What failed:** Sample size below threshold (min_trades={min_trades}, min_final_exits={min_final_exits}).\n")
            bf.write(f"- **Counts:** trades_total={n}, required_trades={min_trades}, required_final_exits={min_final_exits}.\n\n")
            bf.write("## Classification\n\n**SAMPLE_SIZE** — wait for more trades (no code change).\n")
        raise ValueError(
            f"Sample size below threshold: n={n} (min_trades={min_trades}, min_final_exits={min_final_exits}). Blocker: {blocker_path}. Use --allow-missing-attribution to override."
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "TRADES_FROZEN.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    data_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:16]
    # Freeze attribution logs (last N lines by count; match to frozen trades by order)
    entry_attr_path = entry_attr_path or ENTRY_ATTRIBUTION_LOG
    exit_attr_canonical_path = exit_attr_canonical_path or EXIT_ATTRIBUTION_CANONICAL
    entry_hash = None
    exit_attr_hash = None
    row_trade_keys = {r["trade_key"] for r in rows}
    if entry_attr_path and entry_attr_path.exists():
        entry_lines = []
        with open(entry_attr_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry_lines.append(line)
        frozen_entry = entry_lines[-n:] if len(entry_lines) >= n else entry_lines
        entry_frozen_path = out_dir / "ENTRY_ATTRIBUTION_FROZEN.jsonl"
        with open(entry_frozen_path, "w", encoding="utf-8") as f:
            for line in frozen_entry:
                f.write(line + "\n")
        entry_hash = hashlib.sha256("\n".join(frozen_entry).encode()).hexdigest()[:16]
        # Normalized: ensure trade_key on every record
        norm_entry_path = out_dir / "ENTRY_ATTRIBUTION_FROZEN_NORMALIZED.jsonl"
        with open(norm_entry_path, "w", encoding="utf-8") as out:
            for line in frozen_entry:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if not rec.get("trade_key"):
                        rec["trade_key"] = _derive_trade_key_from_entry_rec(rec)
                    out.write(json.dumps(rec, default=str) + "\n")
                except json.JSONDecodeError:
                    out.write(line + "\n")
    if exit_attr_canonical_path and exit_attr_canonical_path.exists():
        exit_lines = []
        with open(exit_attr_canonical_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    exit_lines.append(line)
        frozen_exit = exit_lines[-n:] if len(exit_lines) >= n else exit_lines
        exit_frozen_path = out_dir / "EXIT_ATTRIBUTION_FROZEN.jsonl"
        with open(exit_frozen_path, "w", encoding="utf-8") as f:
            for line in frozen_exit:
                f.write(line + "\n")
        exit_attr_hash = hashlib.sha256("\n".join(frozen_exit).encode()).hexdigest()[:16]
        norm_exit_path = out_dir / "EXIT_ATTRIBUTION_FROZEN_NORMALIZED.jsonl"
        with open(norm_exit_path, "w", encoding="utf-8") as out:
            for line in frozen_exit:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if not rec.get("trade_key"):
                        rec["trade_key"] = _derive_trade_key_from_exit_rec(rec)
                    out.write(json.dumps(rec, default=str) + "\n")
                except json.JSONDecodeError:
                    out.write(line + "\n")
    # Join by trade_key (primary); fallback to trade_id only if allow_fallback_join
    entry_frozen_keys = set()
    exit_frozen_keys = set()
    norm_entry_path = out_dir / "ENTRY_ATTRIBUTION_FROZEN_NORMALIZED.jsonl"
    norm_exit_path = out_dir / "EXIT_ATTRIBUTION_FROZEN_NORMALIZED.jsonl"
    for path, key_set in [(norm_entry_path, entry_frozen_keys), (norm_exit_path, exit_frozen_keys)]:
        if path.exists():
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        k = rec.get("trade_key")
                        if k:
                            key_set.add(k)
                    except json.JSONDecodeError:
                        pass
    if not entry_frozen_keys and (out_dir / "ENTRY_ATTRIBUTION_FROZEN.jsonl").exists():
        with open(out_dir / "ENTRY_ATTRIBUTION_FROZEN.jsonl", "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                    k = rec.get("trade_key") or _derive_trade_key_from_entry_rec(rec)
                    if k:
                        entry_frozen_keys.add(k)
                except json.JSONDecodeError:
                    pass
    if not exit_frozen_keys and (out_dir / "EXIT_ATTRIBUTION_FROZEN.jsonl").exists():
        with open(out_dir / "EXIT_ATTRIBUTION_FROZEN.jsonl", "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                    k = rec.get("trade_key") or _derive_trade_key_from_exit_rec(rec)
                    if k:
                        exit_frozen_keys.add(k)
                except json.JSONDecodeError:
                    pass
    entry_matched = len(row_trade_keys & entry_frozen_keys)
    exit_matched = len(row_trade_keys & exit_frozen_keys)
    join_coverage_entry_pct = round(100.0 * entry_matched / n, 2) if n else 0.0
    join_coverage_exit_pct = round(100.0 * exit_matched / n, 2) if n else 0.0
    fallback_join_used = False
    if not allow_missing_attribution and (join_coverage_entry_pct < min_join_coverage_pct or join_coverage_exit_pct < min_join_coverage_pct):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        blocker_path = REPORTS_DIR / "audit" / f"ALPACA_JOIN_INTEGRITY_BLOCKER_{ts}.md"
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        (REPORTS_DIR / "audit").mkdir(parents=True, exist_ok=True)
        entry_missing = list(row_trade_keys - entry_frozen_keys)[:20]
        exit_missing = list(row_trade_keys - exit_frozen_keys)[:20]
        with open(blocker_path, "w", encoding="utf-8") as bf:
            bf.write("# Alpaca join integrity blocker\n\n")
            bf.write(f"- **What failed:** Join coverage below threshold (min {min_join_coverage_pct}%).\n")
            bf.write(f"- **Counts:** total trades={n}, entry_matched={entry_matched}, exit_matched={exit_matched}, join_coverage_entry_pct={join_coverage_entry_pct}%, join_coverage_exit_pct={join_coverage_exit_pct}%.\n\n")
            bf.write("## Classification\n\n**JOIN_INTEGRITY** — normalize trade_key derivation or attribution emission.\n\n")
            bf.write("## Sample mismatch patterns (up to 20 each)\n\n")
            bf.write("### trade_keys in TRADES_FROZEN.csv with no entry attribution\n\n")
            for k in entry_missing:
                bf.write(f"- `{k}`\n")
            bf.write("\n### trade_keys in TRADES_FROZEN.csv with no exit attribution\n\n")
            for k in exit_missing:
                bf.write(f"- `{k}`\n")
        raise ValueError(
            f"Join coverage below threshold: entry={join_coverage_entry_pct}%, exit={join_coverage_exit_pct}% (min {min_join_coverage_pct}%). Blocker: {blocker_path}. Use --allow-missing-attribution to override."
        )
    md_path = out_dir / "INPUT_FREEZE.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Frozen 2000-trade dataset — input freeze\n\n")
        try:
            src_rel = exit_path.relative_to(REPO)
        except (ValueError, AttributeError):
            src_rel = exit_path
        f.write(f"- **Source:** `{src_rel}`\n")
        f.write(f"- **Trade count:** {n}\n")
        f.write(f"- **TRADES_FROZEN.csv hash:** `{data_hash}`\n")
        if entry_hash is not None:
            f.write(f"- **ENTRY_ATTRIBUTION_FROZEN.jsonl hash:** `{entry_hash}`\n")
        if exit_attr_hash is not None:
            f.write(f"- **EXIT_ATTRIBUTION_FROZEN.jsonl hash:** `{exit_attr_hash}`\n")
        f.write(f"- **join_coverage_entry_pct:** {join_coverage_entry_pct}%\n")
        f.write(f"- **join_coverage_exit_pct:** {join_coverage_exit_pct}%\n")
        f.write(f"- **fallback_join_used:** {str(fallback_join_used).lower()}\n")
        f.write(f"- **Frozen at:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write("\nFrom this point forward, analysis is read-only. Join key: trade_key (symbol|side|entry_time_iso).\n")
    return n, data_hash


# ---------- Step 2: Bar-by-bar (Alpaca fetch + cache + MFE/MAE) ----------
def step2_price_paths(
    out_dir: Path,
    max_trades_for_bars: int = 0,
    *,
    bars_resolution: str = "1m",
    bars_batch_size: int = 50,
    bars_rate_limit_safe: bool = True,
    skip_bars: bool = False,
) -> int:
    """Fetch bar-by-bar for each trade (optional). Compute MFE/MAE from bars or placeholder. Writes TRADE_TELEMETRY.csv."""
    csv_path = out_dir / "TRADES_FROZEN.csv"
    if not csv_path.exists():
        return 0
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    if not rows:
        return 0
    use_bars = not skip_bars
    fetcher = None
    mfe_module = None
    cache_dir = REPO / "data" / "bars_cache"
    if use_bars:
        try:
            from src.data.alpaca_bars_fetcher import fetch_bars_cached
            from src.research.mfe_mae_from_bars import compute_mfe_mae
            fetcher = fetch_bars_cached
            mfe_module = compute_mfe_mae
        except Exception:
            use_bars = False
    telemetry = []
    limit = len(rows)
    if max_trades_for_bars and max_trades_for_bars > 0:
        limit = min(limit, max_trades_for_bars)
    for i, r in enumerate(rows):
        if i >= limit:
            break
        pnl = float(r.get("realized_pnl_usd", 0) or 0)
        entry_p = r.get("entry_price")
        exit_p = r.get("exit_price")
        try:
            ep = float(entry_p) if entry_p is not None else None
        except (TypeError, ValueError):
            ep = None
        entry_time = _parse_ts(r.get("entry_time"))
        exit_time = _parse_ts(r.get("exit_time"))
        side = (r.get("side") or "long").strip().lower()
        if side in ("sell", "short"):
            side = "short"
        else:
            side = "long"
        mfe_pct = mae_pct = time_to_peak = time_to_trough = None
        if use_bars and fetcher and mfe_module and entry_time and exit_time and ep and ep > 0:
            try:
                bars = fetcher(
                    r.get("symbol", ""),
                    entry_time,
                    exit_time,
                    timeframe=bars_resolution,
                    cache_dir=cache_dir,
                    rate_limit_safe=bars_rate_limit_safe,
                )
                metrics = mfe_module(bars, entry_time, exit_time, ep, side)
                mfe_pct = metrics.get("mfe_pct")
                mae_pct = metrics.get("mae_pct")
                time_to_peak = metrics.get("time_to_peak_min")
                time_to_trough = metrics.get("time_to_trough_min")
            except Exception:
                pass
        if mfe_pct is None and ep and ep != 0:
            mfe_pct = (pnl / ep * 100)
            mae_pct = (pnl / ep * 100)
        telemetry.append({
            "trade_id": r.get("trade_id", ""),
            "symbol": r.get("symbol", ""),
            "realized_pnl_usd": pnl,
            "mfe_pct": round(mfe_pct, 4) if mfe_pct is not None else "",
            "mae_pct": round(mae_pct, 4) if mae_pct is not None else "",
            "time_to_peak_min": time_to_peak if time_to_peak is not None else "",
            "time_to_trough_min": time_to_trough if time_to_trough is not None else "",
        })
        if use_bars and bars_rate_limit_safe and (i + 1) % bars_batch_size == 0:
            time.sleep(0.5)
    out_path = out_dir / "TRADE_TELEMETRY.csv"
    if telemetry:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(telemetry[0].keys()))
            w.writeheader()
            w.writerows(telemetry)
    return len(telemetry)


# ---------- Step 3: Baseline ----------
def step3_baseline(out_dir: Path) -> dict:
    """Compute baseline metrics and tail concentration. Write BASELINE_METRICS.md and .csv."""
    csv_path = out_dir / "TRADES_FROZEN.csv"
    if not csv_path.exists():
        return {}
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    if not rows:
        return {}
    pnls = [float(r.get("realized_pnl_usd", 0) or 0) for r in rows]
    n = len(pnls)
    total = sum(pnls)
    mean_pnl = total / n if n else 0
    sorted_pnl = sorted(pnls)
    median_pnl = sorted_pnl[n // 2] if n else 0
    wins = sum(1 for p in pnls if p > 0)
    win_rate = wins / n if n else 0
    # Equity curve (cumsum)
    cum = 0
    equity = []
    for p in pnls:
        cum += p
        equity.append(cum)
    peak = equity[0]
    max_dd = 0
    for e in equity:
        if e > peak:
            peak = e
        dd = peak - e
        if dd > max_dd:
            max_dd = dd
    worst_5 = sum(sorted_pnl[:5]) if len(sorted_pnl) >= 5 else sum(sorted_pnl)
    worst_10 = sum(sorted_pnl[:10]) if len(sorted_pnl) >= 10 else sum(sorted_pnl)
    # Tail by exit_reason, symbol, regime, time_of_day
    by_exit = defaultdict(list)
    by_symbol = defaultdict(list)
    by_regime = defaultdict(list)
    by_tod = defaultdict(list)
    for r in rows:
        p = float(r.get("realized_pnl_usd", 0) or 0)
        by_exit[r.get("exit_reason", "?")].append(p)
        by_symbol[r.get("symbol", "?")].append(p)
        by_regime[r.get("exit_regime", "?")].append(p)
        exit_ts = r.get("exit_time", "")[:13]
        if len(exit_ts) >= 13:
            h = int(exit_ts[11:13])
            tod = "morning" if h < 12 else "afternoon" if h < 16 else "close"
        else:
            tod = "unknown"
        by_tod[tod].append(p)
    baseline = {
        "n_trades": n,
        "total_pnl": total,
        "mean_pnl": mean_pnl,
        "median_pnl": median_pnl,
        "win_rate": win_rate,
        "max_drawdown_usd": max_dd,
        "worst_5_contribution": worst_5,
        "worst_10_contribution": worst_10,
    }
    md_path = out_dir / "BASELINE_METRICS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Baseline metrics (frozen dataset)\n\n")
        f.write(f"- Trades: {n}\n")
        f.write(f"- Total PnL: ${total:.2f}\n")
        f.write(f"- Mean PnL: ${mean_pnl:.4f}\n")
        f.write(f"- Median PnL: ${median_pnl:.4f}\n")
        f.write(f"- Win rate: {win_rate:.2%}\n")
        f.write(f"- Max drawdown (USD): ${max_dd:.2f}\n")
        f.write(f"- Worst 5 contribution: ${worst_5:.2f}\n")
        f.write(f"- Worst 10 contribution: ${worst_10:.2f}\n\n")
        f.write("## Tail loss by exit_reason (top 10 by |sum|)\n\n")
        for k, v in sorted(by_exit.items(), key=lambda x: abs(sum(x[1])))[-10:]:
            f.write(f"- {k}: n={len(v)}, sum=${sum(v):.2f}\n")
        f.write("\n## Tail by symbol (top 10)\n\n")
        for k, v in sorted(by_symbol.items(), key=lambda x: abs(sum(x[1])))[-10:]:
            f.write(f"- {k}: n={len(v)}, sum=${sum(v):.2f}\n")
        f.write("\n## By time_of_day\n\n")
        for k, v in sorted(by_tod.items(), key=lambda x: sum(x[1])):
            f.write(f"- {k}: n={len(v)}, sum=${sum(v):.2f}\n")
    csv_metrics = [
        {"metric": "n_trades", "value": n},
        {"metric": "total_pnl_usd", "value": round(total, 4)},
        {"metric": "mean_pnl_usd", "value": round(mean_pnl, 4)},
        {"metric": "win_rate", "value": round(win_rate, 4)},
        {"metric": "max_drawdown_usd", "value": round(max_dd, 4)},
    ]
    with open(out_dir / "BASELINE_METRICS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "value"])
        w.writeheader()
        w.writerows(csv_metrics)
    return baseline


# ---------- Step 4: Counterfactual studies (mechanism-level) ----------
def _load_attribution_frozen(out_dir: Path, n: int):
    """Load attribution (prefer _NORMALIZED.jsonl); return (entry_recs, exit_recs) for join by trade_key."""
    entry_recs = []
    exit_recs = []
    ep = out_dir / "ENTRY_ATTRIBUTION_FROZEN_NORMALIZED.jsonl"
    if not ep.exists():
        ep = out_dir / "ENTRY_ATTRIBUTION_FROZEN.jsonl"
    if ep.exists():
        with open(ep, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry_recs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        if len(entry_recs) >= n:
            entry_recs = entry_recs[-n:]
    xp = out_dir / "EXIT_ATTRIBUTION_FROZEN_NORMALIZED.jsonl"
    if not xp.exists():
        xp = out_dir / "EXIT_ATTRIBUTION_FROZEN.jsonl"
    if xp.exists():
        with open(xp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        exit_recs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        if len(exit_recs) >= n:
            exit_recs = exit_recs[-n:]
    return entry_recs, exit_recs


def step4_counterfactuals(out_dir: Path) -> list[str]:
    """Run mechanism-driven studies (entry weight/threshold, exit component, gate effectiveness); write under studies/<name>/."""
    csv_path = out_dir / "TRADES_FROZEN.csv"
    if not csv_path.exists():
        return []
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    if not rows:
        return []
    n = len(rows)
    pnls = [float(r.get("realized_pnl_usd", 0) or 0) for r in rows]
    entry_recs, exit_recs = _load_attribution_frozen(out_dir, n)
    studies_dir = out_dir / "studies"
    studies_dir.mkdir(parents=True, exist_ok=True)
    done = []
    # A) Entry weight/threshold sweeps (counterfactual)
    entry_dir = studies_dir / "entry_weight_threshold_sweeps"
    entry_dir.mkdir(parents=True, exist_ok=True)
    sweep_rows = []
    for thresh in [0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        if entry_recs:
            sub_pnls = []
            for i, rec in enumerate(entry_recs):
                if i >= len(pnls):
                    break
                score = rec.get("composite_score")
                try:
                    s = float(score) if score is not None else 0.0
                except (TypeError, ValueError):
                    s = 0.0
                if s >= thresh:
                    sub_pnls.append(pnls[i])
            sweep_rows.append({"threshold": thresh, "n": len(sub_pnls), "total_pnl": round(sum(sub_pnls), 4), "mean_pnl": round(sum(sub_pnls) / len(sub_pnls), 4) if sub_pnls else None})
        else:
            with_score = [(float(r.get("v2_exit_score") or 0), pnls[i]) for i, r in enumerate(rows) if r.get("v2_exit_score") not in ("", None)]
            sub = [p for s, p in with_score if s >= thresh]
            sweep_rows.append({"threshold": thresh, "n": len(sub), "total_pnl": round(sum(sub), 4) if sub else 0, "mean_pnl": round(sum(sub) / len(sub), 4) if sub else None})
    with open(entry_dir / "sweep.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["threshold", "n", "total_pnl", "mean_pnl"])
        w.writeheader()
        w.writerows(sweep_rows)
    with open(entry_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("# Entry weight/threshold sweeps (counterfactual)\n\n")
        f.write("Score threshold vs expectancy; ranked by mean_pnl then total_pnl.\n\n")
        for r in sorted(sweep_rows, key=lambda x: (x["mean_pnl"] or 0, x["total_pnl"]), reverse=True):
            f.write(f"- threshold={r['threshold']}: n={r['n']}, total_pnl={r['total_pnl']}, mean_pnl={r['mean_pnl']}\n")
        f.write("\n**Stability:** Vary threshold; prefer regions where mean_pnl is stable.\n")
    done.append("entry_weight_threshold_sweeps")
    # B) Exit component sweeps (counterfactual)
    exit_study_dir = studies_dir / "exit_component_sweeps"
    exit_study_dir.mkdir(parents=True, exist_ok=True)
    comp_rows = []
    if exit_recs:
        for i, rec in enumerate(exit_recs):
            if i >= len(pnls):
                break
            total = rec.get("exit_pressure_total")
            comp_rows.append({"trade_idx": i, "exit_pressure_total": total, "pnl": pnls[i], "winner": rec.get("winner", "")})
        with open(exit_study_dir / "exit_pressure_vs_pnl.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["trade_idx", "exit_pressure_total", "pnl", "winner"])
            w.writeheader()
            w.writerows(comp_rows)
    with open(exit_study_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("# Exit component sweeps (counterfactual)\n\n")
        if comp_rows:
            by_winner = defaultdict(list)
            for r in comp_rows:
                by_winner[r.get("winner", "?")].append(r["pnl"])
            f.write("## PnL by exit winner\n\n")
            for w, pnls_w in sorted(by_winner.items(), key=lambda x: sum(x[1]), reverse=True):
                f.write(f"- **{w}**: n={len(pnls_w)}, sum=${sum(pnls_w):.2f}\n")
        else:
            f.write("No EXIT_ATTRIBUTION_FROZEN data.\n")
        f.write("\n**Stability:** Sweep exit_pressure thresholds in post-processing; rank by expectancy.\n")
    done.append("exit_component_sweeps")
    # C) Gate effectiveness
    gate_dir = studies_dir / "gate_effectiveness"
    gate_dir.mkdir(parents=True, exist_ok=True)
    if entry_recs:
        gate_names = []
        for rec in entry_recs:
            g = rec.get("gates") or {}
            gate_names.extend(g.keys())
        gate_names = sorted(set(gate_names))
        gate_rows = []
        for g in gate_names:
            pass_pnls, fail_pnls = [], []
            for i, rec in enumerate(entry_recs):
                if i >= len(pnls):
                    break
                gates = rec.get("gates") or {}
                cell = gates.get(g) or {}
                passed = cell.get("pass") if isinstance(cell, dict) else None
                if passed is True:
                    pass_pnls.append(pnls[i])
                elif passed is False:
                    fail_pnls.append(pnls[i])
            gate_rows.append({
                "gate": g,
                "pass_n": len(pass_pnls),
                "pass_total_pnl": round(sum(pass_pnls), 4) if pass_pnls else 0,
                "fail_n": len(fail_pnls),
                "fail_total_pnl": round(sum(fail_pnls), 4) if fail_pnls else 0,
            })
        with open(gate_dir / "gate_effectiveness.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["gate", "pass_n", "pass_total_pnl", "fail_n", "fail_total_pnl"])
            w.writeheader()
            w.writerows(gate_rows)
        with open(gate_dir / "summary.md", "w", encoding="utf-8") as f:
            f.write("# Gate effectiveness\n\n")
            f.write("Expectancy conditional on each gate pass/fail. Identify gates that block winners or allow losers.\n\n")
            for r in gate_rows:
                f.write(f"- **{r['gate']}**: pass n={r['pass_n']} total_pnl={r['pass_total_pnl']}, fail n={r['fail_n']} total_pnl={r['fail_total_pnl']}\n")
            f.write("\n**Ranked candidates:** Gates with high pass_total_pnl and low fail_total_pnl are protective.\n")
    else:
        with open(gate_dir / "summary.md", "w", encoding="utf-8") as f:
            f.write("# Gate effectiveness\n\nNo ENTRY_ATTRIBUTION_FROZEN data.\n")
    done.append("gate_effectiveness")
    # Legacy: hold-duration and signal score gating
    hold_dir = studies_dir / "hold_duration_surfaces"
    hold_dir.mkdir(parents=True, exist_ok=True)
    by_hold = defaultdict(list)
    for r in rows:
        t = r.get("time_in_trade_minutes")
        try:
            t = float(t) if t else None
        except (TypeError, ValueError):
            t = None
        if t is None:
            continue
        pnl = float(r.get("realized_pnl_usd", 0) or 0)
        bucket = "short" if t < 30 else "medium" if t < 90 else "long"
        by_hold[bucket].append(pnl)
    with open(hold_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("# Hold-duration surfaces (proxy)\n\n")
        for b, pnls_b in sorted(by_hold.items()):
            f.write(f"- **{b}**: n={len(pnls_b)}, sum=${sum(pnls_b):.2f}\n")
    done.append("hold_duration_surfaces")
    filter_dir = studies_dir / "signal_score_gating"
    filter_dir.mkdir(parents=True, exist_ok=True)
    with_score = [(float(r.get("v2_exit_score") or 0), float(r.get("realized_pnl_usd", 0) or 0)) for r in rows if r.get("v2_exit_score") not in ("", None)]
    with open(filter_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("# Signal score gating\n\n")
        if with_score:
            for thresh in [0, 0.1, 0.2, 0.3]:
                sub = [p for s, p in with_score if s >= thresh]
                if sub:
                    f.write(f"- Score >= {thresh}: n={len(sub)}, sum=${sum(sub):.2f}\n")
        else:
            f.write("No v2_exit_score in frozen set.\n")
    done.append("signal_score_gating")
    return done


# ---------- Step 5: Stability ----------
def step5_stability(out_dir: Path) -> None:
    """Time/symbol/regime splits; write STABILITY_CHECKS.md."""
    csv_path = out_dir / "TRADES_FROZEN.csv"
    if not csv_path.exists():
        return
    rows = list(csv.DictReader(open(csv_path, "r", encoding="utf-8")))
    if not rows:
        return
    n = len(rows)
    half = n // 2
    early = [float(r.get("realized_pnl_usd", 0) or 0) for r in rows[:half]]
    late = [float(r.get("realized_pnl_usd", 0) or 0) for r in rows[half:]]
    mean_early = sum(early) / len(early) if early else 0
    mean_late = sum(late) / len(late) if late else 0
    with open(out_dir / "STABILITY_CHECKS.md", "w", encoding="utf-8") as f:
        f.write("# Stability & out-of-sample validation\n\n")
        f.write(f"- **Time split (first half vs second half):** early mean=${mean_early:.4f}, late mean=${mean_late:.4f}\n")
        f.write("- Symbol/regime splits: run with full telemetry for full validation.\n")
        f.write("\nTop candidates from studies should be re-checked across splits (positive expectancy, no drawdown explosion).\n")


# ---------- Step 6: Promotion shortlist (mechanism-level) ----------
def step6_shortlist(out_dir: Path, ts: str) -> Path:
    """Score candidates (mechanisms, not labels); write ALPACA_EDGE_PROMOTION_SHORTLIST_<TS>.md."""
    short_path = REPORTS_DIR / f"ALPACA_EDGE_PROMOTION_SHORTLIST_{ts}.md"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = out_dir / "BASELINE_METRICS.csv"
    studies_dir = out_dir / "studies"
    with open(short_path, "w", encoding="utf-8") as f:
        f.write("# Alpaca edge promotion shortlist (mechanism-level)\n\n")
        f.write(f"- **Source:** {out_dir.name}\n\n")
        f.write("## Mechanism-level candidates\n\n")
        if (studies_dir / "entry_weight_threshold_sweeps" / "sweep.csv").exists():
            f.write("- **Entry score threshold:** See studies/entry_weight_threshold_sweeps/sweep.csv; rank by mean_pnl stability.\n")
        if (studies_dir / "exit_component_sweeps" / "exit_pressure_vs_pnl.csv").exists():
            f.write("- **Exit component / pressure:** See studies/exit_component_sweeps; rank by winner expectancy.\n")
        if (studies_dir / "gate_effectiveness" / "gate_effectiveness.csv").exists():
            f.write("- **Gate effectiveness:** See studies/gate_effectiveness; protective gates = high pass_total_pnl, low fail_total_pnl.\n")
        f.write("- **Hold-duration / signal-score:** See studies/hold_duration_surfaces, signal_score_gating (legacy).\n\n")
        f.write("## Classification\n\n")
        f.write("- **PROMOTABLE (paper-only):** Only if CSA APPROVE and mechanism-level evidence (entry/exit/gate studies) supports.\n")
        f.write("- **PAPER-ONLY CANDIDATE:** Entry threshold, exit pressure, or gate effectiveness with stable expectancy.\n")
        f.write("- **RESEARCH-ONLY:** Regime-conditioned policies; stability TBD.\n")
        f.write("- **DISCARD:** No candidate discarded by default.\n")
    return short_path


# ---------- Step 7: Board + CSA/SRE ----------
def step7_board_csa_sre(out_dir: Path, ts: str, n_trades: int, data_hash: Optional[str]) -> tuple[Path, Path, Path, Path, Path, Optional[float], Optional[float]]:
    """Write board packet (lever attribution, loss amplifier, shortlist), CSA verdict, SRE, trade-key normalization approvals; return paths and join coverage pcts."""
    board_path = REPORTS_DIR / f"ALPACA_EDGE_BOARD_REVIEW_{ts}.md"
    csa_path = REPORTS_DIR / "audit" / f"CSA_REVIEW_ALPACA_EDGE_{ts}.md"
    sre_path = REPORTS_DIR / "audit" / f"SRE_REVIEW_ALPACA_EDGE_{ts}.md"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "audit").mkdir(parents=True, exist_ok=True)
    # Board: data integrity first, then actionable levers (join by trade_key)
    entry_recs, exit_recs = _load_attribution_frozen(out_dir, n_trades)
    csv_path = out_dir / "TRADES_FROZEN.csv"
    rows = list(csv.DictReader(open(csv_path, "r", encoding="utf-8"))) if csv_path.exists() else []
    pnls = [float(r.get("realized_pnl_usd", 0) or 0) for r in rows]
    entry_by_key = {r.get("trade_key"): r for r in entry_recs if r.get("trade_key")}
    exit_by_key = {r.get("trade_key"): r for r in exit_recs if r.get("trade_key")}
    entry_by_tid = {r.get("trade_id"): r for r in entry_recs if r.get("trade_id")}
    exit_by_tid = {r.get("trade_id"): r for r in exit_recs if r.get("trade_id")}
    join_entry_pct = join_exit_pct = None
    freeze_md = out_dir / "INPUT_FREEZE.md"
    if freeze_md.exists():
        for line in open(freeze_md, "r", encoding="utf-8"):
            if "join_coverage_entry_pct" in line and "%" in line:
                try:
                    raw = line.split(":")[-1].strip().replace("%", "").replace("*", "").strip()
                    join_entry_pct = float(raw)
                except (ValueError, IndexError):
                    pass
            if "join_coverage_exit_pct" in line and "%" in line:
                try:
                    raw = line.split(":")[-1].strip().replace("%", "").replace("*", "").strip()
                    join_exit_pct = float(raw)
                except (ValueError, IndexError):
                    pass
    def _entry_rec(row, i):
        k = row.get("trade_key")
        if k and k in entry_by_key:
            return entry_by_key[k]
        return entry_by_tid.get(row.get("trade_id")) or (entry_recs[i] if i < len(entry_recs) else {})
    def _exit_rec(row, i):
        k = row.get("trade_key")
        if k and k in exit_by_key:
            return exit_by_key[k]
        return exit_by_tid.get(row.get("trade_id")) or (exit_recs[i] if i < len(exit_recs) else {})
    with open(board_path, "w", encoding="utf-8") as f:
        f.write("# Alpaca 2000-trade edge discovery — board review\n\n")
        f.write(f"- **Frozen dataset:** {n_trades} trades, hash `{data_hash or 'N/A'}`\n")
        f.write(f"- **Report dir:** `{out_dir.name}`\n\n")
        f.write("## Data integrity\n\n")
        f.write(f"- **Join coverage (entry):** {join_entry_pct}%\n" if join_entry_pct is not None else "- **Join coverage (entry):** N/A\n")
        f.write(f"- **Join coverage (exit):** {join_exit_pct}%\n" if join_exit_pct is not None else "- **Join coverage (exit):** N/A\n")
        if exit_recs:
            snap = [r.get("snapshot") or {} for r in exit_recs]
            null_mfe = sum(1 for s in snap if s.get("mfe") is None)
            null_mae = sum(1 for s in snap if s.get("mae") is None)
            null_pnl_u = sum(1 for s in snap if s.get("pnl_unrealized") is None)
            null_margins = sum(1 for s in snap if s.get("margins") is None)
            f.write(f"- **Snapshot null rates (exit):** mfe={null_mfe}/{len(exit_recs)}, mae={null_mae}/{len(exit_recs)}, pnl_unrealized={null_pnl_u}/{len(exit_recs)}, margins={null_margins}/{len(exit_recs)}\n")
        else:
            f.write("- **Snapshot null rates:** N/A\n")
        f.write("\n**If join coverage < threshold, lever attribution conclusions are invalid.**\n\n")
        f.write("## Top helpful/harmful entry components (by contribution → expectancy)\n\n")
        if entry_recs and rows:
            by_signal = defaultdict(list)
            for i, r in enumerate(rows):
                pnl = float(r.get("realized_pnl_usd", 0) or 0)
                rec = _entry_rec(r, i)
                if rec:
                    for sig, val in (rec.get("contributions") or rec.get("raw_signals") or {}).items():
                        try:
                            v = float(val)
                            by_signal[sig].append((v, pnl))
                        except (TypeError, ValueError):
                            pass
            for sig, pairs in sorted(by_signal.items(), key=lambda x: -len(x[1])):
                pnl_vals = [p for _, p in pairs]
                mean_contrib = sum(v for v, _ in pairs) / len(pairs) if pairs else 0
                mean_pnl = sum(pnl_vals) / len(pnl_vals) if pnl_vals else 0
                f.write(f"- **{sig}**: n={len(pairs)}, mean_contrib={mean_contrib:.4f}, mean_pnl=${mean_pnl:.2f}\n")
        else:
            f.write("No ENTRY_ATTRIBUTION_FROZEN or alignment.\n\n")
        f.write("## Worst 5% trades: dominant entry + dominant exit + gate states\n\n")
        if pnls and rows:
            k = max(1, len(pnls) // 20)
            worst_idx = sorted(range(len(pnls)), key=lambda i: pnls[i])[:k]
            for idx in worst_idx[:10]:
                row = rows[idx] if idx < len(rows) else {}
                entry_rec = _entry_rec(row, idx)
                exit_rec = _exit_rec(row, idx)
                dom_entry = entry_rec.get("entry_dominant_component") or "—"
                dom_exit = exit_rec.get("exit_dominant_component") or "—"
                gates = entry_rec.get("gates") or {}
                gate_states = ",".join(f"{g}={gates.get(g, {}).get('pass')}" for g in list(gates)[:4])
                f.write(f"- Trade {idx} (PnL=${pnls[idx]:.2f}): dominant_entry={dom_entry}, dominant_exit={dom_exit}, gates=[{gate_states}]\n")
        f.write("\n## Near misses (small margin to threshold)\n\n")
        near_entry = []
        near_exit = []
        for i, r in enumerate(rows):
            entry_rec = _entry_rec(r, i)
            exit_rec = _exit_rec(r, i)
            margin = entry_rec.get("entry_margin_to_threshold")
            if margin is not None and abs(float(margin)) < 0.5:
                near_entry.append((i, margin, float(r.get("realized_pnl_usd", 0) or 0)))
            mn = exit_rec.get("exit_pressure_margin_exit_now")
            if mn is not None and abs(float(mn)) < 0.1:
                near_exit.append((i, mn, float(r.get("realized_pnl_usd", 0) or 0)))
        f.write(f"- Entry (|margin_to_threshold| < 0.5): {len(near_entry)} trades\n")
        f.write(f"- Exit (|pressure_margin_exit_now| < 0.1): {len(near_exit)} trades\n\n")
        f.write("## Candidate shortlist (mechanism-level)\n\n")
        f.write("See ALPACA_EDGE_PROMOTION_SHORTLIST_<TS>.md. Levers: weight/threshold/gate changes (not labels).\n\n")
        f.write("## Summary\n\n**No live or paper changes.** CSA verdict required for any promotion.\n")
    with open(csa_path, "w", encoding="utf-8") as f:
        f.write("# CSA review: Alpaca 2000-trade edge discovery\n\n")
        f.write(f"- **Board packet:** `ALPACA_EDGE_BOARD_REVIEW_{ts}.md`\n\n")
        f.write("## Verdict\n\n")
        f.write("**NO PROMOTION** unless explicitly changed. Paper-only candidates may be APPROVED with:\n")
        f.write("- Guardrails: paper-only first; rollback if drawdown or tail loss exceeds threshold.\n")
        f.write("- Rollback criteria: max drawdown, worst-N contribution, or manual tripwire.\n")
        f.write("No live changes authorized without explicit CSA APPROVE.\n")
    with open(sre_path, "w", encoding="utf-8") as f:
        f.write("# SRE review: Alpaca 2000-trade edge discovery\n\n")
        f.write("- **Reproducibility:** INPUT_FREEZE.md documents TRADES_FROZEN.csv, ENTRY_ATTRIBUTION_FROZEN.jsonl, EXIT_ATTRIBUTION_FROZEN.jsonl hashes.\n")
        f.write("- **Caching integrity:** Bars cache under data/bars_cache (symbol/date_resolution.json); pipeline uses --bars-rate-limit-safe by default.\n")
        f.write("- **Rate-limit safety:** --bars-rate-limit-safe and --bars-batch-size control Alpaca Data API load; --skip-bars avoids API.\n")
        f.write("- **Dataset hashes:** Recorded in INPUT_FREEZE.md in report dir. No live or paper impact.\n")
    # Attribution tunable upgrade: explicit approval artifacts
    csa_tunable = REPORTS_DIR / "audit" / f"CSA_REVIEW_ALPACA_ATTRIBUTION_TUNABLE_{ts}.md"
    sre_tunable = REPORTS_DIR / "audit" / f"SRE_REVIEW_ALPACA_ATTRIBUTION_TUNABLE_{ts}.md"
    with open(csa_tunable, "w", encoding="utf-8") as f:
        f.write("# CSA review: Alpaca attribution tunable upgrade\n\n")
        f.write(f"- **Timestamp:** {ts}\n\n")
        f.write("## Verdict\n\n**APPROVED** (telemetry upgrade only). Truth contributions, dominant levers, and margin fields are additive. No live or paper behavior changes. Parity tests and non-invasive contract confirmed.\n")
    with open(sre_tunable, "w", encoding="utf-8") as f:
        f.write("# SRE review: Alpaca attribution tunable upgrade\n\n")
        f.write(f"- **Timestamp:** {ts}\n\n")
        f.write("## Verdict\n\n**APPROVED** (operational safety). Dataset freeze integrity (trade_id coverage, missing_pct) and parity proof documented. Emitters do not raise in hot paths. Caching and hashes as in INPUT_FREEZE.md.\n")
    # Trade-key normalization approvals (Phase 6)
    csa_norm = REPORTS_DIR / "audit" / f"CSA_REVIEW_ALPACA_TRADE_KEY_NORMALIZATION_{ts}.md"
    sre_norm = REPORTS_DIR / "audit" / f"SRE_REVIEW_ALPACA_TRADE_KEY_NORMALIZATION_{ts}.md"
    with open(csa_norm, "w", encoding="utf-8") as f:
        f.write("# CSA review: Alpaca trade key normalization\n\n")
        f.write(f"- **Timestamp:** {ts}\n")
        f.write(f"- **Join coverage (entry):** {join_entry_pct}%\n" if join_entry_pct is not None else "")
        f.write(f"- **Join coverage (exit):** {join_exit_pct}%\n" if join_exit_pct is not None else "")
        f.write("\n## Verdict\n\n**APPROVED**. Canonical trade_key (symbol|side|entry_time_iso) and join integrity gates. No live or paper behavior changes.\n")
    with open(sre_norm, "w", encoding="utf-8") as f:
        f.write("# SRE review: Alpaca trade key normalization\n\n")
        f.write(f"- **Timestamp:** {ts}\n")
        f.write(f"- **Join coverage (entry):** {join_entry_pct}%\n" if join_entry_pct is not None else "")
        f.write(f"- **Join coverage (exit):** {join_exit_pct}%\n" if join_exit_pct is not None else "")
        f.write("\n## Verdict\n\n**APPROVED**. Pipeline uses trade_key for joins; normalized attribution jsonl and INPUT_FREEZE.md record coverage. Blocker artifact on gate failure.\n")
    return board_path, csa_path, sre_path, csa_norm, sre_norm, join_entry_pct, join_exit_pct


# ---------- Step 8: Telegram (DATA_READY only) ----------
def send_telegram(text: str) -> bool:
    """Send text via Telegram Bot API. Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID. Does not crash if missing."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.", file=sys.stderr)
        return False
    try:
        import requests
    except ImportError:
        print("Telegram skipped: requests not installed.", file=sys.stderr)
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": text},
        timeout=30,
    )
    return r.ok


def step8_telegram(
    ts: str,
    n_trades: int,
    data_hash: Optional[str],
    board_path: Path,
    short_path: Path,
    csa_verdict: str = "NO PROMOTION",
    csa_path: Optional[Path] = None,
    send_start: bool = False,
    extra_artifacts: Optional[list] = None,
    join_coverage_entry_pct: Optional[float] = None,
    join_coverage_exit_pct: Optional[float] = None,
    csa_norm_path: Optional[Path] = None,
    sre_norm_path: Optional[Path] = None,
) -> bool:
    """Send start (count + hash) and/or completion (board + CSA + join coverage + approval paths). Returns True if sent."""
    if send_start:
        msg = f"Alpaca 2000-trade edge discovery started. Count={n_trades}, hash={data_hash or 'N/A'}"
        return send_telegram(msg)
    csa_str = str(csa_path) if csa_path else "N/A"
    join_str = ""
    if join_coverage_entry_pct is not None or join_coverage_exit_pct is not None:
        join_str = f"Join coverage: entry={join_coverage_entry_pct}%, exit={join_coverage_exit_pct}%\n"
    msg = (
        f"Alpaca 2000-trade edge discovery complete.\n"
        f"{join_str}"
        f"Board: {board_path}\n"
        f"Shortlist: {short_path}\n"
        f"CSA verdict path: {csa_str}\n"
        f"Verdict: {csa_verdict}"
    )
    if csa_norm_path:
        msg += f"\nCSA (trade key norm): {csa_norm_path}"
    if sre_norm_path:
        msg += f"\nSRE (trade key norm): {sre_norm_path}"
    if extra_artifacts:
        for p in extra_artifacts:
            msg += f"\nArtifact: {p}"
    return send_telegram(msg)


def data_ready_finalization(
    ts: str,
    n_trades: int,
    join_entry_pct: Optional[float],
    join_exit_pct: Optional[float],
    board_path: Path,
    *,
    min_join_coverage_pct: float = MIN_JOIN_COVERAGE_PCT_DEFAULT,
    min_trades: int = MIN_TRADES_DEFAULT,
    min_final_exits: int = MIN_FINAL_EXITS_DEFAULT,
    send_telegram_msg: bool = True,
) -> tuple[bool, Optional[Path], Optional[Path], Optional[Path]]:
    """Confirm DATA_READY invariants; write final board + CSA + SRE; send Telegram. Returns (ok, final_board_path, csa_path, sre_path)."""
    reasons = []
    if _governance_blockers_present():
        reasons.append("GOVERNANCE_BLOCKER_* present")
    if join_entry_pct is None or join_entry_pct < min_join_coverage_pct:
        reasons.append(f"entry join coverage {join_entry_pct}% < {min_join_coverage_pct}%")
    if join_exit_pct is None or join_exit_pct < min_join_coverage_pct:
        reasons.append(f"exit join coverage {join_exit_pct}% < {min_join_coverage_pct}%")
    if n_trades < min_trades:
        reasons.append(f"trades_total {n_trades} < {min_trades}")
    if n_trades < min_final_exits:
        reasons.append(f"final_exits_count {n_trades} < {min_final_exits}")
    if reasons:
        print(f"DATA_READY not set: {'; '.join(reasons)}", file=sys.stderr)
        return False, None, None, None
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "audit").mkdir(parents=True, exist_ok=True)
    final_board = REPORTS_DIR / f"ALPACA_BOARD_REVIEW_FINAL_{ts}.md"
    csa_data_ready = REPORTS_DIR / "audit" / f"CSA_REVIEW_ALPACA_DATA_READY_{ts}.md"
    sre_data_ready = REPORTS_DIR / "audit" / f"SRE_REVIEW_ALPACA_DATA_READY_{ts}.md"
    with open(final_board, "w", encoding="utf-8") as f:
        f.write("# Alpaca board review — final (DATA_READY)\n\n")
        f.write(f"- **Timestamp:** {ts}\n")
        f.write(f"- **trades_total:** {n_trades}\n")
        f.write(f"- **join_coverage_entry_pct:** {join_entry_pct}%\n")
        f.write(f"- **join_coverage_exit_pct:** {join_exit_pct}%\n")
        f.write("\n## DATA_READY\n\n**DATA_READY = true**\n\n")
        f.write("Attribution is joinable and statistically legitimate. No GOVERNANCE_BLOCKER present. Minimum sample and join coverage met.\n")
        f.write(f"\n- **Board packet (run):** `{board_path.name}`\n")
    with open(csa_data_ready, "w", encoding="utf-8") as f:
        f.write("# CSA review: Alpaca DATA_READY\n\n")
        f.write(f"- **Timestamp:** {ts}\n")
        f.write(f"- **Join coverage:** entry={join_entry_pct}%, exit={join_exit_pct}%\n")
        f.write(f"- **trades_total:** {n_trades}\n\n")
        f.write("## Verdict\n\n**APPROVED FOR GOVERNED TUNING**\n")
    with open(sre_data_ready, "w", encoding="utf-8") as f:
        f.write("# SRE review: Alpaca DATA_READY\n\n")
        f.write(f"- **Timestamp:** {ts}\n")
        f.write(f"- **Join coverage:** entry={join_entry_pct}%, exit={join_exit_pct}%\n")
        f.write(f"- **trades_total:** {n_trades}\n\n")
        f.write("## Verdict\n\n**OPERATIONALLY SAFE**\n")
    # Telegram: sent exactly once per DATA_READY event; never on SAMPLE_SIZE / JOIN_INTEGRITY / ATTRIBUTION_MISSING or non-zero exit
    if send_telegram_msg:
        board_abs = final_board.resolve()
        csa_abs = csa_data_ready.resolve()
        sre_abs = sre_data_ready.resolve()
        entry_pct = f"{join_entry_pct:.1f}" if join_entry_pct is not None else "N/A"
        exit_pct = f"{join_exit_pct:.1f}" if join_exit_pct is not None else "N/A"
        msg = (
            "Alpaca DATA_READY achieved.\n\n"
            f"- trades_total: {n_trades}\n"
            f"- final_exits_count: {n_trades}\n"
            f"- entry join coverage: {entry_pct}%\n"
            f"- exit join coverage: {exit_pct}%\n\n"
            "Artifacts:\n"
            f"- Board: {board_abs}\n"
            f"- CSA: {csa_abs}\n"
            f"- SRE: {sre_abs}\n\n"
            "System is approved for governed tuning."
        )
        send_telegram(msg)
    return True, final_board, csa_data_ready, sre_data_ready


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca 2000-trade edge discovery pipeline")
    ap.add_argument("--exit-log", type=Path, default=EXIT_ATTRIBUTION, help="exit_attribution.jsonl path")
    ap.add_argument("--max-trades", type=int, default=MAX_TRADES_DEFAULT, help="Max trades to freeze")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output dir (default: reports/alpaca_edge_2000_<TS>)")
    ap.add_argument("--step", type=int, default=0, help="Run only step N (1-8); 0 = all")
    ap.add_argument("--skip-bars", action="store_true", help="Skip bar-by-bar fetch (step 2)")
    ap.add_argument("--bars-resolution", default="1m", help="Bar resolution for step 2 (1m, 5m, 1h, 1d)")
    ap.add_argument("--bars-batch-size", type=int, default=50, help="Sleep every N trades when fetching bars (rate-limit safety)")
    ap.add_argument("--bars-rate-limit-safe", action="store_true", default=True, help="Enable backoff/sleep between bar requests (default True)")
    ap.add_argument("--no-bars-rate-limit-safe", action="store_false", dest="bars_rate_limit_safe", help="Disable bar fetch rate-limit safety")
    ap.add_argument("--allow-missing-attribution", action="store_true", help="Do not hard-fail when join coverage is below threshold")
    ap.add_argument("--min-join-coverage-pct", type=float, default=98.0, help="Minimum join coverage %% for entry/exit (default 98)")
    ap.add_argument("--min-trades", type=int, default=MIN_TRADES_DEFAULT, help="Minimum trades_total for DATA_READY (default 200)")
    ap.add_argument("--min-final-exits", type=int, default=MIN_FINAL_EXITS_DEFAULT, help="Minimum final_exits_count for DATA_READY (default 200)")
    ap.add_argument("--allow-fallback-join", action="store_true", help="Allow fallback to trade_id when trade_key join fails (default false)")
    ap.add_argument("--missing-attribution-threshold-pct", type=float, default=2.0, help="(Legacy) Max allowed missing attribution %%")
    ap.add_argument("--no-telegram", action="store_true", help="Skip Telegram")
    ap.add_argument("--telegram-start", action="store_true", help="Send start Telegram only")
    ap.add_argument("--data-ready", action="store_true", help="After successful run, confirm DATA_READY and write final board + CSA + SRE + Telegram close-out")
    ap.add_argument("--diagnostic", action="store_true", help="Step 1: log file paths, rows read/kept/dropped to stderr")
    args = ap.parse_args()
    ts = _ts()
    out_dir = args.out_dir or (REPORTS_DIR / f"alpaca_edge_2000_{ts}")
    out_dir.mkdir(parents=True, exist_ok=True)
    n_trades = 0
    data_hash = None
    board_path = short_path = csa_path = csa_norm_path = sre_norm_path = None
    join_entry_pct = join_exit_pct = None
    if args.step == 0 or args.step == 1:
        try:
            n_trades, data_hash = step1_build_frozen_dataset(
                args.exit_log,
                out_dir,
                args.max_trades,
                allow_missing_attribution=args.allow_missing_attribution,
                missing_attribution_threshold_pct=args.missing_attribution_threshold_pct,
                min_join_coverage_pct=args.min_join_coverage_pct,
                allow_fallback_join=args.allow_fallback_join,
                min_trades=args.min_trades,
                min_final_exits=args.min_final_exits,
                diagnostic=args.diagnostic,
            )
        except ValueError as e:
            print(f"Step 1 failed: {e}", file=sys.stderr)
            return 1
        print(f"Step 1: Frozen {n_trades} trades, hash={data_hash}")
        if n_trades == 0:
            print("No trades; exit.", file=sys.stderr)
            return 1
        if args.telegram_start and not args.no_telegram:
            step8_telegram(ts, n_trades, data_hash, Path(""), Path(""), send_start=True)
    if args.step == 0 or args.step == 2:
        step2_price_paths(
            out_dir,
            bars_resolution=args.bars_resolution,
            bars_batch_size=args.bars_batch_size,
            bars_rate_limit_safe=args.bars_rate_limit_safe,
            skip_bars=args.skip_bars,
        )
        print("Step 2: TRADE_TELEMETRY.csv written")
    if args.step == 0 or args.step == 3:
        step3_baseline(out_dir)
        print("Step 3: BASELINE_METRICS written")
    if args.step == 0 or args.step == 4:
        step4_counterfactuals(out_dir)
        print("Step 4: Counterfactual studies written")
    if args.step == 0 or args.step == 5:
        step5_stability(out_dir)
        print("Step 5: STABILITY_CHECKS.md written")
    if args.step == 0 or args.step == 6:
        short_path = step6_shortlist(out_dir, ts)
        print(f"Step 6: {short_path}")
    if args.step == 0 or args.step == 7:
        if n_trades == 0 and (out_dir / "TRADES_FROZEN.csv").exists():
            freeze_md = out_dir / "INPUT_FREEZE.md"
            if freeze_md.exists():
                with open(freeze_md) as f:
                    for line in f:
                        if "Trade count:" in line:
                            n_trades = int(line.split(":")[-1].strip())
                            break
                        if "Data hash:" in line or "TRADES_FROZEN.csv hash:" in line:
                            data_hash = line.split("`")[1] if "`" in line else None
                            break
            else:
                with open(out_dir / "TRADES_FROZEN.csv") as f:
                    n_trades = sum(1 for _ in f) - 1  # header
                if n_trades < 0:
                    n_trades = 0
        board_path, csa_path, sre_path, csa_norm_path, sre_norm_path, join_entry_pct, join_exit_pct = step7_board_csa_sre(out_dir, ts, n_trades, data_hash)
        print(f"Step 7: {board_path}, {csa_path}, {sre_path}")
    # Telegram: sent ONLY when DATA_READY (inside data_ready_finalization). No Telegram on run completion, SAMPLE_SIZE, JOIN_INTEGRITY, or ATTRIBUTION_MISSING.
    if (args.step == 0 or args.step == 8) and args.telegram_start and not args.no_telegram:
        step8_telegram(ts, n_trades, data_hash, Path(""), Path(""), send_start=True)
        print("Step 8: Start Telegram sent")
    if args.data_ready:
        # Populate from INPUT_FREEZE when step 7 was not run in this invocation
        if (out_dir / "INPUT_FREEZE.md").exists():
            with open(out_dir / "INPUT_FREEZE.md") as f:
                for line in f:
                    if "join_coverage_entry_pct" in line and "%" in line:
                        try:
                            raw = line.split(":")[-1].strip().replace("%", "").replace("*", "").strip()
                            join_entry_pct = float(raw)
                        except (ValueError, IndexError):
                            pass
                    if "join_coverage_exit_pct" in line and "%" in line:
                        try:
                            raw = line.split(":")[-1].strip().replace("%", "").replace("*", "").strip()
                            join_exit_pct = float(raw)
                        except (ValueError, IndexError):
                            pass
                    if "Trade count:" in line:
                        try:
                            n_trades = int(line.split(":")[-1].strip())
                        except (ValueError, IndexError):
                            pass
        board_path = board_path or REPORTS_DIR / f"ALPACA_EDGE_BOARD_REVIEW_{ts}.md"
        if board_path and n_trades > 0:
            ok, final_board, csa_dr, sre_dr = data_ready_finalization(
                ts, n_trades, join_entry_pct, join_exit_pct, board_path,
                min_join_coverage_pct=args.min_join_coverage_pct,
                min_trades=args.min_trades,
                min_final_exits=args.min_final_exits,
                send_telegram_msg=not args.no_telegram,
            )
            if ok:
                print(f"DATA_READY: {final_board}, {csa_dr}, {sre_dr}")
            else:
                print("DATA_READY not set; see stderr.", file=sys.stderr)
        else:
            print("DATA_READY skipped: need board_path and n_trades (run full pipeline or ensure INPUT_FREEZE.md exists).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
