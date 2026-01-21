#!/usr/bin/env python3
"""
Intel Dashboard Generator (additive)
===================================

Inputs:
- state/daily_universe*.json
- state/premarket_intel.json, state/postmarket_intel.json
- state/regime_state.json
- state/uw_intel_pnl_summary.json
- logs/uw_attribution.jsonl (tail)
- state/intel_health_state.json (optional)

Output:
- reports/INTEL_DASHBOARD_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _tail_jsonl(path: Path, n: int = 30) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
        out: List[Dict[str, Any]] = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
                if isinstance(rec, dict):
                    out.append(rec)
            except Exception:
                continue
        return out
    except Exception:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    args = ap.parse_args()

    day = args.date.strip() or datetime.now(timezone.utc).date().isoformat()

    daily = _read_json(Path("state/daily_universe.json"))
    daily_v2 = _read_json(Path("state/daily_universe_v2.json"))
    pm = _read_json(Path("state/premarket_intel.json"))
    post = _read_json(Path("state/postmarket_intel.json"))
    regime = _read_json(Path("state/regime_state.json"))
    pnl = _read_json(Path("state/uw_intel_pnl_summary.json"))
    health = _read_json(Path("state/intel_health_state.json"))
    daemon_health = _read_json(Path("state/uw_daemon_health_state.json"))
    attrib_tail = _tail_jsonl(Path("logs/uw_attribution.jsonl"), n=25)

    out_path = Path("reports") / f"INTEL_DASHBOARD_{day}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append(f"# Intel Dashboard — {day}")
    lines.append("")

    # 1) Universe Overview
    lines.append("## 1. Universe Overview")
    du_n = len(daily.get("symbols") or []) if isinstance(daily, dict) else 0
    du2_n = len(daily_v2.get("symbols") or []) if isinstance(daily_v2, dict) else 0
    lines.append(f"- Daily universe (v1): **{du_n}**")
    lines.append(f"- Daily universe (v2, shadow-only): **{du2_n}**")
    if isinstance(daily, dict) and isinstance(daily.get("_meta"), dict):
        lines.append(f"- Universe v1 version: `{daily['_meta'].get('version','')}`")
    if isinstance(daily_v2, dict) and isinstance(daily_v2.get("_meta"), dict):
        lines.append(f"- Universe v2 version: `{daily_v2['_meta'].get('version','')}`")
    lines.append("")

    # 2) Premarket/Postmarket Intel
    lines.append("## 2. Premarket/Postmarket Intel")
    pm_n = len((pm.get("symbols") or {}).keys()) if isinstance(pm.get("symbols"), dict) else 0
    post_n = len((post.get("symbols") or {}).keys()) if isinstance(post.get("symbols"), dict) else 0
    pm_ver = (pm.get("_meta") or {}).get("uw_intel_version", "") if isinstance(pm.get("_meta"), dict) else ""
    post_ver = (post.get("_meta") or {}).get("uw_intel_version", "") if isinstance(post.get("_meta"), dict) else ""
    lines.append(f"- Premarket intel symbols: **{pm_n}** (version `{pm_ver}`)")
    lines.append(f"- Postmarket intel symbols: **{post_n}** (version `{post_ver}`)")
    lines.append("")

    # 3) Regime & Sector Profiles
    lines.append("## 3. Regime & Sector Profiles")
    if regime:
        lines.append(f"- Regime: **{regime.get('regime_label','NEUTRAL')}** (conf {regime.get('regime_confidence',0.0)})")
        meta = regime.get("_meta") if isinstance(regime.get("_meta"), dict) else {}
        lines.append(f"- Regime engine version: `{(meta or {}).get('version','')}`")
    else:
        lines.append("- Regime state missing.")
    lines.append("")

    # 4) UW Attribution Highlights
    lines.append("## 4. UW Attribution Highlights (tail)")
    if not attrib_tail:
        lines.append("- No attribution records yet.")
    else:
        for rec in attrib_tail[-10:]:
            sym = rec.get("symbol", "")
            d = rec.get("direction", "")
            c = (rec.get("uw_contribution") or {}).get("score_delta", 0.0) if isinstance(rec.get("uw_contribution"), dict) else 0.0
            lines.append(f"- **{sym}** dir={d} uw_score_delta={c}")
    lines.append("")

    # 5) UW Intel P&L Summary
    lines.append("## 5. UW Intel P&L Summary")
    counts = pnl.get("counts") if isinstance(pnl.get("counts"), dict) else {}
    lines.append(f"- Attribution records: **{counts.get('attribution_records',0)}**, matched: **{counts.get('matched_to_pnl',0)}**")
    byf = pnl.get("by_feature") if isinstance(pnl.get("by_feature"), dict) else {}
    if not byf:
        lines.append("- No per-feature P&L aggregates available yet.")
    else:
        for k in sorted(byf.keys()):
            r = byf[k]
            if not isinstance(r, dict):
                continue
            lines.append(f"- **{k}**: win_rate={r.get('win_rate')}, avg_pnl_pct={r.get('avg_pnl_pct')}, avg_score_delta={r.get('avg_score_delta')}")
    lines.append("")

    # 6) Health & Self-Healing Status
    lines.append("## 6. Health & Self-Healing Status")
    if health:
        ok = bool(health.get("ok", False))
        lines.append(f"- Health: **{'OK' if ok else 'NOT_OK'}**")
        checks = health.get("checks") if isinstance(health.get("checks"), list) else []
        lines.append(f"- Checks: **{len(checks)}**")
        for c in checks[:12]:
            if isinstance(c, dict):
                lines.append(f"  - {c.get('name','')}: {c.get('status','')}")
    else:
        lines.append("- Health state missing (run `scripts/run_intel_health_checks.py`).")

    lines.append("")
    # 7) UW Flow Daemon Health
    lines.append("## 7. UW Flow Daemon Health")
    if daemon_health:
        lines.append(f"- Status: **{daemon_health.get('status','unknown')}**")
        det = daemon_health.get("details") if isinstance(daemon_health.get("details"), dict) else {}
        lines.append(f"- PID ok: **{daemon_health.get('pid_ok')}** (ExecMainPID={det.get('exec_main_pid')})")
        lines.append(f"- Lock ok: **{daemon_health.get('lock_ok')}** (lock_pid={det.get('lock_pid')}, held={det.get('lock_held')})")
        lines.append(f"- Poll fresh: **{daemon_health.get('poll_fresh')}** (age_sec={det.get('flow_cache_age_sec')})")
        lines.append(f"- Crash loop: **{daemon_health.get('crash_loop')}** (restarts={det.get('n_restarts')})")
        lines.append(f"- Endpoint errors: **{daemon_health.get('endpoint_errors')}** (counts={det.get('endpoint_error_counts')})")
        sh = det.get("self_heal") if isinstance(det.get("self_heal"), dict) else {}
        if sh:
            lines.append(f"- Self-heal attempted: **{sh.get('attempted', False)}** (success={sh.get('success', None)})")
    else:
        lines.append("- Daemon health state missing (run `scripts/run_daemon_health_check.py`).")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

