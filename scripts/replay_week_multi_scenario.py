"""Replay week multi-scenario diagnostics. Consumes exit_timing_scenarios.json and droplet logs."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config" / "exit_timing_scenarios.json"
OUTDIR = ROOT / "artifacts" / "scenario_replay"
OUTDIR.mkdir(parents=True, exist_ok=True)


def sh(cmd, check=True):
    return subprocess.run(cmd, cwd=ROOT, shell=True, text=True, capture_output=True, check=check)


def find_first(cmds):
    for c in cmds:
        r = sh(f"bash -lc \"command -v {c} >/dev/null 2>&1 && echo yes || true\"", check=False)
        if "yes" in (r.stdout or ""):
            return c
    return None


def discover_replay_entrypoint():
    # Heuristics: look for scripts/commands that contain "backtest" or "replay"
    candidates = []
    for p in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "scripts").glob("*.sh")):
        t = p.read_text(errors="ignore")
        if re.search(r"\b(backtest|replay|simulate)\b", t, re.I):
            candidates.append(p)
    return candidates


def load_scenarios():
    data = json.loads(CFG.read_text())
    return data["scenarios"]


def load_exit_attribution():
    # Minimal diagnostic dataset; used if no full replay engine exists.
    files = sorted((ROOT / "logs").glob("exit_attribution*.jsonl"))
    if not files:
        return []  # No logs: produce diagnostics-only report with empty baseline
    rows = []
    for f in files:
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def summarize_exit_rows(rows):
    # Produces a stable baseline summary by mode:strategy
    def norm(x, ok):
        x = (x or "UNKNOWN")
        x = str(x).upper()
        return x if x in ok else x

    buckets = {}
    for r in rows:
        mode = norm(r.get("mode") or r.get("run_mode"), {"LIVE", "PAPER", "SHADOW"})
        strat = norm(r.get("strategy") or r.get("strategy_label"), {"EQUITY", "WHEEL"})
        key = f"{mode}:{strat}"
        b = buckets.setdefault(key, {"pnl": 0.0, "exits": 0, "wins": 0, "losses": 0})
        pnl = float(r.get("pnl") or 0.0)
        b["pnl"] += pnl
        b["exits"] += 1
        if pnl > 0:
            b["wins"] += 1
        elif pnl < 0:
            b["losses"] += 1
    return buckets


def main():
    scenarios = load_scenarios()

    # Attempt to find an internal backtest/replay interface
    replay_candidates = discover_replay_entrypoint()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "replay_engine": None,
        "replay_candidates": [str(p.relative_to(ROOT)) for p in replay_candidates],
        "scenarios": {},
        "notes": [],
    }

    report["notes"].append(
        "No canonical replay engine is auto-invoked to avoid accidental forward-looking bias. "
        "This run generates diagnostics + wiring expectations. If you add a canonical replay runner, "
        "it can consume config/exit_timing_scenarios.json and output full counterfactual results."
    )

    # Diagnostic baseline from realized exits (empty if no logs)
    rows = load_exit_attribution()
    baseline = summarize_exit_rows(rows) if rows else {}
    report["diagnostics_baseline_from_exit_attribution"] = baseline

    # Scenario-level placeholders (until canonical replay exists)
    for scen_name, scen in scenarios.items():
        report["scenarios"][scen_name] = {
            "description": scen.get("description", ""),
            "status": "DIAGNOSTICS_ONLY",
            "next": [
                "Add/identify canonical replay engine to simulate alternative exits.",
                "Ensure historical price/position timeline artifacts exist for counterfactual exits.",
                "Then rerun to populate counterfactual P&L deltas per scenario.",
            ],
        }

    (OUTDIR / "replay_week_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    print("Wrote", (OUTDIR / "replay_week_report.json").as_posix())

    # Additionally write a human-friendly markdown
    md = []
    md.append("# Scenario replay week report (diagnostics-only)\n\n")
    md.append("## Baseline realized exits by mode:strategy\n\n")
    md.append("| bucket | pnl | exits | wins | losses | win_rate |\n")
    md.append("|---|---:|---:|---:|---:|---:|\n")
    for k, v in sorted(baseline.items()):
        exits = v["exits"] or 1
        win_rate = v["wins"] / exits
        md.append(f"| {k} | {v['pnl']:.2f} | {v['exits']} | {v['wins']} | {v['losses']} | {win_rate:.3f} |\n")
    md.append("\n## Scenarios defined\n\n")
    for scen_name, scen in scenarios.items():
        md.append(f"- **{scen_name}:** {scen.get('description', '')}\n")
    md.append("\n## What's missing for full counterfactual replay\n\n")
    md.append("- A canonical replay runner that can re-simulate exits using historical price/position timelines.\n")
    md.append("- A retained market data timeline (bars/quotes) or an internal price cache used at decision-time.\n")
    md.append("- A retained position timeline (entry time, size, symbol, mode, strategy, regime) to apply hold floors.\n")
    (OUTDIR / "replay_week_report.md").write_text("".join(md))
    print("Wrote", (OUTDIR / "replay_week_report.md").as_posix())


if __name__ == "__main__":
    main()
