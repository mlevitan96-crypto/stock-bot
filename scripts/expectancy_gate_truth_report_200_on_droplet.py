#!/usr/bin/env python3
"""
Phase 1: Build expectancy_gate_truth_200.md from logs/expectancy_gate_truth.jsonl.
Run ON THE DROPLET after >= 200 truth lines captured (EXPECTANCY_GATE_TRUTH_LOG=1).
Output: reports/signal_review/expectancy_gate_truth_200.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TRUTH_PATH = REPO / "logs" / "expectancy_gate_truth.jsonl"
OUT_DIR = REPO / "reports" / "signal_review"
OUT_MD = OUT_DIR / "expectancy_gate_truth_200.md"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not TRUTH_PATH.exists():
        OUT_MD.write_text(
            "# Expectancy gate truth (200 lines)\n\n"
            "No logs/expectancy_gate_truth.jsonl found. Run main with EXPECTANCY_GATE_TRUTH_LOG=1 until >= 200 lines.\n\n"
            "## DROPLET COMMANDS\n\n```bash\ncd /root/stock-bot\nexport EXPECTANCY_GATE_TRUTH_LOG=1\n# run paper/live until 200+ lines, then:\npython3 scripts/expectancy_gate_truth_report_200_on_droplet.py\n```\n",
            encoding="utf-8",
        )
        print("No truth log; wrote placeholder. Run with EXPECTANCY_GATE_TRUTH_LOG=1 until >= 200 lines.")
        return 1

    rows = []
    for line in TRUTH_PATH.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue

    if len(rows) < 200:
        OUT_MD.write_text(
            f"# Expectancy gate truth (200 lines)\n\nOnly {len(rows)} lines. Need >= 200. Keep running with EXPECTANCY_GATE_TRUTH_LOG=1.\n\n"
            "## DROPLET COMMANDS\n\n```bash\nexport EXPECTANCY_GATE_TRUTH_LOG=1\n# run until 200+ lines\npython3 scripts/expectancy_gate_truth_report_200_on_droplet.py\n```\n",
            encoding="utf-8",
        )
        print(f"Only {len(rows)} lines; need 200.")
        return 1

    scores = [r.get("score_used_by_gate") for r in rows if r.get("score_used_by_gate") is not None]
    scores = [float(x) for x in scores]
    scores.sort()
    n = len(scores)
    p10 = scores[int(0.10 * n)] if n else None
    p50 = scores[int(0.50 * n)] if n else None
    p90 = scores[int(0.90 * n)] if n else None

    pass_count = sum(1 for r in rows if r.get("gate_outcome") == "pass")
    pass_rate = (100.0 * pass_count / len(rows)) if rows else 0.0

    example_rows = rows[:20]
    example_lines = []
    for r in example_rows:
        example_lines.append("  " + json.dumps({k: r.get(k) for k in [
            "ts_eval_iso", "symbol", "score_used_by_gate", "min_exec_score",
            "gate_outcome", "fail_reason", "score_pre_adjust", "score_post_adjust",
        ]}, default=str))

    lines = [
        "# Expectancy gate truth (≥200 lines)",
        "",
        f"Total lines: {len(rows)}",
        "",
        "## Distributions (score_used_by_gate)",
        "",
        f"- p10: {p10}",
        f"- p50 (median): {p50}",
        f"- p90: {p90}",
        "",
        f"Pass rate: {pass_rate:.2f}% ({pass_count} / {len(rows)})",
        "",
        "## 20 example rows",
        "",
        "```json",
        *example_lines,
        "```",
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "export EXPECTANCY_GATE_TRUTH_LOG=1",
        "# run paper/live until >= 200 lines in logs/expectancy_gate_truth.jsonl",
        "python3 scripts/expectancy_gate_truth_report_200_on_droplet.py",
        "```",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD} (n={len(rows)}, pass_rate={pass_rate:.2f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
