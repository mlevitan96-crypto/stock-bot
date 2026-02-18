#!/usr/bin/env python3
"""
Run on droplet (via DropletClient): trace exit_attribution.jsonl for exit_quality_metrics / high_water / giveback,
and fetch entry_vs_exit_blame.json for blame trace. Writes reports/phase9_data_integrity/20260218_*_trace.md locally.
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


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    with DropletClient() as c:
        # Sample exit_attribution: last 200 lines, check for exit_quality_metrics
        out_tail, _, _ = c._execute_with_cd(
            "tail -n 200 logs/exit_attribution.jsonl 2>/dev/null || true",
            timeout=15,
        )
        lines = (out_tail or "").strip().split("\n")
        with_eqm = 0
        with_giveback = 0
        with_mfe = 0
        with_high_water = 0
        samples_with = []
        samples_without = []
        for line in lines:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            eqm = r.get("exit_quality_metrics") or {}
            has_eqm = bool(eqm)
            has_gb = eqm.get("profit_giveback") is not None
            has_mfe = eqm.get("mfe") is not None
            # high_water is not in exit_attribution record; it's in info before we call log. So we can't see it in logs.
            if has_eqm:
                with_eqm += 1
            if has_gb:
                with_giveback += 1
            if has_mfe:
                with_mfe += 1
            if len(samples_with) < 3 and has_gb:
                samples_with.append({"symbol": r.get("symbol"), "profit_giveback": eqm.get("profit_giveback"), "mfe": eqm.get("mfe")})
            if len(samples_without) < 3 and not has_gb and has_eqm:
                samples_without.append({"symbol": r.get("symbol"), "eqm_keys": list(eqm.keys()) if eqm else []})

        # Count total lines in file
        out_wc, _, _ = c._execute_with_cd("wc -l logs/exit_attribution.jsonl 2>/dev/null || echo 0", timeout=10)
        total_lines = int((out_wc or "0").split()[0]) if out_wc else 0

    # Write exit quality trace
    trace_lines = [
        "# Exit quality end-to-end trace (2026-02-18)",
        "",
        "## 1) Where exit quality is computed",
        "",
        "- **main.py** → `log_exit_attribution()` (around 2170–2226) calls `compute_exit_quality_metrics()` from `src/exit/exit_quality_metrics.py`.",
        "- **Input:** `high_water = (info.get(\"high_water\") or entry_price)`. So **info[\"high_water\"]** must be set by the caller; otherwise we default to entry_price → MFE = 0 → profit_giveback = None.",
        "",
        "## 2) Inspection of logs/exit_attribution.jsonl (droplet)",
        "",
        f"- **Total lines in file:** {total_lines}",
        f"- **Sample (last 200 lines):** {len(lines)} lines parsed.",
        f"- **Records with exit_quality_metrics present:** {with_eqm}",
        f"- **Records with profit_giveback non-null:** {with_giveback}",
        f"- **Records with mfe non-null:** {with_mfe}",
        "",
        "### Sample records WITH profit_giveback",
        "```json",
        json.dumps(samples_with, indent=2),
        "```",
        "",
        "### Sample records with exit_quality_metrics but WITHOUT profit_giveback",
        "```json",
        json.dumps(samples_without, indent=2),
        "```",
        "",
        "## 3) Why giveback is N/A",
        "",
        "- **high_water** is not stored in exit_attribution.jsonl; it is only used inside `log_exit_attribution` to compute MFE. If the **caller** does not set **info[\"high_water\"]**, we use `entry_price` → MFE = 0 for long → no giveback.",
        "- **Root cause:** The two call sites (displacement exit ~5545, time/trail exit ~7227) pass **info** from `self.opens.get(symbol, {})` or similar; **info** does not include **high_water** unless the executor has been updating it in opens/metadata. The executor tracks **self.high_water[symbol]** separately but never injects it into **info** before calling `log_exit_attribution`.",
        "- **Fix:** Before each `log_exit_attribution(..., info=info, ...)`, set `info[\"high_water\"] = self.high_water.get(symbol, info.get(\"high_water\") or entry_price)` so that giveback can be computed when the position had upside.",
        "",
    ]
    (OUT_DIR / f"{DATE}_exit_quality_trace.md").write_text("\n".join(trace_lines), encoding="utf-8")
    print("Wrote", OUT_DIR / f"{DATE}_exit_quality_trace.md")

    # Blame trace: fetch entry_vs_exit_blame from baseline v2
    with DropletClient() as c:
        out_blame, _, _ = c._execute_with_cd(
            "cat reports/effectiveness_baseline_blame_v2/entry_vs_exit_blame.json 2>/dev/null || echo '{}'",
            timeout=10,
        )
    blame = {}
    try:
        blame = json.loads(out_blame) if out_blame and out_blame.strip() else {}
    except Exception:
        pass
    blame_lines = [
        "# Blame classification trace (2026-02-18)",
        "",
        "## 1) entry_vs_exit_blame.json (effectiveness_baseline_blame_v2)",
        "",
        "```json",
        json.dumps(blame, indent=2)[:2500],
        "```",
        "",
        "## 2) Why everything is unclassified",
        "",
        "- **Weak entry** requires `entry_score` present and **< 3.0**. Joined rows get `entry_score` from attribution (context.entry_score). If attribution does not write context.entry_score, joined rows lack it → score treated as 0 → condition `score > 0 and score < 3` is false.",
        "- **Exit timing** requires `exit_quality_metrics.profit_giveback >= 0.3` or (MFE > 0 and PnL < 0). If exit_attribution rarely has profit_giveback/MFE (because high_water was missing), no loser is classified as exit_timing.",
        "- **Result:** 100% unclassified until (1) attribution writes entry_score into context, (2) exit_attribution has giveback/MFE from high_water fix.",
        "",
        "## 3) Modifications to blame logic",
        "",
        "- **Do NOT loosen classification rules.** Only ensure **unclassified_count** and **unclassified_pct** are always present in the report so we never show silent 0/0.",
        "- Script `scripts/analysis/run_effectiveness_reports.py` already includes unclassified_count and unclassified_pct in `build_entry_vs_exit_blame`; after deploy and re-run, baseline v3 will show them explicitly.",
        "",
    ]
    (OUT_DIR / f"{DATE}_blame_trace.md").write_text("\n".join(blame_lines), encoding="utf-8")
    print("Wrote", OUT_DIR / f"{DATE}_blame_trace.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
