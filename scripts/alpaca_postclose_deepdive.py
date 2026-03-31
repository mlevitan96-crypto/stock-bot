#!/usr/bin/env python3
"""
ALPACA POST-CLOSE FULL-DAY DEEP DIVE + TELEGRAM (Alpaca droplet).

READ-ONLY sinks. Writes ONLY:
  reports/ALPACA_POSTCLOSE_DEEPDIVE_<YYYYMMDD>_<TS>.md
  reports/ALPACA_POSTCLOSE_SUMMARY_<YYYYMMDD>_<TS>.md
  reports/alpaca_daily_close_telegram.jsonl (append-only audit for Telegram sends)
  state/postclose_watermark.json (unless --dry-run)

No strategy/trading logic changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MB_START = "<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START -->"
MB_END = "<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_END -->"
MB_TITLE = "## Alpaca attribution truth contract (canonical)"
MAX_JSONL_LINES = 300_000
ET = ZoneInfo("America/New_York")
AUDIT_JSONL_NAME = "alpaca_daily_close_telegram.jsonl"


def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", os.environ.get("DROPLET_TRADING_ROOT", "")).strip()
    return Path(r).resolve() if r else REPO_ROOT


def _ts_tag_utc() -> str:
    return datetime.now(timezone.utc).strftime("%H%M")


def _load_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    out: List[dict] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= MAX_JSONL_LINES:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(r, dict):
                    out.append(r)
    except OSError:
        return []
    return out


def _num(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _row_timestamps(r: dict) -> List[datetime]:
    keys = (
        "timestamp",
        "exit_timestamp",
        "entry_timestamp",
        "filled_at",
        "closed_at",
        "event_time",
        "ts",
    )
    out: List[datetime] = []
    for k in keys:
        v = r.get(k)
        if not v:
            continue
        dt = _parse_iso(str(v))
        if dt:
            out.append(dt)
    return out


def _parse_iso(s: str) -> Optional[datetime]:
    if not s or s in ("null", "None"):
        return None
    try:
        s2 = s.replace("Z", "+00:00")[:32]
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _et_date_of(dt: datetime) -> date:
    return _as_utc(dt).astimezone(ET).date()


def _session_bounds_utc(d: date) -> Tuple[datetime, datetime]:
    start_et = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=ET)
    end_et = start_et + timedelta(days=1)
    return start_et.astimezone(timezone.utc), end_et.astimezone(timezone.utc)


def _in_session_window(row: dict, u0: datetime, u1: datetime) -> bool:
    for dt in _row_timestamps(row):
        u = _as_utc(dt)
        if u0 <= u < u1:
            return True
    return False


def _latest_session_date(rows_list: List[List[dict]]) -> Optional[date]:
    best: Optional[date] = None
    for rows in rows_list:
        for r in rows:
            for dt in _row_timestamps(r):
                ed = _et_date_of(dt)
                if best is None or ed > best:
                    best = ed
    return best


def _verify_memory_bank(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MEMORY_BANK.md missing"
    t = path.read_text(encoding="utf-8", errors="replace")
    if MB_START not in t or MB_END not in t:
        return False, "canonical markers missing"
    if MB_TITLE not in t:
        return False, "canonical title missing"
    for needle in (
        "decision_event_id",
        "canonical_trade_id",
        "symbol_normalized",
        "time_bucket_id",
    ):
        if needle not in t:
            return False, f"required phrase missing: {needle}"
    return True, "ok"


def _fingerprint(root: Path, session: date, exit_rows: int, order_rows: int) -> dict:
    p = root / "logs" / "exit_attribution.jsonl"
    st = p.stat() if p.is_file() else None
    return {
        "session_date": session.isoformat(),
        "exit_attribution_lines": exit_rows,
        "orders_jsonl_lines": order_rows,
        "exit_file_mtime": st.st_mtime if st else None,
    }


def _read_watermark(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _flatten_nums(d: Any, prefix: str = "", depth: int = 0) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if depth > 4 or not isinstance(d, dict):
        return out
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else str(k)
        fn = _num(v)
        if fn is not None:
            out[key] = fn
        elif isinstance(v, dict):
            out.update(_flatten_nums(v, key, depth + 1))
    return out


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    n = len(xs)
    if n < 15 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    if denx < 1e-12 or deny < 1e-12:
        return None
    return num / (denx * deny)


def _audit_path(rep: Path) -> Path:
    return rep / AUDIT_JSONL_NAME


def _message_hash_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _already_sent_live_for_session(audit_p: Path, session_iso: str) -> bool:
    """Exactly one live Telegram per session_date (ET); dry-run and dedupe_skip lines do not count."""
    if not audit_p.is_file():
        return False
    try:
        with audit_p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if o.get("session_date_et") != session_iso:
                    continue
                if o.get("dry_run") is True:
                    continue
                if o.get("dedupe_skip") is True:
                    continue
                ok = o.get("success") is True or o.get("telegram_ok") is True
                if ok:
                    return True
    except OSError:
        return False
    return False


def _append_telegram_audit(rep: Path, record: dict) -> None:
    p = _audit_path(rep)
    rep.mkdir(parents=True, exist_ok=True)
    record.setdefault("logged_at_utc", datetime.now(timezone.utc).isoformat())
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _learning_snapshot(root: Path) -> Dict[str, Any]:
    """Read-only strict learning gate (Alpaca); does not mutate logs or learning state."""
    try:
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        return evaluate_completeness(root, open_ts_epoch=None, audit=False)
    except Exception as e:
        return {
            "LEARNING_STATUS": "UNKNOWN",
            "learning_fail_closed_reason": f"evaluate_completeness_error:{e}",
            "trades_seen": None,
            "trades_complete": None,
            "trades_incomplete": None,
        }


def _pnl_usd_session(ex_w: List[dict]) -> Tuple[Optional[float], int]:
    total = 0.0
    n = 0
    for r in ex_w:
        snap = r.get("snapshot") if isinstance(r.get("snapshot"), dict) else {}
        v = _num(snap.get("pnl")) if snap else _num(r.get("pnl"))
        if v is not None:
            total += v
            n += 1
    if n == 0:
        return None, 0
    return total, n


def _send_telegram(text: str, *, dry_run: bool) -> bool:
    from scripts.alpaca_telegram import send_governance_telegram

    if dry_run:
        print("--- DRY-RUN (no Telegram HTTP) ---\n", text, "\n--- end ---", flush=True)
        return True
    return send_governance_telegram(text, script_name="postclose_deepdive")


def _format_daily_alpaca_telegram(
    *,
    session_date: date,
    trade_intent_n: int,
    exit_rows_session: int,
    exits_with_pnl_pct: int,
    mean_pnl: Any,
    med_pnl: Any,
    pnl_usd_sum: Optional[float],
    pnl_usd_n: int,
    learn: Dict[str, Any],
    join_block: bool,
    approved: str,
    board_rec: List[str],
    no_new_data: bool,
    report_names: Tuple[str, str],
) -> str:
    ls = learn.get("LEARNING_STATUS", "UNKNOWN")
    rsn = learn.get("learning_fail_closed_reason") or "—"
    seen = learn.get("trades_seen")
    inc = learn.get("trades_incomplete")
    gate = "BLOCKED" if join_block else "PASS"
    pnl_snap = (
        f"mean pnl%={mean_pnl} | median pnl%={med_pnl}"
        if mean_pnl is not None or med_pnl is not None
        else "pnl% N/A (no exit rows with pnl_pct in session)"
    )
    usd_part = (
        f"sum realized pnl (USD, where snapshot.pnl set)={pnl_usd_sum:.2f} (n={pnl_usd_n})"
        if pnl_usd_sum is not None
        else "realized USD sum N/A"
    )
    refresh = "Log fingerprint unchanged since last post-close run." if no_new_data else "Fresh session analysis + reports written."
    deep, summ = report_names
    zero_note = (
        "(explicit 0 trades in session window — synthetic / quiet day OK)\n"
        if trade_intent_n == 0 and exit_rows_session == 0
        else ""
    )
    return (
        "ALPACA DAILY POST-MARKET\n"
        f"Date (ET): {session_date.isoformat()}\n"
        f"{zero_note}"
        f"Trades in session window: trade_intent={trade_intent_n} | exit_attribution_rows={exit_rows_session}\n"
        f"Exits w/ pnl% in session: {exits_with_pnl_pct}\n"
        f"PnL snapshot: {pnl_snap} | {usd_part}\n"
        f"Learning (strict read-only): {ls} | seen={seen} incomplete={inc} | reason={rsn}\n"
        f"CSA: APPROVED_PLAN={approved} | join_gate={gate}\n"
        f"Top 3:\n"
        + "\n".join(f"  - {r}" for r in board_rec[:3])
        + f"\n{refresh}\n"
        f"Reports: {deep} | {summ}\n"
        "Alpaca-only; no trading or learning logic changed."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca post-close deep dive + Telegram")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Render message to stdout; do not send Telegram HTTP; do not update watermark; still append audit with dry_run=true",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Ignore no-new-data short-circuit and live-send dedupe (SRE test only)",
    )
    ap.add_argument(
        "--session-date-et",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Pin session to this America/New_York calendar date (synthetic proof; default: infer from logs or today ET)",
    )
    args = ap.parse_args()

    if not Path("/proc").is_dir():
        print("This mission expects Linux (Alpaca droplet).", file=sys.stderr)
        return 2

    root = _root()
    os.chdir(root)
    rep = root / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    wm_path = state_dir / "postclose_watermark.json"

    mb_path = root / "MEMORY_BANK.md"
    mb_ok, mb_msg = _verify_memory_bank(mb_path)
    if not mb_ok:
        print("STOP — Memory Bank:", mb_msg, file=sys.stderr)
        return 4

    from scripts.alpaca_telegram_env_detect import apply_detected_telegram_env

    tg_ok, tg_src = apply_detected_telegram_env(root)
    if not tg_ok:
        print(
            "USER INPUT NEEDED (copy/paste):\n"
            "- Path to the env file or activation script that defines "
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID\n"
            "(Do NOT send token values.)",
            file=sys.stderr,
        )
        return 3

    run_rows = _load_jsonl(root / "logs" / "run.jsonl")
    ord_rows = _load_jsonl(root / "logs" / "orders.jsonl")
    sig_rows = _load_jsonl(root / "logs" / "signal_context.jsonl")
    blk_rows = _load_jsonl(root / "state" / "blocked_trades.jsonl")
    ex_rows = _load_jsonl(root / "logs" / "exit_attribution.jsonl")

    if args.session_date_et:
        try:
            session_date = date.fromisoformat(args.session_date_et.strip())
        except ValueError:
            print("STOP — invalid --session-date-et (use YYYY-MM-DD)", file=sys.stderr)
            return 6
    else:
        session_date = _latest_session_date([run_rows, ord_rows, sig_rows, blk_rows, ex_rows])
        if session_date is None:
            session_date = datetime.now(ET).date()

    u0, u1 = _session_bounds_utc(session_date)
    ymd = session_date.strftime("%Y%m%d")
    ts = _ts_tag_utc()
    out_deep = rep / f"ALPACA_POSTCLOSE_DEEPDIVE_{ymd}_{ts}.md"
    out_sum = rep / f"ALPACA_POSTCLOSE_SUMMARY_{ymd}_{ts}.md"

    def filt(rs: List[dict]) -> List[dict]:
        return [r for r in rs if _in_session_window(r, u0, u1)]

    run_w = filt(run_rows)
    ord_w = filt(ord_rows)
    sig_w = filt(sig_rows)
    blk_w = filt(blk_rows)
    ex_w = filt(ex_rows)

    fp_now = _fingerprint(root, session_date, len(ex_rows), len(ord_rows))
    wm_prev = _read_watermark(wm_path)
    no_new = (
        not args.force
        and wm_prev.get("fingerprint") == fp_now
        and wm_prev.get("session_date") == fp_now["session_date"]
    )

    session_iso = session_date.isoformat()
    if not args.dry_run and not args.force and _already_sent_live_for_session(_audit_path(rep), session_iso):
        print("dedupe_skip: live Telegram already recorded for session", session_iso, flush=True)
        _append_telegram_audit(
            rep,
            {
                "session_date_et": session_iso,
                "dry_run": False,
                "dedupe_skip": True,
                "success": False,
                "telegram_ok": False,
                "message_hash": None,
                "message_kind": "dedupe_skip",
            },
        )
        return 0

    trade_intent = [r for r in run_w if r.get("event_type") == "trade_intent"]
    exit_intent = [r for r in run_w if r.get("event_type") == "exit_intent"]
    orders_typed = [o for o in ord_w if o.get("type") == "order"]
    fills = [o for o in ord_w if str(o.get("type", "")).lower() in ("fill", "fill_event")]
    closed = [o for o in ord_w if str(o.get("type", "")).lower() in ("order_closed", "closed")]

    o_with_ct = sum(1 for o in orders_typed if o.get("canonical_trade_id"))
    o_with_de = sum(1 for o in orders_typed if o.get("decision_event_id"))
    ti_with_ct = sum(1 for r in trade_intent if r.get("canonical_trade_id"))
    ti_with_de = sum(1 for r in trade_intent if r.get("decision_event_id"))
    ex_with_ct = sum(1 for r in ex_w if r.get("canonical_trade_id"))
    ex_with_de = sum(1 for r in ex_w if r.get("decision_event_id"))
    ex_with_tb = sum(1 for r in ex_w if r.get("time_bucket_id"))
    sym_norm_o = sum(1 for o in orders_typed if o.get("symbol_normalized"))
    sym_norm_ti = sum(1 for r in trade_intent if r.get("symbol_normalized"))

    join_block = False
    join_reasons: List[str] = []
    if len(orders_typed) > 0 and o_with_ct == 0 and o_with_de == 0:
        join_block = True
        join_reasons.append("Session orders present but zero canonical_trade_id and zero decision_event_id")
    if len(trade_intent) > 0 and ti_with_ct == 0 and ti_with_de == 0:
        join_block = True
        join_reasons.append("Session trade_intent rows present but zero join keys")
    if len(ex_w) > 0 and ex_with_ct == 0 and ex_with_de == 0 and (len(orders_typed) > 0 or len(trade_intent) > 0):
        join_block = True
        join_reasons.append(
            "Session exit_attribution rows present with activity but zero canonical_trade_id/decision_event_id"
        )

    pnls: List[float] = []
    for r in ex_w:
        p = _num(r.get("pnl_pct"))
        if p is None and isinstance(r.get("snapshot"), dict):
            p = _num(r["snapshot"].get("pnl_pct"))
        if p is not None:
            pnls.append(p)

    win = sum(1 for p in pnls if p > 0)
    loss = sum(1 for p in pnls if p < 0)
    mean_pnl = sum(pnls) / len(pnls) if pnls else None
    if pnls:
        srt = sorted(pnls)
        m = len(srt) // 2
        med_pnl = (srt[m - 1] + srt[m]) / 2 if len(srt) % 2 == 0 else srt[m]
    else:
        med_pnl = None

    v2_pairs: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    for r in ex_w:
        p = _num(r.get("pnl_pct"))
        if p is None:
            continue
        v2 = r.get("v2_exit_components") if isinstance(r.get("v2_exit_components"), dict) else {}
        for k, v in _flatten_nums(v2, "v2_exit").items():
            v2_pairs[k].append((v, p))

    cors: List[Tuple[str, float, int]] = []
    for k, pairs in v2_pairs.items():
        if len(pairs) < 20:
            continue
        xs = [a for a, _ in pairs]
        ys = [b for _, b in pairs]
        c = _pearson(xs, ys)
        if c is not None:
            cors.append((k, c, len(pairs)))
    cors.sort(key=lambda x: abs(x[1]), reverse=True)

    blk_reasons = Counter()
    for r in blk_w:
        blk_reasons[str(r.get("reason") or r.get("block_reason") or "unknown")] += 1

    ci_github = root / ".github"
    ci_marker = "present" if ci_github.is_dir() else "not present on droplet (expected)"

    approved = "NO" if join_block else "YES"
    board_rec = [
        "Maintain deterministic join keys on all new emits (canonical_trade_id, decision_event_id).",
        "Expand signal_context.jsonl coverage for blocked vs entered forensics.",
        "Track explicit fee/slippage fields on orders when paper economics are enabled.",
    ]
    if join_block:
        board_rec = [
            "Unblock CSA: backfill or enable join keys for the post-close session window before promotion use.",
            "Treat offline attribution as narrative-only until join coverage meets MEMORY_BANK contract.",
            "Re-run this job after next session once emitters populate keys.",
        ]

    learn = _learning_snapshot(root)
    pnl_usd_sum, pnl_usd_n = _pnl_usd_session(ex_w)

    if no_new:
        tg_body = _format_daily_alpaca_telegram(
            session_date=session_date,
            trade_intent_n=len(trade_intent),
            exit_rows_session=len(ex_w),
            exits_with_pnl_pct=len(pnls),
            mean_pnl=mean_pnl,
            med_pnl=med_pnl,
            pnl_usd_sum=pnl_usd_sum,
            pnl_usd_n=pnl_usd_n,
            learn=learn,
            join_block=join_block,
            approved=approved,
            board_rec=board_rec,
            no_new_data=True,
            report_names=("no_new_md_refresh", "watermark_unchanged"),
        )
        ok = _send_telegram(tg_body, dry_run=args.dry_run)
        if not ok:
            print("STOP — Telegram send failed (verify credentials and requests).", file=sys.stderr)
            return 5
        live_ok = bool(not args.dry_run and ok)
        mh = _message_hash_sha256(tg_body)
        _append_telegram_audit(
            rep,
            {
                "session_date_et": session_iso,
                "dry_run": args.dry_run,
                "dedupe_skip": False,
                "success": live_ok,
                "telegram_ok": live_ok,
                "message_hash": mh,
                "message_kind": "no_new_data",
                "no_new_data": True,
            },
        )
        print("no_new_data:", fp_now, flush=True)
        return 0

    # --- Markdown ---
    lines = [
        f"# ALPACA Post-Close Deep Dive — `{ymd}` `{ts}` UTC tag",
        "",
        f"- **TRADING_ROOT:** `{root}`",
        f"- **Telegram env source:** `{tg_src}`",
        f"- **Session window (ET calendar day):** {session_date.isoformat()} → UTC [{u0.isoformat()}, {u1.isoformat()})",
        f"- **Dry-run:** {args.dry_run}",
        "",
        "## 1) Data integrity & coverage (SRE + Eng Lead)",
        "",
        "### Global row counts (loaded, cap per file {})".format(MAX_JSONL_LINES),
        f"| Sink | Total | In session window |",
        f"|------|------:|------------------:|",
        f"| run.jsonl | {len(run_rows)} | {len(run_w)} |",
        f"| orders.jsonl | {len(ord_rows)} | {len(ord_w)} |",
        f"| signal_context.jsonl | {len(sig_rows)} | {len(sig_w)} |",
        f"| blocked_trades.jsonl | {len(blk_rows)} | {len(blk_w)} |",
        f"| exit_attribution.jsonl | {len(ex_rows)} | {len(ex_w)} |",
        "",
        "### Session event mix",
        f"- trade_intent: **{len(trade_intent)}** (entered/blocked per decision_outcome field when present)",
        f"- exit_intent: **{len(exit_intent)}**",
        f"- orders (typed `order`): **{len(orders_typed)}**",
        f"- fills / closed (heuristic type): **{len(fills)}** / **{len(closed)}**",
        "",
        "### Deterministic join coverage (session window)",
        f"| Cohort | n | canonical_trade_id | decision_event_id | symbol_normalized |",
        f"|--------|---|--------------------|--------------------|-----------------|",
        f"| orders | {len(orders_typed)} | {o_with_ct} | {o_with_de} | {sym_norm_o} |",
        f"| trade_intent | {len(trade_intent)} | {ti_with_ct} | {ti_with_de} | {sym_norm_ti} |",
        f"| exit_attribution | {len(ex_w)} | {ex_with_ct} | {ex_with_de} | time_bucket_id={ex_with_tb} |",
        "",
        "**Eng Lead:** schemas are read as-is; missing keys are reported, not imputed.",
        "",
        "## 2) PnL deep dive (Quant)",
        "",
        f"- Exit rows in session with pnl_pct: **{len(pnls)}**",
        f"- Win / loss count: **{win}** / **{loss}**",
        f"- Mean / median pnl_pct: **{mean_pnl}** / **{med_pnl}**",
        "",
        "## 3) Correlation & contribution (Quant)",
        "",
        "Pearson(v2_exit_component, pnl_pct) — associative only; exit-time leakage risk (CSA).",
        "",
        "| feature | n | r |",
        "|---------|---:|---:|",
    ]
    for k, r, n in cors[:25]:
        lines.append(f"| `{k}` | {n} | {r:.4f} |")
    if not cors:
        lines.append("| — | — | insufficient n |")
    lines.extend(
        [
            "",
            "## 4) Blocked trades & opportunity cost (Quant + CSA)",
            "",
            f"- Blocked rows in session: **{len(blk_w)}**",
            "- Top reasons:",
        ]
    )
    for reason, c in blk_reasons.most_common(12):
        lines.append(f"  - `{reason}`: {c}")
    lines.extend(
        [
            "- **Opportunity cost / counterfactual PnL:** not computed (no deterministic post-hoc execution path).",
            "",
            "## 5) What-if analysis (Quant + CSA)",
            "",
            "- **Status:** not executed — would require replay with frozen bars and promotion-safe simulator.",
            "- **NOT PROMOTED** for live behavior changes from this section.",
            "",
            "## 6) CI / infra incidents (SRE)",
            "",
            f"- Local `.github/`: **{ci_marker}**",
            "- Review `journalctl -u stock-bot.service` / disk manually if incidents suspected (not scraped here).",
            "",
            "## 7) Board recommendations (Board)",
            "",
        ]
    )
    for i, rec in enumerate(board_rec, 1):
        lines.append(f"{i}. {rec}")
    lines.extend(
        [
            "",
            "## 8) CSA approval gate (CSA)",
            "",
            f"- **APPROVED_PLAN:** **{approved}**",
            "",
        ]
    )
    if join_block:
        lines.extend(
            [
                "### CSA join blockers (FAIL CLOSED)",
                "",
            ]
        )
        for jr in join_reasons:
            lines.append(f"- {jr}")
        lines.append("")
        lines.append("Deterministic joins on canonical keys are required for attribution-grade post-close sign-off.")
    else:
        lines.extend(
            [
                "- Join keys present for session cohorts at minimum threshold.",
                "- **Single best next plan:** use this report as read-only input to governance; schedule rampant / board review with keyed data.",
                "",
            ]
        )
    lines.extend(
        [
            "---",
            f"- Reports: `{out_deep.name}`, `{out_sum.name}`",
            "- **No live trading changes made.**",
            "",
        ]
    )

    out_deep.write_text("\n".join(lines) + "\n", encoding="utf-8")

    sum_lines = [
        f"# ALPACA Post-Close Summary — `{ymd}` `{ts}`",
        "",
        f"- Session (ET): **{session_date.isoformat()}**",
        f"- Telegram source: `{tg_src}`",
        f"- Exits w/ pnl in session: **{len(pnls)}** | mean pnl%: **{mean_pnl}**",
        f"- Join gate: **{'BLOCKED' if join_block else 'PASS'}** | APPROVED_PLAN: **{approved}**",
        "",
        "## Top 3 board recommendations",
        "",
    ]
    for i, rec in enumerate(board_rec[:3], 1):
        sum_lines.append(f"{i}. {rec}")
    sum_lines.extend(
        [
            "",
            f"**Full:** `{out_deep}`",
            "",
            "_No strategy or risk changes; analysis and notifications only._",
        ]
    )
    out_sum.write_text("\n".join(sum_lines) + "\n", encoding="utf-8")

    if not args.dry_run:
        wm_path.write_text(json.dumps({"fingerprint": fp_now, "updated_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n", encoding="utf-8")

    tg_body = _format_daily_alpaca_telegram(
        session_date=session_date,
        trade_intent_n=len(trade_intent),
        exit_rows_session=len(ex_w),
        exits_with_pnl_pct=len(pnls),
        mean_pnl=mean_pnl,
        med_pnl=med_pnl,
        pnl_usd_sum=pnl_usd_sum,
        pnl_usd_n=pnl_usd_n,
        learn=learn,
        join_block=join_block,
        approved=approved,
        board_rec=board_rec,
        no_new_data=False,
        report_names=(out_deep.name, out_sum.name),
    )
    ok = _send_telegram(tg_body, dry_run=args.dry_run)
    if not ok:
        print("STOP — Telegram send failed (verify credentials and requests).", file=sys.stderr)
        return 5
    live_ok = bool(not args.dry_run and ok)
    mh = _message_hash_sha256(tg_body)
    _append_telegram_audit(
        rep,
        {
            "session_date_et": session_iso,
            "dry_run": args.dry_run,
            "dedupe_skip": False,
            "success": live_ok,
            "telegram_ok": live_ok,
            "message_hash": mh,
            "message_kind": "full_deepdive",
            "no_new_data": False,
            "report_deep": str(out_deep),
            "report_summary": str(out_sum),
        },
    )

    print("ALPACA_POSTCLOSE_DEEPDIVE:", out_deep)
    print("ALPACA_POSTCLOSE_SUMMARY:", out_sum)
    print("telegram_source:", tg_src)
    print("APPROVED_PLAN:", approved)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
