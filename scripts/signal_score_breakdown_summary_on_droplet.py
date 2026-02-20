#!/usr/bin/env python3
"""
Summarize logs/signal_score_breakdown.jsonl (droplet-only, no inference).
Writes reports/signal_review/signal_score_breakdown_summary.md and adversarial section.
Run on droplet after SIGNAL_SCORE_BREAKDOWN_LOG=1 has captured >= 100 candidates.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BREAKDOWN_JSONL = REPO / "logs" / "signal_score_breakdown.jsonl"
OUT_DIR = REPO / "reports" / "signal_review"
SUMMARY_MD = OUT_DIR / "signal_score_breakdown_summary.md"
ADVERSARIAL_MD = OUT_DIR / "signal_score_breakdown_adversarial.md"

MIN_EXEC_SCORE = 2.5
MIN_CANDIDATES = 100


def _median(arr: list[float]) -> float:
    if not arr:
        return 0.0
    arr = sorted(arr)
    m = len(arr) // 2
    if len(arr) % 2:
        return float(arr[m])
    return (arr[m - 1] + arr[m]) / 2.0


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not BREAKDOWN_JSONL.exists():
        SUMMARY_MD.write_text(
            "# Signal score breakdown summary\n\n"
            "No logs/signal_score_breakdown.jsonl found. Run with SIGNAL_SCORE_BREAKDOWN_LOG=1 until >= 100 candidates.\n\n"
            "## DROPLET COMMANDS\n\n```bash\ncd /root/stock-bot\nexport SIGNAL_SCORE_BREAKDOWN_LOG=1\n# run paper/live until 100+ candidates\nwc -l logs/signal_score_breakdown.jsonl\npython3 scripts/signal_score_breakdown_summary_on_droplet.py\n```\n",
            encoding="utf-8",
        )
        print("No breakdown log. Run with SIGNAL_SCORE_BREAKDOWN_LOG=1 until >= 100 candidates.", file=sys.stderr)
        return 1

    rows = []
    for line in BREAKDOWN_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue

    if len(rows) < MIN_CANDIDATES:
        SUMMARY_MD.write_text(
            f"# Signal score breakdown summary\n\nOnly {len(rows)} candidates. Need >= {MIN_CANDIDATES}. Keep running with SIGNAL_SCORE_BREAKDOWN_LOG=1.\n\n"
            "## DROPLET COMMANDS\n\n```bash\nexport SIGNAL_SCORE_BREAKDOWN_LOG=1\npython3 scripts/signal_score_breakdown_summary_on_droplet.py\n```\n",
            encoding="utf-8",
        )
        print(f"Only {len(rows)} candidates; need {MIN_CANDIDATES}.", file=sys.stderr)
        return 1

    n = len(rows)
    below_min = sum(1 for r in rows if (r.get("composite_score_post") or 0) < MIN_EXEC_SCORE)
    pct_below = round(100.0 * below_min / n, 1)

    # Per-signal aggregates (across all candidates and their signal entries)
    by_signal: dict[str, list[float]] = defaultdict(list)
    missing_count: dict[str, int] = defaultdict(int)
    zero_count: dict[str, int] = defaultdict(int)
    signal_names: set[str] = set()

    for r in rows:
        for s in r.get("signals") or []:
            name = s.get("signal_name") or "unknown"
            signal_names.add(name)
            contrib = float(s.get("contribution") or 0.0)
            by_signal[name].append(contrib)
            if s.get("is_missing"):
                missing_count[name] += 1
            if s.get("is_zero"):
                zero_count[name] += 1

    # % missing and % zero per signal (relative to n candidates)
    pct_missing = {k: round(100.0 * missing_count[k] / n, 1) for k in signal_names}
    pct_zero = {k: round(100.0 * zero_count[k] / n, 1) for k in signal_names}
    median_contrib = {k: _median(by_signal[k]) for k in signal_names}

    # Top 10 and bottom 10 by median contribution
    sorted_by_median = sorted(signal_names, key=lambda x: median_contrib[x], reverse=True)
    top10 = sorted_by_median[:10]
    bottom10 = sorted_by_median[-10:] if len(sorted_by_median) >= 10 else sorted_by_median

    # 10 example rows (human-readable table)
    example_rows = rows[:10]

    lines = [
        "# Signal score breakdown summary",
        "",
        f"**Candidates:** {n} (from logs/signal_score_breakdown.jsonl)",
        f"**% candidates with composite_score_post < MIN_EXEC_SCORE ({MIN_EXEC_SCORE}):** {pct_below}% ({below_min} / {n})",
        "",
        "## % missing per signal",
        "",
        "| signal_name | % missing |",
        "|-------------|-----------|",
    ]
    for name in sorted(signal_names):
        lines.append(f"| {name} | {pct_missing.get(name, 0)}% |")
    lines.extend([
        "",
        "## % zero per signal",
        "",
        "| signal_name | % zero |",
        "|-------------|--------|",
    ])
    for name in sorted(signal_names):
        lines.append(f"| {name} | {pct_zero.get(name, 0)}% |")
    lines.extend([
        "",
        "## Median contribution per signal",
        "",
        "| signal_name | median_contribution |",
        "|-------------|--------------------|",
    ])
    for name in sorted(signal_names):
        lines.append(f"| {name} | {median_contrib.get(name, 0):.4f} |")
    lines.extend([
        "",
        "## Top 10 contributors (by median contribution)",
        "",
        "| rank | signal_name | median_contribution |",
        "|------|-------------|--------------------|",
    ])
    for i, name in enumerate(top10, 1):
        lines.append(f"| {i} | {name} | {median_contrib.get(name, 0):.4f} |")
    lines.extend([
        "",
        "## Bottom 10 contributors",
        "",
        "| rank | signal_name | median_contribution |",
        "|------|-------------|--------------------|",
    ])
    for i, name in enumerate(bottom10, 1):
        lines.append(f"| {i} | {name} | {median_contrib.get(name, 0):.4f} |")
    lines.extend([
        "",
        "## 10 example rows (human-readable)",
        "",
        "Each row: symbol, composite_score_pre, composite_score_post, gate_outcome, then first 5 signals (name, contribution, is_missing, is_zero).",
        "",
        "| # | symbol | composite_pre | composite_post | gate_outcome | signal_samples |",
        "|---|--------|--------------|----------------|--------------|----------------|",
    ])
    for i, r in enumerate(example_rows, 1):
        pre = r.get("composite_score_pre")
        post = r.get("composite_score_post")
        pre_s = f"{pre:.3f}" if pre is not None else "N/A"
        post_s = f"{post:.3f}" if post is not None else "N/A"
        samples = []
        for s in (r.get("signals") or [])[:5]:
            samples.append(f"{s.get('signal_name')}={s.get('contribution', 0):.3f}(m={s.get('is_missing')},z={s.get('is_zero')})")
        samples_s = "; ".join(samples) if samples else "—"
        lines.append(f"| {i} | {r.get('symbol', '')} | {pre_s} | {post_s} | {r.get('gate_outcome', '')} | {samples_s} |")
    lines.extend([
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "export SIGNAL_SCORE_BREAKDOWN_LOG=1",
        "# run paper/live until >= 100 lines in logs/signal_score_breakdown.jsonl",
        "python3 scripts/signal_score_breakdown_summary_on_droplet.py",
        "```",
        "",
    ])
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {SUMMARY_MD} (n={n}, % below MIN_EXEC_SCORE={pct_below}%)")

    # Multi-model adversarial review for signal breakdown
    write_adversarial(rows, n, pct_below, median_contrib, pct_missing, pct_zero, top10, bottom10)
    return 0


def write_adversarial(
    rows: list,
    n: int,
    pct_below: float,
    median_contrib: dict,
    pct_missing: dict,
    pct_zero: dict,
    top10: list,
    bottom10: list,
) -> None:
    from datetime import datetime, timezone
    lines = [
        "# Signal score breakdown — multi-model adversarial review",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Evidence: reports/signal_review/signal_score_breakdown_summary.md, logs/signal_score_breakdown.jsonl.",
        "",
        "---",
        "",
        "## 1) Prosecution",
        "",
        "**Strongest explanation for 0 trades based on signal breakdown.**",
        "",
        f"- {pct_below}% of candidates have composite_score_post < MIN_EXEC_SCORE ({MIN_EXEC_SCORE}).",
        f"- Top contributors (median): {', '.join(f'{k}={median_contrib.get(k, 0):.2f}' for k in top10[:5])}.",
        f"- Bottom contributors: {', '.join(bottom10[:5])}.",
        "",
        "Conclusion: Composite is genuinely low because [fill from summary: signals mostly missing / normalization crush / UW zeroing / dominant signals near zero].",
        "",
        "---",
        "",
        "## 2) Defense",
        "",
        "**Alternative explanations + falsification tests.**",
        "",
        "- **Alternative 1:** Scores are crushed by clamping/normalization, not by missing signals. **Falsified if:** composite_score_pre distribution is high and post is low; or pre ≈ post and both low.",
        "- **Alternative 2:** One or two signals dominate and are zero/missing. **Falsified if:** top 10 by median contribution have healthy medians and low % missing.",
        "",
        "---",
        "",
        "## 3) SRE / Operations",
        "",
        "**Telemetry completeness, ordering, correctness.**",
        "",
        "- Breakdown emitted at composition time (before expectancy gate); no cross-artifact joins.",
        "- Each record has ts_eval, symbol, trace_id, composite_score_pre/post, gate_outcome, and per-signal contribution/is_missing/is_zero.",
        "- Verify: same candidate count as expectancy_gate_truth.jsonl in same run window (optional cross-check).",
        "",
        "---",
        "",
        "## 4) Board verdict",
        "",
        "- **ONE dominant cause:** [e.g. signals mostly missing / normalization crush / UW zeroing] — from summary % missing, % zero, median contributions.",
        "",
        "- **ONE minimal reversible experiment (paper-only):** Log signal breakdown for 100 candidates; compare composite_pre vs composite_post and % missing per signal. No threshold or weight changes.",
        "",
        "- **Numeric acceptance criteria:** (1) Breakdown summary shows % below MIN_EXEC_SCORE. (2) Top 10 contributors named with median contribution. (3) No contradictory claim (e.g. composite high in one artifact, low in breakdown).",
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "export SIGNAL_SCORE_BREAKDOWN_LOG=1",
        "# run until >= 100 candidates",
        "python3 scripts/signal_score_breakdown_summary_on_droplet.py",
        "```",
        "",
    ]
    ADVERSARIAL_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {ADVERSARIAL_MD}")


if __name__ == "__main__":
    sys.exit(main())
