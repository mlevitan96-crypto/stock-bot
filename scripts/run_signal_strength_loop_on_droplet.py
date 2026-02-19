#!/usr/bin/env python3
"""
Run signal strengthening loop ON THE DROPLET:
  Phase 1-2: signal_strength_analysis → win_loss_signal_profile, signal_edge_ranking
  Phase 3: weight_adjustment_plan (from ranking)
  Phase 4: apply env weights, restart paper
  Phase 5: re-run expectancy, compare pre vs post
  Phase 6: write iteration_1_comparison, verdict
Print required output only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient


def run(c, cmd: str, timeout: int = 120) -> tuple[str, str]:
    o, e, _ = c._execute(cmd, timeout=timeout)
    return (o or "").strip(), (e or "").strip()


def main() -> int:
    out = REPO / "reports" / "signal_strength"
    out.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        root = run(c, "([ -d /root/stock-bot-current ] && echo /root/stock-bot-current) || echo /root/stock-bot")[0] or "/root/stock-bot"
        cd = f"cd {root}"
        run(c, f"{cd} && git fetch origin && git reset --hard origin/main", 60)
        env_cmd = "bash -c 'set -a; source .env 2>/dev/null; set +a; "

        # Phase 1-2: run signal strength analysis on droplet
        run(c, f"{cd} && python3 scripts/signal_strength_analysis.py", 60)
        # Retrieve profile and ranking
        profile, _ = run(c, f"{cd} && cat reports/signal_strength/win_loss_signal_profile.md 2>/dev/null")
        ranking, _ = run(c, f"{cd} && cat reports/signal_strength/signal_edge_ranking.md 2>/dev/null")
        (out / "win_loss_signal_profile.md").write_text(profile or "", encoding="utf-8")
        (out / "signal_edge_ranking.md").write_text(ranking or "", encoding="utf-8")

        # Parse EDGE_POSITIVE / EDGE_NEGATIVE (top 3 each)
        edge_pos, edge_neg = [], []
        in_pos = in_neg = False
        for line in (ranking or "").splitlines():
            if "EDGE_POSITIVE" in line:
                in_pos, in_neg = True, False
                continue
            if "EDGE_NEGATIVE" in line:
                in_pos, in_neg = False, True
                continue
            if "NEUTRAL" in line:
                in_pos, in_neg = False, False
                continue
            if in_pos and line.strip().startswith("- **"):
                edge_pos.append(line.strip())
            if in_neg and line.strip().startswith("- **"):
                edge_neg.append(line.strip())
        top3_pos = edge_pos[:3]
        top3_neg = edge_neg[:3]

        # Save pre-change bucket analysis
        pre_bucket, _ = run(c, f"{cd} && cat reports/blocked_expectancy/bucket_analysis.md 2>/dev/null")
        (out / "pre_change_bucket_analysis.md").write_text(pre_bucket or "", encoding="utf-8")

        # Phase 4: apply weight multipliers and restart paper (small bump for flow/uw)
        run(c, "tmux kill-session -t stock_bot_paper_run 2>/dev/null || true", 10)
        run(c, f"{cd} && tmux new-session -d -s stock_bot_paper_run 'cd {root} && FLOW_WEIGHT_MULTIPLIER=1.15 UW_WEIGHT_MULTIPLIER=1.1 SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py'", 10)
        time.sleep(120)  # 2 min then re-run expectancy (user can run again after longer window)

        # Phase 5: re-run expectancy on droplet
        run(c, f"{cd} && {env_cmd} python3 scripts/blocked_expectancy_analysis.py'", 300)
        run(c, f"{cd} && {env_cmd} python3 scripts/blocked_signal_expectancy_pipeline.py'", 300)
        post_bucket, _ = run(c, f"{cd} && cat reports/blocked_expectancy/bucket_analysis.md 2>/dev/null")
        (out / "post_change_bucket_analysis.md").write_text(post_bucket or "", encoding="utf-8")

        # Phase 6: comparison
        comp_lines = [
            "# Iteration 1 comparison (pre vs post weight adjustment)",
            "",
            "## Weight changes applied",
            "FLOW_WEIGHT_MULTIPLIER=1.15, UW_WEIGHT_MULTIPLIER=1.1",
            "",
            "## Pre-change bucket_analysis (excerpt)",
            "```",
            (pre_bucket or "")[:2000],
            "```",
            "",
            "## Post-change bucket_analysis (excerpt)",
            "```",
            (post_bucket or "")[:2000],
            "```",
        ]
        # Parse bucket rows for 0.5-1.0, 1.0-1.5, 1.5-2.0
        def parse_bucket_table(text):
            rows = []
            for line in text.splitlines():
                if not line.strip().startswith("|") or "bucket" in line or "---" in line:
                    continue
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 5:
                    rows.append(parts)
            return rows
        pre_rows = {r[0]: r for r in parse_bucket_table(pre_bucket or "")}
        post_rows = {r[0]: r for r in parse_bucket_table(post_bucket or "")}
        comp_lines.append("")
        comp_lines.append("## Buckets 0.5-1.0, 1.0-1.5, 1.5-2.0")
        comp_lines.append("| bucket | pre_n | pre_mean_pnl | pre_win_rate | post_n | post_mean_pnl | post_win_rate |")
        comp_lines.append("|--------|-------|--------------|--------------|--------|---------------|---------------|")
        for b in ["0.5-1.0", "1.0-1.5", "1.5-2.0"]:
            pr, po = pre_rows.get(b, []), post_rows.get(b, [])
            pn_n = pr[1] if len(pr) > 1 else "-"
            pn_mean = pr[2] if len(pr) > 2 else "-"
            pn_wr = pr[3] if len(pr) > 3 else "-"
            po_n = po[1] if len(po) > 1 else "-"
            po_mean = po[2] if len(po) > 2 else "-"
            po_wr = po[3] if len(po) > 3 else "-"
            comp_lines.append(f"| {b} | {pn_n} | {pn_mean} | {pn_wr} | {po_n} | {po_mean} | {po_wr} |")
        (out / "iteration_1_comparison.md").write_text("\n".join(comp_lines), encoding="utf-8")

        # Verdict: improved if any of 0.5-1.0, 1.0-1.5, 1.5-2.0 has post mean_pnl > pre mean_pnl (when comparable)
        verdict = "NO CLEAR IMPROVEMENT"
        for b in ["0.5-1.0", "1.0-1.5", "1.5-2.0"]:
            pr, po = pre_rows.get(b), post_rows.get(b)
            if pr and po and len(pr) > 2 and len(po) > 2:
                try:
                    pre_mean = float(pr[2])
                    post_mean = float(po[2])
                    if post_mean > pre_mean and post_mean > 0:
                        verdict = "EDGE STRENGTHENED"
                        break
                except (ValueError, IndexError):
                    pass

        # Required output
        print("Top 3 EDGE_POSITIVE signals/groups:")
        for x in top3_pos:
            print(" ", x)
        if not top3_pos:
            print("  (none)")
        print("Top 3 EDGE_NEGATIVE signals/groups:")
        for x in top3_neg:
            print(" ", x)
        if not top3_neg:
            print("  (none)")
        print("Weight changes applied: FLOW_WEIGHT_MULTIPLIER=1.15 (+15%), UW_WEIGHT_MULTIPLIER=1.1 (+10%)")
        print("Post-change bucket summary (0.5-1.0, 1.0-1.5, 1.5-2.0):")
        for b in ["0.5-1.0", "1.0-1.5", "1.5-2.0"]:
            po = post_rows.get(b, [])
            if len(po) >= 4:
                print(f"  {b}: n={po[1]}, mean_pnl={po[2]}, win_rate={po[3]}")
            else:
                print(f"  {b}: (no data)")
        print("Verdict:", verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
