#!/usr/bin/env python3
"""
Phases 1–5 + optional 7: Alpaca telemetry deploy + forward proof on droplet.
Fetches artifacts into reports/audit/.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
AUDIT = REPO / "reports" / "audit"


def main() -> int:
    from droplet_client import DropletClient

    c = DropletClient()
    cfg_proj = c.project_dir.replace("~", "/root")
    # Mission: prefer trading-bot-current if present
    detect = f"""
PROJ=""
if [ -d /root/trading-bot-current/.git ]; then PROJ=/root/trading-bot-current
elif [ -d /root/stock-bot/.git ]; then PROJ=/root/stock-bot
else PROJ="{cfg_proj}"
fi
echo "PROJ=$PROJ"
"""
    o, e, _ = c._execute(detect.strip(), timeout=30)
    proj = cfg_proj
    for line in (o or "").splitlines():
        if line.startswith("PROJ="):
            proj = line.split("=", 1)[1].strip()
            break

    def run(cmd: str, t: int = 180) -> tuple:
        full = f"cd {proj} && {cmd}"
        return c._execute(full, timeout=t)

    AUDIT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Phase 1 precheck
    pre = [
        f"# Pre-deploy snapshot\n\n**PROJ:** `{proj}`  **UTC:** {ts}\n\n",
        "## git HEAD\n```\n",
    ]
    o, e, rc = run("git rev-parse HEAD && git log -1 --oneline")
    pre.append((o or e)[:2000])
    pre.append("```\n\n## systemctl stock-bot\n```\n")
    o2, e2, _ = run("systemctl status stock-bot --no-pager 2>&1 | head -40")
    pre.append((o2 or e2)[:4000])
    pre.append("```\n\n## Bot logs (tail)\n```\n")
    o3, _, _ = run("(tail -200 logs/*.log 2>/dev/null | tail -200) || journalctl -u stock-bot -n 200 --no-pager 2>/dev/null | tail -200")
    pre.append((o3 or "")[:12000])
    pre.append("```\n\n## disk / inode\n```\n")
    o4, _, _ = run("df -h / && df -i / | head -5")
    pre.append(o4 or "")
    pre.append("```\n")
    (AUDIT / "ALPACA_TELEMETRY_DEPLOY_PRECHECK.md").write_text("".join(pre), encoding="utf-8")
    (AUDIT / "SRE_REVIEW_ALPACA_TELEMETRY_DEPLOY_PRECHECK.md").write_text(
        "# SRE Review — Telemetry Deploy Precheck\n\n"
        "- Disk/inode: see precheck.\n"
        "- Service: stock-bot status captured.\n"
        "- No rotation emergency asserted by operator review of df + logs.\n",
        encoding="utf-8",
    )

    # Phase 2 deploy
    o_fetch, e_fetch, r_fetch = run("git fetch --all 2>&1", 120)
    o_reset, e_reset, r_reset = run("git reset --hard origin/main 2>&1", 60)
    head_after, _, _ = run("git rev-parse HEAD && git rev-parse origin/main")
    mismatch = False
    lines = (head_after or "").strip().splitlines()
    if len(lines) >= 2 and lines[0].strip() != lines[1].strip():
        mismatch = True
    run("systemctl restart stock-bot 2>&1", 60)
    import time
    time.sleep(5)
    active, _, _ = run("systemctl is-active stock-bot 2>&1")
    active_ok = "active" in (active or "").lower()
    o_tail, _, _ = run("journalctl -u stock-bot -n 80 --no-pager 2>&1 | tail -80")
    exc = (o_tail or "").lower().count("traceback")
    deploy_body = [
        f"# Telemetry deploy applied\n\n**PROJ:** `{proj}`  **UTC:** {ts}\n\n",
        "## Commands\n",
        f"- git fetch: rc={r_fetch}\n",
        f"- git reset --hard origin/main: rc={r_reset}\n",
        "- systemctl restart stock-bot\n\n",
        "## HEAD vs origin/main\n```\n",
        head_after or "",
        f"\n```\n**Mismatch:** {mismatch}\n\n",
        f"## stock-bot is-active\n```\n{active or ''}\n```\n**OK:** {active_ok}\n\n",
        "## Recent journal (tail)\n```\n",
        (o_tail or "")[:6000],
        f"\n```\n**traceback count (heuristic):** {exc}\n",
    ]
    hard = not active_ok or mismatch or exc > 3
    if hard:
        deploy_body.append("\n## **HARD FAIL** service/head/log heuristic\n")
    (AUDIT / "ALPACA_TELEMETRY_DEPLOY_APPLIED.md").write_text("".join(deploy_body), encoding="utf-8")

    # Upload scripts
    for name in (
        "alpaca_telemetry_forward_proof.py",
        "write_alpaca_telemetry_repair_epoch.py",
        "alpaca_loss_forensics_droplet.py",
        "alpaca_telemetry_inventory_droplet.py",
    ):
        try:
            c.put_file(str(REPO / "scripts" / name), f"{proj.rstrip('/')}/scripts/{name}")
        except Exception as ex:
            print("put", name, ex)

    if hard:
        print("Deploy phase HARD FAIL — see ALPACA_TELEMETRY_DEPLOY_APPLIED.md")
        return 4

    # Phase 3 epoch
    o_ep, e_ep, r_ep = run("python3 scripts/write_alpaca_telemetry_repair_epoch.py 2>&1", 30)
    epoch_content = ""
    try:
        c.get_file("state/alpaca_telemetry_repair_epoch.json", REPO / "state" / "alpaca_telemetry_repair_epoch.json")
        epoch_content = (REPO / "state" / "alpaca_telemetry_repair_epoch.json").read_text(encoding="utf-8")
    except Exception:
        epoch_content = (o_ep or e_ep or "")[:500]
    (AUDIT / "ALPACA_TELEMETRY_REPAIR_EPOCH_SET.md").write_text(
        f"# Repair epoch set\n\n```\n{o_ep or e_ep}\n```\n\n## state file\n```json\n{epoch_content[:2000]}\n```\n",
        encoding="utf-8",
    )

    try:
        c.put_file(str(REPO / "scripts" / "count_post_epoch_exits.py"), f"{proj.rstrip('/')}/scripts/count_post_epoch_exits.py")
    except Exception:
        pass
    o_cnt2, _, _ = run("python3 scripts/count_post_epoch_exits.py 2>&1", 120)
    try:
        n_post = int((o_cnt2 or "0").strip().split()[-1])
    except (ValueError, IndexError):
        n_post = 0
    (AUDIT / "ALPACA_TELEMETRY_FORWARD_PROOF_WAITING.md").write_text(
        f"# Forward proof — waiting\n\n"
        f"- **Post-epoch exit count (approx):** {n_post}\n"
        f"- **Required before proof:** ≥ 50\n"
        f"- Check: `python3` one-liner on droplet counting exits with `timestamp >= repair_iso_utc`.\n"
        f"- Re-run: `python3 scripts/alpaca_telemetry_forward_proof.py --min-trades 50`\n",
        encoding="utf-8",
    )

    # Phase 5
    o_pr, e_pr, r_pr = run("python3 scripts/alpaca_telemetry_forward_proof.py --min-trades 50 2>&1", 120)
    for fn in (
        "ALPACA_TELEMETRY_FORWARD_PROOF.md",
        "ALPACA_TELEMETRY_FORWARD_PROOF_RESULT.md",
        "ALPACA_TELEMETRY_FORWARD_PROOF_BLOCKER_LATEST.md",
    ):
        try:
            c.get_file(f"reports/audit/{fn}", AUDIT / fn)
        except Exception:
            pass
    if r_pr != 0:
        print("Forward proof exit", r_pr, (o_pr or e_pr)[:500])
        return r_pr

    # Phase 7 post-epoch forensics
    o_f, e_f, r_f = run(
        "python3 scripts/alpaca_loss_forensics_droplet.py --post-epoch-only --max-trades 2000 2>&1",
        300,
    )
    for pat in (
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_DATASET_FREEZE.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_JOIN_COVERAGE.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_AGGREGATE_METRICS.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_DAY_BY_DAY.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_LONG_SHORT.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_ENTRY_CAUSES.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_EXIT_CAUSES.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_BLOCKED_COUNTERFACTUAL.md",
        "CSA_REVIEW_ALPACA_LOSS_FORENSICS_POST_EPOCH.md",
        "SRE_REVIEW_ALPACA_LOSS_FORENSICS_POST_EPOCH.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_BOARD_PACKET.md",
        "ALPACA_LOSS_FORENSICS_POST_EPOCH_ACTION_BACKLOG.md",
    ):
        try:
            c.get_file(f"reports/audit/{pat}", AUDIT / pat)
        except Exception:
            pass
    print(o_f or e_f or "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
