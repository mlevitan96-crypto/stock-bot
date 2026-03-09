#!/usr/bin/env python3
"""
Autonomous Promotion & Exit Capture Review. Run ON DROPLET (DROPLET_RUN=1).
Detects when PROMOTION_REVIEW or EXIT_CAPTURE_REVIEW is required; runs audits; produces CSA-gated artifacts.
No human input: triggers are trade count, economic divergence, structural (config/B2 change).
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"
STATE = REPO / "reports" / "state"
LOGS = REPO / "logs"
CONFIG = REPO / "config"
DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
N_TRADES = 300


def _load_json(path: Path, default=None):
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _load_jsonl(path: Path, tail_n: int = 0) -> list:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if tail_n > 0:
        lines = lines[-tail_n:]
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _parse_ts(r: dict):
    for k in ("ts", "ts_iso", "timestamp", "exit_timestamp", "entry_timestamp"):
        v = r.get(k)
        if v is None:
            continue
        try:
            if isinstance(v, (int, float)):
                return int(float(v))
            s = str(v).replace("Z", "+00:00")[:26]
            from datetime import datetime as dt
            d = dt.fromisoformat(s)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return int(d.timestamp())
        except Exception:
            pass
    return None


def _safe_float(x, default=0.0):
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


# ---------- PHASE 1: TRIGGER DETECTION ----------
def detect_triggers() -> tuple[dict, bool, bool]:
    """Returns (trigger_status_dict, promotion_required, exit_capture_required)."""
    status = {
        "date": DATE,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "triggers_fired": [],
        "trade_count_trigger": {},
        "economic_trigger": {},
        "structural_trigger": {},
        "status": "NO_REVIEW_REQUIRED",
    }
    promotion = False
    exit_capture = False

    # A) Trade count
    csa_state = _load_json(STATE / "TRADE_CSA_STATE.json")
    if not csa_state and (REPO / "reports" / "state" / "TRADE_CSA_STATE.json").exists():
        csa_state = _load_json(REPO / "reports" / "state" / "TRADE_CSA_STATE.json")
    total = int(csa_state.get("total_trade_events", 0))
    last_csa = int(csa_state.get("last_csa_trade_count", 0))
    trades_since = total - last_csa
    status["trade_count_trigger"] = {
        "total_trade_events": total,
        "last_csa_trade_count": last_csa,
        "trades_since_last_csa": trades_since,
        "threshold": 100,
        "fired": trades_since >= 100,
    }
    if trades_since >= 100:
        status["triggers_fired"].append("PROMOTION_REVIEW_REQUIRED (trades_since_last_csa >= 100)")
        promotion = True

    # B) Economic: realized vs unrealized
    exit_path = LOGS / "exit_attribution.jsonl"
    exits = _load_jsonl(exit_path, tail_n=500)
    realized_sum = sum(_safe_float(r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd") or r.get("realized_pnl")) for r in exits)
    unrealized = 0.0
    try:
        try:
            from dotenv import load_dotenv
            load_dotenv(REPO / ".env")
        except Exception:
            pass
        key = os.getenv("ALPACA_KEY") or os.getenv("APCA_API_KEY_ID")
        secret = os.getenv("ALPACA_SECRET") or os.getenv("APCA_API_SECRET_KEY")
        base = os.getenv("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets"
        if key and secret:
            import alpaca_trade_api as tradeapi
            api = tradeapi.REST(key, secret, base)
            positions = api.list_positions() or []
            for p in positions:
                unrealized += _safe_float(getattr(p, "unrealized_pl", 0))
    except Exception:
        pass
    status["economic_trigger"] = {
        "realized_pnl_sum": round(realized_sum, 2),
        "unrealized_pnl": round(unrealized, 2),
        "ratio": round(unrealized / realized_sum, 2) if realized_sum != 0 else None,
        "realized_negative_unrealized_positive": realized_sum < 0 and unrealized > 0,
        "fired": False,
    }
    if realized_sum != 0 and unrealized / abs(realized_sum) >= 1.5:
        status["economic_trigger"]["fired"] = True
        status["triggers_fired"].append("EXIT_CAPTURE_REVIEW_REQUIRED (unrealized/realized >= 1.5)")
        exit_capture = True
    elif realized_sum < 0 and unrealized > 0:
        status["economic_trigger"]["fired"] = True
        status["triggers_fired"].append("EXIT_CAPTURE_REVIEW_REQUIRED (realized<0, unrealized>0)")
        exit_capture = True

    # C) Structural: config/B2 change since last CSA
    verdict_path = AUDIT / "CSA_VERDICT_LATEST.json"
    last_csa_ts = None
    if verdict_path.exists():
        v = _load_json(verdict_path)
        last_csa_ts = v.get("generated_ts") or v.get("timestamp") or v.get("last_updated")
    b2_path = CONFIG / "b2_governance.json"
    b2_mtime = int(b2_path.stat().st_mtime) if b2_path.exists() else None
    status["structural_trigger"] = {
        "config_change_since_last_csa": False,
        "b2_mtime": b2_mtime,
        "last_csa_ts": last_csa_ts,
    }
    if b2_mtime and last_csa_ts:
        try:
            if isinstance(last_csa_ts, (int, float)):
                last_ts = int(float(last_csa_ts))
            else:
                from datetime import datetime as dt
                last_ts = int(dt.fromisoformat(str(last_csa_ts).replace("Z", "+00:00")).timestamp())
            if b2_mtime > last_ts:
                status["structural_trigger"]["config_change_since_last_csa"] = True
                status["structural_trigger"]["fired"] = True
                status["triggers_fired"].append("PROMOTION_REVIEW_REQUIRED (config/B2 changed since last CSA)")
                promotion = True
        except Exception:
            pass
    if "fired" not in status["structural_trigger"]:
        status["structural_trigger"]["fired"] = False

    if promotion or exit_capture:
        status["status"] = "REVIEW_REQUIRED"
    return status, promotion, exit_capture


# ---------- PHASE 2: EXIT CAPTURE & TRADE SHAPE ----------
def run_exit_capture_audit() -> tuple[list, dict]:
    """Analyze last N trades; return (exit_audit_lines_md, trade_shape_table_dict)."""
    exit_path = LOGS / "exit_attribution.jsonl"
    rows = _load_jsonl(exit_path, tail_n=N_TRADES)
    if not rows:
        return ["# Exit Capture Audit\n\n**Date:** " + DATE + "\n\nNo exit_attribution records.\n"], {"trades": [], "summary": {}}

    # Trade shape
    shapes = []
    by_reason = defaultdict(list)
    hold_winners = []
    hold_losers = []
    green_then_red = 0
    for r in rows:
        pnl = _safe_float(r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd"))
        qm = r.get("exit_quality_metrics") or {}
        mfe = qm.get("mfe") if qm.get("mfe") is not None else None
        mae = qm.get("mae") if qm.get("mae") is not None else None
        giveback = qm.get("profit_giveback")
        hold = r.get("time_in_trade_minutes") or r.get("hold_minutes")
        reason = str(r.get("exit_reason") or r.get("exit_reason_code") or r.get("close_reason") or "unknown")[:64]
        by_reason[reason].append({"pnl": pnl, "hold": hold})
        if hold is not None:
            if pnl >= 0:
                hold_winners.append(hold)
            else:
                hold_losers.append(hold)
        if mfe is not None and mfe > 0 and pnl < 0:
            green_then_red += 1
        shapes.append({
            "symbol": r.get("symbol"),
            "pnl_usd": round(pnl, 4),
            "mfe": mfe,
            "mae": mae,
            "profit_giveback": giveback,
            "hold_minutes": hold,
            "exit_reason": reason,
        })

    # Exit reason stats
    reason_stats = {}
    for reason, trades in by_reason.items():
        pnls = [t["pnl"] for t in trades]
        n = len(pnls)
        wins = sum(1 for p in pnls if p >= 0)
        reason_stats[reason] = {
            "count": n,
            "win_rate_pct": round(100.0 * wins / n, 1) if n else 0,
            "avg_pnl": round(sum(pnls) / n, 4) if n else None,
        }

    # Hold time
    med_hold_w = sorted(hold_winners)[len(hold_winners) // 2] if hold_winners else None
    med_hold_l = sorted(hold_losers)[len(hold_losers) // 2] if hold_losers else None
    total = len(rows)
    pct_green_then_red = round(100.0 * green_then_red / total, 1) if total else 0

    # Fail closed checks
    winners_cut_earlier = med_hold_w is not None and med_hold_l is not None and med_hold_w < med_hold_l
    majority_green_then_red = pct_green_then_red > 50

    # Trade frequency (trades/day)
    ts_min, ts_max = None, None
    for r in rows:
        t = _parse_ts(r)
        if t:
            ts_min = t if ts_min is None else min(ts_min, t)
            ts_max = t if ts_max is None else max(ts_max, t)
    days = ((ts_max - ts_min) / 86400.0) if (ts_min and ts_max and ts_max > ts_min) else 1.0
    trades_per_day = round(total / days, 1) if days else None
    by_symbol = defaultdict(int)
    for r in rows:
        by_symbol[(r.get("symbol") or "").upper() or "unknown"] += 1
    trades_per_symbol = dict(by_symbol)

    md = [
        "# Exit Capture Audit",
        "",
        f"**Date:** {DATE}",
        f"**Trades analyzed:** {total}",
        "",
        "## Trade shape summary",
        "",
        f"- MFE/MAE present: {sum(1 for s in shapes if s.get('mfe') is not None)} / {total}",
        f"- Green then red (MFE>0, PnL<0): {green_then_red} ({pct_green_then_red}%)",
        f"- Median hold winners (min): {med_hold_w}",
        f"- Median hold losers (min): {med_hold_l}",
        f"- **Winners cut earlier than losers:** " + ("YES — review" if winners_cut_earlier else "No"),
        f"- **Majority green→red:** " + ("YES — review" if majority_green_then_red else "No"),
        "",
        "## Trade frequency",
        "",
        f"- Trades/day (window): {trades_per_day}",
        f"- Trades/symbol (top): " + ", ".join(f"{s}={c}" for s, c in sorted(trades_per_symbol.items(), key=lambda x: -x[1])[:10]),
        "",
        "## By exit reason",
        "",
        "| Reason | Count | Win rate % | Avg PnL |",
        "|--------|-------|------------|---------|",
    ]
    for reason, st in sorted(reason_stats.items(), key=lambda x: -x[1]["count"]):
        md.append(f"| {reason[:40]} | {st['count']} | {st['win_rate_pct']} | {st['avg_pnl']} |")

    table = {
        "date": DATE,
        "n_trades": total,
        "trades_per_day": trades_per_day,
        "trades_per_symbol": dict(trades_per_symbol),
        "shapes": shapes[-100:],
        "by_exit_reason": reason_stats,
        "median_hold_winners_min": med_hold_w,
        "median_hold_losers_min": med_hold_l,
        "pct_green_then_red": pct_green_then_red,
        "winners_cut_earlier_than_losers": winners_cut_earlier,
        "majority_green_then_red": majority_green_then_red,
        "summary": {
            "total_realized_pnl": round(sum(s["pnl_usd"] for s in shapes), 2),
            "win_rate": round(100.0 * sum(1 for s in shapes if s["pnl_usd"] >= 0) / total, 1) if total else 0,
        },
    }
    return md, table


# ---------- PHASE 3: CSA PROMOTION VERDICT ----------
def run_csa_verdict(promotion_triggered: bool, exit_capture_triggered: bool, trade_shape: dict) -> dict:
    verdict = "HOLD"
    confidence = 0.5
    adversarial_notes = []
    if not promotion_triggered:
        return {"date": DATE, "verdict": "NO_PROMOTION_REVIEW", "confidence": 0, "required_next_actions": [], "rollback_plan": "", "adversarial_notes": []}
    if trade_shape.get("winners_cut_earlier_than_losers") or trade_shape.get("majority_green_then_red"):
        verdict = "TUNE_EXITS_ONLY"
        confidence = 0.6
        required = ["Fix exit timing so winners are not cut earlier than losers.", "Reduce green→red exits before any promotion."]
        adversarial_notes.append("Exit shape supports bottleneck; require more data before PROMOTE.")
    else:
        verdict = "HOLD"
        confidence = 0.7
        required = ["Continue paper observation.", "Next CSA at next 100-trade milestone."]
    adversarial_notes.append("Unrealized/realized ratio from single snapshot; cross-check with positions API.")
    adversarial_notes.append("Exit attribution from exit_attribution.jsonl only; reconcile with trades API if promotion considered.")
    if len(adversarial_notes) > 2:
        confidence = max(0.0, confidence - 0.05)
    return {
        "date": DATE,
        "verdict": verdict,
        "confidence": confidence,
        "required_next_actions": required,
        "rollback_plan": "Revert config/b2_governance.json; set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false; restart stock-bot." if promotion_triggered else "",
        "adversarial_notes": adversarial_notes,
    }


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    BOARD.mkdir(parents=True, exist_ok=True)
    (REPO / "reports" / "state").mkdir(parents=True, exist_ok=True)
    state_dir = STATE if STATE.exists() else REPO / "reports" / "state"

    # Phase 1
    trigger_status, promotion_required, exit_capture_required = detect_triggers()
    trigger_path = AUDIT / f"PROMOTION_TRIGGER_STATUS_{DATE}.json"
    trigger_path.write_text(json.dumps(trigger_status, indent=2), encoding="utf-8")

    if not promotion_required and not exit_capture_required:
        print("NO_REVIEW_REQUIRED")
        return 0

    # Phase 2 (if exit capture triggered)
    exit_md_lines = []
    trade_shape_table = {}
    if exit_capture_required:
        exit_md_lines, trade_shape_table = run_exit_capture_audit()
        (AUDIT / f"EXIT_CAPTURE_AUDIT_{DATE}.md").write_text("\n".join(exit_md_lines), encoding="utf-8")
        (AUDIT / f"TRADE_SHAPE_TABLE_{DATE}.json").write_text(json.dumps(trade_shape_table, indent=2), encoding="utf-8")

    # Phase 3 (if promotion triggered)
    csa_verdict = run_csa_verdict(promotion_required, exit_capture_required, trade_shape_table)
    (AUDIT / f"CSA_PROMOTION_VERDICT_{DATE}.json").write_text(json.dumps(csa_verdict, indent=2), encoding="utf-8")

    # Phase 4 & 5: Owner packet
    promotion_allowed = csa_verdict.get("verdict") == "PROMOTE"
    exits_bottleneck = trade_shape_table.get("winners_cut_earlier_than_losers") or trade_shape_table.get("majority_green_then_red")
    overtrading = False
    if trigger_status.get("trade_count_trigger", {}).get("trades_since_last_csa", 0) > 200:
        overtrading = True  # simple heuristic
    packet = [
        "# Weekly Economic Truth Packet",
        "",
        f"**Date:** {DATE}",
        "",
        "## Is promotion allowed?",
        "**" + ("Yes" if promotion_allowed else "No — " + csa_verdict.get("verdict", "HOLD")) + "**",
        "",
        "## Are exits the bottleneck?",
        "**" + ("Yes" if exits_bottleneck else "No") + "**",
        "",
        "## Are we overtrading?",
        "**" + ("Review (high trade count)" if overtrading else "No") + "**",
        "",
        "## What must change next?",
        "",
    ] + ["- " + a for a in csa_verdict.get("required_next_actions", [])] + [
        "",
        "## What must NOT change yet?",
        "- Do not enable LIVE.",
        "- Do not change B2 live_paper without CSA.",
        "",
    ]
    (BOARD / f"WEEKLY_ECONOMIC_TRUTH_PACKET_{DATE}.md").write_text("\n".join(packet), encoding="utf-8")

    print("REVIEW_REQUIRED", "promotion=" + str(promotion_required), "exit_capture=" + str(exit_capture_required))
    return 0


if __name__ == "__main__":
    sys.exit(main())
