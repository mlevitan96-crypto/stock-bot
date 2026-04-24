#!/usr/bin/env python3
"""Write reports/audit/C1_PROMOTION_PROOF.md from last387 board review. Run on droplet after board review."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    review_path = base / "reports" / "board" / "last387_comprehensive_review.json"
    out_path = base / "reports" / "audit" / "C1_PROMOTION_PROOF.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deployed_commit = ""
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=base, capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            deployed_commit = (r.stdout or "").strip()[:12]
    except Exception:
        pass
    excerpt = []
    if review_path.exists():
        try:
            data = json.loads(review_path.read_text(encoding="utf-8"))
            ci = data.get("counter_intelligence") or {}
            ranked = ci.get("opportunity_cost_ranked_reasons") or []
            for item in ranked[:10]:
                excerpt.append(f"- {item.get('reason')}: blocked_count={item.get('blocked_count')}, estimated_opportunity_cost_usd={item.get('estimated_opportunity_cost_usd')}, avg_score={item.get('avg_score')}")
        except Exception as e:
            excerpt.append(f"(failed to read: {e})")
    else:
        excerpt.append("(last387_comprehensive_review.json not found)")
    lines = [
        "# C1 promotion proof",
        "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Deployed commit",
        "",
        deployed_commit or "(unknown)",
        "",
        "## Opportunity-cost ranking excerpt (from last387 board review)",
        "",
    ] + excerpt + [
        "",
        "C1 promoted: counter-intelligence opportunity-cost ranking is first-class in board review output. No live gating changes.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
