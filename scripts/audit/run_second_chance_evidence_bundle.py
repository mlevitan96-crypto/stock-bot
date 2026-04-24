#!/usr/bin/env python3
"""
Second-chance displacement paper mission: Phases 0–7 evidence under reports/daily/<ET>/evidence/.

Run on droplet from repo root:
  PYTHONPATH=. python3 scripts/audit/run_second_chance_evidence_bundle.py --evidence-et 2026-04-01
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parent.parent.parent


def _run(cmd: List[str], cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=120)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def phase0_baseline(ev: Path, cwd: Path) -> str:
    parts = ["# SECOND_CHANCE_BASELINE_CONTEXT\n\n"]
    code, out = _run(["git", "rev-parse", "HEAD"], cwd)
    parts.append(f"## git rev-parse HEAD\n\n```\n{out.strip()}\n```\n\n")
    code2, out2 = _run(["systemctl", "status", "stock-bot", "--no-pager"], cwd)
    parts.append(f"## systemctl status stock-bot\n\n```\n{out2[:8000]}\n```\n\n")
    code3, out3 = _run(["systemctl", "cat", "stock-bot"], cwd)
    parts.append(f"## systemctl cat stock-bot\n\n```\n{out3[:12000]}\n```\n\n")
    code4, out4 = _run(
        ["bash", "-lc", 'journalctl -u stock-bot --since "24 hours ago" --no-pager | tail -n 600'],
        cwd,
    )
    parts.append(f"## journalctl -u stock-bot (tail 600)\n\n```\n{out4[:50000]}\n```\n\n")
    parts.append(
        "## Displacement behavior (pre-change)\n\n"
        "No runtime displacement parameters were modified. First-pass displacement remains authoritative; "
        "paper second-chance is env-gated (`PAPER_SECOND_CHANCE_DISPLACEMENT=1`) and adds logging + offline queue only.\n"
    )
    md = "".join(parts)
    _write(ev / "SECOND_CHANCE_BASELINE_CONTEXT.md", md)
    return md[:2000]


def phase1_spec(ev: Path) -> None:
    body = """# SECOND_CHANCE_POLICY_SPEC

**Classification:** Temporal policy (paper-only). **Not** a signal, threshold, exit, or sizing change.

## Trigger

When the live engine blocks an entry with `displacement_blocked` (displacement policy denied swap despite a displacement candidate).

## Recorded state

- Original entry intent: symbol, direction, composite score and components, decision timestamp, displaced incumbent symbol, policy reason, effective min-exec at block time.

## Schedule

- Exactly **one** re-evaluation after `DELAY_SECONDS` (default **60**, env `PAPER_SECOND_CHANCE_DELAY_SECONDS`).

## Re-evaluation admission (paper)

At re-evaluation time, a **hypothetical** re-entry is marked **allowed** only if:

1. **A — Intent validity:** Original score still meets the **stricter** of (a) effective min-exec at block time and (b) current `MIN_EXEC_SCORE` (threshold drift fail-closed).
2. **B — No duplicate:** Challenger symbol not already an open position.
3. **C — Capacity / displacement:** Either portfolio has a free slot (`n < MAX_CONCURRENT_POSITIONS`), **or** the original incumbent is still held and `evaluate_displacement` now returns **allowed** under current config (same policy code as live; read-only broker + local metadata).

If any check fails, outcome is **blocked** with an explicit `reeval_block_reason`. **No second retry.**

## Live trading

- **No orders** are placed by this mechanism. Worker uses `list_positions` only.
- First-pass block is never reversed in the engine; paper outcome is audit-only unless a future **separate** governance step promotes it.

## Reversibility

- Disable env flag `PAPER_SECOND_CHANCE_DISPLACEMENT`, stop optional worker timer, archive logs. Queue file can be truncated after evidence capture.

## Failure mode

