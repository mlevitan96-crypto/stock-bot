#!/usr/bin/env python3
"""
ALPACA LOSS FORENSICS — run on droplet only (reads canonical logs).
READ-ONLY. Writes reports under reports/audit/.
Exit non-zero on Truth Gate HARD FAILURE (join coverage, missing streams).
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import subprocess
import sys
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

AUDIT = REPO / "reports" / "audit"
LOGS = REPO / "logs"
STATE = REPO / "state"

EXIT_PATH = LOGS / "exit_attribution.jsonl"
UNIFIED_PATH = LOGS / "alpaca_unified_events.jsonl"
ENTRY_ATTR_PATH = LOGS / "alpaca_entry_attribution.jsonl"
ATTRIBUTION_PATH = LOGS / "attribution.jsonl"
BLOCKED_PATH = STATE / "blocked_trades.jsonl"
MASTER_PATH = LOGS / "master_trade_log.jsonl"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _parse_ts(s: Any) -> Optional[datetime]:
    if not s:
        return None
    try:
        s = str(s).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _side_norm(rec: dict) -> str:
    s = (rec.get("side") or rec.get("direction") or "long").strip().lower()
    if s in ("sell", "short"):
        return "short"
    return "long"


def _pnl(rec: dict) -> float:
    try:
        return float(rec.get("realized_pnl_usd") or rec.get("pnl") or rec.get("pnl_usd") or 0)
    except (TypeError, ValueError):
        return 0.0


def _exit_ts_str(rec: dict) -> str:
    return str(rec.get("timestamp") or rec.get("exit_timestamp") or rec.get("ts") or "")


def load_exits_last_n(path: Path, max_trades: int) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            if not _exit_ts_str(rec):
                continue
            rows.append(rec)
    return rows[-max_trades:] if len(rows) > max_trades else rows


def load_exits_since_epoch(path: Path, epoch_path: Path, max_trades: int) -> List[Dict[str, Any]]:
    if not path.exists() or not epoch_path.exists():
        return []
    try:
        ep = json.loads(epoch_path.read_text(encoding="utf-8"))
        t0s = str(ep.get("repair_iso_utc") or ep.get("iso_utc") or "")
        t0 = _parse_ts(t0s)
    except Exception:
        return []
    if not t0:
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            ets = _parse_ts(_exit_ts_str(rec))
            if not ets or ets < t0:
                continue
            rows.append(rec)
    return rows[-max_trades:] if len(rows) > max_trades else rows


def build_trade_key_for_exit(rec: dict) -> str:
    from src.telemetry.alpaca_trade_key import build_trade_key
    sym = (rec.get("symbol") or "?").strip().upper()
    side = _side_norm(rec)
    et = rec.get("entry_timestamp") or rec.get("entry_ts") or rec.get("entry_time_iso") or ""
    return build_trade_key(sym, side, str(et))


def index_entry_streams(needed_keys: set) -> Tuple[Dict[str, dict], Dict[str, str]]:
    """
    Map trade_key -> entry record. Also trade_id -> trade_key for attribution open_*.
    Returns (by_trade_key, join_source per key: unified|entry_attr|attribution)
    """
    by_tk: Dict[str, dict] = {}
    source: Dict[str, str] = {}

    def absorb(rec: dict, src: str) -> None:
        tk = rec.get("trade_key") or ""
        if not tk and rec.get("symbol"):
            from src.telemetry.alpaca_trade_key import build_trade_key
            tk = build_trade_key(
                rec.get("symbol", ""),
                rec.get("side") or "long",
                rec.get("entry_time_iso") or rec.get("entry_timestamp") or rec.get("timestamp") or "",
            )
        if tk in needed_keys and tk not in by_tk:
            by_tk[tk] = rec
            source[tk] = src

    for p in (ENTRY_ATTR_PATH,):
        if not p.exists():
            continue
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(rec, dict):
                    continue
                absorb(rec, "alpaca_entry_attribution")

    # attribution.jsonl: entry rows use open_* trade_id; exits often use live: — join by trade_key only
    if ATTRIBUTION_PATH.exists():
        from src.telemetry.alpaca_trade_key import build_trade_key as btk
        with open(ATTRIBUTION_PATH, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(rec, dict):
                    continue
                ctx = rec.get("context") or {}
                sym_a = (rec.get("symbol") or ctx.get("symbol") or "").strip().upper()
                if not sym_a:
                    continue
                side_raw = ctx.get("side") or rec.get("side") or "long"
                et_a = ctx.get("entry_ts") or ctx.get("entry_timestamp") or rec.get("entry_timestamp") or ""
                if not et_a:
                    continue
                tk = btk(sym_a, side_raw, str(et_a))
                if tk in needed_keys and tk not in by_tk:
                    by_tk[tk] = {
                        "trade_key": tk,
                        "composite_score": ctx.get("entry_score"),
                        "regime_label": ctx.get("regime"),
                        "attribution_components": ctx.get("attribution_components"),
                    }
                    source[tk] = "attribution.jsonl"

    return by_tk, source


def merge_master_trade_log(needed_keys: set, by_tk: Dict[str, dict], source: Dict[str, str]) -> None:
    if not MASTER_PATH.exists():
        return
    from src.telemetry.alpaca_trade_key import build_trade_key as btk
    missing = needed_keys - set(by_tk.keys())
    if not missing:
        return
    try:
        lines = MASTER_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for line in lines[-25000:]:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        ev = (rec.get("lifecycle_event") or rec.get("event") or "").upper()
        if "ENTRY" not in ev and ev not in ("ENTRY_FILL", "ENTRY_DECISION"):
            continue
        sym = (rec.get("symbol") or "").strip().upper()
        if not sym:
            continue
        side = rec.get("side") or "long"
        ts = rec.get("timestamp_utc") or rec.get("timestamp") or rec.get("ts") or ""
        tk = btk(sym, side, str(ts))
        if tk in missing:
            by_tk[tk] = {
                "trade_key": tk,
                "composite_score": rec.get("composite_score_v2"),
                "regime_label": rec.get("regime_label"),
                "attribution_components": rec.get("components"),
            }
            source[tk] = "master_trade_log.jsonl"
            missing.discard(tk)
            if not missing:
                break


def merge_unified_for_missing(
    needed_keys: set, by_tk: Dict[str, dict], source: Dict[str, str]
) -> None:
    if not UNIFIED_PATH.exists():
        return
    missing = needed_keys - set(by_tk.keys())
    if not missing:
        return
    with open(UNIFIED_PATH, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not missing:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            if (rec.get("event_type") or "") != "alpaca_entry_attribution":
                continue
            tk = rec.get("trade_key") or ""
            if not tk and rec.get("symbol"):
                from src.telemetry.alpaca_trade_key import build_trade_key
                tk = build_trade_key(
                    rec.get("symbol", ""),
                    rec.get("side") or "long",
                    rec.get("entry_time_iso") or rec.get("entry_timestamp") or "",
                )
            if tk in missing:
                by_tk[tk] = rec
                source[tk] = "alpaca_unified_events"
                missing.discard(tk)


def run_shell(cmd: str, timeout: int = 60) -> Tuple[str, str, int]:
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO),
        )
        return p.stdout or "", p.stderr or "", p.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 124
    except Exception as e:
        return "", str(e), 1


def phase1_inventory() -> str:
    parts = []
    cmds = [
        ("## systemd (running)", "systemctl list-units --type=service --state=running 2>/dev/null | head -50"),
        ("## cron", "(crontab -l 2>/dev/null || echo '(no crontab)') | head -40"),
        ("## python processes", "ps aux 2>/dev/null | grep -E '[p]ython' | head -25"),
        ("## disk", "df -h 2>/dev/null | head -15"),
        ("## memory", "free -m 2>/dev/null || true"),
        ("## git HEAD", "git rev-parse HEAD 2>/dev/null; git log -1 --oneline 2>/dev/null"),
        ("## log line counts", "wc -l logs/exit_attribution.jsonl logs/alpaca_unified_events.jsonl logs/alpaca_entry_attribution.jsonl logs/attribution.jsonl state/blocked_trades.jsonl 2>/dev/null || true"),
        ("## log file sizes", "ls -la logs/exit_attribution.jsonl logs/alpaca_unified_events.jsonl 2>/dev/null || true"),
    ]
    for title, c in cmds:
        o, e, rc = run_shell(c, timeout=45)
        parts.append(f"{title}\n```\n{(o or e or '(empty)')[:8000]}\n```\n")
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-trades", type=int, default=2000)
    ap.add_argument("--min-join-pct", type=float, default=80.0, help="Truth Gate: min %% exits with entry join")
    ap.add_argument("--post-epoch-only", action="store_true")
    ap.add_argument("--epoch-json", default=str(REPO / "state" / "alpaca_telemetry_repair_epoch.json"))
    args = ap.parse_args()
    post = bool(args.post_epoch_only)
    epoch_p = Path(args.epoch_json)

    def audit_out(sfx: str) -> Path:
        if post:
            if sfx == "CSA_REVIEW":
                return AUDIT / "CSA_REVIEW_ALPACA_LOSS_FORENSICS_POST_EPOCH.md"
            if sfx == "SRE_REVIEW":
                return AUDIT / "SRE_REVIEW_ALPACA_LOSS_FORENSICS_POST_EPOCH.md"
            return AUDIT / f"ALPACA_LOSS_FORENSICS_POST_EPOCH_{sfx}.md"
        if sfx == "CSA_REVIEW":
            return AUDIT / "CSA_REVIEW_ALPACA_LOSS_FORENSICS.md"
        if sfx == "SRE_REVIEW":
            return AUDIT / "SRE_REVIEW_ALPACA_LOSS_FORENSICS.md"
        return AUDIT / f"ALPACA_LOSS_FORENSICS_{sfx}.md"

    AUDIT.mkdir(parents=True, exist_ok=True)
    ts = _ts()
    hard_fail = False
    fail_msgs: List[str] = []

    if not post:
        inv = phase1_inventory()
    proc_path = AUDIT / "ALPACA_LOSS_FORENSICS_PROCESS_INVENTORY.md"
    if not post:
        with open(proc_path, "w", encoding="utf-8") as f:
            f.write(f"# Alpaca Loss Forensics — Process Inventory (SRE)\n\n**Droplet run:** `{ts}` UTC\n\n")
            f.write(inv)
        sre_health = AUDIT / "SRE_REVIEW_ALPACA_RUNTIME_HEALTH.md"
        with open(sre_health, "w", encoding="utf-8") as f:
            f.write("# SRE Review — Alpaca Runtime Health (Loss Forensics)\n\n")
            f.write("**Scope:** Inventory snapshot at forensic run; not a substitute for 24/7 SRE monitoring.\n\n")
            f.write("## Findings\n\n")
            f.write("- **Services/processes:** See process inventory.\n")
            f.write("- **Git commit:** Verify `git HEAD` matches expected deploy.\n")
            f.write("- **Logs:** Line counts should grow monotonically for protected paths (no silent truncation).\n")
            f.write("- **Disk/memory:** Pressure can drop events if OOM/kill; correlate with gaps in exit stream.\n\n")
            f.write("## Verdict placeholder\n\nCompleted after dataset gate — see `SRE_REVIEW_ALPACA_LOSS_FORENSICS.md`.\n")

    if not EXIT_PATH.exists():
        blocker = (audit_out(f"JOIN_BLOCKER_{ts}") if post else AUDIT / f"ALPACA_LOSS_FORENSICS_JOIN_BLOCKER_{ts}.md")
        with open(blocker, "w", encoding="utf-8") as bf:
            bf.write("# HARD FAILURE — Missing exit_attribution\n\n`logs/exit_attribution.jsonl` missing.\n")
        with open(audit_out("JOIN_COVERAGE"), "w", encoding="utf-8") as f:
            f.write("# Join Coverage — BLOCKER\n\nMissing exit_attribution.jsonl\n")
        return 2

    exits = load_exits_since_epoch(EXIT_PATH, epoch_p, args.max_trades) if post else load_exits_last_n(EXIT_PATH, args.max_trades)
    n = len(exits)
    if n == 0:
        blocker = (audit_out(f"JOIN_BLOCKER_{ts}") if post else AUDIT / f"ALPACA_LOSS_FORENSICS_JOIN_BLOCKER_{ts}.md")
        with open(blocker, "w", encoding="utf-8") as bf:
            bf.write("# HARD FAILURE — No closed exits in window\n\n")
        hard_fail = True
        fail_msgs.append("Zero exits in freeze window")

    needed_keys = set()
    enriched: List[Dict[str, Any]] = []
    for rec in exits:
        tk = build_trade_key_for_exit(rec)
        needed_keys.add(tk)
        enriched.append({"exit": rec, "trade_key": tk})

    by_entry, join_src = index_entry_streams(needed_keys)
    merge_master_trade_log(needed_keys, by_entry, join_src)
    merge_unified_for_missing(needed_keys, by_entry, join_src)
    joined_log = sum(1 for e in enriched if e["trade_key"] in by_entry)

    def has_entry_path_intel(e: Dict[str, Any]) -> bool:
        if e["trade_key"] in by_entry:
            return True
        ex = e["exit"]
        eu = ex.get("entry_uw")
        if isinstance(eu, dict) and eu and str(ex.get("entry_regime") or "").strip():
            return True
        return False

    joined = sum(1 for e in enriched if has_entry_path_intel(e))
    join_pct = (100.0 * joined / n) if n else 0.0
    join_log_pct = (100.0 * joined_log / n) if n else 0.0

    unified_ok = UNIFIED_PATH.exists() and UNIFIED_PATH.stat().st_size > 0
    entry_attr_ok = ENTRY_ATTR_PATH.exists() and ENTRY_ATTR_PATH.stat().st_size > 0

    join_md = audit_out("JOIN_COVERAGE")
    embedded_only = sum(
        1
        for e in enriched
        if e["trade_key"] not in by_entry
        and isinstance(e["exit"].get("entry_uw"), dict)
        and e["exit"]["entry_uw"]
        and str(e["exit"].get("entry_regime") or "").strip()
    )
    with open(join_md, "w", encoding="utf-8") as f:
        f.write("# Alpaca Loss Forensics — Join Coverage" + (" (**POST-EPOCH**)\n\n" if post else "\n\n"))
        f.write(
            ("**Gate (post-epoch):** strict log join (`alpaca_entry_attribution` / unified) ≥95%%.\n\n" if post else "")
            + "**Gate metric (forensics):** log join OR exit row carries `entry_uw` + `entry_regime` "
            "(canonical exit_attribution embeds entry context).\n\n"
        )
        f.write(f"- **Frozen exits:** {n}\n")
        f.write(f"- **With entry path intel (gate):** {joined} ({join_pct:.1f}%)\n")
        f.write(f"- **Strict log-only join (attribution/unified/entry_attr):** {joined_log} ({join_log_pct:.1f}%)\n")
        f.write(f"- **Embedded-only (no log line, entry_uw+regime on exit):** {embedded_only}\n")
        f.write(f"- **Threshold:** {(95.0 if post else args.min_join_pct)}% ({'post-epoch log join' if post else 'mission'})\n")
        f.write(f"- **alpaca_unified_events.jsonl:** {'present' if unified_ok else 'missing/empty'}\n")
        f.write(f"- **alpaca_entry_attribution.jsonl:** {'present' if entry_attr_ok else 'missing/empty'}\n")
        f.write("\n## Join sources (log lines; excludes embedded-only)\n\n")
        for e in enriched:
            if e["trade_key"] in by_entry:
                pass
        src_counts = Counter(join_src.get(e["trade_key"], "none") for e in enriched if e["trade_key"] in by_entry)
        src_counts["no_log_join_exit_embedded"] = n - joined_log
        for k, v in src_counts.most_common():
            f.write(f"- {k}: {v}\n")

    join_need = 95.0 if post else args.min_join_pct
    join_have = join_log_pct if post else join_pct
    if n and join_have < join_need:
        hard_fail = True
        fail_msgs.append(f"Join {'log' if post else 'path'} {join_have:.1f}% < {join_need}%")
        bl = (
            f"# HARD FAILURE — Join coverage below Truth Gate\n\n"
            f"**Classification:** ENTRY_PATH_JOIN_INSUFFICIENT\n\n"
            f"- **Frozen exits:** {n}\n"
            f"- **Entry path intel (gate):** {joined} ({join_pct:.2f}%)\n"
            f"- **Strict log join:** {joined_log} ({join_log_pct:.2f}%)\n"
            f"- **Required:** >= {join_need}%\n\n"
            f"## Root cause (typical)\n\n"
            f"- `alpaca_unified_events.jsonl` / `alpaca_entry_attribution.jsonl` missing or empty on droplet.\n"
            f"- `attribution.jsonl` line count << exit window → historical exits never had entry rows.\n"
            f"- Many exits rely on embedded `entry_uw` only; ~{(100-join_pct):.1f}% lack both log join and rich embed.\n\n"
            f"## Required ops (data — not tuning)\n\n"
            f"1. Ensure entry emitters write unified/entry_attr for all new trades.\n"
            f"2. Do not truncate `logs/attribution.jsonl` / `logs/master_trade_log.jsonl`.\n"
            f"3. Re-run forensics after 7+ sessions of unified events.\n\n"
            f"**Phases 3–6 exit aggregates remain valid; entry-attribution causality is NOT decision-grade.**\n"
        )
        bp = (audit_out(f"JOIN_BLOCKER_{ts}") if post else AUDIT / f"ALPACA_LOSS_FORENSICS_JOIN_BLOCKER_{ts}.md")
        with open(bp, "w", encoding="utf-8") as bf:
            bf.write(bl)
        latest_blk = (
            AUDIT / "ALPACA_LOSS_FORENSICS_POST_EPOCH_JOIN_BLOCKER_LATEST.md"
            if post
            else AUDIT / "ALPACA_LOSS_FORENSICS_JOIN_BLOCKER_LATEST.md"
        )
        with open(latest_blk, "w", encoding="utf-8") as bf:
            bf.write(bl)

    # trade_id integrity
    blank_tid = sum(1 for e in enriched if not str(e["exit"].get("trade_id") or "").strip())
    dup_tk = len(enriched) - len({e["trade_key"] for e in enriched})

    freeze_md = audit_out("DATASET_FREEZE")
    with open(freeze_md, "w", encoding="utf-8") as f:
        f.write("# Alpaca Loss Forensics — Dataset Freeze\n\n")
        f.write(f"| Field | Value |\n|---|---|\n")
        f.write(f"| Max trades cap | {args.max_trades} |\n")
        f.write(f"| Actual exits | {n} |\n")
        f.write(f"| Join coverage | {join_pct:.2f}% |\n")
        f.write(f"| Exits missing trade_id | {blank_tid} |\n")
        f.write(f"| Duplicate trade_key in window | {dup_tk} |\n")
        f.write("\n## Partitions\n\n- By exit day (UTC date from exit timestamp)\n")
        f.write("- By symbol\n")
        f.write("- By side (long/short)\n")
        if hard_fail:
            f.write("\n**STATUS: HARD FAILURE** — see join blocker.\n")

    # Aggregate metrics (Phase 3) — always useful even on hard fail for diagnostics
    total_pnl = sum(_pnl(e["exit"]) for e in enriched)
    wins = [e for e in enriched if _pnl(e["exit"]) > 0]
    losses = [e for e in enriched if _pnl(e["exit"]) < 0]
    flats = [e for e in enriched if _pnl(e["exit"]) == 0]
    total_minutes = 0.0
    for e in enriched:
        try:
            total_minutes += float(e["exit"].get("time_in_trade_minutes") or 0)
        except (TypeError, ValueError):
            pass
    hours = total_minutes / 60.0 if total_minutes else 0
    avg_win = sum(_pnl(e["exit"]) for e in wins) / len(wins) if wins else 0
    avg_loss = sum(_pnl(e["exit"]) for e in losses) / len(losses) if losses else 0
    payoff = (avg_win / abs(avg_loss)) if avg_loss else None

    sorted_pnl = sorted(enriched, key=lambda x: _pnl(x["exit"]))
    worst10 = sorted_pnl[:10]

    by_sym = defaultdict(float)
    by_regime = defaultdict(float)
    by_hour = defaultdict(float)
    for e in enriched:
        ex = e["exit"]
        sym = (ex.get("symbol") or "?").upper()
        by_sym[sym] += _pnl(ex)
        by_regime[(ex.get("entry_regime") or "unknown").strip() or "unknown"] += _pnl(ex)
        dt = _parse_ts(_exit_ts_str(ex))
        by_hour[dt.hour if dt else -1] += _pnl(ex)

    # drawdown on cumulative pnl series (chronological)
    chron = sorted(enriched, key=lambda x: _parse_ts(_exit_ts_str(x["exit"])) or datetime.min.replace(tzinfo=timezone.utc))
    peak = 0.0
    cum = 0.0
    max_dd = 0.0
    for e in chron:
        cum += _pnl(e["exit"])
        peak = max(peak, cum)
        max_dd = min(max_dd, cum - peak)

    agg_path = audit_out("AGGREGATE_METRICS")
    with open(agg_path, "w", encoding="utf-8") as f:
        f.write("# Alpaca Loss Forensics — Aggregate Metrics\n\n")
        f.write(f"- **n trades:** {n}\n")
        f.write(f"- **total PnL USD:** {total_pnl:.4f}\n")
        f.write(f"- **PnL/trade:** {(total_pnl/n) if n else 0:.6f}\n")
        f.write(f"- **PnL/hour in-trade (approx):** {(total_pnl/hours) if hours else 0:.6f}\n")
        f.write(f"- **win rate:** {100*len(wins)/n if n else 0:.2f}%\n")
        f.write(f"- **avg win:** {avg_win:.4f}  **avg loss:** {avg_loss:.4f}\n")
        f.write(f"- **payoff (avg_win/|avg_loss|):** {payoff if payoff is not None else 'n/a'}\n")
        f.write(f"- **max drawdown (cum PnL):** {max_dd:.4f}\n")
        f.write("\n## Worst 10 trades (PnL)\n\n")
        for e in worst10:
            ex = e["exit"]
            f.write(f"- {ex.get('symbol')} {_pnl(ex):.4f} | {ex.get('exit_reason')} | {e['trade_key'][:60]}...\n")
        f.write("\n## Top losing symbols\n\n")
        for sym, p in sorted(by_sym.items(), key=lambda x: x[1])[:15]:
            f.write(f"- {sym}: {p:.4f}\n")
        f.write("\n## Top losing entry_regime\n\n")
        for r, p in sorted(by_regime.items(), key=lambda x: x[1])[:12]:
            f.write(f"- {r}: {p:.4f}\n")
        f.write("\n## PnL by exit hour (UTC)\n\n")
        for h in sorted(by_hour.keys()):
            if h < 0:
                continue
            f.write(f"- hour {h}: {by_hour[h]:.4f}\n")

    # Day by day
    by_day: Dict[str, List] = defaultdict(list)
    for e in enriched:
        dt = _parse_ts(_exit_ts_str(e["exit"]))
        day = dt.strftime("%Y-%m-%d") if dt else "unknown"
        by_day[day].append(e)

    days_sorted = sorted(by_day.keys())
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pnl_by_day = {d: sum(_pnl(x["exit"]) for x in by_day[d]) for d in by_day}
    baseline_days = [pnl_by_day[d] for d in days_sorted if d != today_utc and d != "unknown"]
    med = statistics.median(baseline_days) if baseline_days else 0
    today_pnl = pnl_by_day.get(today_utc)

    day_path = audit_out("DAY_BY_DAY")
    with open(day_path, "w", encoding="utf-8") as f:
        f.write("# Alpaca Loss Forensics — Day by Day\n\n")
        f.write(f"- **Today UTC:** {today_utc}  PnL: {today_pnl if today_pnl is not None else 'no trades'}\n")
        f.write(f"- **Median daily PnL (ex-today):** {med:.4f}\n\n")
        f.write("| day | n | PnL | long PnL | short PnL |\n|---|---:|---:|---:|---:|\n")
        for d in days_sorted:
            xs = by_day[d]
            lp = sum(_pnl(x["exit"]) for x in xs if _side_norm(x["exit"]) == "long")
            sp = sum(_pnl(x["exit"]) for x in xs if _side_norm(x["exit"]) == "short")
            f.write(f"| {d} | {len(xs)} | {sum(_pnl(x['exit']) for x in xs):.4f} | {lp:.4f} | {sp:.4f} |\n")
        f.write("\n## Entry vs exit attribution (proxy)\n\n")
        f.write("Loss *realized* at exit; entry quality vs exit timing split requires join — see long/short and entry/exit cause docs.\n")

    # Phase 4 long/short
    long_pn = sum(_pnl(e["exit"]) for e in enriched if _side_norm(e["exit"]) == "long")
    short_pn = sum(_pnl(e["exit"]) for e in enriched if _side_norm(e["exit"]) == "short")
    nl = max(1, sum(1 for e in enriched if _side_norm(e["exit"]) == "long"))
    ns = max(1, sum(1 for e in enriched if _side_norm(e["exit"]) == "short"))

    by_side_exit = defaultdict(Counter)
    mae_mfe_long = {"mae": [], "mfe": []}
    mae_mfe_short = {"mae": [], "mfe": []}
    for e in enriched:
        ex = e["exit"]
        side = _side_norm(ex)
        eq = ex.get("exit_quality_metrics") or {}
        try:
            mae = float(eq.get("mae_pct") or 0)
            mfe = float(eq.get("mfe_pct") or 0)
        except (TypeError, ValueError):
            mae = mfe = 0
        (mae_mfe_long if side == "long" else mae_mfe_short)["mae"].append(mae)
        (mae_mfe_long if side == "long" else mae_mfe_short)["mfe"].append(mfe)
        by_side_exit[side][ex.get("exit_reason") or "unknown"] += 1

    down_days = [d for d in days_sorted if d != "unknown" and pnl_by_day.get(d, 0) < 0]
    long_on_down = sum(
        sum(1 for x in by_day[d] if _side_norm(x["exit"]) == "long")
        for d in down_days
    )
    short_on_down = sum(
        sum(1 for x in by_day[d] if _side_norm(x["exit"]) == "short")
        for d in down_days
    )

    ls_path = audit_out("LONG_SHORT")
    with open(ls_path, "w", encoding="utf-8") as f:
        f.write("# Alpaca Loss Forensics — Long vs Short\n\n")
        f.write(f"| Side | Trades | Total PnL |\n|---|---:|---:|\n")
        f.write(f"| LONG | {sum(1 for e in enriched if _side_norm(e['exit'])=='long')} | {long_pn:.4f} |\n")
        f.write(f"| SHORT | {sum(1 for e in enriched if _side_norm(e['exit'])=='short')} | {short_pn:.4f} |\n")
        f.write(f"\n**Net long skew on losing days:** On calendar days with negative daily PnL, long exits={long_on_down}, short exits={short_on_down}.\n\n")
        if long_pn < short_pn:
            f.write("**Asymmetry:** Short leg contributed *less negative* (or more positive) PnL than long in this window.\n\n")
        else:
            f.write("**Asymmetry:** Long leg PnL vs short — compare magnitudes above.\n\n")
        f.write("## MAE/MFE mean by side (%%)\n\n")
        for label, bucket in ("LONG", mae_mfe_long), ("SHORT", mae_mfe_short):
            maes = bucket["mae"]
            mfes = bucket["mfe"]
            f.write(f"- **{label}** MAE mean: {sum(maes)/len(maes) if maes else 0:.4f}  MFE mean: {sum(mfes)/len(mfes) if mfes else 0:.4f}\n")
        f.write("\n## Exit reason × side (counts)\n\n")
        for side in ("long", "short"):
            f.write(f"### {side.upper()}\n")
            for reason, cnt in by_side_exit[side].most_common(12):
                f.write(f"- {reason}: {cnt}\n")

    # Phase 5 — worst 200 losers entry causes
    losers = [e for e in enriched if _pnl(e["exit"]) < 0]
    losers.sort(key=lambda x: _pnl(x["exit"]))
    worst200 = losers[:200]
    # stratified sample: up to 5 random per day from losers
    by_d_losers: Dict[str, List] = defaultdict(list)
    for e in losers:
        dt = _parse_ts(_exit_ts_str(e["exit"]))
        by_d_losers[dt.strftime("%Y-%m-%d") if dt else "unk"].append(e)
    sample_extra: List = []
    rng = random.Random(42)
    for d, xs in by_d_losers.items():
        rng.shuffle(xs)
        sample_extra.extend(xs[:5])
    seen = set()
    combined = []
    for e in worst200 + sample_extra:
        k = e["trade_key"]
        if k not in seen:
            seen.add(k)
            combined.append(e)

    entry_path = audit_out("ENTRY_CAUSES")
    with open(entry_path, "w", encoding="utf-8") as f:
        f.write("# Alpaca Loss Forensics — Entry Path (losing trades)\n\n")
        f.write(f"Analyzed **{len(worst200)}** worst PnL trades + stratified daily sample (deduped **{len(combined)}**).\n\n")
        low_score = hi_vol = regime_mismatch = 0
        for e in combined[:80]:
            ex = e["exit"]
            ent = by_entry.get(e["trade_key"]) or {}
            comp = ent.get("composite_score")
            try:
                cs = float(comp) if comp is not None else None
            except (TypeError, ValueError):
                cs = None
            if cs is not None and cs < 3.0:
                low_score += 1
            reg_e = str(ent.get("regime_label") or "").upper()
            reg_x = str(ex.get("entry_regime") or "").upper()
            if reg_e and reg_x and reg_e != reg_x:
                regime_mismatch += 1
            f.write(f"### {_pnl(ex):.2f} {ex.get('symbol')} {e['trade_key'][:50]}...\n")
            f.write(f"- entry composite_score: {comp}  regime(entry log): {ent.get('regime_label')}  exit entry_regime: {ex.get('entry_regime')}\n")
            comps = ent.get("attribution_components")
            if isinstance(comps, list) and comps:
                top = sorted(
                    [c for c in comps if isinstance(c, dict)],
                    key=lambda c: abs(float(c.get("contribution_to_score") or 0)),
                    reverse=True,
                )[:5]
                f.write(f"- top entry contributions: {[(c.get('signal_id'), c.get('contribution_to_score')) for c in top]}\n")
            f.write("\n")
        f.write("\n## Pattern tallies (heuristic)\n\n")
        f.write(f"- Low composite (<3) among sampled with score: counted in sample scan\n")
        f.write(f"- Regime label mismatch (entry log vs exit entry_regime): ~{regime_mismatch} in first 80 detailed\n")

    # Phase 6 exit causes
    exit_c_path = audit_out("EXIT_CAUSES")
    with open(exit_c_path, "w", encoding="utf-8") as f:
        f.write("# Alpaca Loss Forensics — Exit Path (losing trades)\n\n")
        gave_back = 0
        for e in worst200[:100]:
            ex = e["exit"]
            eq = ex.get("exit_quality_metrics") or {}
            mfe = float(eq.get("mfe_pct") or 0)
            mae = float(eq.get("mae_pct") or 0)
            if mfe > 0.05 and _pnl(ex) < 0:
                gave_back += 1
            v2 = ex.get("v2_exit_components") or {}
            f.write(f"### {ex.get('symbol')} PnL {_pnl(ex):.4f}\n")
            f.write(f"- exit_reason: {ex.get('exit_reason')}  v2_exit_score: {ex.get('v2_exit_score')}\n")
            f.write(f"- MAE% {mae:.4f} MFE% {mfe:.4f} hold_min {ex.get('time_in_trade_minutes')}\n")
            if isinstance(v2, dict) and v2:
                topv = sorted(v2.items(), key=lambda x: abs(float(x[1]) if isinstance(x[1], (int, float)) else 0), reverse=True)[:6]
                f.write(f"- v2_exit_components top: {topv}\n")
            f.write("\n")
        f.write(f"\n## Gave back MFE (MFE>0.05%% but loss): ~{gave_back} in top 100 losers\n")

    # Phase 7 blocked
    blocked_n = 0
    blocked_by_day = Counter()
    blocked_reasons = Counter()
    if BLOCKED_PATH.exists():
        with open(BLOCKED_PATH, "r", encoding="utf-8", errors="replace") as bf:
            for line in bf:
                line = line.strip()
                if not line:
                    continue
                try:
                    b = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(b, dict):
                    blocked_n += 1
                    tsb = str(b.get("timestamp") or b.get("ts") or "")[:10]
                    blocked_by_day[tsb or "unknown"] += 1
                    blocked_reasons[str(b.get("reason") or b.get("block_reason") or "unknown")] += 1

    blk_path = audit_out("BLOCKED_COUNTERFACTUAL")
    with open(blk_path, "w", encoding="utf-8") as f:
        f.write("# Blocked + Counterfactual Forensics\n\n")
        f.write(f"- **blocked_trades.jsonl records (total file):** {blocked_n}\n")
        f.write("Would-have PnL for blocked trades requires shadow replay (not computed here — READ-ONLY).\n\n")
        f.write("## Top block reasons\n\n")
        for r, c in blocked_reasons.most_common(20):
            f.write(f"- {r}: {c}\n")

    # Phase 8 market context (omitted in post-epoch mission artifact set)
    if not post:
        mc_path = audit_out("MARKET_CONTEXT")
        with open(mc_path, "w", encoding="utf-8") as f:
            f.write("# Market Context (internal proxies only)\n\n")
            f.write("- **Down days (negative daily PnL):** " + ", ".join(down_days[-10:]) + "\n")
            f.write("- **Short trade share on down days:** see long_short doc.\n")
            f.write("- External index data not loaded (MB: no new external deps).\n")

    loss_reasons = Counter()
    for e in enriched:
        if _pnl(e["exit"]) >= 0:
            continue
        r = str(e["exit"].get("exit_reason") or "unknown")
        loss_reasons[r.split("(")[0].strip()[:50]] += 1

    # Phase 9 CSA
    drivers = []
    if n:
        if (join_log_pct if post else join_pct) < join_need:
            drivers.append(
                (
                    "Truth Gate: entry join failed",
                    f"log {join_log_pct:.1f}% / path {join_pct:.1f}% vs need {join_need}%",
                    "critical",
                )
            )
        elif join_log_pct < 90 and not post:
            drivers.append(("Incomplete log-level entry join", f"{join_log_pct:.1f}% log join — enable unified emitter", "high"))
        top_lr = loss_reasons.most_common(3)
        if top_lr:
            drivers.append(
                (
                    "Dominant loss exit reasons",
                    ", ".join(f"{a}({b})" for a, b in top_lr),
                    "high",
                )
            )
        if long_pn < short_pn and long_pn < 0:
            drivers.append(("Long leg drag", f"LONG PnL {long_pn:.2f} vs SHORT {short_pn:.2f}", "high"))
        if payoff and payoff < 1:
            drivers.append(("Negative payoff ratio", f"avg_win/|avg_loss|={payoff:.2f}", "high"))
        sym_worst = min(by_sym.items(), key=lambda x: x[1])
        drivers.append((f"Worst symbol bucket: {sym_worst[0]}", f"cumulative {sym_worst[1]:.2f}", "medium"))
        drivers.append(("Exit timing / give-back", f"MFE>0 but loss in top-100 losers: {gave_back}", "medium"))
    csa_path = audit_out("CSA_REVIEW")
    with open(csa_path, "w", encoding="utf-8") as f:
        f.write("# CSA Review — Alpaca Loss Forensics (Causal)" + (" — **POST-EPOCH**\n\n" if post else "\n\n"))
        f.write("## Ranked drivers (evidence-backed)\n\n")
        for i, (name, ev, sev) in enumerate(drivers[:7], 1):
            f.write(f"{i}. **{name}** [{sev}] — {ev}\n")
        f.write("\n## Classification\n\n")
        f.write("- **Entry-quality vs exit-timing:** Use entry composite vs MFE/MAE on losers; high MFE+loss suggests exit path.\n")
        f.write("- **Directional bias:** long_short.md\n")
        f.write("- **Gating:** blocked_counterfactual.md\n")
        f.write("\n## Most likely root cause (hypothesis)\n\n")
        f.write("Dominant realized loss mechanism in-window: see top driver above; confirm with shadow replay.\n\n")
        f.write("## Disconfirming tests\n\n")
        f.write("- If join coverage improves to >95% and driver ranking unchanged → not a pipeline lie.\n")
        f.write("- If shorts on down days show high block rate → gating hypothesis strengthens.\n")

    # Phase 10 SRE integrity
    sre_final = audit_out("SRE_REVIEW")
    with open(sre_final, "w", encoding="utf-8") as f:
        f.write("# SRE Review — Loss Forensics Integrity" + (" (**POST-EPOCH**)\n\n" if post else "\n\n"))
        f.write(f"- **Log join:** {join_log_pct:.2f}%  **Path intel:** {join_pct:.2f}% (gate {join_need}%)\n")
        f.write(f"- **Unified stream:** {unified_ok}\n")
        f.write(f"- **trade_id blank count:** {blank_tid}\n")
        f.write(f"- **Duplicate trade_key in window:** {dup_tk}\n")
        if hard_fail:
            f.write("\n**VERDICT: NOT DECISION-GRADE** — Truth Gate failed.\n")
        else:
            f.write("\n**VERDICT:** Pipeline plausible for exploratory loss review; promotion still requires stricter gates.\n")

    # Phase 11 board
    board = audit_out("BOARD_PACKET")
    with open(board, "w", encoding="utf-8") as f:
        f.write("# Board Packet — Alpaca Loss Forensics\n\n")
        f.write("## Executive summary\n\n")
        f.write(f"- Window: last **{n}** exits. Total PnL **{total_pnl:.2f} USD**.\n")
        f.write(f"- Today UTC vs baseline: see day_by_day.\n")
        f.write(f"- Join coverage: **{join_pct:.1f}%**.\n\n")
        f.write("## Causal drivers\n\nSee CSA review.\n\n")
        f.write("## Recommended next experiments (SHADOW-ONLY)\n\n")
        f.write("- Shadow hold/exit grid on frozen CSV (no live changes).\n")
        f.write("- Blocked-trade counterfactual harness if not already run.\n\n")
        f.write("## Hard fixes (data/ops/logic)\n\n")
        f.write("- Raise entry-exit join rate (emitters, trade_id parity).\n")
        f.write("- Ensure protected logs never truncated.\n\n")
        f.write("## **DO NOT PROMOTE / DO NOT TUNE** until Truth Gate passes and fixes land.\n")

    backlog = audit_out("ACTION_BACKLOG")
    with open(backlog, "w", encoding="utf-8") as f:
        f.write("# Action Backlog (post-forensics)\n\n")
        f.write("1. [ ] Fix join coverage if <98% for promotion-grade reads.\n")
        f.write("2. [ ] Re-run forensics after deploy.\n")
        f.write("3. [ ] Shadow experiments only — no parameter tuning on live.\n")

    return 3 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
