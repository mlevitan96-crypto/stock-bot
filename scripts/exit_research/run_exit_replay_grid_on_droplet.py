#!/usr/bin/env python3
"""
Run the full exit replay grid ON THE DROPLET (real 30d data), then fetch all artifacts to local.
Offline only on droplet; no live config changes.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"
    with DropletClient() as c:
        c._execute(f"mkdir -p {proj}/scripts/exit_research {proj}/scripts/analysis {proj}/reports/exit_research/scenarios")
        for local_name, remote_path in [
            ("scripts/exit_research/exit_replay_config.json", f"{proj}/scripts/exit_research/exit_replay_config.json"),
            ("scripts/exit_research/exit_scenarios.json", f"{proj}/scripts/exit_research/exit_scenarios.json"),
            ("scripts/exit_research/exit_component_map.py", f"{proj}/scripts/exit_research/exit_component_map.py"),
            ("scripts/exit_research/run_exit_replay_scenario.py", f"{proj}/scripts/exit_research/run_exit_replay_scenario.py"),
            ("scripts/exit_research/run_exit_replay_grid.py", f"{proj}/scripts/exit_research/run_exit_replay_grid.py"),
            ("scripts/analysis/attribution_loader.py", f"{proj}/scripts/analysis/attribution_loader.py"),
        ]:
            local = REPO / local_name
            if local.exists():
                c.put_file(local, remote_path)

        cmd = f"cd {proj} && python3 scripts/exit_research/run_exit_replay_grid.py --base {proj}"
        out, err, rc = c._execute(cmd, timeout=300)
        print(out)
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Grid run exited with", rc, file=sys.stderr)
            return rc

        for name in [
            "exit_replay_grid_summary.json",
            "exit_replay_grid_summary.md",
            "exit_replay_ranked_scenarios.json",
            "exit_replay_ranked_scenarios.md",
        ]:
            src = f"{proj}/reports/exit_research/{name}"
            try:
                content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
                if content.strip():
                    dest = REPO / "reports" / "exit_research" / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    print(f"Fetched {name}", file=sys.stderr)
            except Exception as e:
                print(f"Could not fetch {name}: {e}", file=sys.stderr)

        # Fetch top scenario summaries
        for scenario_name in ["baseline", "minhold_15", "minhold_60", "decay_086", "minhold_15_decay_086"]:
            src = f"{proj}/reports/exit_research/scenarios/{scenario_name}/summary.json"
            try:
                content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
                if content.strip():
                    dest = REPO / "reports" / "exit_research" / "scenarios" / scenario_name / "summary.json"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
            except Exception:
                pass

    print("Exit replay grid artifacts in reports/exit_research/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
