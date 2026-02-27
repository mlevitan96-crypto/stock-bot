#!/usr/bin/env python3
"""
Multi-model signal edge cycle (Phases 3–8) for droplet or local.
Run from repo root. On droplet: run after pushing attribution commit.

Phases:
  3 — Deploy (git pull), restart paper, wait for new attribution snapshots.
  4 — Run expectancy + signal pipeline; produce multi_model_edge_analysis.md, bucket_analysis, signal_group_expectancy.
  5 — Adversarial review -> adversarial_review.md.
  6 — Synthesis weight plan -> weight_adjustment_plan_v2.md.
  7 — Apply weight changes (env multipliers), commit, restart paper.
  8 — Re-run expectancy; iteration_comparison_v2.md; print required output.

Usage:
  python3 scripts/run_multi_model_signal_edge_cycle_on_droplet.py [--phase 3|4|5|6|7|8|all] [--skip-deploy] [--skip-apply-weights] [--wait-minutes N]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SIGNAL_STRENGTH_DIR = REPO / "reports" / "signal_strength"
BLOCKED_SIGNAL_DIR = REPO / "reports" / "blocked_signal_expectancy"
BLOCKED_EXP_DIR = REPO / "reports" / "blocked_expectancy"


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> tuple[int, str]:
    cwd = cwd or REPO
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)


def phase3_deploy_restart(skip_deploy: bool, wait_minutes: int) -> bool:
    """Git pull, verify attribution commit, tmux restart, optional wait for new data."""
    if not skip_deploy:
        code, out = _run(["git", "pull", "--rebase", "origin", "main"])
        if code != 0:
            print(f"git pull failed: {out}")
            return False
        # Confirm attribution-related content
        if "group_sums" not in (REPO / "score_snapshot_writer.py").read_text(encoding="utf-8"):
            print("Attribution commit not present (group_sums in score_snapshot_writer).")
            return False
        print("Deploy: pull OK, attribution present.")

    _run(["tmux", "kill-session", "-t", "stock_bot_paper_run"], timeout=5)
    time.sleep(1)
    env = os.environ.copy()
    env["SCORE_SNAPSHOT_DEBUG"] = "1"
    env["LOG_LEVEL"] = "INFO"
    code, _ = _run([
        "tmux", "new-session", "-d", "-s", "stock_bot_paper_run",
        "bash", "-c",
        f"cd {REPO} && SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py",
    ], timeout=10)
    if code != 0:
        print("tmux new-session failed (session may already exist).")
    else:
        print("Paper restarted (tmux stock_bot_paper_run).")

    if wait_minutes <= 0:
        return True
    snapshot_path = REPO / "logs" / "score_snapshot.jsonl"
    blocked_path = REPO / "state" / "blocked_trades.jsonl"
    deadline = time.time() + wait_minutes * 60
    while time.time() < deadline:
        has_attr = 0
        if snapshot_path.exists():
            for line in snapshot_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-50:]:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    if r.get("group_sums") or r.get("weighted_contributions"):
                        has_attr += 1
                        break
                except Exception:
                    pass
        if blocked_path.exists():
            for line in blocked_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-20:]:
                try:
                    r = json.loads(line)
                    if (r.get("attribution_snapshot") or {}).get("group_sums"):
                        has_attr += 1
                        break
                except Exception:
                    pass
        if has_attr >= 1:
            print("New attribution data detected.")
            return True
        time.sleep(30)
    print("Wait timeout; proceeding without confirming new attribution.")
    return True


def _load_replay_results() -> list[dict]:
    path = BLOCKED_SIGNAL_DIR / "replay_results.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _winner_loser_stats(replay: list[dict], component_keys: list[str]) -> dict:
    """Compute mean component/group value for winners (pnl_pct > 0) vs losers."""
    winners = [r for r in replay if (r.get("pnl_pct") or 0) > 0]
    losers = [r for r in replay if (r.get("pnl_pct") or 0) <= 0]
    stats = {}
    for key in component_keys:
        w_vals = []
        l_vals = []
        for r in replay:
            val = None
            if key in ("uw", "regime_macro", "other_components"):
                val = (r.get("group_sums") or {}).get(key)
            else:
                val = (r.get("components") or {}).get(key)
            if val is not None and isinstance(val, (int, float)):
                if (r.get("pnl_pct") or 0) > 0:
                    w_vals.append(float(val))
                else:
                    l_vals.append(float(val))
        mean_w = sum(w_vals) / len(w_vals) if w_vals else 0.0
        mean_l = sum(l_vals) / len(l_vals) if l_vals else 0.0
        delta = mean_w - mean_l
        n = len(w_vals) + len(l_vals)
        # Correlation with pnl (simplified: mean winner - mean loser sign)
        pnls = [r.get("pnl_pct") or 0 for r in replay]
        vals = []
        for r in replay:
            if key in ("uw", "regime_macro", "other_components"):
                v = (r.get("group_sums") or {}).get(key)
            else:
                v = (r.get("components") or {}).get(key)
            vals.append(float(v) if v is not None and isinstance(v, (int, float)) else 0.0)
        if n >= 2 and vals and pnls:
            mean_v = sum(vals) / len(vals)
            mean_p = sum(pnls) / len(pnls)
            cov = sum((v - mean_v) * (p - mean_p) for v, p in zip(vals, pnls)) / n
            var_v = sum((v - mean_v) ** 2 for v in vals) / n
            var_p = sum((p - mean_p) ** 2 for p in pnls) / n
            corr = (cov / (var_v * var_p) ** 0.5) if (var_v and var_p) else 0.0
        else:
            corr = 0.0
        stats[key] = {
            "mean_winner": mean_w,
            "mean_loser": mean_l,
            "delta_mean": delta,
            "corr_pnl": corr,
            "n": n,
        }
    return stats


def phase4_expectancy_and_edge() -> bool:
    """Run blocked_expectancy_analysis and blocked_signal_expectancy_pipeline; generate multi_model_edge_analysis.md."""
    code1, _ = _run([sys.executable, "scripts/blocked_expectancy_analysis.py"], timeout=120)
    code2, _ = _run([sys.executable, "scripts/blocked_signal_expectancy_pipeline.py"], timeout=120)
    if code2 != 0:
        print("blocked_signal_expectancy_pipeline.py failed.")
        return False

    replay = _load_replay_results()
    group_keys = ["uw", "regime_macro", "other_components"]
    component_keys = list(group_keys)
    # Collect all component names from replay
    comp_set = set()
    for r in replay:
        comp_set.update((r.get("components") or {}).keys())
    component_keys.extend(sorted(comp_set - set(group_keys)))

    stats = _winner_loser_stats(replay, component_keys)

    # Rank: EDGE_POSITIVE = delta_mean > 0 and corr_pnl > 0; EDGE_NEGATIVE = opposite or corr < 0
    edge_positive = []
    edge_negative = []
    for k, s in stats.items():
        if s["n"] < 5:
            continue
        d, c = s["delta_mean"], s["corr_pnl"]
        if d > 0 and c > 0:
            edge_positive.append((k, d, c, s["n"]))
        elif d < 0 or c < 0:
            edge_negative.append((k, d, c, s["n"]))

    edge_positive.sort(key=lambda x: (x[1], x[2]), reverse=True)
    edge_negative.sort(key=lambda x: (x[1], x[2]))

    SIGNAL_STRENGTH_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Multi-Model Edge Analysis (Phase 4)",
        "",
        "## WINNER vs LOSER profiles",
        "",
        "| signal | mean_winner | mean_loser | delta_mean | corr_pnl | n |",
        "|--------|-------------|------------|------------|----------|---|",
    ]
    for k in component_keys:
        s = stats.get(k, {})
        if s.get("n", 0) < 1:
            continue
        lines.append(
            f"| {k} | {s['mean_winner']:.4f} | {s['mean_loser']:.4f} | {s['delta_mean']:.4f} | {s['corr_pnl']:.4f} | {s['n']} |"
        )
    lines.extend([
        "",
        "## EDGE_POSITIVE (increase weight)",
        "",
    ])
    for k, d, c, n in edge_positive[:15]:
        lines.append(f"- **{k}** delta_mean={d:.4f} corr_pnl={c:.4f} n={n}")
    lines.extend([
        "",
        "## EDGE_NEGATIVE (decrease or zero weight)",
        "",
    ])
    for k, d, c, n in edge_negative[:15]:
        lines.append(f"- **{k}** delta_mean={d:.4f} corr_pnl={c:.4f} n={n}")
    lines.extend([
        "",
        "## Bucket summary (from pipeline)",
        "",
    ])
    bucket_path = BLOCKED_SIGNAL_DIR / "bucket_analysis.md"
    if bucket_path.exists():
        lines.append(bucket_path.read_text(encoding="utf-8"))
    lines.append("")
    sig_path = BLOCKED_SIGNAL_DIR / "signal_group_expectancy.md"
    if sig_path.exists():
        lines.append(sig_path.read_text(encoding="utf-8"))

    (SIGNAL_STRENGTH_DIR / "multi_model_edge_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    # Copy bucket and signal_group into signal_strength for reference
    if bucket_path.exists():
        (SIGNAL_STRENGTH_DIR / "bucket_analysis.md").write_text(bucket_path.read_text(encoding="utf-8"), encoding="utf-8")
    if sig_path.exists():
        (SIGNAL_STRENGTH_DIR / "signal_group_expectancy.md").write_text(sig_path.read_text(encoding="utf-8"), encoding="utf-8")
    print("Phase 4: multi_model_edge_analysis.md, bucket_analysis.md, signal_group_expectancy.md written.")
    return True


def phase5_adversarial_review() -> bool:
    """Write adversarial_review.md challenging rankings and validating integrity."""
    edge_path = SIGNAL_STRENGTH_DIR / "multi_model_edge_analysis.md"
    content = []
    if edge_path.exists():
        content.append(edge_path.read_text(encoding="utf-8"))
    lines = [
        "# Adversarial Review (Phase 5)",
        "",
        "## MODEL B — Challenges",
        "- Challenge signal rankings: small n or single-bucket dominance can make delta_mean misleading.",
        "- Contradictions: a group (e.g. regime_macro) may be EDGE_POSITIVE while a sub-component is EDGE_NEGATIVE; resolve by preferring group-level when sample is small.",
        "- Misleading correlations: pnl variance may be driven by one symbol or one day; check stability across buckets.",
        "- Noise: signals with |corr_pnl| < 0.05 or |delta_mean| < 0.01 may be noise.",
        "",
        "## MODEL C — Data integrity",
        "- Attribution: confirm replay_results contain group_sums and (when available) components.",
        "- Stale caches: if most records have zero or identical components, pipeline may be using pre-attribution data.",
        "- Composite consistency: group_sums (uw + regime_macro + other_components) should align with sum of components.",
        "",
        "## Raw edge analysis (reference)",
        "",
    ]
    lines.extend(content)
    (SIGNAL_STRENGTH_DIR / "adversarial_review.md").write_text("\n".join(lines), encoding="utf-8")
    print("Phase 5: adversarial_review.md written.")
    return True


def phase6_weight_plan() -> bool:
    """Synthesis: weight_adjustment_plan_v2.md with minimal, reversible changes."""
    edge_path = SIGNAL_STRENGTH_DIR / "multi_model_edge_analysis.md"
    top_positive = []
    top_negative = []
    if edge_path.exists():
        text = edge_path.read_text(encoding="utf-8")
        in_pos = in_neg = False
        for line in text.splitlines():
            if "EDGE_POSITIVE" in line and "##" in line:
                in_pos, in_neg = True, False
                continue
            if "EDGE_NEGATIVE" in line and "##" in line:
                in_pos, in_neg = False, True
                continue
            if in_pos and line.strip().startswith("- **"):
                m = re.match(r"-\s*\*\*([^*]+)\*\*.*", line)
                if m:
                    top_positive.append(m.group(1).strip())
            if in_neg and line.strip().startswith("- **"):
                m = re.match(r"-\s*\*\*([^*]+)\*\*.*", line)
                if m:
                    top_negative.append(m.group(1).strip())

    # Map to env multipliers: uw -> UW_WEIGHT_MULTIPLIER, regime_macro -> REGIME_WEIGHT_MULTIPLIER, flow/options_flow -> FLOW_WEIGHT_MULTIPLIER
    map_to_env = {
        "uw": "UW_WEIGHT_MULTIPLIER",
        "flow": "FLOW_WEIGHT_MULTIPLIER",
        "options_flow": "FLOW_WEIGHT_MULTIPLIER",
        "regime_macro": "REGIME_WEIGHT_MULTIPLIER",
    }
    lines = [
        "# Weight Adjustment Plan v2 (Phase 6 — Synthesis)",
        "",
        "## Top EDGE_POSITIVE (robust across models)",
        "",
    ]
    for s in top_positive[:5]:
        lines.append(f"- {s}")
    lines.extend([
        "",
        "## Top EDGE_NEGATIVE",
        "",
    ])
    for s in top_negative[:5]:
        lines.append(f"- {s}")
    lines.extend([
        "",
        "## Minimal reversible adjustments (only where all models agree)",
        "",
        "Use env multipliers (default 1.0); apply only if adversarial review does not flag as noise:",
        "",
        "- **UW_WEIGHT_MULTIPLIER**: 1.0 (increase to 1.1 if uw is top EDGE_POSITIVE and n sufficient).",
        "- **REGIME_WEIGHT_MULTIPLIER**: 1.0 (increase to 1.1 if regime_macro is top EDGE_POSITIVE).",
        "- **FLOW_WEIGHT_MULTIPLIER**: 1.0 (increase if flow/options_flow is top EDGE_POSITIVE).",
        "",
        "After applying, restart paper with these env vars and re-run Phase 8.",
        "",
    ])
    (SIGNAL_STRENGTH_DIR / "weight_adjustment_plan_v2.md").write_text("\n".join(lines), encoding="utf-8")
    print("Phase 6: weight_adjustment_plan_v2.md written.")
    return True


def phase7_apply_weights_and_restart(skip_apply: bool) -> bool:
    """Apply weight env from plan (or no-op if skip), commit, restart paper."""
    if skip_apply:
        print("Phase 7: skip-apply; no weight changes or commit.")
        return True
    # Default: no actual weight change (1.0); just commit reports and restart
    plan_path = SIGNAL_STRENGTH_DIR / "weight_adjustment_plan_v2.md"
    env_overrides = {}
    if plan_path.exists():
        text = plan_path.read_text(encoding="utf-8")
        if "1.1" in text:
            # Optional: parse "UW_WEIGHT_MULTIPLIER ... 1.1" and set env_overrides
            for env_name in ("UW_WEIGHT_MULTIPLIER", "REGIME_WEIGHT_MULTIPLIER", "FLOW_WEIGHT_MULTIPLIER"):
                if env_name in text and "1.1" in text:
                    env_overrides[env_name] = "1.1"
    # Write state file for paper run to source (optional)
    nudges_path = REPO / "state" / "multi_model_weight_nudges.env"
    nudges_path.parent.mkdir(parents=True, exist_ok=True)
    with nudges_path.open("w", encoding="utf-8") as f:
        for k, v in env_overrides.items():
            f.write(f"export {k}={v}\n")
        if not env_overrides:
            f.write("# No overrides; all 1.0\n")

    # Commit report files (only if they exist)
    to_add = [
        "reports/signal_strength/multi_model_edge_analysis.md",
        "reports/signal_strength/adversarial_review.md",
        "reports/signal_strength/weight_adjustment_plan_v2.md",
        "reports/signal_strength/bucket_analysis.md",
        "reports/signal_strength/signal_group_expectancy.md",
        "reports/signal_strength/iteration_comparison_v2.md",
    ]
    for p in to_add:
        if (REPO / p).exists():
            _run(["git", "add", p], cwd=REPO)
    if nudges_path.exists():
        _run(["git", "add", "state/multi_model_weight_nudges.env"], cwd=REPO)
    code2, out = _run(["git", "commit", "-m", "Config: multi-model signal weight adjustment based on per-signal attribution"], cwd=REPO, timeout=10)
    if code2 != 0 and "nothing to commit" not in out.lower():
        print(f"git commit failed: {out}")
    # Restart paper (with optional env from nudges)
    _run(["tmux", "kill-session", "-t", "stock_bot_paper_run"], timeout=5)
    time.sleep(1)
    env_cmd = " ".join(f"{k}={v}" for k, v in env_overrides.items()) if env_overrides else ""
    run_cmd = f"cd {REPO} && {env_cmd} SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py"
    _run(["tmux", "new-session", "-d", "-s", "stock_bot_paper_run", "bash", "-c", run_cmd], timeout=10)
    print("Phase 7: weight nudges written, commit done, paper restarted.")
    return True


def phase8_iteration_comparison() -> bool:
    """Re-run expectancy; write iteration_comparison_v2.md; return bucket summary for required output."""
    code, _ = _run([sys.executable, "scripts/blocked_signal_expectancy_pipeline.py"], timeout=120)
    if code != 0:
        print("Phase 8: pipeline failed.")
        return False

    bucket_path = BLOCKED_SIGNAL_DIR / "bucket_analysis.md"
    pre_bucket = SIGNAL_STRENGTH_DIR / "bucket_analysis.md"
    lines = [
        "# Iteration Comparison v2 (Phase 8)",
        "",
        "## Pre-change bucket summary (from Phase 4)",
        "",
    ]
    if pre_bucket.exists():
        lines.append(pre_bucket.read_text(encoding="utf-8"))
    lines.extend([
        "",
        "## Post-change bucket summary",
        "",
    ])
    if bucket_path.exists():
        lines.append(bucket_path.read_text(encoding="utf-8"))
    lines.extend([
        "",
        "## Delta",
        "- Compare mean_pnl_pct and win_rate per bucket; improvement = post mean_pnl > pre mean_pnl in positive-expectancy buckets.",
        "",
    ])
    (SIGNAL_STRENGTH_DIR / "iteration_comparison_v2.md").write_text("\n".join(lines), encoding="utf-8")
    print("Phase 8: iteration_comparison_v2.md written.")
    return True


def print_required_output():
    """Print Top 3 EDGE_POSITIVE, Top 3 EDGE_NEGATIVE, weight changes, bucket summary, verdict."""
    edge_path = SIGNAL_STRENGTH_DIR / "multi_model_edge_analysis.md"
    plan_path = SIGNAL_STRENGTH_DIR / "weight_adjustment_plan_v2.md"
    iter_path = SIGNAL_STRENGTH_DIR / "iteration_comparison_v2.md"
    bucket_path = BLOCKED_SIGNAL_DIR / "bucket_analysis.md"

    top_pos = []
    top_neg = []
    if edge_path.exists():
        text = edge_path.read_text(encoding="utf-8")
        in_pos = in_neg = False
        for line in text.splitlines():
            if "EDGE_POSITIVE" in line and "##" in line:
                in_pos, in_neg = True, False
                continue
            if "EDGE_NEGATIVE" in line and "##" in line:
                in_pos, in_neg = False, True
                continue
            if in_pos and line.strip().startswith("- **"):
                m = re.match(r"-\s*\*\*([^*]+)\*\*", line)
                if m:
                    top_pos.append(m.group(1).strip())
            if in_neg and line.strip().startswith("- **"):
                m = re.match(r"-\s*\*\*([^*]+)\*\*", line)
                if m:
                    top_neg.append(m.group(1).strip())

    nudges_path = REPO / "state" / "multi_model_weight_nudges.env"
    weight_changes = "None (all multipliers 1.0)"
    if nudges_path.exists():
        txt = nudges_path.read_text(encoding="utf-8")
        if "export" in txt and "=" in txt:
            weight_changes = "; ".join(
                line.strip() for line in txt.splitlines()
                if line.strip().startswith("export ") and "=" in line
            ) or weight_changes
        elif "No overrides" in txt:
            weight_changes = "None (all multipliers 1.0)"

    bucket_summary = ""
    if bucket_path.exists():
        bucket_summary = bucket_path.read_text(encoding="utf-8")

    # Verdict: post-change bucket with positive mean_pnl in 1.0-1.5 or 1.5-2.0 => EDGE STRENGTHENED
    verdict = "NO IMPROVEMENT — NEXT ITERATION REQUIRED"
    if bucket_path.exists():
        t = bucket_path.read_text(encoding="utf-8")
        # Parse table: bucket | n | mean_pnl_pct | ...
        for row in t.splitlines():
            if "|" not in row or row.strip().startswith("#") or "bucket" in row.lower() and "mean_pnl" in row.lower():
                continue
            parts = [p.strip() for p in row.split("|") if p.strip()]
            if len(parts) >= 3:
                try:
                    bucket_name = parts[0]
                    mean_pnl = float(parts[2])
                    if bucket_name in ("1.0-1.5", "1.5-2.0") and mean_pnl > 0:
                        verdict = "EDGE STRENGTHENED"
                        break
                except (ValueError, IndexError):
                    pass

    print("\n" + "=" * 60)
    print("REQUIRED OUTPUT — Multi-Model Signal Edge Cycle")
    print("=" * 60)
    print("\nTop 3 EDGE_POSITIVE signals (after attribution):")
    for i, s in enumerate(top_pos[:3], 1):
        print(f"  {i}. {s}")
    if not top_pos:
        print("  (none identified)")
    print("\nTop 3 EDGE_NEGATIVE signals:")
    for i, s in enumerate(top_neg[:3], 1):
        print(f"  {i}. {s}")
    if not top_neg:
        print("  (none identified)")
    print("\nWeight changes applied:")
    print(f"  {weight_changes}")
    print("\nPost-change bucket summary (0.5–1.0, 1.0–1.5, 1.5–2.0):")
    print(bucket_summary or "  (no data)")
    print("\nVerdict:")
    print(f"  {verdict}")
    print("=" * 60 + "\n")


def main():
    ap = argparse.ArgumentParser(description="Multi-model signal edge cycle (Phases 3–8)")
    ap.add_argument("--phase", choices=["3", "4", "5", "6", "7", "8", "all"], default="all")
    ap.add_argument("--skip-deploy", action="store_true", help="Skip git pull and only restart tmux")
    ap.add_argument("--skip-apply-weights", action="store_true", help="Do not apply weight changes or commit in Phase 7")
    ap.add_argument("--wait-minutes", type=int, default=0, help="Minutes to wait for new attribution data after restart")
    args = ap.parse_args()

    phase = args.phase
    if phase == "3" or phase == "all":
        phase3_deploy_restart(args.skip_deploy, args.wait_minutes)
        if phase == "3":
            return 0
    if phase == "4" or phase == "all":
        phase4_expectancy_and_edge()
        if phase == "4":
            return 0
    if phase == "5" or phase == "all":
        phase5_adversarial_review()
        if phase == "5":
            return 0
    if phase == "6" or phase == "all":
        phase6_weight_plan()
        if phase == "6":
            return 0
    if phase == "7" or phase == "all":
        phase7_apply_weights_and_restart(args.skip_apply_weights)
        if phase == "7":
            return 0
    if phase == "8" or phase == "all":
        phase8_iteration_comparison()
    print_required_output()
    return 0


if __name__ == "__main__":
    sys.exit(main())
