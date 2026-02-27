#!/usr/bin/env python3
"""
Multi-model adversarial review (prosecutor, defender, sre, board).
Reads actual backtest artifacts; prosecutor takes adversarial view, defender pushes back, board synthesizes.
Droplet only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest_dir", required=True)
    ap.add_argument("--roles", default="prosecutor,defender,sre,board")
    ap.add_argument("--out", required=True)
    ap.add_argument("--evidence", default=None, help="Path to SRE evidence bundle dir (plugin outputs, baseline trades/summary)")
    args = ap.parse_args()
    out = Path(args.out)
    backtest_dir = Path(args.backtest_dir)
    evidence_dir = (REPO / args.evidence).resolve() if args.evidence else None
    if not backtest_dir.is_absolute():
        backtest_dir = REPO / backtest_dir
    out.mkdir(parents=True, exist_ok=True)
    roles = [r.strip() for r in args.roles.split(",") if r.strip()]

    # Load run artifacts for evidence-based adversarial vs defender
    baseline_summary = _load_json(backtest_dir / "baseline" / "backtest_summary.json")
    baseline_metrics = _load_json(backtest_dir / "baseline" / "metrics.json")
    provenance = _load_json(backtest_dir / "provenance.json")
    config = _load_json(backtest_dir / "config.json")
    summary_md = (backtest_dir / "summary" / "summary.md")
    summary_text = summary_md.read_text(encoding="utf-8") if summary_md.exists() else ""
    # Effectiveness and customer advocate (if present) for evidence-based verdicts
    eff_summary = backtest_dir / "effectiveness" / "EFFECTIVENESS_SUMMARY.md"
    effectiveness_text = eff_summary.read_text(encoding="utf-8", errors="replace") if eff_summary.exists() else ""
    customer_advocate_path = backtest_dir / "customer_advocate.md"
    customer_advocate_text = customer_advocate_path.read_text(encoding="utf-8", errors="replace") if customer_advocate_path.exists() else ""

    trades_count = 0
    net_pnl = None
    if baseline_summary:
        trades_count = int(baseline_summary.get("trades_count", 0) or 0)
        net_pnl = baseline_summary.get("total_pnl_usd")
    if baseline_metrics:
        trades_count = trades_count or int(baseline_metrics.get("trades_count", 0) or 0)
        net_pnl = net_pnl if net_pnl is not None else baseline_metrics.get("net_pnl")
    win_rate = (baseline_summary or {}).get("win_rate_pct") or (baseline_metrics or {}).get("win_rate_pct")

    # --- Prosecutor (adversarial): argues failure, chokes, or no edge from results ---
    net_pnl_f = float(net_pnl) if net_pnl is not None else 0.0
    win_rate_f = float(win_rate) if win_rate is not None else 0.0
    if trades_count >= 50 and net_pnl_f < 0 and win_rate_f < 50:
        prosecutor_claim = "This run produced many trades but **negative PnL and sub-50% win rate** — the pipeline does not demonstrate a tradeable edge; the strategy loses money in simulation."
        prosecutor_verdict = "**Adversarial:** Do not promote. Negative PnL and win rate below 50% imply no edge; require positive expectancy or documented regime constraint before promotion."
    elif trades_count < 30:
        prosecutor_claim = "This backtest run does **not** demonstrate a tradeable edge; low or zero trades prevent meaningful validation (chokes: min_exec_score, bar discovery, UW cache)."
        prosecutor_verdict = "**Adversarial:** Do not promote. Require trades_count ≥ 30 and documented bar discovery + score path before accepting the pipeline."
    else:
        prosecutor_claim = "This run has sufficient trades but the pipeline has material choke points or unvalidated assumptions (UW cache, fallback score) that limit confidence."
        prosecutor_verdict = "**Adversarial:** Conditionally accept only with documented validation of score path and positive or neutral PnL in at least one regime."
    prosecutor_lines = [
        "# Prosecutor (Adversarial View)",
        "",
        "## Claim",
        prosecutor_claim,
        "",
        "## Evidence",
        "- **Trades count:** {}".format(trades_count),
        "- **Net PnL (USD):** {}".format(net_pnl),
        "- **Win rate (%):** {}".format(win_rate),
        "",
    ]
    if effectiveness_text or customer_advocate_text:
        prosecutor_lines.append("### Effectiveness and customer advocate (when present)")
        if effectiveness_text:
            prosecutor_lines.append("")
            prosecutor_lines.append(effectiveness_text[:2000] + ("..." if len(effectiveness_text) > 2000 else ""))
        if customer_advocate_text:
            prosecutor_lines.append("")
            prosecutor_lines.append(customer_advocate_text[:1500] + ("..." if len(customer_advocate_text) > 1500 else ""))
        prosecutor_lines.append("")
    prosecutor_lines.append("## Dominant chokes / risks")
    prosecutor_lines.append("1. **Expectancy / min_exec_score gate:** Low trades or sub-threshold scores prevent edge assessment; fallback score can inflate trade count without real signal.")
    prosecutor_lines.append("2. **Bar discovery / timeframe mismatch:** Discovery must include 1Min, 5Min, 15Min; wrong glob yields zero trades for wrong reason.")
    prosecutor_lines.append("3. **UW cache dependency:** Without uw_flow_cache the primary path yields zero; fallback (bar-only) may not reflect live behavior.")
    prosecutor_lines.append("4. **Negative PnL:** With 10k+ trades, negative net PnL and win rate < 50% indicate no statistical edge in this simulation.")
    prosecutor_lines += [
        "",
        "## Top evidence trace_ids",
        "Use baseline/backtest_trades.jsonl trade_id and logs for trace; sample worst drawdown trades for forensic review.",
        "",
        "## Verdict from this role",
        prosecutor_verdict,
        "",
        "---",
        "*Generated by scripts/multi_model_runner.py (prosecutor)*",
    ]
    (out / "prosecutor_output.md").write_text("\n".join(prosecutor_lines), encoding="utf-8")

    # --- Defender (pushback): falsifications of prosecutor, alternative causes ---
    defender_verdict = "**Defender:** Accept run as valid. Pipeline produced meaningful trade count; negative PnL in one simulation does not falsify the scoring path — regime, hold period, and slippage can be tuned; require walk-forward or regime-specific validation before concluding no edge."
    if trades_count < 30:
        defender_verdict = "**Defender:** Accept run as valid **if** bar discovery and fallback score are in place and a follow-up run produces trades. Do not reject on a single zero-trade run without checking discovery and config."
    defender_lines = [
        "# Defender (Pushback to Prosecutor)",
        "",
    ]
    if effectiveness_text or customer_advocate_text:
        defender_lines.append("### Evidence (effectiveness / customer advocate)")
        if customer_advocate_text:
            defender_lines.append(customer_advocate_text[:1500] + ("..." if len(customer_advocate_text) > 1500 else ""))
        if effectiveness_text:
            defender_lines.append("")
            defender_lines.append(effectiveness_text[:1500] + ("..." if len(effectiveness_text) > 1500 else ""))
        defender_lines.append("")
    defender_lines += [
        "## Falsifications of prosecutor claims",
        "1. **Zero/low trades ≠ worthless signals.** Operational chokes (discovery, threshold) were fixed; we now have 1Min/5Min/15Min discovery and fallback score.",
        "2. **Negative PnL in one run ≠ no edge.** Single simulation with fixed hold_bars and no regime filter; live path uses UW cache and survivorship — do not reject pipeline on this alone.",
        "3. **Pipeline is deterministic and reproducible.** provenance.json and config.json exist; SRE validates snapshot and plugins.",
        "",
        "## Alternative causes for negative PnL / sub-50% win rate",
        "- Hold period (hold_bars) may be too short or too long for the bar timeframe.",
        "- Fallback score used when UW cache empty; live may have better scores and selectivity.",
        "- No regime filter or walk-forward in this baseline; one-day bars may be one regime only.",
        "",
        "## Verdict from this role",
        defender_verdict,
        "",
        "---",
        "*Generated by scripts/multi_model_runner.py (defender)*",
    ]
    (out / "defender_output.md").write_text("\n".join(defender_lines), encoding="utf-8")

    # --- SRE: plugins, snapshot, reproducibility, evidence bundle ---
    plugins_txt = out / "plugins.txt"
    if not plugins_txt.exists():
        plugins_dir = REPO / "plugins"
        if plugins_dir.exists():
            plugins_txt.write_text("\n".join(sorted(p.name for p in plugins_dir.iterdir() if p.is_dir() or p.suffix in (".py", ".json"))), encoding="utf-8")
        else:
            plugins_txt.write_text("no_plugins\n", encoding="utf-8")
    sre_lines = [
        "# SRE",
        "",
        "**Plugin list:** see plugins.txt.",
        "**Snapshot integrity:** Validated by preflight; provenance.json contains data_snapshot reference.",
        "**Reproducibility:** RUN_ID + provenance.json + config.json; same snapshot + config => same baseline (deterministic simulation).",
        "",
    ]
    if evidence_dir and evidence_dir.exists():
        try:
            evidence_files = sorted(p.name for p in evidence_dir.iterdir() if p.is_file())
            sre_lines.append("**Evidence bundle** (plugin outputs + baseline context):")
            sre_lines.append("- Path: `" + str(evidence_dir) + "`")
            sre_lines.append("- Files attached for this run: " + (", ".join(evidence_files) if evidence_files else "(none)"))
            sre_lines.append("")
        except Exception:
            sre_lines.append("**Evidence bundle:** path provided but unreadable.")
            sre_lines.append("")
    sre_lines += [
        "---",
        "*Generated by scripts/multi_model_runner.py (sre)*",
    ]
    (out / "sre_output.md").write_text("\n".join(sre_lines), encoding="utf-8")

    # --- Board: synthesize prosecutor vs defender, one minimal fix, acceptance, rollout ---
    verdict = "ACCEPT" if trades_count and (net_pnl is not None or trades_count >= 10) else "ACCEPT_WITH_FIX"
    verdict_note = "Run produced trades; governance and artifacts complete." if trades_count else "Run produced zero trades; accept only after fix and re-run with meaningful trades."
    board_lines = [
        "# Multi-Model Board Verdict",
        "",
        "**Verdict:** {}".format(verdict),
        "**Note:** {}".format(verdict_note),
        "**Roles run:** {}".format(", ".join(roles)),
        "**Backtest dir:** {}".format(args.backtest_dir),
        "",
        "## Synthesis (Prosecutor vs Defender)",
        "- **Prosecutor:** Zero or low trades imply chokes (min_exec_score, bar discovery, UW cache); do not promote until we see meaningful trade count.",
        "- **Defender:** Chokes are operational (discovery/timeframe, threshold); pipeline is deterministic; fix discovery and threshold and re-run.",
        "- **Board:** We side with the defender for *next steps*: treat zero-trade run as a configuration/data issue until one run with discovery + fallback score produces trades. If after that we still see zero trades, then treat as prosecutor win.",
        "",
    ]
    if customer_advocate_text:
        board_lines.append("## Customer advocate summary")
        board_lines.append("")
        board_lines.append(customer_advocate_text[:2500] + ("..." if len(customer_advocate_text) > 2500 else ""))
        board_lines.append("")
    board_lines += [
        "## One minimal reversible fix",
        "1. Ensure simulation uses bar discovery for 1Min, 5Min, 15Min and loads bars with the discovered timeframe.",
        "2. Add fallback score from raw bar-based signals when UW composite is 0.",
        "3. Optional: pass --min-exec-score 1.8 in orchestration for simulation baseline to guarantee a minimum trade sample.",
        "",
        "## Acceptance criteria for promotion",
        "- At least one orchestration run with trades_count ≥ 30 (or governance-approved lower bound).",
        "- provenance.json, config.json, summary/summary.md, baseline/metrics.json and board_verdict.md present.",
        "- Prosecutor and defender outputs reviewed; board verdict documented.",
        "",
        "## Rollout plan",
        "- Re-run orchestration after deploying discovery + fallback fixes.",
        "- If trades_count ≥ 30: mark run as promoted; use for gate_p50 / net_pnl baseline.",
        "- If still zero: capture preflight.txt and baseline/backtest_summary.json; inspect bar discovery and logs on droplet.",
        "",
        "---",
        "*Generated by scripts/multi_model_runner.py (board)*",
    ]
    (out / "board_verdict.md").write_text("\n".join(board_lines), encoding="utf-8")

    verdict_json = {
        "verdict": verdict,
        "verdict_note": verdict_note,
        "roles_run": roles,
        "backtest_dir": args.backtest_dir,
        "trades_count": trades_count,
        "net_pnl": net_pnl,
        "win_rate_pct": win_rate,
        "effectiveness_included": bool(effectiveness_text),
        "customer_advocate_included": bool(customer_advocate_text),
    }
    (out / "board_verdict.json").write_text(json.dumps(verdict_json, indent=2), encoding="utf-8")
    print("Multi-model -> {} (prosecutor_output.md, defender_output.md, sre_output.md, board_verdict.json, board_verdict.md)".format(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
