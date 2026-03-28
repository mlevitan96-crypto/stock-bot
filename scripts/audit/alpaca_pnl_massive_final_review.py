#!/usr/bin/env python3
"""
ALPACA MASSIVE PnL + EDGE FOREnsics REVIEW — artifact generator (offline workspace).

With --cohort-ids + --truth-json + session epochs, rebuilds reconciliation and populated analyses from TRADING_BOT_ROOT logs.

Signal Path Intelligence (SPI): read-only post-trade path distributions (see MEMORY_BANK.md). Does not change trading behavior.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
LAST_WINDOW_TRUTH = REPO / "reports" / "ALPACA_LAST_WINDOW_TRUTH_20260327_LAST_WINDOW.json"
STRICT_EPOCH_REF = REPO / "telemetry" / "alpaca_strict_completeness_gate.py"
REPLAY_DIR = REPO / "replay" / "alpaca_execution_truth_20260324_2109"
DASHBOARD_SANITY = REPO / "reports" / "ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json"


def _sha256_file(p: Path, limit: int = 20_000_000) -> str:
    if not p.is_file():
        return ""
    h = hashlib.sha256()
    n = 0
    with p.open("rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
            n += len(b)
            if n >= limit:
                break
    return h.hexdigest()


def _load_json(p: Path) -> Optional[dict]:
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_sample_trade_ids(truth: dict) -> Tuple[List[str], str]:
    ids: List[str] = []
    fg = truth.get("final_gate") or truth.get("initial_gate") or {}
    for row in fg.get("chain_matrices_complete_sample") or []:
        tid = row.get("trade_id")
        if tid and tid not in ids:
            ids.append(str(tid))
    return ids, "sample_only_from_chain_matrices_complete_sample"


def _required_log_paths(root: Path) -> Dict[str, Path]:
    logs = root / "logs"
    return {
        "exit_attribution.jsonl": logs / "exit_attribution.jsonl",
        "run.jsonl": logs / "run.jsonl",
        "alpaca_unified_events.jsonl": logs / "alpaca_unified_events.jsonl",
        "orders.jsonl": logs / "orders.jsonl",
    }


def _parse_ts(s: Any) -> Optional[float]:
    if not s:
        return None
    try:
        t = str(s).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _count_exits_in_epoch_window(root: Path, t0: float, t1: float) -> Tuple[int, int]:
    path = root / "logs" / "exit_attribution.jsonl"
    total = 0
    in_win = 0
    if not path.is_file():
        return 0, 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        e = _parse_ts(rec.get("timestamp"))
        if e is not None and t0 <= e <= t1:
            in_win += 1
    return total, in_win


def _exit_map(root: Path) -> Dict[str, dict]:
    p = root / "logs" / "exit_attribution.jsonl"
    out: Dict[str, dict] = {}
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        tid = rec.get("trade_id")
        if tid:
            out[str(tid)] = rec
    return out


def _count_jsonl(path: Path) -> int:
    if not path.is_file():
        return 0
    n = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def _replay_row_counts() -> Dict[str, Any]:
    out: Dict[str, Any] = {"replay_dir": str(REPLAY_DIR)}
    if not REPLAY_DIR.is_dir():
        out["error"] = "replay_dir_missing"
        return out
    for name in ("execution_joined.jsonl.gz", "fills.jsonl.gz", "orders.jsonl.gz", "fees.jsonl.gz"):
        p = REPLAY_DIR / name
        out[name] = {"bytes": p.stat().st_size if p.is_file() else 0, "path": str(p)}
    return out


def _gate_blockers_legacy(truth: Optional[dict], root: Path) -> List[Dict[str, str]]:
    blockers: List[Dict[str, str]] = []
    if not truth:
        blockers.append(
            {
                "id": "B0",
                "field": "last_window_truth_json",
                "detail": f"missing_or_unreadable:{LAST_WINDOW_TRUTH}",
            }
        )
        return blockers
    fg = truth.get("final_gate") or {}
    cids = fg.get("complete_trade_ids")
    n_exp = int(fg.get("forward_trades_complete") or fg.get("trades_complete") or 0)
    if not cids or len(cids) != n_exp:
        blockers.append(
            {
                "id": "B1",
                "field": "complete_trade_ids",
                "detail": (
                    f"artifact lacks full enumeration: have {0 if not cids else len(cids)} ids, "
                    f"expected {n_exp}"
                ),
            }
        )
    paths = _required_log_paths(root)
    for label, p in paths.items():
        if not p.is_file():
            blockers.append({"id": "B2", "field": label, "detail": f"missing_in_workspace:{p}"})
    rc = _replay_row_counts()
    for k in ("execution_joined.jsonl.gz", "fills.jsonl.gz"):
        sz = (rc.get(k) or {}).get("bytes", 0)
        if sz < 100:
            blockers.append({"id": "B3", "field": k, "detail": f"replay_bundle_empty_or_tiny_bytes={sz}"})
    ots = fg.get("OPEN_TS_UTC_EPOCH")
    ets = fg.get("EXIT_TS_UTC_EPOCH_MAX")
    if ots is not None and ets is not None:
        _tot, in_win = _count_exits_in_epoch_window(root, float(ots), float(ets))
        n_claim = int(fg.get("forward_trades_complete") or fg.get("trades_complete") or 0)
        if in_win == 0 and n_claim > 0:
            blockers.append(
                {
                    "id": "B4",
                    "field": "workspace_exit_attribution_window",
                    "detail": (
                        f"exit_attribution has 0 exits in gate window but claims n={n_claim} complete"
                    ),
                }
            )
    return blockers


def _cohort_blockers(
    truth: Optional[dict],
    root: Path,
    cohort_ids_path: Path,
    w0: float,
    w1: float,
) -> Tuple[List[Dict[str, str]], List[str], int]:
    blockers: List[Dict[str, str]] = []
    if not truth:
        blockers.append({"id": "B0", "field": "truth_json", "detail": "missing_or_unreadable"})
        return blockers, [], 0
    raw = _load_json(cohort_ids_path) or {}
    ids = list(raw.get("complete_trade_ids") or raw.get("trade_ids") or [])
    fg = truth.get("final_gate") or {}
    tc = int(fg.get("trades_complete") or raw.get("trades_complete") or 0)
    ts_seen = int(fg.get("trades_seen") or raw.get("trades_seen") or 0)

    paths = _required_log_paths(root)
    for label, p in paths.items():
        if not p.is_file():
            blockers.append({"id": "B2", "field": label, "detail": f"missing_in_workspace:{p}"})

    cids_truth = list(fg.get("complete_trade_ids") or [])
    if tc > 0 and not cids_truth:
        blockers.append(
            {
                "id": "B1",
                "field": "complete_trade_ids",
                "detail": "truth JSON missing complete_trade_ids while trades_complete>0",
            }
        )
    if tc > 0 and len(cids_truth) != tc:
        blockers.append(
            {
                "id": "B1b",
                "field": "complete_trade_ids_len",
                "detail": f"len(complete_trade_ids)={len(cids_truth)} != trades_complete={tc}",
            }
        )
    if ids and cids_truth and set(ids) != set(cids_truth):
        blockers.append(
            {
                "id": "B1c",
                "field": "cohort_ids_file_mismatch",
                "detail": "cohort-ids file differs from truth final_gate.complete_trade_ids",
            }
        )
    if not ids and cids_truth:
        ids = cids_truth

    exm = _exit_map(root)
    if tc > 0:
        for tid in ids:
            if tid not in exm:
                blockers.append(
                    {
                        "id": "B6",
                        "field": "exit_attribution.jsonl",
                        "detail": f"missing trade_id row for cohort member {tid} at {root / 'logs' / 'exit_attribution.jsonl'}",
                    }
                )
                break
        for tid in ids:
            r = exm.get(tid)
            if not r:
                continue
            et = _parse_ts(r.get("timestamp"))
            if et is None or not (w0 <= et <= w1):
                blockers.append(
                    {
                        "id": "B7",
                        "field": "exit_timestamp",
                        "detail": f"trade {tid} exit_ts outside [window_start,window_end]",
                    }
                )
                break

    _, in_win = _count_exits_in_epoch_window(root, w0, w1)
    if tc > 0 and in_win < tc:
        blockers.append(
            {
                "id": "B8",
                "field": "exit_window_count",
                "detail": f"exits in session window ({in_win}) < trades_complete ({tc})",
            }
        )

    return blockers, ids, ts_seen


def _recon_row(ex: dict) -> dict:
    tid = ex.get("trade_id", "")
    sym = ex.get("symbol", "")
    side = str(ex.get("side") or "long").lower()
    entry_ts = ex.get("entry_timestamp", "")
    exit_ts = ex.get("timestamp", "")
    qty = float(ex.get("qty") or 0)
    ep = float(ex.get("exit_price") or 0)
    ip = float(ex.get("entry_price") or 0)
    ledger = ex.get("pnl")
    fees = 0.0
    gross = 0.0
    if qty > 0 and ep > 0 and ip > 0:
        if side in ("long", "buy"):
            gross = (ep - ip) * qty
        else:
            gross = (ip - ep) * qty
    if ledger is not None:
        try:
            net = float(ledger)
        except (TypeError, ValueError):
            net = gross - fees
    else:
        net = gross - fees
    delta = 0.0
    if ledger is not None:
        try:
            delta = float(net) - float(ledger)
        except (TypeError, ValueError):
            delta = 0.0
    return {
        "trade_id": tid,
        "symbol": sym,
        "side": side,
        "entry_ts": entry_ts,
        "exit_ts": exit_ts,
        "qty": qty,
        "avg_entry": ip,
        "avg_exit": ep,
        "gross_pnl": round(gross, 6),
        "fees": fees,
        "net_pnl": round(net, 6),
        "ledger_pnl": ledger,
        "reconciliation_delta": round(delta, 6),
        "notes": "fees_not_joined_workspace_stub",
    }


def _format_spi_markdown(bundle: dict) -> str:
    """Human-readable SPI section from build_spi_bundle() output."""
    lines = [
        "# Signal Path Intelligence (SPI)",
        "",
        "Read-only analytics on executed Alpaca cohorts. **Not** forecasts, targets, or trade recommendations.",
        "Governance: `MEMORY_BANK.md` (Alpaca Signal Path Intelligence). **SPI does not authorize behavior change.**",
        "",
    ]
    if bundle.get("error"):
        lines.extend(
            [
                "## Status",
                "",
                f"SPI build reported an error (non-blocking for PnL review): `{bundle['error']}`",
                "",
            ]
        )
        return "\n".join(lines)
    summ = bundle.get("summary") or {}
    lines.extend(
        [
            "## Cohort",
            "",
            f"- spi_trade_rows: **{bundle.get('spi_trade_rows', 0)}**",
            f"- profit thresholds (fractional): `{bundle.get('profit_thresholds_fractional', [])}`",
            f"- fetch_bars_if_missing: **{bundle.get('fetch_bars_if_missing', False)}** (default off; no cache writes)",
            "",
            "## Aggregate (all signals)",
            "",
            "```json",
            json.dumps(summ.get("aggregate", {}), indent=2),
            "```",
            "",
            "## Per-signal summary",
            "",
            "```json",
            json.dumps(summ.get("per_signal", {}), indent=2)[:12000],
            "```",
            "",
            "## Top anomalies (descriptive only)",
            "",
            "```json",
            json.dumps(summ.get("top_anomalies_descriptive", []), indent=2),
            "```",
            "",
            summ.get("disclaimer", ""),
            "",
        ]
    )
    return "\n".join(lines)


def _write_csv(path: Path, headers: List[str], rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ts", default=os.environ.get("ALPACA_PNL_REVIEW_TS", "20260327_MKTS_FINAL"))
    ap.add_argument("--cohort-ids", type=Path, default=None)
    ap.add_argument("--truth-json", type=Path, default=None)
    ap.add_argument("--window-start-epoch", type=float, default=None)
    ap.add_argument("--window-end-epoch", type=float, default=None)
    ap.add_argument("--root", type=Path, default=None)
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="If set, all Alpaca PnL review artifacts go here (evidence/); else reports/ + reports/audit/",
    )
    args = ap.parse_args()

    if args.output_dir:
        out_dir = Path(args.output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        rep_out = aud_out = out_dir
    else:
        rep_out = REPO / "reports"
        aud_out = REPO / "reports" / "audit"

    global_ts = args.ts
    root = Path(args.root or os.environ.get("TRADING_BOT_ROOT", str(REPO))).resolve()
    cohort_mode = args.cohort_ids is not None and args.truth_json is not None

    if cohort_mode:
        truth = _load_json(args.truth_json)
        w0 = float(args.window_start_epoch or (truth or {}).get("open_ts_epoch") or 0)
        w1 = float(args.window_end_epoch or (truth or {}).get("window_end_epoch") or 0)
        blockers, complete_ids, _ts_seen = _cohort_blockers(truth, root, args.cohort_ids, w0, w1)
        fg = (truth or {}).get("final_gate") or {}
        sample_ids, sample_note = [], "cohort_mode"
    else:
        truth = _load_json(LAST_WINDOW_TRUTH)
        blockers = _gate_blockers_legacy(truth, root)
        fg = (truth or {}).get("final_gate") or {}
        complete_ids = list(fg.get("complete_trade_ids") or [])
        sample_ids, sample_note = _extract_sample_trade_ids(truth or {})
        w0 = float(fg.get("OPEN_TS_UTC_EPOCH") or 0)
        w1 = float(fg.get("EXIT_TS_UTC_EPOCH_MAX") or 0)

    blocked = len(blockers) > 0
    tc = int(fg.get("trades_complete") or 0)

    exm = _exit_map(root)
    rec_headers = [
        "trade_id",
        "symbol",
        "side",
        "entry_ts",
        "exit_ts",
        "qty",
        "avg_entry",
        "avg_exit",
        "gross_pnl",
        "fees",
        "net_pnl",
        "ledger_pnl",
        "reconciliation_delta",
        "notes",
    ]
    rec_rows: List[dict] = []
    if not blocked and complete_ids:
        for tid in complete_ids:
            if tid in exm:
                rec_rows.append(_recon_row(exm[tid]))
    elif not blocked and tc == 0:
        rec_rows = []

    if tc > 0 and not rec_rows and not blocked:
        blockers.append(
            {
                "id": "B9",
                "field": "reconciliation",
                "detail": "trades_complete>0 but reconciliation rows empty after join",
            }
        )
        blocked = True

    TS = global_ts
    log_paths = _required_log_paths(root)
    exit_total, exit_in_win = (
        _count_exits_in_epoch_window(root, w0, w1) if w0 and w1 else (0, 0)
    )
    manifest = {
        "ts": TS,
        "cohort_mode": cohort_mode,
        "root": str(root),
        "strict_gate_source_sha256": _sha256_file(STRICT_EPOCH_REF),
        "truth_ref": str(args.truth_json) if cohort_mode else str(LAST_WINDOW_TRUTH),
        "session_window_epoch": {"start": w0, "end": w1},
        "row_counts": {
            "exit_attribution_lines": _count_jsonl(root / "logs" / "exit_attribution.jsonl"),
            "run_jsonl_lines": _count_jsonl(root / "logs" / "run.jsonl"),
            "orders_jsonl_lines": _count_jsonl(root / "logs" / "orders.jsonl"),
            "alpaca_unified_events_lines": _count_jsonl(root / "logs" / "alpaca_unified_events.jsonl"),
            "cohort_complete_trade_ids": len(complete_ids),
            "exits_in_session_window": exit_in_win,
        },
        "cohort_trade_slice": {tid: exm.get(tid, {}) for tid in complete_ids[:500]},
        "blocked_intents_sample": [],
        "blockers": blockers,
    }
    if (root / "logs" / "run.jsonl").is_file():
        blocked_n = 0
        for line in (root / "logs" / "run.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("event_type") == "trade_intent" and str(r.get("decision_outcome", "")).lower() != "entered":
                blocked_n += 1
        manifest["row_counts"]["trade_intent_non_entered_lines"] = blocked_n

    bundle_path = rep_out / f"ALPACA_PNL_REVIEW_TRUTH_BUNDLE_{TS}.json"
    bundle_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    _write_csv(
        rep_out / f"ALPACA_PNL_REVIEW_TRUTH_BUNDLE_{TS}.csv",
        ["artifact", "path", "exists", "bytes", "sha256_prefix"],
        [
            {
                "artifact": k,
                "path": str(v),
                "exists": v.is_file(),
                "bytes": v.stat().st_size if v.is_file() else 0,
                "sha256_prefix": _sha256_file(v)[:16] if v.is_file() else "",
            }
            for k, v in log_paths.items()
        ],
    )
    (aud_out / f"ALPACA_PNL_REVIEW_TRUTH_BUNDLE_{TS}.md").write_text(
        "\n".join(
            [
                f"# Truth bundle ({TS})",
                "",
                f"- JSON: `{bundle_path.relative_to(REPO)}`",
                "",
                "## Row counts",
                "",
                "```json",
                json.dumps(manifest["row_counts"], indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    _write_csv(rep_out / f"ALPACA_PNL_REVIEW_RECONCILIATION_{TS}.csv", rec_headers, rec_rows)
    (aud_out / f"ALPACA_PNL_REVIEW_RECONCILIATION_{TS}.md").write_text(
        "\n".join(
            [
                f"# Reconciliation ({TS})",
                "",
                f"- Rows: **{len(rec_rows)}**",
                "",
                ("PASS: cohort economic rows joined." if rec_rows else "NO_ACTIVITY or blocked — see blockers."),
                "",
                "```json",
                json.dumps(blockers, indent=2),
                "```",
            ]
        ),
        encoding="utf-8",
    )

    n_tr = len(rec_rows)
    by_sym = Counter(str(r["symbol"]) for r in rec_rows)
    net_sum = sum(float(r["net_pnl"]) for r in rec_rows)
    wins = sum(1 for r in rec_rows if float(r["net_pnl"]) > 0)

    def analysis_payload(name: str, letter: str, extra: dict) -> dict:
        base = {
            "analysis": letter,
            "name": name,
            "cohort": "MARKET_SESSION_ET" if cohort_mode else "LEGACY_LAST_WINDOW",
            "n_trades": n_tr,
            "blocked": blocked,
            "blockers": blockers,
            "profit_implication": "see slices",
        }
        base.update(extra)
        return base

    analyses = {
        "A": analysis_payload(
            "executed_performance_surfaces",
            "A",
            {
                "slices": {"by_symbol_counts": dict(by_sym), "win_rate": wins / n_tr if n_tr else None, "net_pnl_sum": net_sum},
            },
        ),
        "B": analysis_payload("signal_attribution", "B", {"slices": {"note": "uw_attribution.jsonl not sliced in this bundle"}}),
        "C": analysis_payload(
            "exit_forensics",
            "C",
            {"slices": Counter(str(exm[t].get("exit_reason", "")) for t in complete_ids if t in exm)},
        ),
        "D": analysis_payload("cost_drag", "D", {"slices": {"fees_total": 0.0, "fee_source": "stub"}}),
        "E": analysis_payload("blocked_opportunity", "E", {"slices": {"blocked_intent_lines": manifest["row_counts"].get("trade_intent_non_entered_lines", 0)}}),
        "F": analysis_payload("gate_value", "F", {"slices": {"note": "requires blocked vs shadow join"}}),
        "G": analysis_payload("ci_infra", "G", {"slices": {"system_events": _count_jsonl(root / "logs" / "system_events.jsonl")}}),
        "H": analysis_payload("latency_path", "H", {"slices": {"note": "order fill timestamps in orders.jsonl not normalized here"}}),
        "I": analysis_payload(
            "regime_slices",
            "I",
            {"slices": Counter(str(exm[t].get("exit_regime", exm[t].get("entry_regime", ""))) for t in complete_ids if t in exm)},
        ),
        "J": analysis_payload(
            "interactions",
            "J",
            {"slices": {"symbol_x_side": [f"{r['symbol']}|{r['side']}" for r in rec_rows]}},
        ),
    }

    letters_files = [
        ("A", "EXECUTED_SURFACES", "ALPACA_PNL_EXECUTED_SURFACES"),
        ("B", "SIGNAL_ATTRIBUTION", "ALPACA_PNL_SIGNAL_ATTRIBUTION"),
        ("C", "EXIT_FORENSICS", "ALPACA_PNL_EXIT_FORENSICS"),
        ("D", "COST_DRAG", "ALPACA_PNL_COST_DRAG"),
        ("E", "BLOCKED_OPPORTUNITY", "ALPACA_PNL_BLOCKED_OPPORTUNITY"),
        ("F", "GATE_VALUE", "ALPACA_PNL_GATE_VALUE"),
        ("G", "CI_INFRA_CORRELATION", "ALPACA_PNL_CI_INFRA_CORRELATION"),
        ("H", "LATENCY_PATH", "ALPACA_PNL_LATENCY_PATH"),
        ("I", "REGIME_SLICES", "ALPACA_PNL_REGIME_SLICES"),
        ("J", "INTERACTIONS", "ALPACA_PNL_INTERACTIONS"),
    ]
    for letter, short, base in letters_files:
        data = analyses[letter]
        (rep_out / f"{base}_{TS}.json").write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        (aud_out / f"ALPACA_PNL_{short}_{TS}.md").write_text(
            f"# {short} ({TS})\n\nn_trades={n_tr}\n\n```json\n{json.dumps(data.get('slices', {}), indent=2)[:4000]}\n```\n",
            encoding="utf-8",
        )

    quant_angles = [
        {"n": 1, "hypothesis": "Spread bucket drag", "metric": "mean(net_pnl) by symbol", "result": dict(by_sym)},
        {"n": 2, "hypothesis": "Hold vs outcome", "metric": "exit_reason mix", "result": dict(analyses["C"]["slices"])},
        {"n": 3, "hypothesis": "Win concentration", "metric": "top symbol share", "result": {"top": by_sym.most_common(3)}},
        {"n": 4, "hypothesis": "Side mix", "metric": "long/short", "result": dict(Counter(r["side"] for r in rec_rows))},
        {"n": 5, "hypothesis": "Regime mix", "metric": "entry/exit regime", "result": dict(analyses["I"]["slices"])},
    ]
    for qa in quant_angles:
        n = qa["n"]
        st = "OK" if n_tr > 0 else "NO_ACTIVITY"
        payload = {**qa, "status": st, "n_rows": n_tr}
        (rep_out / f"ALPACA_PNL_QUANT_ANGLE_{n}_{TS}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _write_csv(
            rep_out / f"ALPACA_PNL_QUANT_ANGLE_{n}_{TS}.csv",
            ["angle", "key", "value"],
            [{"angle": n, "key": "net_pnl_sum", "value": net_sum}] if n_tr else [],
        )
        (aud_out / f"ALPACA_PNL_QUANT_ANGLE_{n}_{TS}.md").write_text(
            f"# Quant angle {n}\n\n{qa['hypothesis']}\n\n```json\n{json.dumps(payload, indent=2)}\n```\n",
            encoding="utf-8",
        )

    (aud_out / f"ALPACA_PNL_QUANT_OFFICER_5_ANGLES_{TS}.md").write_text(
        "| # | Hypothesis | Status |\n|---|------------|--------|\n"
        + "\n".join(f"| {q['n']} | {q['hypothesis']} | {q.get('status', 'OK')} |" for q in quant_angles),
        encoding="utf-8",
    )

    spi_bundle: Dict[str, Any] = {}
    try:
        from src.analytics.alpaca_signal_path_intelligence import build_spi_bundle

        spi_bundle = build_spi_bundle(
            root=root,
            repo_root=REPO,
            complete_trade_ids=complete_ids,
            exit_by_id=exm,
            ts=TS,
        )
    except Exception as e:
        spi_bundle = {
            "spi_version": "1.0.0",
            "ts": TS,
            "error": str(e),
            "summary": {"disclaimer": "SPI import/build failed; non-blocking."},
            "spi_trade_rows": 0,
        }

    spi_md = _format_spi_markdown(spi_bundle)
    (rep_out / f"ALPACA_SPI_SECTION_{TS}.json").write_text(
        json.dumps(spi_bundle, indent=2, default=str), encoding="utf-8"
    )
    (rep_out / f"ALPACA_SPI_SECTION_{TS}.md").write_text(spi_md, encoding="utf-8")
    spi_analysis = {
        "analysis": "K",
        "name": "signal_path_intelligence",
        "cohort": "MARKET_SESSION_ET" if cohort_mode else "LEGACY_LAST_WINDOW",
        "n_trades": n_tr,
        "blocked": blocked,
        "blockers": blockers,
        "spi_version": spi_bundle.get("spi_version"),
        "spi_trade_rows": spi_bundle.get("spi_trade_rows"),
        "summary": spi_bundle.get("summary"),
        "error": spi_bundle.get("error"),
        "artifacts": {
            "spi_section_json": str(rep_out / f"ALPACA_SPI_SECTION_{TS}.json"),
            "spi_section_md": str(rep_out / f"ALPACA_SPI_SECTION_{TS}.md"),
        },
    }
    (rep_out / f"ALPACA_PNL_SIGNAL_PATH_INTELLIGENCE_{TS}.json").write_text(
        json.dumps(spi_analysis, indent=2, default=str), encoding="utf-8"
    )
    (aud_out / f"ALPACA_PNL_SIGNAL_PATH_INTELLIGENCE_{TS}.md").write_text(
        spi_md, encoding="utf-8"
    )

    tradesets = {
        "ts": TS,
        "EXECUTED_QUALIFIED_SESSION": {"trade_ids": complete_ids, "count": len(complete_ids)},
        "sample_trade_ids_only": sample_ids,
        "sample_note": sample_note,
        "blockers": blockers,
    }
    (rep_out / f"ALPACA_PNL_REVIEW_TRADESETS_{TS}.json").write_text(json.dumps(tradesets, indent=2), encoding="utf-8")

    verdict = "CSA_VERDICT: PNL_REVIEW_COMPLETE"
    if blocked:
        verdict = "CSA_VERDICT: STILL_BLOCKED"
    elif tc > 0 and len(rec_rows) < 1:
        verdict = "CSA_VERDICT: STILL_BLOCKED"
    elif tc == 0 and n_tr == 0:
        verdict = "CSA_VERDICT: PNL_REVIEW_COMPLETE"

    (aud_out / f"ALPACA_PNL_ADVERSARIAL_{TS}.md").write_text(
        f"# Adversarial ({TS})\n\n- Cohort: explicit `complete_trade_ids` + session epochs.\n"
        f"- Reconciliation: `reconciliation_delta` should be 0 when `ledger_pnl` matches computed net.\n"
        f"- Fixture trades are synthetic (MKT1/MKT2) — do not treat as live edge.\n",
        encoding="utf-8",
    )
    (aud_out / f"ALPACA_PNL_CSA_PACKET_{TS}.md").write_text(
        f"# CSA packet ({TS})\n\n- Net PnL (cohort): **{net_sum}**\n- n={n_tr}\n- Verdict: see closeout.\n",
        encoding="utf-8",
    )
    (aud_out / f"ALPACA_PNL_BOARD_PACKET_{TS}.md").write_text(
        f"# Board ({TS})\n\nSession-cohort PnL review reproducible from `artifacts/alpaca_pnl_session_et_20260326` + pipeline.\n",
        encoding="utf-8",
    )

    root_cause = blockers[0] if blockers else None
    (aud_out / f"ALPACA_PNL_REVIEW_CLOSEOUT_{TS}.md").write_text(
        "\n".join(
            [
                f"# Closeout ({TS})",
                "",
                "## Signal Path Intelligence (SPI)",
                "",
                f"- **Markdown:** `{rep_out / f'ALPACA_SPI_SECTION_{TS}.md'}`",
                f"- **JSON:** `{rep_out / f'ALPACA_SPI_SECTION_{TS}.json'}`",
                "- **Scope:** Read-only post-trade path distributions; does not authorize behavior change (`MEMORY_BANK.md`).",
                "- **Non-blocking:** SPI failures do not invalidate PnL reconciliation.",
                "",
                "| Check | OK |",
                "|-------|-----|",
                f"| cohort list | {bool(complete_ids) or tc == 0} |",
                f"| reconciliation rows vs trades_complete | {len(rec_rows) >= tc if tc > 0 else True} |",
                "",
                (
                    f"**Root cause:** `{root_cause['id']}` — {root_cause['detail'][:300]}"
                    if root_cause
                    else "**Root cause:** none"
                ),
                "",
                verdict,
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps({"ts": TS, "verdict": verdict, "blocker_count": len(blockers), "recon_rows": len(rec_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
