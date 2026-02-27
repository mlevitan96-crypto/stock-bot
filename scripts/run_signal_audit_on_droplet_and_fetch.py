#!/usr/bin/env python3
"""
Fetch droplet's uw_flow_cache, run signal_audit_diagnostic locally, write SIGNAL_FLOW_FINDINGS.md.
Use when we need full signal flow and which signals are zero/missing/not wired.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
FETCHED_DIR = REPO / "reports" / "investigation" / "fetched"
FINDINGS_MD = REPO / "reports" / "investigation" / "SIGNAL_FLOW_FINDINGS.md"
CACHE_JSON = REPO / "data" / "uw_flow_cache.json"


def main() -> int:
    try:
        from droplet_client import DropletClient
    except Exception as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1

    pd = "~/stock-bot"
    FETCHED_DIR.mkdir(parents=True, exist_ok=True)
    FINDINGS_MD.parent.mkdir(parents=True, exist_ok=True)
    CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        # 1) Fetch droplet's uw_flow_cache.json (droplet has it; script may not be on droplet)
        out_cat, _, _ = c._execute(f"cat {pd}/data/uw_flow_cache.json 2>/dev/null || echo '{{\"error\":\"no cache\"}}'", timeout=30)
        raw_cache = (out_cat or "").strip()
        if not raw_cache or "error" in raw_cache[:100]:
            FINDINGS_MD.write_text(
                "# Signal flow findings (from droplet)\n\n"
                "Could not fetch data/uw_flow_cache.json from droplet. Cache missing or empty.\n",
                encoding="utf-8",
            )
            print("No cache on droplet.")
            return 1
        try:
            cache_data = json.loads(raw_cache)
        except json.JSONDecodeError:
            FINDINGS_MD.write_text("# Signal flow findings\n\nCache fetch was not valid JSON.\n", encoding="utf-8")
            return 1
        CACHE_JSON.write_text(json.dumps(cache_data, indent=0, default=str), encoding="utf-8")
        print(f"Fetched cache: {len(cache_data)} keys")

        # 2) Run diagnostic locally with droplet's cache
        import subprocess
        r = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "signal_audit_diagnostic.py")],
            cwd=str(REPO), capture_output=True, text=True, timeout=90,
        )
        raw = (r.stdout or "").strip()
        if r.stderr:
            print(r.stderr[:500], file=sys.stderr)
        if not raw:
            FINDINGS_MD.write_text(
                "# Signal flow findings (from droplet)\n\n"
                "signal_audit_diagnostic.py produced no output. Check: data/uw_flow_cache.json exists; script runs without import errors.\n",
                encoding="utf-8",
            )
            print("No output from diagnostic.")
            return 1
        try:
            audit = json.loads(raw)
        except json.JSONDecodeError:
            (FETCHED_DIR / "signal_audit_diagnostic_raw.txt").write_text(raw[:80000], encoding="utf-8")
            FINDINGS_MD.write_text(
                "# Signal flow findings (from droplet)\n\nDiagnostic output was not valid JSON. Raw saved to fetched/signal_audit_diagnostic_raw.txt\n",
                encoding="utf-8",
            )
            print("Diagnostic output was not JSON.")
            return 1
        (FETCHED_DIR / "signal_audit_diagnostic.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
        print(f"sample_size={audit.get('sample_size', 0)}, error={audit.get('error')}, dead_or_muted={len(audit.get('dead_or_muted', []))}")

        # Write SIGNAL_FLOW_FINDINGS.md
        lines = [
            "# Signal flow findings (from droplet)",
            "",
            "Source: `scripts/signal_audit_diagnostic.py` run on droplet with `data/uw_flow_cache.json`. Enrichment path: enrich_signal → compute_composite_score_v2 (same as main.py when available).",
            "",
            "## Summary",
            "",
            f"- **Sample size:** {audit.get('sample_size', 0)} symbols",
            f"- **Error:** {audit.get('error') or 'None'}",
            f"- **Composite distribution:** {audit.get('composite_distribution', {})}",
            "",
            "## Signals not working / passing 0 / not wired",
            "",
        ]
        dead = audit.get("dead_or_muted") or []
        if dead:
            lines.append("| signal_name | failure_mode | suspected_root_cause | confidence |")
            lines.append("|-------------|--------------|----------------------|------------|")
            for d in dead:
                lines.append(f"| {d.get('signal_name', '')} | {d.get('failure_mode', '')} | {d.get('suspected_root_cause', '')} | {d.get('confidence', '')} |")
        else:
            lines.append("(None identified as dead_or_muted by diagnostic.)")
        lines.extend(["", "## Value audit (per-signal across samples)", ""])
        va = audit.get("value_audit") or {}
        for name in sorted(va.keys(), key=lambda n: (va[n].get("pct_zero", 100), -(va[n].get("mean") or 0))):
            v = va[name]
            lines.append(f"- **{name}:** mean={v.get('mean')}, pct_zero={v.get('pct_zero')}%, constant={v.get('constant')}")
        lines.extend(["", "## Per-symbol breakdown (SPY, QQQ, COIN, NVDA, TSLA)", ""])
        per = audit.get("per_symbol") or {}
        for sym in ["SPY", "QQQ", "COIN", "NVDA", "TSLA"]:
            p = per.get(sym) or {}
            if "error" in p:
                lines.append(f"### {sym}: {p.get('error')}")
            else:
                lines.append(f"### {sym}: score={p.get('score')}, missing={p.get('missing_components', [])}")
                src = p.get("component_sources") or {}
                comps = p.get("components") or {}
                zero_or_missing = [n for n in comps if src.get(n) == "missing" or (comps.get(n) or 0) == 0]
                if zero_or_missing:
                    lines.append(f"- Zero or missing: {', '.join(zero_or_missing)}")
            lines.append("")
        lines.append("## Root cause (why low scores)")
        lines.append("")
        dist = audit.get("composite_distribution") or {}
        mean_score = dist.get("mean")
        if mean_score is not None and float(mean_score) < 2.5:
            lines.append(f"Composite mean score is **{mean_score}** (below MIN_EXEC_SCORE 2.5). ")
        if dead:
            lines.append(f"**{len(dead)}** signals are dead or muted (zeroed, unweighted, or no contribution). ")
        lines.append("Primary drivers: (1) Many components default to 0.2 or 0.25 when data is missing (congress, shorts, institutional, market_tide, calendar, greeks, ftd, oi, etf, squeeze_score). (2) Flow/conviction/dark_pool/insider from UW cache—if cache is sparse or conviction/sentiment missing, flow component is small. (3) Freshness decay: if data is stale, composite_raw * freshness drops. **Fix:** Ensure UW cache is populated and fresh; ensure expanded_intel has symbol data; check conviction/sentiment not None in cache.")
        lines.append("")
        FINDINGS_MD.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {FINDINGS_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