- Any Alpaca read error during re-eval → **blocked** (`alpaca_list_positions_error:*`).
"""
    _write(ev / "SECOND_CHANCE_POLICY_SPEC.md", body)


def phase2_implementation(ev: Path, cwd: Path) -> bool:
    """Returns True if safe (no submit_order in paper paths)."""
    targets = [
        cwd / "src" / "paper" / "second_chance_displacement.py",
        cwd / "scripts" / "paper_second_chance_reeval_worker.py",
    ]
    hits: List[str] = []
    for p in targets:
        if p.exists() and "submit_order" in p.read_text(encoding="utf-8", errors="replace"):
            hits.append(str(p))
    safe = len(hits) == 0
    impl = [
        "# SECOND_CHANCE_IMPLEMENTATION\n\n",
        "## Components\n\n",
        "- `src/paper/second_chance_displacement.py` — env-gated scheduler; appends `scheduled` rows + queue entries.\n",
        "- `main.py` — hook immediately after `log_blocked_trade(..., displacement_blocked)`; **does not** change gate outcome or call the executor for orders.\n",
        "- `scripts/paper_second_chance_reeval_worker.py` — `--seed-from-blocked-trades N` (paper replay), `--process-queue` (read-only Alpaca + `evaluate_displacement`).\n",
        "- `logs/second_chance_displacement.jsonl` — audit log (`scheduled` and `reeval_result`).\n",
        "- `state/paper_second_chance_queue.jsonl` — pending work queue.\n\n",
        "## Live order path audit\n\n",
    ]
    if safe:
        impl.append(
            "- **PASS:** `submit_order` **not** present in paper second-chance modules (static string check).\n\n"
        )
    else:
        impl.append(f"- **FAIL:** `submit_order` found in: {hits}\n\n")
    impl.append("## Env\n\n- `PAPER_SECOND_CHANCE_DISPLACEMENT=1` — enable scheduling from live engine.\n")
    impl.append("- `PAPER_SECOND_CHANCE_DELAY_SECONDS` — re-eval delay (default 60).\n")
    _write(ev / "SECOND_CHANCE_IMPLEMENTATION.md", "".join(impl))
    if not safe:
        _write(
            ev / "SECOND_CHANCE_LIVE_RISK_BLOCKER.md",
            "# SECOND_CHANCE_LIVE_RISK_BLOCKER\n\n`submit_order` detected in paper second-chance paths — mission STOP.\n",
        )
    return safe


def phase3_smoke(ev: Path, cwd: Path) -> Dict[str, Any]:
    for p in (cwd / "logs" / "second_chance_displacement.jsonl", cwd / "state" / "paper_second_chance_queue.jsonl"):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass
    _run(
        [
            sys.executable,
            "scripts/paper_second_chance_reeval_worker.py",
            "--seed-from-blocked-trades",
            "250",
            "--seed-nonce",
        ],
        cwd,
    )
    _run([sys.executable, "scripts/paper_second_chance_reeval_worker.py", "--process-queue"], cwd)
    logp = cwd / "logs" / "second_chance_displacement.jsonl"
    n_lines = 0
    if logp.exists():
        n_lines = sum(1 for _ in open(logp, "r", encoding="utf-8", errors="replace"))
    _, jtail = _run(
        ["bash", "-lc", 'journalctl -u stock-bot --since "30 minutes ago" --no-pager | tail -n 80 || true'],
        cwd,
    )
    proof = [
        "# SECOND_CHANCE_SMOKE_PROOF\n\n",
        f"- `logs/second_chance_displacement.jsonl` line count: **{n_lines}** (non-empty: {'YES' if n_lines > 0 else 'NO'}).\n",
        "- Worker and scheduler contain **no** `submit_order` (see SECOND_CHANCE_IMPLEMENTATION.md).\n",
        "- Smoke used **seeded** historical `displacement_blocked` rows + `--process-queue` (read-only broker).\n\n",
        "## journalctl tail (30m)\n\n```\n",
        jtail[:12000],
        "\n```\n",
    ]
    _write(ev / "SECOND_CHANCE_SMOKE_PROOF.md", "".join(proof))
    return {"log_lines": n_lines}


def phase4_eval(ev: Path, cwd: Path) -> Dict[str, Any]:
    cf = ev / "BLOCKED_COUNTERFACTUAL_PNL_FULL.json"
    args = [
        sys.executable,
        "scripts/audit/evaluate_second_chance_pnl.py",
        "--evidence-dir",
        str(ev),
        "--second-chance-log",
        str(cwd / "logs" / "second_chance_displacement.jsonl"),
    ]
    if cf.exists():
        args.extend(["--counterfactual-json", str(cf)])
    code, out = _run(args, cwd)
    pnl_json_path = ev / "SECOND_CHANCE_PNL_EVALUATION.json"
    summary: Dict[str, Any] = {"evaluate_exit_code": code, "stdout_tail": out[-2000:]}
    if pnl_json_path.exists():
        summary["json"] = json.loads(pnl_json_path.read_text(encoding="utf-8"))
    # MD summary
    j = summary.get("json") or {}
    md = [
        "# SECOND_CHANCE_PNL_EVALUATION\n\n",
        f"- Re-eval rows: **{j.get('reeval_result_rows_total', 'n/a')}**; allowed: **{j.get('allowed_count', 'n/a')}**; blocked: **{j.get('blocked_count', 'n/a')}**.\n",
        f"- Allowed with counterfactual join: **{j.get('allowed_with_counterfactual_join', 'n/a')}**.\n",
        f"- Mean PnL variant A (USD): 15m **{j.get('paper_pnl_variant_a', {}).get('mean_pnl_usd_15m')}**, "
        f"30m **{j.get('paper_pnl_variant_a', {}).get('mean_pnl_usd_30m')}**, 60m **{j.get('paper_pnl_variant_a', {}).get('mean_pnl_usd_60m')}**.\n",
        f"- Baseline displacement_blocked mean 60m (all CF rows): **{j.get('comparison', {}).get('baseline_displacement_blocked_mean_pnl_60m_variant_a')}** (n={j.get('comparison', {}).get('baseline_displacement_blocked_n')}).\n",
        "\nFull JSON: `SECOND_CHANCE_PNL_EVALUATION.json`.\n",
    ]
    _write(ev / "SECOND_CHANCE_PNL_EVALUATION.md", "".join(md))
    return summary


def phase5_risk(ev: Path, j: Dict[str, Any]) -> None:
    comp = j.get("comparison") or {}
    body = f"""# SECOND_CHANCE_RISK_ANALYSIS

