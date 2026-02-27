#!/usr/bin/env python3
"""
Droplet: pull, confirm fix, sample exit_attribution for exit_quality_metrics, re-run baseline v3.
Writes: droplet_pull_proof, exit_quality_postfix_sample, baseline_v3_verification_postdeploy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE = "20260218"
OUT_DIR = REPO / "reports" / "phase9_data_integrity"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_float(x, d=0.0):
    try:
        return float(x) if x is not None else d
    except Exception:
        return d


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    with DropletClient() as c:
        # Step 2 — Stash, pull, confirm
        c._execute_with_cd("git stash push -u -m 'pre-data-integrity-pull-20260218' 2>/dev/null || true", timeout=15)
        out_pull, _, rc_pull = c._execute_with_cd("git pull origin main 2>&1", timeout=90)
        out_rev, _, _ = c._execute_with_cd("git rev-parse HEAD 2>/dev/null", timeout=5)
        out_gh, _, _ = c._execute_with_cd("grep -n 'high_water' main.py 2>/dev/null | head -50", timeout=10)
        out_guard, _, _ = c._execute_with_cd("grep -n 'exit_quality_high_water_unavailable' main.py 2>/dev/null | head -10", timeout=5)
        out_imp, _, _ = c._execute_with_cd("python3 -c \"import scripts.analysis.run_effectiveness_reports as r; print('ok')\" 2>&1", timeout=15)

        pull_lines = [
            "# Droplet pull proof (2026-02-18)",
            "",
            "## git pull",
            "```",
            (out_pull or "").strip()[-1200:],
            "```",
            "",
            "## Commit hash after pull",
            (out_rev or "").strip(),
            "",
            "## grep high_water main.py (first 50)",
            "```",
            (out_gh or "").strip(),
            "```",
            "",
            "## grep exit_quality_high_water_unavailable",
            "```",
            (out_guard or "").strip(),
            "```",
            "",
            "## import run_effectiveness_reports",
            "```",
            (out_imp or "").strip(),
            "```",
            "",
        ]
        (OUT_DIR / f"{DATE}_droplet_pull_proof.md").write_text("\n".join(pull_lines), encoding="utf-8")

        # Step 3 — Paper state + sample exit_attribution
        out_state, _, _ = c._execute_with_cd("cat state/live_paper_run_state.json 2>/dev/null || echo '{}'", timeout=5)
        out_tmux, _, _ = c._execute_with_cd("tmux ls 2>/dev/null || echo 'none'", timeout=5)
        out_pane, _, _ = c._execute_with_cd("tmux capture-pane -pt stock_bot_paper_run -S -20 2>/dev/null || echo 'no-pane'", timeout=5)
        out_sample, _, _ = c._execute_with_cd(
            "tail -n 300 logs/exit_attribution.jsonl 2>/dev/null | python3 -c \""
            "import sys, json\n"
            "n=0\nm=0\n"
            "for line in sys.stdin:\n"
            "  try:\n"
            "    r=json.loads(line)\n"
            "  except:\n"
            "    continue\n"
            "  n+=1\n"
            "  if r.get('exit_quality_metrics') is not None:\n"
            "    m+=1\n"
            "print('sample_records', n, 'with_exit_quality_metrics', m)\n"
            "\" 2>&1",
            timeout=15,
        )
        # One redacted example with exit_quality_metrics if any
        out_example, _, _ = c._execute_with_cd(
            "tail -n 500 logs/exit_attribution.jsonl 2>/dev/null | python3 -c \""
            "import sys, json\n"
            "for line in reversed(list(sys.stdin)):\n"
            "  try:\n"
            "    r=json.loads(line)\n"
            "    if r.get('exit_quality_metrics'):\n"
            "      print(json.dumps({'symbol': r.get('symbol'), 'exit_quality_metrics': r.get('exit_quality_metrics'), 'ts': r.get('timestamp') or r.get('ts')}))\n"
            "      break\n"
            "  except: pass\n"
            "\" 2>&1",
            timeout=15,
        )
        sample_records = with_eqm = 0
        for part in (out_sample or "").strip().split():
            if part == "sample_records" and "sample_records" in (out_sample or ""):
                try:
                    parts = (out_sample or "").strip().split()
                    if "sample_records" in parts:
                        i = parts.index("sample_records")
                        if i + 1 < len(parts):
                            sample_records = int(parts[i + 1])
                        if "with_exit_quality_metrics" in parts:
                            j = parts.index("with_exit_quality_metrics")
                            if j + 1 < len(parts):
                                with_eqm = int(parts[j + 1])
                except Exception:
                    pass
                break
        if not sample_records and out_sample:
            try:
                parts = (out_sample or "").strip().split()
                for i, p in enumerate(parts):
                    if p == "sample_records" and i + 1 < len(parts):
                        sample_records = int(parts[i + 1])
                    if p == "with_exit_quality_metrics" and i + 1 < len(parts):
                        with_eqm = int(parts[i + 1])
            except Exception:
                pass

        sample_lines = [
            "# Exit quality post-fix sample (2026-02-18)",
            "",
            "## Paper run state (no overlay)",
            "```json",
            (out_state or "").strip()[:800],
            "```",
            "",
            "## tmux",
            "```",
            (out_tmux or "").strip(),
            "```",
            "",
            "## Sample: last 300 exit_attribution lines",
            "```",
            (out_sample or "").strip(),
            "```",
            "",
            "- **sample_records:** " + str(sample_records),
            "- **with_exit_quality_metrics:** " + str(with_eqm),
            "",
            "## Example record with exit_quality_metrics (redacted)",
            "```",
            (out_example or "").strip() or "(none yet)",
            "```",
            "",
        ]
        (OUT_DIR / f"{DATE}_exit_quality_postfix_sample.md").write_text("\n".join(sample_lines), encoding="utf-8")

        # Step 4 — Re-run baseline v3
        out_end, _, _ = c._execute_with_cd("date +%Y-%m-%d 2>/dev/null", timeout=5)
        end_date = (out_end or "").strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cmd = f"python3 scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end {end_date} --out-dir reports/effectiveness_baseline_blame_v3 2>&1"
        out_eff, _, rc_eff = c._execute_with_cd(cmd, timeout=300)
        out_agg, _, _ = c._execute_with_cd("cat reports/effectiveness_baseline_blame_v3/effectiveness_aggregates.json 2>/dev/null || echo '{}'", timeout=10)
        out_blame, _, _ = c._execute_with_cd("cat reports/effectiveness_baseline_blame_v3/entry_vs_exit_blame.json 2>/dev/null || echo '{}'", timeout=10)
        out_exit, _, _ = c._execute_with_cd(
            "head -60 reports/effectiveness_baseline_blame_v3/exit_effectiveness.json 2>/dev/null || echo '{}'",
            timeout=10,
        )

    agg = {}
    blame = {}
    try:
        agg = json.loads(out_agg) if out_agg and out_agg.strip() else {}
    except Exception:
        pass
    try:
        blame = json.loads(out_blame) if out_blame and out_blame.strip() else {}
    except Exception:
        pass

    joined = agg.get("joined_count", 0)
    losers = agg.get("total_losing_trades", 0)
    giveback = agg.get("avg_profit_giveback")
    weak_pct = blame.get("weak_entry_pct", 0)
    timing_pct = blame.get("exit_timing_pct", 0)
    uncl_pct = blame.get("unclassified_pct")
    uncl_count = blame.get("unclassified_count")
    if not joined and blame:
        losers = blame.get("total_losing_trades", 0)

    # Top 3 exit reasons by frequency (loss contribution proxy)
    try:
        exit_data = json.loads(out_exit) if out_exit and isinstance(out_exit, str) and out_exit.strip() else {}
        if isinstance(exit_data, dict):
            sorted_reasons = sorted(
                exit_data.items(),
                key=lambda x: (x[1].get("frequency") or 0) * abs(_safe_float(x[1].get("avg_realized_pnl"))),
                reverse=True,
            )[:3]
            top_reasons = [(r, v.get("frequency"), v.get("avg_realized_pnl"), v.get("avg_profit_giveback")) for r, v in sorted_reasons]
        else:
            top_reasons = []
    except Exception:
        top_reasons = []

    ver_lines = [
        "# Baseline v3 verification post-deploy (2026-02-18)",
        "",
        "## Command",
        "```",
        cmd,
        "```",
        "",
        "## Verification",
        "",
        "| Check | Result |",
        "|-------|--------|",
        f"| joined_count | {joined} |",
        f"| total_losing_trades | {losers} |",
        f"| avg_profit_giveback | {giveback} |",
        f"| weak_entry_pct | {weak_pct} |",
        f"| exit_timing_pct | {timing_pct} |",
        f"| unclassified_pct | {uncl_pct} |",
        f"| unclassified_count | {uncl_count} |",
        "",
        "## effectiveness_aggregates.json",
        "```json",
        json.dumps(agg, indent=2),
        "```",
        "",
        "## entry_vs_exit_blame.json (excerpt)",
        "```json",
        json.dumps({k: blame.get(k) for k in ["total_losing_trades", "weak_entry_pct", "exit_timing_pct", "unclassified_count", "unclassified_pct"] if blame.get(k) is not None}, indent=2),
        "```",
        "",
        "## Top 3 exit reasons (by loss contribution proxy: freq * |avg_pnl|)",
        "```",
        str(top_reasons),
        "```",
        "",
    ]
    (OUT_DIR / f"{DATE}_baseline_v3_verification_postdeploy.md").write_text("\n".join(ver_lines), encoding="utf-8")

    print("Wrote:", OUT_DIR / f"{DATE}_droplet_pull_proof.md")
    print("Wrote:", OUT_DIR / f"{DATE}_exit_quality_postfix_sample.md")
    print("Wrote:", OUT_DIR / f"{DATE}_baseline_v3_verification_postdeploy.md")
    return 0 if rc_pull == 0 and rc_eff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
