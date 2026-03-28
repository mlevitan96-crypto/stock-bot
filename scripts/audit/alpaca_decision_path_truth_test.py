#!/usr/bin/env python3
"""
Alpaca decision-path truth test: dry replay via production telemetry builders + test sink.

Constraints: no orders, no StrategyEngine, no production run.jsonl writes.
Test sink only: logs/test_run.jsonl (under repo root; logs/ is gitignored).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _ts_suffix() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def _et_date_str() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _test_run_path(root: Path) -> Path:
    return root / "logs" / "test_run.jsonl"


def _write_test_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = {**record, "ts": datetime.now(timezone.utc).isoformat()}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, default=str) + "\n")


def _make_test_write_run(sink: Path) -> Callable[[str, Dict[str, Any]], None]:
    def _w(name: str, rec: Dict[str, Any]) -> None:
        if name != "run":
            raise RuntimeError(f"unexpected jsonl name {name!r} (test harness expects run only)")
        _write_test_jsonl(sink, rec)

    return _w


def _load_entry_decision_made_rows(path: Path) -> List[dict]:
    rows: List[dict] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event_type") == "entry_decision_made":
                rows.append(rec)
    return rows


def _production_trace_entered(
    symbol: str,
    side: str,
    score: float,
    comps: Dict[str, Any],
    cluster: Dict[str, Any],
    frozen_ts: str,
) -> Dict[str, Any]:
    from telemetry.decision_intelligence_trace import (
        append_gate_result,
        build_initial_trace,
        set_final_decision,
    )

    tr = build_initial_trace(symbol, side, score, comps, cluster, ts=frozen_ts, cycle_id=None, engine=None)
    append_gate_result(tr, "score_gate", True)
    append_gate_result(tr, "capacity_gate", True)
    append_gate_result(tr, "risk_gate", True)
    append_gate_result(tr, "momentum_gate", True)
    set_final_decision(tr, "entered", "all_gates_passed", [])
    return tr


def phase1_snapshot(root: Path, evidence_dir: Path, ts: str) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out = evidence_dir / f"ALPACA_DECISION_SNAPSHOT_{ts}.md"
    now_utc = datetime.now(timezone.utc).isoformat()
    strat = root / "config" / "strategies.yaml"
    gov = root / "config" / "strategy_governance.json"
    strat_head = strat.read_text(encoding="utf-8", errors="replace")[:1200] if strat.is_file() else "(missing)"
    gov_head = gov.read_text(encoding="utf-8", errors="replace")[:800] if gov.is_file() else "(missing)"
    snap = {
        "captured_utc": now_utc,
        "symbol": "TESTPATH",
        "reference_bid_ask_mid": 100.25,
        "indicator_stub_atr14": 1.05,
        "indicator_stub_rsi14": 52.3,
        "regime_label": "mixed",
        "policy_config_note": "Frozen read-only snippets from repo config below; not live market feed.",
    }
    body = f"""# Alpaca decision snapshot (frozen, dry-run)

**UTC:** {now_utc}  
**Evidence TS:** `{ts}`

## Snapshot JSON (decision inputs for replay)

```json
{json.dumps(snap, indent=2)}
```

## Policy / config excerpts (read-only)

### strategies.yaml (prefix)

```
{strat_head}
```

### strategy_governance.json (prefix)

```
{gov_head}
```

## Isolation

