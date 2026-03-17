#!/usr/bin/env python3
"""
Alpaca Fast-Lane 25-trade multi-cycle deep review and board analysis.
Read-only: ingests ledger + cycles + exit_attribution, writes reports and one Telegram.
No live changes.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
STATE_DIR = REPO / "state" / "fast_lane_experiment"
LEDGER_PATH = STATE_DIR / "fast_lane_ledger.json"
CYCLES_DIR = STATE_DIR / "cycles"
EXIT_ATTRIBUTION = REPO / "logs" / "exit_attribution.jsonl"
REPORTS_DIR = REPO / "reports"


def _norm(s: Any) -> str:
    v = (s or "").strip() or "unknown"
    return v if v else "unknown"


def _ts_hour(ts: str) -> int:
    if not ts or len(ts) < 13:
        return -1
    try:
        return int(ts[11:13])
    except (ValueError, IndexError):
        return -1


def _time_of_day(ts: str) -> str:
    h = _ts_hour(ts)
    if h < 0:
        return "unknown"
    if h < 12:
        return "morning"
    if h < 16:
        return "afternoon"
    return "close"


def _hold_bucket(rec: dict) -> str:
    try:
        m = float(rec.get("time_in_trade_minutes") or rec.get("hold_minutes") or -1)
    except (TypeError, ValueError):
        return "unknown"
    if m < 0:
        return "unknown"
    if m < 60:
        return "short"
    if m <= 240:
        return "medium"
    return "long"


def _exit_score_band(rec: dict) -> str:
    try:
        s = float(rec.get("v2_exit_score") or rec.get("exit_score") or -999)
    except (TypeError, ValueError):
        return "unknown"
    if s < 0:
        return "unknown"
    if s < 2:
        return "low"
    if s <= 5:
        return "mid"
    return "high"


def _sector_primary(rec: dict) -> str:
    for key in ("exit_sector_profile", "entry_sector_profile"):
        prof = rec.get(key)
        if isinstance(prof, dict) and prof:
            primary = prof.get("primary") or prof.get("sector") or (list(prof.keys())[0] if prof else None)
            if primary:
                return _norm(str(primary)).upper()
    return "UNKNOWN"


# ---------- Step 1: Ingest ----------
def load_ledger(ledger_path: Path) -> list:
    if not ledger_path.exists():
        return []
    with open(ledger_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def load_post_epoch_trades(exit_path: Path, epoch_iso: str) -> list[tuple[str, float, str, dict]]:
    """Yield (trade_id, pnl_usd, timestamp_iso, record) for each exit with timestamp >= epoch."""
    if not exit_path.exists():
        return []
    out = []
    with open(exit_path, "r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            ts = rec.get("timestamp") or rec.get("ts") or rec.get("exit_timestamp") or ""
            if ts < epoch_iso:
                continue
            trade_id = rec.get("trade_id") or f"exit_attr_{idx}"
            pnl = rec.get("realized_pnl_usd") or rec.get("pnl") or rec.get("pnl_usd") or 0.0
            try:
                pnl = float(pnl)
            except (TypeError, ValueError):
                pnl = 0.0
            out.append((str(trade_id), pnl, ts, rec))
    return out


def get_epoch_from_config(state_dir: Path) -> str:
    cfg_path = state_dir / "config.json"
    if cfg_path.exists():
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
                if cfg.get("epoch_start_iso"):
                    return cfg["epoch_start_iso"].strip()
        except (json.JSONDecodeError, OSError):
            pass
    return "2026-03-14T00:00:00Z"


def build_aggregate_rows(
    ledger: list,
    post_epoch_trades: list[tuple[str, float, str, dict]],
    window_size: int = 25,
) -> list[dict]:
    """One row per trade: cycle_id, trade_id, pnl_usd, window_pnl, promoted_angle, factor columns.
    Trades are ordered as in exit log (post-epoch); cycle 1 = indices 0..24, cycle 2 = 25..49, etc.
    """
    rows = []
    n_cycles = len(ledger)
    n_expected = n_cycles * window_size
    trades = post_epoch_trades[:n_expected]
    if len(trades) < n_expected:
        # Fewer post-epoch trades than ledger implies; only use full cycles we have data for
        n_full = len(trades) // window_size
        if n_full == 0:
            return []
        trades = trades[: n_full * window_size]
        ledger = ledger[:n_full]
        n_cycles = n_full
    for i, (trade_id, pnl_usd, ts, rec) in enumerate(trades):
        cidx = i // window_size
        if cidx >= n_cycles:
            break
        entry = ledger[cidx]
        cycle_id = entry.get("cycle_id") or f"cycle_{cidx+1:04d}"
        window_pnl = entry.get("pnl_usd", 0)
        promoted_angle = entry.get("promoted_angle") or entry.get("best_candidate_id") or ""
        exit_reason = _norm(rec.get("exit_reason") or rec.get("close_reason"))
        entry_regime = _norm(rec.get("entry_regime")).upper() or "UNKNOWN"
        exit_regime = _norm(rec.get("exit_regime")).upper() or "UNKNOWN"
        symbol = _norm(rec.get("symbol")).upper() or "UNKNOWN"
        sector = _sector_primary(rec)
        hold_bucket = _hold_bucket(rec)
        score_band = _exit_score_band(rec)
        time_of_day = _time_of_day(ts)
        rows.append({
            "cycle_id": cycle_id,
            "trade_id": trade_id,
            "pnl_usd": round(pnl_usd, 4),
            "window_pnl": round(window_pnl, 4),
            "promoted_angle": promoted_angle,
            "exit_reason": exit_reason,
            "entry_regime": entry_regime,
            "exit_regime": exit_regime,
            "regime_transition": "same" if entry_regime == exit_regime else "shift",
            "symbol": symbol,
            "sector": sector,
            "hold_bucket": hold_bucket,
            "exit_score_band": score_band,
            "time_of_day": time_of_day,
            "timestamp": ts[:19] if ts else "",
        })
    return rows


def write_aggregate_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


# ---------- Step 2: Factor stability ----------
FACTOR_COLS = ["exit_reason", "hold_bucket", "entry_regime", "exit_regime", "symbol", "sector", "time_of_day", "exit_score_band"]


def factor_stability(rows: list[dict]) -> dict:
    """Per (dimension, value): freq, mean_pnl, median_pnl, var, win_rate, total_pnl, trade_count."""
    by_factor: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        for col in FACTOR_COLS:
            val = r.get(col) or "unknown"
            by_factor[(col, val)].append(r["pnl_usd"])
    stats = {}
    for (dim, val), pnls in by_factor.items():
        n = len(pnls)
        total = sum(pnls)
        wins = sum(1 for p in pnls if p > 0)
        sorted_p = sorted(pnls)
        median = sorted_p[n // 2] if n else 0
        mean = total / n if n else 0
        variance = (sum((p - mean) ** 2 for p in pnls) / n) if n else 0
        stats[(dim, val)] = {
            "dimension": dim,
            "value": val,
            "trade_count": n,
            "total_pnl": round(total, 4),
            "mean_pnl": round(mean, 4),
            "median_pnl": round(median, 4),
            "variance": round(variance, 4),
            "win_rate": round(wins / n, 4) if n else 0,
        }
    return stats


# ---------- Step 3: Regime-conditioned ----------
def regime_conditioned_slices(rows: list[dict]) -> dict:
    """Factor stats conditioned on exit_regime, time_of_day."""
    slices = {}
    for regime in set(r.get("exit_regime") or "UNKNOWN" for r in rows):
        sub = [r for r in rows if (r.get("exit_regime") or "UNKNOWN") == regime]
        if sub:
            slices[f"exit_regime={regime}"] = factor_stability(sub)
    for tod in set(r.get("time_of_day") or "unknown" for r in rows):
        sub = [r for r in rows if (r.get("time_of_day") or "unknown") == tod]
        if sub:
            slices[f"time_of_day={tod}"] = factor_stability(sub)
    return slices


# ---------- Step 4: Exit-reason decomposition ----------
def parse_exit_reason(s: str) -> dict:
    """Extract signal_decay threshold, stale_alpha_cutoff window/%, flow_reversal."""
    out = {"raw": s, "signal_decay": None, "stale_alpha": None, "flow_reversal": False}
    if "flow_reversal" in (s or "").lower():
        out["flow_reversal"] = True
    m = re.search(r"signal_decay\(([\d.]+)\)", s or "")
    if m:
        out["signal_decay"] = float(m.group(1))
    m = re.search(r"stale_alpha_cutoff\((\d+)min,([-\d.]+)%\)", s or "")
    if m:
        out["stale_alpha"] = (int(m.group(1)), float(m.group(2)))
    return out


def exit_reason_decomposition(rows: list[dict]) -> dict:
    by_reason: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        er = r.get("exit_reason") or "unknown"
        by_reason[er].append(r["pnl_usd"])
    decomposition = {}
    for reason, pnls in by_reason.items():
        parsed = parse_exit_reason(reason)
        decomposition[reason] = {
            **parsed,
            "trade_count": len(pnls),
            "total_pnl": round(sum(pnls), 4),
            "mean_pnl": round(sum(pnls) / len(pnls), 4) if pnls else 0,
        }
    return decomposition


# ---------- Step 5: Promotion readiness ----------
def promotion_readiness_scores(
    factor_stats: dict,
    baseline_mean_pnl: float,
    min_trades: int = 10,
) -> list[dict]:
    """Score each factor; classify PROMOTABLE / PAPER-ONLY / RESEARCH-ONLY / DISCARD."""
    scored = []
    for (dim, val), s in factor_stats.items():
        n = s["trade_count"]
        mean_pnl = s["mean_pnl"]
        var = s["variance"]
        win_rate = s["win_rate"]
        improvement = mean_pnl - baseline_mean_pnl if baseline_mean_pnl is not None else mean_pnl
        stability = 1.0 / (1.0 + var) if var >= 0 else 0
        interpretability = 1.0 if dim in ("exit_reason", "hold_bucket", "symbol", "time_of_day") else 0.7
        if n < min_trades:
            verdict = "DISCARD"
        elif n < 20 and (improvement > 0 or win_rate > 0.55):
            verdict = "RESEARCH-ONLY"
        elif improvement > 0 and stability > 0.2 and win_rate >= 0.5:
            verdict = "PAPER-ONLY CANDIDATE"
        elif improvement > 0.1 and n >= 30 and win_rate >= 0.52:
            verdict = "PROMOTABLE"
        else:
            verdict = "DISCARD"
        scored.append({
            "dimension": dim,
            "value": val,
            "trade_count": n,
            "mean_pnl": mean_pnl,
            "improvement_vs_baseline": round(improvement, 4),
            "win_rate": win_rate,
            "stability_score": round(stability, 4),
            "verdict": verdict,
        })
    return sorted(scored, key=lambda x: (-(x["mean_pnl"]), -x["trade_count"]))


# ---------- Step 6: Board packet ----------
def write_board_packet(
    out_path: Path,
    ledger: list,
    rows: list[dict],
    factor_stats: dict,
    slices: dict,
    exit_decomp: dict,
    scored: list[dict],
    ts: str,
) -> None:
    total_trades = len(rows)
    n_cycles = len(ledger)
    total_pnl = sum(r["pnl_usd"] for r in rows)
    baseline_mean = total_pnl / total_trades if total_trades else 0
    promotable = [x for x in scored if x["verdict"] == "PROMOTABLE"]
    paper_only = [x for x in scored if x["verdict"] == "PAPER-ONLY CANDIDATE"]
    research = [x for x in scored if x["verdict"] == "RESEARCH-ONLY"]
    lines = [
        "# Alpaca Fast-Lane 25-Trade Deep Review — Board Packet",
        "",
        f"**Generated:** {ts}",
        f"**Cycles:** {n_cycles} | **Total trades:** {total_trades} | **Cumulative PnL:** ${total_pnl:.2f}",
        "",
        "---",
        "## Executive summary",
        "",
        f"This packet aggregates all {n_cycles} completed 25-trade cycles. "
        f"Total trades analyzed: {total_trades}; cumulative PnL: ${total_pnl:.2f}. "
        f"Baseline mean PnL per trade: ${baseline_mean:.4f}.",
        "",
        "---",
        "## What is working",
        "",
    ]
    if promotable:
        lines.append("- **Promotion-grade factors:** " + "; ".join(f"{x['dimension']}={x['value']} (mean PnL ${x['mean_pnl']:.2f}, n={x['trade_count']})" for x in promotable[:5]))
    else:
        lines.append("- No factor met PROMOTABLE bar (stability + improvement + sample size).")
    if paper_only:
        lines.append("- **Paper-only candidates:** " + "; ".join(f"{x['dimension']}={x['value']}" for x in paper_only[:5]))
    lines.extend(["", "---", "## What is noise", ""])
    discard_high_n = [x for x in scored if x["verdict"] == "DISCARD" and x["trade_count"] >= 20]
    if discard_high_n:
        lines.append("- High-sample factors with no edge (DISCARD): " + ", ".join(f"{x['value']}" for x in discard_high_n[:8]))
    lines.extend(["", "---", "## What is dangerous", ""])
    lines.append("- No automatic promotion is applied; all recommendations are advisory. Overfitting risk: factors with low trade count or high variance are RESEARCH-ONLY or DISCARD.")
    lines.extend(["", "---", "## Promotion verdict", ""])
    if promotable:
        lines.append("**PROMOTABLE:** " + ", ".join(f"{x['dimension']}:{x['value']}" for x in promotable))
    else:
        lines.append("**NO PROMOTION.** No factor cleared the stability, improvement, and sample-size bar for live promotion. Paper-only and research-only candidates may be trialled in shadow.")
    lines.extend(["", "---", "## Factor stability (top 15 by |mean PnL|)", ""])
    top = sorted(factor_stats.items(), key=lambda kv: -abs(kv[1]["mean_pnl"]))[:15]
    for (dim, val), s in top:
        lines.append(f"- **{dim}:{val}** — trades={s['trade_count']}, mean_pnl=${s['mean_pnl']:.2f}, win_rate={s['win_rate']:.2f}")
    lines.extend(["", "---", "## Exit-reason decomposition (sample)", ""])
    for reason, d in sorted(exit_decomp.items(), key=lambda x: -abs(x[1]["total_pnl"]))[:12]:
        lines.append(f"- {reason}: n={d['trade_count']}, total_pnl=${d['total_pnl']:.2f}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------- Step 7: Telegram ----------
def send_telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID", file=sys.stderr)
        return False
    try:
        import requests
    except ImportError:
        print("pip install requests for Telegram", file=sys.stderr)
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": text},
        timeout=30,
    )
    return r.ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca Fast-Lane multi-cycle deep review")
    ap.add_argument("--state-dir", type=Path, default=STATE_DIR, help="Fast-lane state dir")
    ap.add_argument("--exit-log", type=Path, default=EXIT_ATTRIBUTION, help="exit_attribution.jsonl path")
    ap.add_argument("--report-dir", type=Path, default=REPORTS_DIR, help="Reports output dir")
    ap.add_argument("--no-telegram", action="store_true", help="Skip Telegram notification")
    args = ap.parse_args()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    ledger_path = args.state_dir / "fast_lane_ledger.json"
    cycles_dir = args.state_dir / "cycles"
    ledger = load_ledger(ledger_path)
    if not ledger:
        print("No ledger entries; run fast-lane cycles first.", file=sys.stderr)
        return 1
    epoch = get_epoch_from_config(args.state_dir)
    post_epoch = load_post_epoch_trades(args.exit_log, epoch)
    rows = build_aggregate_rows(ledger, post_epoch)
    if not rows:
        print("No aggregate rows (ledger cycles vs post-epoch trade count mismatch?).", file=sys.stderr)
        return 1
    csv_path = args.report_dir / f"alpaca_fastlane_25_cycle_aggregate_{ts}.csv"
    write_aggregate_csv(rows, csv_path)
    print(f"Step 1: Wrote {csv_path} ({len(rows)} rows)")
    factor_stats = factor_stability(rows)
    print("Step 2: Factor stability done")
    slices = regime_conditioned_slices(rows)
    print("Step 3: Regime-conditioned slices done")
    exit_decomp = exit_reason_decomposition(rows)
    print("Step 4: Exit-reason decomposition done")
    total_pnl = sum(r["pnl_usd"] for r in rows)
    baseline_mean = total_pnl / len(rows) if rows else 0
    scored = promotion_readiness_scores(factor_stats, baseline_mean)
    print("Step 5: Promotion readiness done")
    packet_path = args.report_dir / f"ALPACA_FASTLANE_25_BOARD_REVIEW_{ts}.md"
    write_board_packet(packet_path, ledger, rows, factor_stats, slices, exit_decomp, scored, ts)
    print(f"Step 6: Wrote {packet_path}")
    if not args.no_telegram:
        msg = (
            "Alpaca Fast-Lane 25-trade deep review complete.\n"
            f"Board packet ready:\nALPACA_FASTLANE_25_BOARD_REVIEW_{ts}.md"
        )
        if send_telegram(msg):
            print("Step 7: Telegram sent")
        else:
            print("Step 7: Telegram send failed (check env)", file=sys.stderr)
    else:
        print("Step 7: Skipped (--no-telegram)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
