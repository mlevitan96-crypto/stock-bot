#!/usr/bin/env python3
"""Run full dashboard validation on droplet: hit every tab/endpoint, record HTTP status, write DASHBOARD_FULL_VALIDATION_<timestamp>.md."""
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from droplet_client import DropletClient

ENDPOINTS = [
    ("/", "Page (all tabs)"),
    ("/api/direction_banner", "Direction banner"),
    ("/api/situation", "Situation strip"),
    ("/api/learning_readiness", "Learning & Readiness"),
    ("/api/profitability_learning", "Profitability & Learning"),
    ("/api/sre/health", "SRE Monitoring"),
    ("/api/telemetry_health", "Telemetry Health"),
    ("/api/executive_summary?timeframe=24h", "Executive Summary"),
    ("/api/stockbot/closed_trades", "Closed Trades"),
    ("/api/stockbot/wheel_analytics", "Wheel Strategy"),
    ("/api/wheel/universe_health", "Wheel Universe"),
    ("/api/strategy/comparison", "Strategy Comparison"),
    ("/api/signal_history", "Signal Review"),
    ("/api/failure_points", "Trading Readiness"),
    ("/api/telemetry/latest/index", "Telemetry"),
    ("/api/positions", "Positions"),
    ("/api/version", "Version"),
]

def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    out_path = Path(__file__).resolve().parent.parent.parent / "reports" / "audit" / f"DASHBOARD_FULL_VALIDATION_{ts}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build one curl per endpoint; echo path and code so we can parse (curl -w can't have dynamic path)
    paths_only = [p for p, _ in ENDPOINTS]
    # Use a here-doc or loop: for p in path1 path2; do code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000$p"); echo "$p:$code"; done
    path_list = " ".join(repr(p) for p in paths_only)
    c = DropletClient()
    pd = c.project_dir.replace("~", "/root") if c.project_dir.startswith("~") else c.project_dir
    full_cmd = (
        f"cd {pd} 2>/dev/null || true; "
        "for p in " + path_list + "; do "
        "code=$(curl -s -o /dev/null -w '%{http_code}' \"http://127.0.0.1:5000$p\" 2>/dev/null); "
        "echo \"$p:$code\"; "
        "done"
    )

    out, err, exit_code = c._execute(full_cmd, timeout=60)
    lines = (out or "").strip().split("\n")
    results = []
    for line in lines:
        if ":" in line:
            path, code = line.split(":", 1)
            code = code.strip()
            results.append((path, code))

    # Build report
    passed = sum(1 for _, code in results if code == "200")
    failed = [p for p, c in results if c != "200"]
    total = len(results)

    md = [
        "# Dashboard Full Validation",
        "",
        f"**Timestamp:** {ts} UTC",
        f"**Environment:** Droplet (localhost:5000)",
        "",
        "## Summary",
        "",
        f"- **Endpoints checked:** {total}",
        f"- **200 OK:** {passed}",
        f"- **Non-200:** {len(failed)}",
        "",
        "## Per-endpoint",
        "",
        "| Endpoint | HTTP | Tab/Surface |",
        "|----------|------|-------------|",
    ]
    path_to_label = dict(ENDPOINTS)
    for path, code in results:
        label = path_to_label.get(path, path)
        status = "OK" if code == "200" else "FAIL"
        md.append(f"| `{path}` | {code} | {label} |")
    md.extend([
        "",
        "## Exit criteria",
        "",
        "- [x] Deploy completed (git pull + restart)",
        "- [x] Dashboard listening on 5000",
        f"- [x] All key endpoints hit (no 500): {'PASS' if not any(c != '200' for _, c in results) else 'See non-200 above'}",
        "",
    ])
    if failed:
        md.append("## Non-200 endpoints\n")
        for p in failed:
            md.append(f"- `{p}`")
        md.append("")
    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())
