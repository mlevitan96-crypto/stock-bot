#!/usr/bin/env python3
"""
Paper-only second-chance displacement re-evaluation worker.

- Reads state/paper_second_chance_queue.jsonl (or seeds from blocked_trades.jsonl).
- Uses read-only Alpaca list_positions + local state/metrics; never submits orders.
- Appends results to logs/second_chance_displacement.jsonl.

Run from repo root:
  PYTHONPATH=. python3 scripts/paper_second_chance_reeval_worker.py --process-queue
  PYTHONPATH=. python3 scripts/paper_second_chance_reeval_worker.py --seed-from-blocked-trades 200
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

import alpaca_trade_api as tradeapi  # type: ignore
from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")

from config.registry import StateFiles
from main import Config, load_metadata_with_lock
from trading.displacement_policy import evaluate_displacement

QUEUE_PATH = REPO / "state" / "paper_second_chance_queue.jsonl"
LOG_PATH = REPO / "logs" / "second_chance_displacement.jsonl"


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, default=str) + "\n")


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _processed_pending_ids(log_path: Path) -> Set[str]:
    done: Set[str] = set()
    if not log_path.exists():
        return done
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except json.JSONDecodeError:
                continue
            if j.get("event") == "reeval_result" and j.get("pending_id"):
                done.add(str(j["pending_id"]))
    return done


def _rewrite_queue(remaining: List[Dict[str, Any]]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE_PATH.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in remaining:
            f.write(json.dumps(row, default=str) + "\n")
    tmp.replace(QUEUE_PATH)


def _coerce_entry_ts(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    s = str(val).strip()
    if not s:
        return None
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t
    except Exception:
        return None


def _meta_for_symbol(metadata: Any, symbol: str) -> Dict[str, Any]:
    if not isinstance(metadata, dict) or not symbol:
        return {}
    su = str(symbol).upper().strip()
    if symbol in metadata and isinstance(metadata[symbol], dict):
        return dict(metadata[symbol])
    if su in metadata and isinstance(metadata.get(su), dict):
        return dict(metadata[su])
    for k, v in metadata.items():
        if str(k).upper().strip() == su and isinstance(v, dict):
            return dict(v)
    return {}


def _position_pnl_pct(pos: Any) -> Optional[float]:
    try:
        ep = float(getattr(pos, "avg_entry_price", 0) or 0)
        cp = float(getattr(pos, "current_price", 0) or 0)
        if ep <= 0 or cp <= 0:
            return None
        return ((cp - ep) / ep) * 100.0
    except Exception:
        return None


def _paper_reevaluate(
    pending: Dict[str, Any],
    api: Any,
    regime_label: str,
    posture: str,
) -> Tuple[str, Optional[str], Dict[str, Any]]:
    """
    Returns (reeval_outcome allowed|blocked, reeval_block_reason or None, diagnostics)
    """
    sym = str(pending.get("symbol") or "").upper().strip()
    displaced = str(pending.get("displaced_symbol") or "").upper().strip()
    score = float(pending.get("original_score") or 0.0)
    min_block = float(pending.get("effective_min_score_at_block") or 0.0)
    min_now = float(getattr(Config, "MIN_EXEC_SCORE", 2.5))

    diag: Dict[str, Any] = {"gates_evaluated": ["min_exec", "duplicate_symbol", "capacity", "displacement_policy"]}

    if score < min_block or score < min_now:
        return "blocked", "score_below_effective_or_current_min_exec", diag

    try:
        positions = api.list_positions() or []
    except Exception as e:
        return "blocked", f"alpaca_list_positions_error:{e}", diag

    held = {getattr(p, "symbol", "") for p in positions}
    if sym in held:
        return "blocked", "symbol_already_in_positions", diag

    max_pos = int(getattr(Config, "MAX_CONCURRENT_POSITIONS", 16))
    n = len(positions)

    if n < max_pos:
        diag["capacity_path"] = "slots_available"
        return "allowed", None, diag

    if displaced not in held:
        diag["capacity_path"] = "incumbent_not_held_book_full"
        return "blocked", "displaced_symbol_no_longer_held_book_still_full", diag

    pos_inc = next(p for p in positions if getattr(p, "symbol", "") == displaced)
    pnl_pct = _position_pnl_pct(pos_inc)

    try:
        metadata = load_metadata_with_lock(StateFiles.POSITION_METADATA) if StateFiles.POSITION_METADATA.exists() else {}
    except Exception:
        metadata = {}
    meta = _meta_for_symbol(metadata, displaced)
    entry_ts = _coerce_entry_ts(meta.get("entry_ts") or meta.get("ts"))
    entry_score = float(meta.get("entry_score") or 0.0)
    current_score = float(meta.get("current_score") or entry_score or 0.0)

    current_position: Dict[str, Any] = {
        "symbol": displaced,
        "entry_ts": entry_ts,
        "entry_score": entry_score,
        "current_score": current_score,
        "pnl_pct": pnl_pct,
    }
    challenger_candidate: Dict[str, Any] = {
        "symbol": sym,
        "score": score,
        "new_signal_score": score,
    }
    uwp = pending.get("challenger_uw_flow_proxy")
    if uwp is not None:
        try:
            challenger_candidate["uw_flow_strength"] = float(uwp)
        except (TypeError, ValueError):
            pass

    context = {"regime_label": regime_label, "posture": posture}
    config_overrides = {
        "DISPLACEMENT_ENABLED": getattr(Config, "DISPLACEMENT_ENABLED", True),
        "DISPLACEMENT_MIN_HOLD_SECONDS": getattr(Config, "DISPLACEMENT_MIN_HOLD_SECONDS", 3600),
        "DISPLACEMENT_MIN_DELTA_SCORE": getattr(Config, "DISPLACEMENT_MIN_DELTA_SCORE", 0.75),
        "DISPLACEMENT_REQUIRE_THESIS_DOMINANCE": getattr(Config, "DISPLACEMENT_REQUIRE_THESIS_DOMINANCE", True),
    }
    allowed, reason, pol_diag = evaluate_displacement(
        current_position, challenger_candidate, context, config_overrides=config_overrides
    )
    diag["displacement_policy"] = pol_diag
    if allowed:
        return "allowed", None, diag
    return "blocked", str(reason or "displacement_policy_denied"), diag


def _read_regime_posture() -> Tuple[str, str]:
    rp = REPO / "state" / "regime_posture_state.json"
    if not rp.exists():
        return "UNKNOWN", "NEUTRAL"
    try:
        j = json.loads(rp.read_text(encoding="utf-8"))
        return str(j.get("regime_label") or "UNKNOWN"), str(j.get("posture") or "NEUTRAL")
    except Exception:
        return "UNKNOWN", "NEUTRAL"


def cmd_process_queue() -> int:
    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version="v2")
    done = _processed_pending_ids(LOG_PATH)
    queue = _load_jsonl(QUEUE_PATH)
    now = int(time.time())
    remaining: List[Dict[str, Any]] = []
    regime, posture = _read_regime_posture()

    for row in queue:
        pid = str(row.get("pending_id") or "")
        if pid in done:
            continue
        due = int(row.get("due_epoch") or 0)
        if due > now:
            remaining.append(row)
            continue

        outcome, blk_reason, diag = _paper_reevaluate(row, api, regime, posture)
        reeval_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        log_row = {
            "paper_only": True,
            "event": "reeval_result",
            "pending_id": pid,
            "original_ts": row.get("original_ts_iso"),
            "reeval_ts": reeval_iso,
            "symbol": row.get("symbol"),
            "direction": row.get("direction"),
            "original_scores": {
                "final_score": row.get("original_score"),
                "components": row.get("original_components") or {},
                "effective_min_score_at_block": row.get("effective_min_score_at_block"),
            },
            "block_reason": "displacement_blocked",
            "reeval_outcome": outcome,
            "reeval_block_reason": blk_reason,
            "displaced_symbol": row.get("displaced_symbol"),
            "policy_reason_at_block": row.get("policy_reason_at_block"),
            "reeval_diagnostics": diag,
        }
        _append_jsonl(LOG_PATH, log_row)
        done.add(pid)

    _rewrite_queue(remaining)
    return 0


def cmd_seed(n: int, seed_nonce: bool) -> int:
    blocked_path = REPO / "state" / "blocked_trades.jsonl"
    if not blocked_path.exists():
        print("seed: blocked_trades.jsonl missing", file=sys.stderr)
        return 1
    picked = 0
    delay = 0
    try:
        delay = int(os.environ.get("PAPER_SECOND_CHANCE_DELAY_SECONDS", "60"))
    except ValueError:
        delay = 60
    now = int(time.time())
    due_epoch = now - 1

    with open(blocked_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if picked >= n:
                break
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            reason = str(r.get("block_reason") or r.get("reason") or "")
            if reason != "displacement_blocked":
                continue
            sym = str(r.get("symbol") or "").upper().strip()
            if not sym:
                continue
            original_ts_iso = str(r.get("timestamp") or "")
            if not original_ts_iso:
                continue
            displaced = str(r.get("displaced_symbol") or "").upper().strip() or "UNKNOWN"
            try:
                score = float(r.get("score") or 0.0)
            except (TypeError, ValueError):
                continue
            mr = r.get("min_required")
            try:
                min_b = float(mr) if mr is not None else float(getattr(Config, "MIN_EXEC_SCORE", 2.5))
            except (TypeError, ValueError):
                min_b = float(getattr(Config, "MIN_EXEC_SCORE", 2.5))
            comps = r.get("components") if isinstance(r.get("components"), dict) else {}
            try:
                dp = float(r.get("decision_price") or r.get("would_have_entered_price") or 0) or None
            except (TypeError, ValueError):
                dp = None
            uw = r.get("uw_signal_quality_score")
            try:
                uw_f = float(uw) if uw is not None else None
            except (TypeError, ValueError):
                uw_f = None

            tail = f"seed|{time.time_ns()}" if seed_nonce else "seed"
            pid = hashlib.sha256(f"{sym}|{original_ts_iso}|{displaced}|{score}|{tail}".encode()).hexdigest()[:20]
            reeval_ts_iso = datetime.fromtimestamp(due_epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            queue_row = {
                "pending_id": pid,
                "due_epoch": due_epoch,
                "original_ts_iso": original_ts_iso,
                "reeval_ts_iso": reeval_ts_iso,
                "symbol": sym,
                "direction": r.get("direction"),
                "original_score": score,
                "original_components": dict(comps),
                "effective_min_score_at_block": min_b,
                "displaced_symbol": displaced,
                "policy_reason_at_block": str(r.get("policy_reason") or ""),
                "challenger_uw_flow_proxy": uw_f,
                "block_reason": "displacement_blocked",
                "decision_price": dp,
                "market_regime_at_block": r.get("market_regime"),
                "variant_id_at_block": r.get("variant_id"),
                "seeded": True,
            }
            _append_jsonl(QUEUE_PATH, queue_row)
            log_sched = {
                "paper_only": True,
                "event": "scheduled",
                "pending_id": pid,
                "original_ts": original_ts_iso,
                "reeval_ts": reeval_ts_iso,
                "symbol": sym,
                "direction": r.get("direction"),
                "original_scores": {
                    "final_score": score,
                    "components": dict(comps),
                    "effective_min_score_at_block": min_b,
                },
                "block_reason": "displacement_blocked",
                "reeval_outcome": None,
                "reeval_block_reason": None,
                "displaced_symbol": displaced,
                "policy_reason_at_block": str(r.get("policy_reason") or ""),
                "delay_seconds": delay,
                "seeded": True,
            }
            _append_jsonl(LOG_PATH, log_sched)
            picked += 1

    print(f"seed: enqueued {picked} displacement_blocked rows (due immediate)")
    return 0 if picked else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--process-queue", action="store_true")
    ap.add_argument("--seed-from-blocked-trades", type=int, default=0, metavar="N")
    ap.add_argument(
        "--seed-nonce",
        action="store_true",
        help="Unique pending_id per seed run (for repeated smoke without clearing result log)",
    )
    args = ap.parse_args()
    if args.seed_from_blocked_trades:
        return cmd_seed(args.seed_from_blocked_trades, args.seed_nonce)
    if args.process_queue:
        return cmd_process_queue()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