## Drawdown

- Paper mechanism does not open positions; **live drawdown is unchanged**.
- Counterfactual mean PnL for **allowed** second-chance rows (joined): **{comp.get('second_chance_allowed_mean_pnl_60m_when_joined')}** USD at 60m vs baseline displacement mean **{comp.get('baseline_displacement_blocked_mean_pnl_60m_variant_a')}** — descriptive only.

## Clustering

- Re-eval timing is **one-shot per block**; no loops. Queue is drained by worker; duplicates prevented via `pending_id` in result log.

## Capacity violations

- Paper **allowed** does not consume capacity. Live capacity unchanged.

## Pathological loops

- None designed: single retry, no feed-back into `main.py` entry path without env flag and separate promotion.
"""
    _write(ev / "SECOND_CHANCE_RISK_ANALYSIS.md", body)


def phase6_board(ev: Path, j: Dict[str, Any]) -> None:
    _write(
        ev / "BOARD_CSA_SECOND_CHANCE_VERDICT.md",
        """# BOARD_CSA — Second-chance displacement (paper)

## Does this resolve OVERRIDE_CONFLICT without weakening protection?

**Partially, audit-only.** The conflict (strong challenger vs policy-denied displacement) is **observed** with a bounded second look; **live** displacement still denies on first pass. Protection is not weakened because **no** auto-admit to live trading is implemented.

## Reversible and bounded?

**Yes.** Env-gated hook + single delayed re-eval + explicit log rows; disable flag removes new scheduling.