- No broker calls. No `main.py` engine. Snapshot is for documentation + replay inputs only.
"""
    out.write_text(body, encoding="utf-8")
    return out


def phase2_replay_positive(root: Path, sink: Path, frozen_ts: str) -> Dict[str, Any]:
    from telemetry.alpaca_entry_decision_made_emit import emit_entry_decision_made

    if sink.exists():
        sink.unlink()
    cluster = {
        "direction": "bullish",
        "strategy_id": "equity_v2_dry",
        "composite_meta": {
            "policy_id": "alpaca_paper_truth_test",
            "components": {"momentum": 1.1, "whale_flow_strength": 0.4},
            "component_contributions": {"momentum": 0.7, "whale_flow_strength": 0.3},
        },
    }
    comps = {"momentum": 1.1, "whale_flow_strength": 0.4}
    trace = _production_trace_entered("TESTPATH", "buy", 2.5, comps, cluster, frozen_ts)
    ct = "TESTPATH|LONG|dry_replay_key"
    tid = "open_TESTPATH_2026-03-28T12:00:00+00:00"
    emit_entry_decision_made(
        _make_test_write_run(sink),
        symbol="TESTPATH",
        side="buy",
        score=2.5,
        comps=comps,
        cluster=cluster,
        intelligence_trace=trace,
        canonical_trade_id=ct,
        trade_id_open=tid,
        decision_event_id="dry-de-1",
        time_bucket_id="dry-tb-1",
        symbol_normalized="TESTPATH",
        phase2_enabled=True,
    )
    rows = _load_entry_decision_made_rows(sink)
    assert len(rows) == 1, rows
    r0 = rows[0]
    assert r0.get("entry_intent_synthetic") is False
    assert r0.get("entry_intent_source") == "live_runtime"
    assert r0.get("entry_intent_status") == "OK"
    return {"row": r0, "cluster": cluster, "comps": comps, "trace_keys": list(trace.keys())}


def phase4_negative(root: Path, sink: Path) -> Dict[str, Any]:
    from telemetry.alpaca_entry_decision_made_emit import emit_entry_decision_made

    cluster = {"direction": "bullish", "composite_meta": {}}
    emit_entry_decision_made(
        _make_test_write_run(sink),
        symbol="TESTPATH",
        side="buy",
        score=None,
        comps={},
        cluster=cluster,
        intelligence_trace=None,
        canonical_trade_id="NEG|LONG|1",
        trade_id_open="open_TESTPATH_2026-03-28T12:01:00+00:00",
        decision_event_id="dry-de-neg",
        time_bucket_id="dry-tb-neg",
        symbol_normalized="TESTPATH",
        phase2_enabled=True,
    )
    rows = _load_entry_decision_made_rows(sink)
    last = rows[-1]
    assert last.get("entry_intent_status") != "OK"
    assert "MISSING" in str(last.get("entry_intent_status") or "")
    return {"row": last}


def phase3_audit(root: Path, sink: Path) -> Dict[str, Any]:
    from telemetry.alpaca_entry_decision_made_emit import (
        audit_entry_decision_made_row_live_truth_present,
        audit_entry_decision_made_row_ok,
        score_entry_decision_made_row,
    )
    from telemetry.alpaca_strict_completeness_gate import _pick_best_entry_decision_made

    rows = _load_entry_decision_made_rows(sink)
    results = []
    for r in rows:
        results.append(
            {
                "trade_id": r.get("trade_id"),
                "status": r.get("entry_intent_status"),
                "audit_ok": audit_entry_decision_made_row_ok(r),
                "live_truth": audit_entry_decision_made_row_live_truth_present(r),
                "score_tuple": list(score_entry_decision_made_row(r)),
            }
        )
    ok_row = next((x for x in rows if x.get("entry_intent_status") == "OK"), None)
    bad_row = next((x for x in rows if x.get("entry_intent_status") != "OK"), None)
    synth = deepcopy(ok_row) if ok_row else {}
    if synth:
        synth = dict(synth)
        synth["strict_backfilled"] = True
        synth["strict_backfill_trade_id"] = "synthetic_injection"
    synth_fail = audit_entry_decision_made_row_ok(synth) is False and audit_entry_decision_made_row_live_truth_present(synth) is False
    aliases = {ok_row.get("canonical_trade_id"), ok_row.get("trade_key")} if ok_row else set()
    aliases.discard(None)
    dup_poor = dict(ok_row) if ok_row else {}
    dup_rich = dict(ok_row) if ok_row else {}
    if ok_row:
        dup_poor = json.loads(json.dumps(ok_row))
        dup_rich = json.loads(json.dumps(ok_row))
        # Poorer = explicit live blocker; richer = full OK — selection must prefer OK (tier 2 > tier 1).
        dup_poor["entry_intent_status"] = "MISSING_INTENT_BLOCKER"
        dup_poor["entry_intent_error"] = "harness_injected_poor"
        dup_poor["entry_score_total"] = 1.0
        dup_poor["entry_score_components"] = {"_blocked": True, "reason": "harness"}
        dup_poor["signal_trace"] = {"policy_anchor": "x", "_blocker": True, "reason": "harness"}
        dup_rich["entry_score_total"] = 2.5
        dup_rich["entry_score_components"] = {"momentum": 1.5, "whale_flow_strength": 1.0}
    pair = [dup_poor, dup_rich] if ok_row else []
    best = _pick_best_entry_decision_made(pair, aliases, "TESTPATH", str(ok_row.get("trade_id"))) if pair else None
    best_is_rich = best and best.get("entry_intent_status") == "OK" and best.get("entry_score_total") == 2.5 if ok_row else True
    return {
        "per_row": results,
        "synthetic_injection_fails": synth_fail,
        "best_row_prefers_richer": bool(best_is_rich),
        "blocker_fails_strict_ok": audit_entry_decision_made_row_ok(bad_row) is False if bad_row else True,
    }


def phase5_no_mutation(root: Path, frozen_ts: str) -> Dict[str, Any]:
    from telemetry.alpaca_entry_decision_made_emit import build_entry_decision_made_record, emit_entry_decision_made

    cluster = {
        "direction": "bullish",
        "strategy_id": "equity_v2_dry",
        "composite_meta": {
            "policy_id": "alpaca_paper_truth_test",
            "components": {"momentum": 1.1, "whale_flow_strength": 0.4},
            "component_contributions": {"momentum": 0.7, "whale_flow_strength": 0.3},
        },
    }
    comps = {"momentum": 1.1, "whale_flow_strength": 0.4}
    trace = _production_trace_entered("TESTPATH", "buy", 2.5, comps, cluster, frozen_ts)
    kwargs = dict(
        symbol="TESTPATH",
        side="buy",
        score=2.5,
        comps=comps,
        cluster=cluster,
        intelligence_trace=trace,
        canonical_trade_id="NM|LONG|1",
        trade_id_open="open_TESTPATH_2026-03-28T12:02:00+00:00",
        decision_event_id="nm-de",
        time_bucket_id="nm-tb",
        symbol_normalized="TESTPATH",
    )
    a = build_entry_decision_made_record(**kwargs)
    b = build_entry_decision_made_record(**kwargs)

    def _norm(d: Dict[str, Any]) -> Dict[str, Any]:
        x = json.loads(json.dumps(d, default=str))
        st = x.get("signal_trace")
        if isinstance(st, dict) and isinstance(st.get("intelligence_trace"), dict):
            it = st["intelligence_trace"]
            it.pop("intent_id", None)
        return x

    identical = _norm(a) == _norm(b)
    sink = _test_run_path(root)
    sz_before = sink.stat().st_size if sink.is_file() else 0
    emit_entry_decision_made(_make_test_write_run(sink), phase2_enabled=False, **kwargs)
    sz_after_disabled = sink.stat().st_size if sink.is_file() else 0
    no_append_on_disabled = sz_after_disabled == sz_before
    return {
        "builds_identical_normalized": identical,
        "no_sink_append_when_telemetry_disabled": no_append_on_disabled,
    }


def _sha256_file(p: Path) -> Optional[str]:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--evidence-dir", type=Path, default=None, help="default: reports/daily/<ET>/evidence")
    args = ap.parse_args()
    root = args.root.resolve()
    ts = _ts_suffix()
    et = _et_date_str()
    evidence_dir = args.evidence_dir or (root / "reports" / "daily" / et / "evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sink = _test_run_path(root)
    run_jsonl = root / "logs" / "run.jsonl"
    hash_before = _sha256_file(run_jsonl)

    frozen_ts = datetime.now(timezone.utc).isoformat()
    p1 = phase1_snapshot(root, evidence_dir, ts)
    p2 = phase2_replay_positive(root, sink, frozen_ts)
    p4 = phase4_negative(root, sink)
    p3 = phase3_audit(root, sink)
    p5 = phase5_no_mutation(root, frozen_ts)
    hash_after = _sha256_file(run_jsonl)

    audit_pass = (
        p3["synthetic_injection_fails"]
        and p3["best_row_prefers_richer"]
        and p3["blocker_fails_strict_ok"]
        and any(r["audit_ok"] for r in p3["per_row"] if r["status"] == "OK")
        and all(not r["audit_ok"] for r in p3["per_row"] if r["status"] != "OK")
    )
    mutation_pass = p5["builds_identical_normalized"] and p5["no_sink_append_when_telemetry_disabled"]
    prod_clean = hash_before == hash_after

    csa_ok = audit_pass and mutation_pass and prod_clean
    sre_ok = prod_clean and sink.is_file()

    p_audit = evidence_dir / f"ALPACA_DECISION_PATH_AUDIT_{ts}.md"
    p_audit.write_text(
        "\n".join(
            [
                f"# Alpaca decision-path audit (test sink)",
                "",
                f"**Sink:** `{sink}`",
                "",
                "## Per-row production audits",
                "",
                "```json",
                json.dumps(p3, indent=2, default=str),
                "```",
                "",
                "## Production run.jsonl integrity",
                "",
                f"- `run.jsonl` sha256 before: `{hash_before}`",
                f"- `run.jsonl` sha256 after: `{hash_after}`",
                f"- **Unchanged:** {prod_clean}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    p_neg = evidence_dir / f"ALPACA_DECISION_PATH_NEGATIVE_TEST_{ts}.md"
    p_neg.write_text(
        "\n".join(
            [
                "# Alpaca decision-path negative test",
                "",
                "Injected replay with `score=None`, empty comps, no intelligence_trace → `MISSING_INTENT_BLOCKER`.",
                "",
                "```json",
                json.dumps(p4["row"], indent=2, default=str),
                "```",
                "",
                f"- **audit_entry_decision_made_row_ok:** False (expected)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    p_nm = evidence_dir / f"ALPACA_DECISION_PATH_NO_MUTATION_{ts}.md"
    p_nm.write_text(
        "\n".join(
            [
                "# Alpaca decision-path no-mutation guard",
                "",
                "```json",
                json.dumps(p5, indent=2, default=str),
                "```",
                "",
                f"- **Normalized builds identical:** {p5['builds_identical_normalized']}",
                f"- **No test sink append when phase2_enabled=False:** {p5['no_sink_append_when_telemetry_disabled']}",
                f"- **Production run.jsonl unchanged:** {prod_clean}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    p2_doc = evidence_dir / f"ALPACA_DECISION_PATH_REPLAY_POSITIVE_{ts}.md"
    p2_doc.write_text(
        "\n".join(
            [
                "# Alpaca dry decision replay (positive)",
                "",
                "Production path: `telemetry.decision_intelligence_trace` (build_initial_trace + gates + set_final_decision) "
                "then `emit_entry_decision_made` with test `write_run` → `logs/test_run.jsonl` only.",
                "",
                "## Emitted row (summary)",
                "",
                "```json",
                json.dumps(
                    {
                        k: p2["row"].get(k)
                        for k in (
                            "event_type",
                            "entry_intent_synthetic",
                            "entry_intent_source",
                            "entry_intent_status",
                            "entry_score_total",
                            "signal_trace",
                            "entry_score_components",
                        )
                    },
                    indent=2,
                    default=str,
                ),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    csa_verdict = "CSA_DECISION_PATH_TRUTH_CONFIRMED" if csa_ok else "CSA_DECISION_PATH_BLOCKED"
    sre_verdict = "SRE_DECISION_PATH_SAFE" if sre_ok else "SRE_DECISION_PATH_UNSAFE"
    (evidence_dir / f"ALPACA_CSA_DECISION_PATH_FINAL_VERDICT_{ts}.md").write_text(
        f"# CSA decision-path final verdict\n\n**{csa_verdict}**\n\n"
        f"- Audit pass: {audit_pass}\n- No-mutation pass: {mutation_pass}\n- Production log untouched: {prod_clean}\n",
        encoding="utf-8",
    )
    (evidence_dir / f"ALPACA_SRE_DECISION_PATH_FINAL_VERDICT_{ts}.md").write_text(
        f"# SRE decision-path final verdict\n\n**{sre_verdict}**\n\n"
        f"- Test sink: `{sink}`\n- `run.jsonl` unchanged: {prod_clean}\n",
        encoding="utf-8",
    )

    summary = {
        "ts": ts,
        "evidence_dir": str(evidence_dir),
        "test_sink": str(sink),
        "csa_verdict": csa_verdict,
        "sre_verdict": sre_verdict,
        "audit_pass": audit_pass,
        "mutation_pass": mutation_pass,
        "production_run_jsonl_unchanged": prod_clean,
    }
    print(json.dumps(summary, indent=2))
    print("SUMMARY_JSON:" + json.dumps(summary, separators=(",", ":")))
    return 0 if csa_ok and sre_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
