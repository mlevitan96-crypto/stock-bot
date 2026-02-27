#!/usr/bin/env python3
"""
Generate a ~300-word full strategy summary (entry/exit scores, signals) plus last-72h adjustments.
Run ON THE DROPLET to capture live configs. Output: reports/STRATEGY_SUMMARY_<DATE>.md
Usage: python3 scripts/generate_strategy_summary_on_droplet.py [--out path]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _git_log_since(hours: int = 72) -> str:
    try:
        out = subprocess.run(
            ["git", "log", f"--since={hours} hours ago", "--oneline", "--no-decorate"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return (out.stdout or "").strip()
    except Exception:
        return ""


def _git_log_stat_since(hours: int = 72) -> str:
    try:
        out = subprocess.run(
            ["git", "log", f"--since={hours} hours ago", "--stat", "--oneline", "-n", "50"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return (out.stdout or "").strip()
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="Output path (default: reports/STRATEGY_SUMMARY_<DATE>.md)")
    ap.add_argument("--hours", type=int, default=72, help="Hours for recent-adjustments window")
    args = ap.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = Path(args.out) if args.out else REPO / "reports" / f"STRATEGY_SUMMARY_{today}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Live config (from droplet) ---
    try:
        from config.registry import Thresholds, COMPOSITE_WEIGHTS_V2
    except Exception as e:
        Thresholds = None
        COMPOSITE_WEIGHTS_V2 = {}
        _reg_err = str(e)
    else:
        _reg_err = None

    try:
        from uw_composite_v2 import WEIGHTS_V3, ENTRY_THRESHOLDS
    except Exception as e:
        WEIGHTS_V3 = {}
        ENTRY_THRESHOLDS = {}
        _uw_err = str(e)
    else:
        _uw_err = None

    try:
        from adaptive_signal_optimizer import EXIT_COMPONENTS, ExitSignalModel
        model = ExitSignalModel()
        exit_weights = model.base_weights
    except Exception as e:
        EXIT_COMPONENTS = []
        exit_weights = {}
        _exit_err = str(e)
    else:
        _exit_err = None

    min_exec = getattr(Thresholds, "MIN_EXEC_SCORE", None) if Thresholds else None
    if min_exec is None:
        min_exec = "N/A (registry load failed)"

    trail_pct = getattr(Thresholds, "TRAILING_STOP_PCT", None) if Thresholds else None
    time_exit_min = getattr(Thresholds, "TIME_EXIT_MINUTES", None) if Thresholds else None
    time_exit_stale_days = getattr(Thresholds, "TIME_EXIT_DAYS_STALE", None) if Thresholds else None
    stale_pnl_thresh = getattr(Thresholds, "TIME_EXIT_STALE_PNL_THRESH_PCT", None) if Thresholds else None

    entry_signal_names = sorted([k for k in (WEIGHTS_V3 or {}).keys() if not k.startswith("_")])
    cw_version = (COMPOSITE_WEIGHTS_V2 or {}).get("version", "N/A")

    git_log = _git_log_since(args.hours)
    git_stat = _git_log_stat_since(args.hours)
    adjustments = []
    for line in git_log.splitlines()[:40]:
        line = line.strip()
        if line:
            adjustments.append(line)
    adjustment_blurb = "\n".join(adjustments) if adjustments else "No commits in the last 72 hours."
    if len(git_stat) > 4000:
        adjustment_blurb += "\n\n(Recent file changes: see git log --stat on droplet.)"

    # --- Build ~300 word narrative ---
    sections = []

    # Strategy (entry + exit) ~250 words
    sections.append("# Stock-Bot Strategy Summary (Live Droplet Config)\n")
    sections.append(f"*Generated on droplet: {datetime.now(timezone.utc).isoformat()}*\n")

    sections.append("## Entry\n")
    sections.append("- **Score gate:** Trades are taken only when the composite **exec score** meets or exceeds **MIN_EXEC_SCORE** (live value: **{}**). ".format(min_exec))
    sections.append("Direction: score >= 3.0 -> long; otherwise short. ")
    sections.append("Hierarchical thresholds (base/canary/champion) from uw_composite_v2 ENTRY_THRESHOLDS: base {:.1f}, canary {:.1f}, champion {:.1f}. ".format(
        ENTRY_THRESHOLDS.get("base", 0), ENTRY_THRESHOLDS.get("canary", 0), ENTRY_THRESHOLDS.get("champion", 0)))
    sections.append("Composite uses **config/registry COMPOSITE_WEIGHTS_V2** (version: {}). ".format(cw_version))
    sections.append("**Entry signal components** (uw_composite_v2 WEIGHTS_V3): options_flow, dark_pool, insider, iv_term_skew, smile_slope, whale_persistence, event_alignment, toxicity_penalty, temporal_motif, regime_modifier; congress, shorts_squeeze, institutional, market_tide, calendar_catalyst, etf_flow; greeks_gamma, ftd_pressure, iv_rank, oi_change, squeeze_score. ")
    sections.append("Structural layer (COMPOSITE_WEIGHTS_V2): vol/beta reward, UW strength proxy, premarket alignment, regime/posture alignment, with optional shaping. ")
    sections.append("Max concurrent positions: {}; position size and spread/watchdog limits apply.\n".format(
        getattr(Thresholds, "MAX_CONCURRENT_POSITIONS", "N/A") if Thresholds else "N/A"))

    sections.append("## Exit\n")
    sections.append("**Exit urgency** (adaptive_signal_optimizer): urgency = sum of weighted components; **urgency >= 6.0 -> EXIT**, **>= 3.0 -> REDUCE**, else **HOLD**. ")
    sections.append("**Exit signal components** (and default weights): entry_decay (1.0), adverse_flow (1.2), drawdown_velocity (1.5), time_decay (0.8), momentum_reversal (1.3), volume_exhaustion (0.9), support_break (1.4). ")
    sections.append("Entry decay: when current_score/entry_score < 0.7. Adverse flow: flow reversal vs position direction. Loss limit: +2.0 urgency if current_pnl_pct < -5%. ")
    sections.append("**Hard/rule-based exits:** Trailing stop at **TRAILING_STOP_PCT** (live: **{}**); ".format(trail_pct))
    sections.append("time exit at **TIME_EXIT_MINUTES** (live: **{}**); ".format(time_exit_min))
    sections.append("stale position: age >= **TIME_EXIT_DAYS_STALE** ({} days) and PnL < **TIME_EXIT_STALE_PNL_THRESH_PCT** ({}). ".format(
        time_exit_stale_days, stale_pnl_thresh))
    sections.append("Profit acceleration: after 30 min in profit, trailing stop can tighten to 0.5%; in MIXED regime default trail 1.0%. ")
    sections.append("Displacement and regime-protection exits also apply.\n")

    sections.append("## Adjustments in the Last 72 Hours\n")
    sections.append("```\n")
    sections.append(adjustment_blurb)
    sections.append("\n```\n")

    if _reg_err:
        sections.append("\n*Note: registry load error: {}*\n".format(_reg_err))
    if _uw_err:
        sections.append("\n*Note: uw_composite_v2 load error: {}*\n".format(_uw_err))
    if _exit_err:
        sections.append("\n*Note: exit model load error: {}*\n".format(_exit_err))

    body = "".join(sections)
    out_path.write_text(body, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Word count (approx): {len(body.split())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