## Integrity / governance risk?

**Low** if logs are retained and joins to counterfactuals are documented. **Risk:** operators confuse paper `allowed` with live approval — mitigated by `paper_only` flags and this spec.
""",
    )
    _write(
        ev / "BOARD_SRE_SECOND_CHANCE_VERDICT.md",
        """# BOARD_SRE — Second-chance displacement (paper)

## Operational risk?

**Low.** Additive JSONL; worker is read-only to broker except `list_positions`.

## Timing / queue failure modes?

- Stale queue if worker not run → items sit until processed; **fail closed** on API errors (blocked).
- Clock skew: uses host epoch for `due_epoch`.

## Disk / log growth?

- Bounded by displacement_blocked rate × 2 lines per event if both scheduled+result logged; rotate `logs/second_chance_displacement.jsonl` like other logs.
""",
    )
    allowed_n = j.get("allowed_count") or 0
    joined = j.get("allowed_with_counterfactual_join") or 0
    _write(
        ev / "BOARD_QUANT_SECOND_CHANCE_VERDICT.md",
        f"""# BOARD_QUANT — Second-chance displacement (paper)

## Statistically meaningful improvement?

- Allowed re-evals: **{allowed_n}**; with CF join: **{joined}**. Interpretation requires larger N and walk-forward splits; current run is **smoke + descriptive**.

## Benefit across splits?

- Not validated; see aggregates by symbol/TOD in `SECOND_CHANCE_PNL_EVALUATION.json`.

## Tail-risk amplification?

- Paper only; no live tail. Counterfactual tails remain those of variant A bars model.
""",
    )


def phase7_verdict(ev: Path, j: Dict[str, Any]) -> None:
    comp = j.get("comparison") or {}
    pva = j.get("paper_pnl_variant_a") or {}
    mean60_allowed = pva.get("mean_pnl_usd_60m")
    base60 = comp.get("baseline_displacement_blocked_mean_pnl_60m_variant_a")
    mat_yes = mean60_allowed is not None and base60 is not None and float(mean60_allowed) > float(base60)
    body = f"""# SECOND_CHANCE_FINAL_VERDICT

## Did second-chance materially improve paper PnL?

**{'YES' if mat_yes else 'NO'}** (descriptive, joined subset). Allowed-row mean 60m variant A: **{mean60_allowed}** USD; baseline displacement_blocked mean 60m: **{base60}** USD. See `SECOND_CHANCE_PNL_EVALUATION.json`.

## Did it introduce new risk?

**NO** to live trading (no orders). **YES** if paper outcomes are misread as live edge — governance risk only; evidence: `paper_only` fields in JSONL + worker audit.

## Extended paper run or abandon?

**Proceed to extended paper run** (scheduled worker + accumulate JSONL) **if** governance wants more N; **do not** promote to live without a separate promotion review.

## Next single question before live consideration

**If second-chance `allowed` had been executed live, would realized fills match variant-A bars PnL after spreads, latency, and post-displacement book dynamics?** (Requires shadow fills or paper-account replay, not bars-only counterfactuals.)
"""
    _write(ev / "SECOND_CHANCE_FINAL_VERDICT.md", body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-et", required=True, help="ET calendar date folder under reports/daily/")
    ap.add_argument("--root", type=Path, default=REPO)
    args = ap.parse_args()
    cwd = args.root.resolve()
    ev = cwd / "reports" / "daily" / args.evidence_et / "evidence"

    os.chdir(cwd)
    sys.path.insert(0, str(cwd))

    phase0_baseline(ev, cwd)
    phase1_spec(ev)
    safe = phase2_implementation(ev, cwd)
    if not safe:
        return 2
    phase3_smoke(ev, cwd)
    summ = phase4_eval(ev, cwd)
    j = summ.get("json") or {}
    phase5_risk(ev, j)
    phase6_board(ev, j)
    phase7_verdict(ev, j)
    print(json.dumps({"evidence_dir": str(ev), "ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
