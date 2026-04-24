#!/usr/bin/env python3
"""
Quant tear-sheet: descriptive stats from logs/exit_attribution.jsonl (deduped by trade_id, last wins).

Remote: PYTHONPATH=/root/stock-bot python3 scripts/_tmp_quant_performance_review.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Tuple


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _f(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _exit_pathology(exit_reason: str, exit_reason_code: str) -> str:
    s = f"{exit_reason or ''} {exit_reason_code or ''}".lower()
    if "displac" in s:
        return "displacement"
    if "stop" in s and "trail" not in s:
        return "stop_loss"
    if "trail" in s:
        return "trailing_stop"
    if "profit" in s or "target" in s or "scale" in s:
        return "take_profit / scale"
    if "signal_decay" in s or "decay" in s:
        return "signal_decay"
    if "time_exit" in s or "time exit" in s:
        return "time_exit"
    if "flip" in s:
        return "position_flip"
    if "risk" in s and "decay" not in s:
        return "risk / generic"
    return "other / mixed"


def _signal_bucket(rec: Dict[str, Any]) -> str:
    junk = {"", "UNKNOWN", "NONE", "NULL", "N/A"}
    for k in ("strategy", "strategy_label", "entry_strategy", "entry_decision_reason"):
        v = rec.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s and s.upper() not in junk:
            return s.upper()[:80]
    v = rec.get("variant_id")
    if v and str(v).strip():
        return str(v).strip().upper()[:80]
    return "UNTAGGED"


def _dedupe_last_wins(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    by_tid: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for rec in rows:
        tid = str(rec.get("trade_id") or "").strip()
        if not tid:
            continue
        if tid not in by_tid:
            order.append(tid)
        by_tid[tid] = rec
    out = [by_tid[t] for t in order]
    return out, len(rows) - len(out)


@dataclass
class Agg:
    n: int = 0
    wins: int = 0
    pnl_sum: float = 0.0
    pnl_pct_sum: float = 0.0
    fees_sum: float = 0.0
    slip_vals: List[float] = field(default_factory=list)
    hold_win: List[float] = field(default_factory=list)
    hold_loss: List[float] = field(default_factory=list)
    win_pnls: List[float] = field(default_factory=list)
    loss_pnls: List[float] = field(default_factory=list)

    def add(self, pnl: float, pnl_pct: float, hold: Optional[float], fee: float, slip: Optional[float], win: bool) -> None:
        self.n += 1
        if win:
            self.wins += 1
        self.pnl_sum += pnl
        self.pnl_pct_sum += pnl_pct
        self.fees_sum += fee
        if slip is not None:
            self.slip_vals.append(slip)
        if hold is not None:
            (self.hold_win if win else self.hold_loss).append(hold)
        (self.win_pnls if win else self.loss_pnls).append(pnl)


def _mean(xs: List[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def _run_strict_gate(root: Path) -> Optional[Dict[str, Any]]:
    gate = root / "telemetry" / "alpaca_strict_completeness_gate.py"
    if not gate.is_file():
        return None
    try:
        p = subprocess.run(
            [sys.executable, str(gate), "--root", str(root), "--audit"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=120,
            env={**dict(os.environ), "PYTHONPATH": str(root)},
        )
        out = (p.stdout or "").strip()
        if not out:
            return None
        return json.loads(out)
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--ledger", type=Path, default=None, help="Override path to exit_attribution.jsonl")
    ap.add_argument("--no-gate", action="store_true", help="Skip invoking strict completeness gate")
    args = ap.parse_args()
    root = args.root.resolve()
    ledger = (args.ledger or (root / "logs" / "exit_attribution.jsonl")).resolve()
    if not ledger.is_file():
        print(f"# Error\n\nMissing ledger: `{ledger}`")
        return 2

    raw: List[Dict[str, Any]] = []
    for rec in _iter_jsonl(ledger):
        tid = str(rec.get("trade_id") or "").strip()
        if not tid or not tid.startswith("open_"):
            continue
        pnl = _f(rec.get("pnl"))
        if pnl is None:
            continue
        raw.append(rec)

    deduped, dup_removed = _dedupe_last_wins(raw)

    global_agg = Agg()
    by_signal: DefaultDict[str, Agg] = defaultdict(Agg)
    by_exit: DefaultDict[str, Agg] = defaultdict(Agg)

    for rec in deduped:
        pnl = float(rec.get("pnl") or 0.0)
        pnl_pct = float(rec.get("pnl_pct") or 0.0)
        hold = _f(rec.get("time_in_trade_minutes"))
        fee = float(_f(rec.get("fees_usd")) or 0.0)
        slip = _f(rec.get("exit_slippage_bps"))
        win = pnl > 1e-9
        sk = _signal_bucket(rec)
        ek = _exit_pathology(str(rec.get("exit_reason") or ""), str(rec.get("exit_reason_code") or ""))
        global_agg.add(pnl, pnl_pct, hold, fee, slip, win)
        by_signal[sk].add(pnl, pnl_pct, hold, fee, slip, win)
        by_exit[ek].add(pnl, pnl_pct, hold, fee, slip, win)

    lines: List[str] = []
    lines.append("# Alpaca exit ledger — quant performance tear-sheet\n")
    lines.append(f"- **Root:** `{root}`\n")
    lines.append(f"- **Ledger:** `{ledger}`\n")
    lines.append(f"- **Raw rows (with `trade_id` + `pnl`):** {len(raw)}\n")
    lines.append(f"- **Duplicate `trade_id` rows collapsed:** {dup_removed}\n")
    lines.append(f"- **Deduped trades (this report):** {len(deduped)}\n")

    if not args.no_gate:
        g = _run_strict_gate(root)
        if g:
            lines.append("\n## Strict completeness gate (authoritative cohort)\n\n")
            lines.append("| Field | Value |\n|---|---|\n")
            lines.append(f"| `trades_seen` | {g.get('trades_seen')} |\n")
            lines.append(f"| `trades_complete` | **{g.get('trades_complete')}** |\n")
            lines.append(f"| `trades_incomplete` | {g.get('trades_incomplete')} |\n")
            lines.append(f"| `LEARNING_STATUS` | `{g.get('LEARNING_STATUS')}` |\n")
            if g.get("reason_histogram"):
                lines.append(f"| `reason_histogram` | `{g.get('reason_histogram')}` |\n")

    ga = global_agg
    wr = (ga.wins / ga.n * 100.0) if ga.n else 0.0
    lines.append("\n## Global metrics (deduped ledger)\n\n")
    lines.append("| Metric | Value |\n|---|---|\n")
    lines.append(f"| Total PnL (USD) | {ga.pnl_sum:,.2f} |\n")
    lines.append(f"| Avg PnL % per trade | {ga.pnl_pct_sum / ga.n:.4f} |\n" if ga.n else "| Avg PnL % per trade | — |\n")
    lines.append(f"| Win rate | {wr:.1f}% ({ga.wins}/{ga.n}) |\n")
    lines.append(f"| Total fees (USD, row field) | {ga.fees_sum:,.4f} |\n")
    if ga.slip_vals:
        lines.append(f"| Avg exit slippage (bps, where present) | {sum(ga.slip_vals)/len(ga.slip_vals):.2f} |\n")
        lines.append(f"| Rows with slippage bps | {len(ga.slip_vals)} / {ga.n} |\n")
    else:
        lines.append("| Avg exit slippage (bps) | *no `exit_slippage_bps` on rows* |\n")

    avg_win = _mean(ga.win_pnls)
    avg_loss = _mean(ga.loss_pnls)
    lines.append(f"| Avg win (USD) | {avg_win:,.2f} |\n" if avg_win is not None else "| Avg win (USD) | — |\n")
    lines.append(f"| Avg loss (USD) | {avg_loss:,.2f} |\n" if avg_loss is not None else "| Avg loss (USD) | — |\n")
    hw = _mean(ga.hold_win)
    hl = _mean(ga.hold_loss)
    lines.append("\n### Holding time (minutes)\n\n")
    lines.append("| cohort | avg minutes |\n|---|---|\n")
    lines.append(f"| winners | {hw:.1f} |\n" if hw is not None else "| winners | — |\n")
    lines.append(f"| losers | {hl:.1f} |\n" if hl is not None else "| losers | — |\n")

    def _table_signal(title: str, aggs: Dict[str, Agg], min_n: int = 1) -> None:
        lines.append(f"\n## {title}\n\n")
        lines.append("| bucket | n | win% | total $ | avg $ | avg win | avg loss | avg hold (w/l min) |\n")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---|\n")
        keys = sorted(aggs.keys(), key=lambda k: aggs[k].pnl_sum, reverse=True)
        for k in keys:
            a = aggs[k]
            if a.n < min_n:
                continue
            wrk = 100.0 * a.wins / a.n
            aw = _mean(a.win_pnls)
            al = _mean(a.loss_pnls)
            hwk = _mean(a.hold_win)
            hlk = _mean(a.hold_loss)
            hold_s = "-"
            if hwk is not None or hlk is not None:
                hold_s = f"{hwk or 0:.0f} / {hlk or 0:.0f}"
            aw_s = f"{aw:,.2f}" if aw is not None else "—"
            al_s = f"{al:,.2f}" if al is not None else "—"
            lines.append(
                f"| `{k[:48]}` | {a.n} | {wrk:.1f}% | {a.pnl_sum:,.2f} | {a.pnl_sum/a.n:,.3f} | {aw_s} | {al_s} | {hold_s} |\n"
            )

    _table_signal("Signal / strategy bucket (`strategy` → `variant_id` → `UNTAGGED`)", dict(by_signal))

    lines.append("\n## Exit pathology (from `exit_reason` + `exit_reason_code`)\n\n")
    total_n = ga.n or 1
    lines.append("| family | n | % of trades | total $ | win% |\n|---|---:|---:|---:|---:|\n")
    for k in sorted(by_exit.keys(), key=lambda x: by_exit[x].n, reverse=True):
        a = by_exit[k]
        pct = 100.0 * a.n / total_n
        wrk = 100.0 * a.wins / a.n if a.n else 0.0
        lines.append(f"| {k} | {a.n} | {pct:.1f}% | {a.pnl_sum:,.2f} | {wrk:.1f}% |\n")

    # Desk call: best / worst bucket by contribution (min 5 trades)
    MIN = 5
    sig_rank = [(k, v.pnl_sum, v.wins / v.n if v.n else 0, v.n) for k, v in by_signal.items() if v.n >= MIN]
    sig_rank.sort(key=lambda x: x[1], reverse=True)
    lines.append("\n## Desk read (deduped ledger, buckets with n ≥ 5)\n\n")
    if not sig_rank:
        lines.append("*No single bucket has ≥5 trades; slice is too thin for stable ranking.*\n")
    else:
        # Sort ascending on total $ so worst drag (most negative) is first.
        sig_by_pnl = sorted(sig_rank, key=lambda x: x[1])
        worst = sig_by_pnl[0]
        best = sig_by_pnl[-1]
        lines.append(
            f"- **Best slice (highest total PnL in cohort):** `{best[0]}` — ${best[1]:,.2f} over {best[3]} trades, "
            f"win rate {100*best[2]:.1f}%.\n"
        )
        lines.append(
            f"- **Largest PnL drag (lowest total PnL):** `{worst[0]}` — ${worst[1]:,.2f} over {worst[3]} trades, "
            f"win rate {100*worst[2]:.1f}%.\n"
        )
        lines.append(
            "- **Caveat:** `strategy` / `entry_decision_reason` are often sparse; **`variant_id`** (e.g. `B2_live_paper`) may dominate buckets. "
            "Interpret as *telemetry slice*, not necessarily a distinct economic strategy unless wired at entry.\n"
        )

    print("".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
