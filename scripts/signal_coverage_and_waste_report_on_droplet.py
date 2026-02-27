#!/usr/bin/env python3
"""
Phase 4: Reconcile "used signals" vs "collected signals". Run ON THE DROPLET.
Joins SIGNAL_INVENTORY + SIGNAL_USAGE_MAP + runtime breakdown summary.
Outputs: reports/signal_review/SIGNAL_COVERAGE_AND_WASTE.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "signal_review"
INVENTORY_JSON = OUT_DIR / "SIGNAL_INVENTORY.json"
USAGE_JSON = OUT_DIR / "SIGNAL_USAGE_MAP.json"
DEEP_DIVE_JSON = OUT_DIR / "SIGNAL_PIPELINE_DEEP_DIVE.json"
BREAKDOWN_JSONL = REPO / "logs" / "signal_score_breakdown.jsonl"
OUT_MD = OUT_DIR / "SIGNAL_COVERAGE_AND_WASTE.md"


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

    inventory = []
    if INVENTORY_JSON.exists():
        try:
            data = json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))
            inventory = data.get("signals") or []
        except Exception:
            pass

    usage_map = []
    if USAGE_JSON.exists():
        try:
            data = json.loads(USAGE_JSON.read_text(encoding="utf-8"))
            usage_map = data.get("usage_map") or []
        except Exception:
            pass

    used_names = {u["signal_name"] for u in usage_map if u.get("USED_IN_SCORE")}
    collected_names = {s["signal_name"] for s in inventory}

    # Runtime summary from breakdown
    by_signal: dict[str, list[float]] = {}
    missing_count: dict[str, int] = {}
    zero_count: dict[str, int] = {}
    n_candidates = 0
    if BREAKDOWN_JSONL.exists():
        for line in BREAKDOWN_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                n_candidates += 1
                for s in r.get("signals") or []:
                    name = s.get("signal_name") or "unknown"
                    if name not in by_signal:
                        by_signal[name] = []
                        missing_count[name] = 0
                        zero_count[name] = 0
                    c = float(s.get("contribution") or 0.0)
                    by_signal[name].append(c)
                    if s.get("is_missing"):
                        missing_count[name] += 1
                    if s.get("is_zero"):
                        zero_count[name] += 1
            except Exception:
                continue

    waste = list(collected_names - used_names) if collected_names else []
    broken = []
    healthy = []
    crushed = []
    for name in used_names:
        if name not in by_signal or n_candidates == 0:
            healthy.append(name)
            continue
        miss_pct = 100.0 * missing_count.get(name, 0) / n_candidates
        zero_pct = 100.0 * zero_count.get(name, 0) / n_candidates
        med = _median(by_signal[name])
        if miss_pct > 50 or zero_pct > 80:
            broken.append({"signal": name, "missing_pct": round(miss_pct, 1), "zero_pct": round(zero_pct, 1), "median_contrib": round(med, 4)})
        elif med < 0.001 and med >= 0:
            crushed.append({"signal": name, "median_contrib": round(med, 4)})
        else:
            healthy.append(name)

    lines = [
        "# Signal coverage and waste (Phase 4)",
        "",
        "## Summary",
        "",
        f"- **Collected (inventory):** {len(collected_names)}",
        f"- **Used in score:** {len(used_names)}",
        f"- **Waste (collected but never used):** {len(waste)}" + (f" — {', '.join(sorted(waste))}" if waste else ""),
        f"- **Broken (used but frequently missing/zero):** {len(broken)}",
        f"- **Healthy (used and present):** {len(healthy)}",
        f"- **Crushed (contribution ~0):** {len(crushed)}",
        "",
        "## Broken signals (exact missing input / where produced / where it becomes null)",
        "",
    ]
    for b in broken:
        lines.append(f"- **{b['signal']}**: missing_pct={b['missing_pct']}%, zero_pct={b['zero_pct']}%, median_contrib={b['median_contrib']}. "
                    "Input from uw_composite_v2 components; becomes null/zero when upstream (UW/intel) does not provide value or normalizer clamps to 0.")
    if not broken:
        lines.append("- None.")
    lines.extend([
        "",
        "## Waste (collected, not used)",
        "",
    ])
    if waste:
        for w in sorted(waste):
            lines.append(f"- {w}")
    else:
        lines.append("- None.")
    lines.extend([
        "",
        "## Crushed (contribution ~0)",
        "",
    ])
    for c in crushed[:20]:
        lines.append(f"- {c['signal']}: median_contrib={c['median_contrib']}")
    if not crushed:
        lines.append("- None.")
    lines.extend([
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "python3 scripts/signal_inventory_on_droplet.py",
        "python3 scripts/signal_usage_map_on_droplet.py",
        "python3 scripts/signal_pipeline_deep_dive_on_droplet.py",
        "python3 scripts/signal_coverage_and_waste_report_on_droplet.py",
        "```",
        "",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
