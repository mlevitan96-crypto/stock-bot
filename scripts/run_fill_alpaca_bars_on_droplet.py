#!/usr/bin/env python3
"""Run fill_alpaca_bars_30d.py on droplet via DropletClient. Get live output and fetch results."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/fill_alpaca_bars_30d.py",
    "scripts/analysis/find_exits_missing_bars.py",
    "scripts/analysis/fetch_missing_bars_from_alpaca.py",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    rc = 1

    with DropletClient() as c:
        for rel in FILES:
            local = REPO / rel
            if not local.is_file():
                print(f"Skip (missing): {rel}", file=sys.stderr)
                continue
            remote = f"{pd}/{rel}".replace("\\", "/")
            remote_dir = "/".join(remote.split("/")[:-1])
            c._execute(f"mkdir -p '{remote_dir}'", timeout=5)
            try:
                c.put_file(local, remote)
                print(f"Uploaded: {rel}")
            except Exception as e:
                print(f"Upload failed {rel}: {e}", file=sys.stderr)

        # Ensure data/bars exists; source .env for Alpaca keys; run fill (last 30d from exit_attribution)
        cmd = (
            f"cd {c.project_dir} && mkdir -p data/bars && "
            "[ -f .env ] && set -a && source .env && set +a; "
            "python3 scripts/fill_alpaca_bars_30d.py --days 30 --max_days_per_symbol 20"
        )
        print("\n--- Running fill_alpaca_bars_30d.py on droplet (live) ---\n")
        out, err, rc = c._execute(cmd, timeout=600)

        print(out or "(no stdout)")
        if err:
            print("stderr:", err[:2000] if len(err) > 2000 else err)
        print("exit code:", rc)

        # Fetch latest fill_bars run dir
        list_out, _, _ = c._execute(
            "ls -td reports/exit_review/fill_bars_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_dir = (list_out or "").strip()
        if run_dir:
            for name in ["missing_bars.json", "normalized_exit_truth.json"]:
                content, _, _ = c._execute(f"cat {run_dir}/{name} 2>/dev/null || true", timeout=10)
                if content and len(content) > 10:
                    local_dir = REPO / "reports" / "exit_review" / Path(run_dir).name
                    local_dir.mkdir(parents=True, exist_ok=True)
                    (local_dir / name).write_text(content, encoding="utf-8")
                    print(f"Fetched: {run_dir}/{name} -> {local_dir / name}")

    return rc


if __name__ == "__main__":
    sys.exit(main())
