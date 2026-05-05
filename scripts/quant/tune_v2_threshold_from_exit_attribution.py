#!/usr/bin/env python3
"""
Tune ``holdout_probability_threshold`` for V2 profit agent using **realized PnL** from
``logs/exit_attribution.jsonl`` joined to ``v2_shadow_proba`` on ``trade_intent`` rows in
``logs/run.jsonl``.

Empirical Bayes (Beta(1,1) prior on win rate): scores each candidate threshold by
``posterior_win_rate * sqrt(n_approved) + lambda * (sum_pnl_usd / scale)`` so sparse slices
do not dominate. PDT **hard gate**: lowering the threshold vs the current JSON value is
blocked when ``PDTWarden.can_trade`` is false (increases approval frequency).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _iter_jsonl(path: Path):
    if not path.is_file():
        return
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _trade_intent_index(run_path: Path) -> Dict[str, Dict[str, Any]]:
    """Last trade_intent row wins per trade_id / canonical_trade_id / trade_key."""
    out: Dict[str, Dict[str, Any]] = {}
    for rec in _iter_jsonl(run_path):
        if str(rec.get("event_type") or rec.get("event") or "") != "trade_intent":
            continue
        for k in ("trade_id", "canonical_trade_id", "trade_key"):
            tid = rec.get(k)
            if tid:
                out[str(tid)] = rec
    return out


def _exit_pnl_usd(rec: Dict[str, Any]) -> Optional[float]:
    for key in ("pnl", "realized_pnl_usd", "realized_pnl_price"):
        if key not in rec:
            continue
        try:
            v = float(rec[key])
            if math.isfinite(v):
                return v
        except (TypeError, ValueError):
            continue
    eqm = rec.get("exit_quality_metrics")
    if isinstance(eqm, dict):
        for key in ("realized_pnl_price", "realized_pnl_usd"):
            if key in eqm:
                try:
                    v = float(eqm[key])
                    if math.isfinite(v):
                        return v
                except (TypeError, ValueError):
                    pass
    return None


def _join_exits_to_intents(
    exit_path: Path,
    intent_by_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ex in _iter_jsonl(exit_path):
        tid = ex.get("trade_id") or ex.get("trade_key") or ex.get("canonical_trade_id")
        if not tid:
            continue
        intent = intent_by_id.get(str(tid))
        if not intent:
            continue
        p = intent.get("v2_shadow_proba")
        if p is None:
            continue
        try:
            proba = float(p)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(proba):
            continue
        pnl = _exit_pnl_usd(ex)
        if pnl is None or not math.isfinite(pnl):
            continue
        ts = ex.get("entry_timestamp") or ex.get("timestamp") or ""
        rows.append(
            {
                "trade_id": str(tid),
                "entry_timestamp": str(ts),
                "pnl_usd": float(pnl),
                "v2_shadow_proba": float(proba),
            }
        )
    rows.sort(key=lambda r: str(r.get("entry_timestamp") or ""))
    return rows


def _beta_posterior_mean(wins: int, losses: int) -> float:
    return (1.0 + wins) / (2.0 + wins + losses)


def _pick_threshold(
    rows: List[Dict[str, Any]],
    *,
    train_frac: float,
    min_approved_train: int,
    top_frac_cap: float,
    lam_pnl: float,
) -> Tuple[float, Dict[str, Any]]:
    n = len(rows)
    if n < max(20, min_approved_train * 2):
        raise SystemExit(f"Not enough joined rows: {n} (need more exit+log overlap).")
    split = max(1, min(n - 1, int(n * float(train_frac))))
    train = rows[:split]
    test = rows[split:]
    probas = sorted({float(r["v2_shadow_proba"]) for r in train}, reverse=True)
    best_thr = float(probas[-1])
    best_score = -1e100
    best_meta: Dict[str, Any] = {}

    for thr in probas:
        tr = [r for r in train if float(r["v2_shadow_proba"]) >= thr]
        if len(tr) < min_approved_train:
            continue
        if len(tr) > int(math.ceil(float(top_frac_cap) * len(train))):
            continue
        pnl = sum(float(r["pnl_usd"]) for r in tr)
        wins = sum(1 for r in tr if float(r["pnl_usd"]) > 0)
        losses = len(tr) - wins
        post = _beta_posterior_mean(wins, losses)
        score = post * math.sqrt(len(tr)) + lam_pnl * (pnl / max(1.0, float(len(tr))))
        if score > best_score + 1e-12 or (abs(score - best_score) <= 1e-12 and thr > best_thr):
            best_score = score
            best_thr = float(thr)
            best_meta = {
                "train_n": len(train),
                "train_approved_n": len(tr),
                "train_net_pnl_usd": round(pnl, 4),
                "train_posterior_win_rate": round(post, 6),
                "train_tuning_score": round(score, 6),
                "threshold": best_thr,
            }

    if not best_meta:
        raise SystemExit("No threshold satisfied min_approved_train / top_frac_cap constraints.")

    te = [r for r in test if float(r["v2_shadow_proba"]) >= best_thr]
    te_pnl = sum(float(r["pnl_usd"]) for r in te)
    te_w = sum(1 for r in te if float(r["pnl_usd"]) > 0)
    best_meta["test_n"] = len(test)
    best_meta["test_approved_n"] = len(te)
    best_meta["test_net_pnl_usd"] = round(te_pnl, 4)
    best_meta["test_posterior_win_rate"] = round(_beta_posterior_mean(te_w, len(te) - te_w), 6) if te else None
    return best_thr, best_meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exit-log", type=Path, default=REPO / "logs" / "exit_attribution.jsonl")
    ap.add_argument("--run-log", type=Path, default=REPO / "logs" / "run.jsonl")
    ap.add_argument(
        "--out-threshold-json",
        type=Path,
        default=REPO / "models" / "vanguard_v2_profit_agent_threshold.json",
    )
    ap.add_argument("--train-frac", type=float, default=0.8)
    ap.add_argument("--min-approved-train", type=int, default=8)
    ap.add_argument("--top-frac-cap", type=float, default=0.55, help="Max fraction of train rows a threshold may approve.")
    ap.add_argument("--lam-pnl", type=float, default=0.02, help="Weight on mean train PnL in the tuning score.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-pdt-gate", action="store_true", help="Skip PDT check (local CI only).")
    args = ap.parse_args()

    intent_by_id = _trade_intent_index(args.run_log)
    joined = _join_exits_to_intents(args.exit_log, intent_by_id)
    thr, meta = _pick_threshold(
        joined,
        train_frac=args.train_frac,
        min_approved_train=args.min_approved_train,
        top_frac_cap=args.top_frac_cap,
        lam_pnl=args.lam_pnl,
    )

    cur_thr: Optional[float] = None
    base_payload: Dict[str, Any] = {}
    if args.out_threshold_json.is_file():
        try:
            base_payload = json.loads(args.out_threshold_json.read_text(encoding="utf-8"))
            if isinstance(base_payload, dict) and base_payload.get("holdout_probability_threshold") is not None:
                cur_thr = float(base_payload["holdout_probability_threshold"])
        except Exception:
            base_payload = {}

    proposed = float(thr)
    pdt_note = "skipped"
    if cur_thr is not None and proposed < cur_thr - 1e-12 and not args.skip_pdt_gate:
        try:
            from config.registry import get_alpaca_trading_credentials

            from src.alpaca.pdt_warden import PDTWarden, allow_v2_threshold_relaxation

            k, s, base = get_alpaca_trading_credentials()
            if not k or not s:
                print("PDT gate: missing Alpaca credentials; refusing to relax threshold.", file=sys.stderr)
                proposed = float(cur_thr)
                pdt_note = "blocked_missing_credentials"
            else:
                w = PDTWarden(k, s, base)
                ok, reason = allow_v2_threshold_relaxation(
                    current_threshold=float(cur_thr),
                    proposed_threshold=float(thr),
                    warden=w,
                )
                if not ok:
                    proposed = float(cur_thr)
                    pdt_note = f"blocked:{reason}"
                else:
                    pdt_note = f"ok:{reason}"
        except Exception as e:
            proposed = float(cur_thr) if cur_thr is not None else proposed
            pdt_note = f"error:{e}"[:200]

    out = dict(base_payload) if isinstance(base_payload, dict) else {}
    out["holdout_probability_threshold"] = float(proposed)
    out["tuning_source_exit_log"] = str(args.exit_log.as_posix())
    out["tuning_source_run_log"] = str(args.run_log.as_posix())
    out["tuning_joined_rows_n"] = len(joined)
    out["tuning_meta"] = meta
    out["tuning_objective"] = "beta_posterior_x_sqrt_n_plus_lam_mean_pnl"
    out["pdt_relaxation_gate"] = pdt_note
    out["tuning_raw_argmax_threshold"] = float(thr)

    print(json.dumps(out, indent=2))
    if args.dry_run:
        return 0
    args.out_threshold_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_threshold_json.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", args.out_threshold_json.resolve(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
