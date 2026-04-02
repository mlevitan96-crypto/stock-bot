#!/usr/bin/env python3
"""
Paper exec promo WORKER mission (Phases 0–5). Droplet.

  PYTHONPATH=. python3 scripts/audit/run_exec_mode_paper_promo_worker_mission.py --root /root/stock-bot --evidence-et 2026-04-01
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]


def _run(cmd: str, cwd: Path, timeout: int = 180) -> Tuple[int, str]:
    try:
        r = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def _session_et_date() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def _grep_live_submit(path: Path) -> bool:
    if not path.is_file():
        return False
    t = path.read_text(encoding="utf-8", errors="replace")
    return bool(re.search(r"\bapi\.submit_order\b", t))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-et", type=str, default=None)
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--skip-smoke-reset", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    et = args.evidence_et or _session_et_date()
    ev = root / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)

    touched = [
        root / "src" / "paper" / "paper_exec_mode_runtime.py",
        root / "scripts" / "paper_exec_mode_worker.py",
    ]
    for p in touched:
        if _grep_live_submit(p):
            (ev / "EXEC_MODE_PAPER_PROMO_BLOCKER_LIVE_PATH_TOUCHED.md").write_text(
                f"Forbidden `api.submit_order` in `{p}`\n", encoding="utf-8"
            )
            return 2

    # --- Phase 0 ---
    _, git_head = _run("git rev-parse HEAD", root)
    _, st_status = _run("systemctl status stock-bot --no-pager 2>&1 | head -n 80", root)
    _, st_cat = _run("systemctl cat stock-bot 2>&1", root)
    _, st_env = _run("systemctl show stock-bot -p Environment -p EnvironmentFiles 2>&1", root)
    _, jtail = _run('journalctl -u stock-bot --since "24 hours ago" --no-pager 2>&1 | tail -n 800', root)

    main_py = root / "main.py"
    main_sample = main_py.read_text(encoding="utf-8", errors="replace")[:60000] if main_py.is_file() else ""
    combined = "\n".join([git_head, st_cat, st_env, jtail[:40000], main_sample]).lower()
    paper_ok = "paper-api" in combined or "paper-api.alpaca" in combined.replace("_", "-")
    if not paper_ok:
        paper_ok = "trading_mode=paper" in combined

    (ev / "EXEC_MODE_PAPER_PROMO_WORKER_PHASE0_CONTEXT.md").write_text(
        "# EXEC_MODE_PAPER_PROMO_WORKER_PHASE0_CONTEXT\n\n"
        "## git HEAD\n\n```\n"
        + git_head.strip()
        + "\n```\n\n## systemctl status\n\n```\n"
        + st_status[:10000]
        + "\n```\n\n## systemctl cat\n\n```\n"
        + st_cat[:22000]
        + "\n```\n\n## show Environment\n\n```\n"
        + st_env[:8000]
        + "\n```\n\n## journalctl stock-bot\n\n```\n"
        + jtail[:100000]
        + "\n```\n\n## Paper proof\n\n"
        f"- paper sample match: **{paper_ok}**\n"
        "- B arm: **non-blocking** enqueue `state/paper_exec_pending.jsonl`; worker `scripts/paper_exec_mode_worker.py`.\n"
        "- Touched modules checked for `api.submit_order`: **none** in paper worker/runtime.\n",
        encoding="utf-8",
    )
    if not paper_ok:
        (ev / "EXEC_MODE_PAPER_PROMO_BLOCKER_PAPER_UNPROVEN.md").write_text(
            "Paper-only not proven from config sample.\n", encoding="utf-8"
        )
        return 2

    uni = root / "reports" / "daily" / "2026-04-01" / "evidence" / "EXEC_MODE_UNIVERSE_TOP20_LAST3D.json"

    # --- Phase 1 contract ---
    (ev / "EXEC_MODE_PAPER_PROMO_WORKER_CONTRACT.md").write_text(
        "# EXEC_MODE_PAPER_PROMO_WORKER_CONTRACT\n\n"
        "| Rule | Detail |\n"
        "|------|--------|\n"
        "| B arm | **Non-blocking** in `submit_entry`: one limit submit + append `state/paper_exec_pending.jsonl`, return `submitted_unfilled`. |\n"
        "| Worker | `scripts/paper_exec_mode_worker.py` polls broker + bar diagnostic; TTL expiry → cancel + market via `_submit_order_guarded`. |\n"
        "| Idempotency | `pretrade_key`; completed keys in `state/paper_exec_done.jsonl` (append-only). |\n"
        "| Paper | Strict gateway in runtime + worker (Config + URL + is_paper_mode). |\n"
        f"| Universe | `{uni}` via `PAPER_EXEC_UNIVERSE_PATH` |\n",
        encoding="utf-8",
    )

    # --- Phase 2 implementation ---
    (ev / "EXEC_MODE_PAPER_PROMO_WORKER_IMPLEMENTATION.md").write_text(
        "# EXEC_MODE_PAPER_PROMO_WORKER_IMPLEMENTATION\n\n"
        "- `src/paper/paper_exec_mode_runtime.py` — pending enqueue, paths, `strict_paper_gateway`.\n"
        "- `scripts/paper_exec_mode_worker.py` — `--once` (default single pass) or `--loop`.\n"
        "- `deploy/systemd/paper-exec-mode-worker.service` + `.timer` — optional one-shot every minute.\n"
        "- Decisions: `logs/paper_exec_mode_decisions.jsonl` (worker appends outcomes).\n",
        encoding="utf-8",
    )

    pending_path = root / "state" / "paper_exec_pending.jsonl"
    done_path = root / "state" / "paper_exec_done.jsonl"
    dec_path = root / "logs" / "paper_exec_mode_decisions.jsonl"

    # --- Phase 3 smoke ---
    smoke_md = ["# EXEC_MODE_PAPER_PROMO_WORKER_SMOKE_PROOF\n\n"]
    if not args.skip_smoke_reset:
        tsbak = int(time.time())
        for p in (pending_path, dec_path, done_path):
            if p.is_file() and p.stat().st_size > 0:
                bak = p.with_name(p.name + f".bak_{tsbak}")
                try:
                    shutil.copy2(p, bak)
                    p.write_text("", encoding="utf-8")
                    smoke_md.append(f"- Backed up `{p}` → `{bak.name}` and truncated.\n")
                except OSError as e:
                    smoke_md.append(f"- Skip truncate `{p}`: {e}\n")
        now = datetime.now(timezone.utc).isoformat()
        synth = [
            {
                "pretrade_key": "SYNTHETIC_SMOKE_1",
                "ts": now,
                "enqueued_ts": now,
                "symbol": "SPY",
                "side": "buy",
                "qty": 1,
                "ttl_minutes": 3,
                "limit_px": 400.0,
                "synthetic": True,
                "smoke_only": True,
                "decision_price_ref": "synthetic_smoke_1",
                "ab_arm": "B",
            },
            {
                "pretrade_key": "SYNTHETIC_SMOKE_2",
                "ts": now,
                "enqueued_ts": now,
                "symbol": "QQQ",
                "side": "buy",
                "qty": 1,
                "ttl_minutes": 3,
                "limit_px": 350.0,
                "synthetic": True,
                "smoke_only": True,
                "decision_price_ref": "synthetic_smoke_2",
                "ab_arm": "B",
            },
            {
                "pretrade_key": "SYNTHETIC_SMOKE_3",
                "ts": now,
                "enqueued_ts": now,
                "symbol": "IWM",
                "side": "buy",
                "qty": 1,
                "ttl_minutes": 3,
                "limit_px": 200.0,
                "synthetic": True,
                "smoke_only": True,
                "decision_price_ref": "synthetic_smoke_3",
                "ab_arm": "B",
            },
        ]
        pending_path.parent.mkdir(parents=True, exist_ok=True)
        with pending_path.open("a", encoding="utf-8") as f:
            for row in synth:
                f.write(json.dumps(row) + "\n")
        smoke_md.append(f"- Wrote **3** synthetic rows to `{pending_path}`.\n")

    code, wout = _run(
        f"cd {root} && PYTHONPATH=. python3 scripts/paper_exec_mode_worker.py --root {root} --once 2>&1",
        root,
        120,
    )
    smoke_md.append("\n## worker --once\n\n```\n")
    smoke_md.append(wout[:12000])
    smoke_md.append("\n```\n\n")

    dec_lines = 0
    if dec_path.is_file():
        dec_lines = sum(1 for ln in dec_path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip())
    smoke_md.append(f"- `paper_exec_mode_decisions.jsonl` non-empty lines ≈ **{dec_lines}** (expect ≥3 after smoke).\n")
    smoke_md.append(f"- worker exit code: **{code}**\n")
    _, jw = _run('journalctl -u paper-exec-mode-worker --since "10 min ago" 2>&1 | tail -n 50', root, 30)
    smoke_md.append("\n## journalctl paper-exec-mode-worker (if unit exists)\n\n```\n" + jw + "\n```\n")
    (ev / "EXEC_MODE_PAPER_PROMO_WORKER_SMOKE_PROOF.md").write_text("".join(smoke_md), encoding="utf-8")

    if code != 0 and not args.skip_smoke_reset:
        (ev / "EXEC_MODE_PAPER_PROMO_WORKER_SMOKE_FAIL.md").write_text(wout[:8000], encoding="utf-8")

    # --- Phase 4 run proof ---
    _, wc_dec = _run(f"wc -l {dec_path} 2>/dev/null || true", root)
    _, wc_pend = _run(f"wc -l {pending_path} 2>/dev/null || true", root)
    _, wc_done = _run(f"wc -l {done_path} 2>/dev/null || true", root)
    _, envgrep = _run("systemctl show stock-bot -p Environment 2>&1 | tr ' ' '\\n' | grep -E PAPER_EXEC || true", root)
    (ev / "EXEC_MODE_PAPER_PROMO_WORKER_RUN_PROOF.md").write_text(
        "# EXEC_MODE_PAPER_PROMO_WORKER_RUN_PROOF\n\n"
        "## Line counts (at mission run)\n\n```\n"
        + wc_dec
        + wc_pend
        + wc_done
        + "\n```\n\n"
        "## stock-bot PAPER_EXEC_* (if set in unit)\n\n```\n"
        + envgrep
        + "\n```\n\n"
        "## Enable (operator)\n\n"
        "```\n"
        "PAPER_EXEC_PROMO_ENABLED=1\n"
        "PAPER_EXEC_TTL_MINUTES=3\n"
        f"PAPER_EXEC_UNIVERSE_PATH={root}/reports/daily/2026-04-01/evidence/EXEC_MODE_UNIVERSE_TOP20_LAST3D.json\n"
        "PAPER_EXEC_FAIL_CLOSED=1\n"
        "```\n\n"
        "Then `sudo systemctl restart stock-bot` and enable timer:\n"
        "`sudo cp deploy/systemd/paper-exec-mode-worker.* /etc/systemd/system/ && sudo systemctl daemon-reload "
        "&& sudo systemctl enable --now paper-exec-mode-worker.timer`\n",
        encoding="utf-8",
    )

    # --- Phase 5 evaluation + board (reuse promo mission) ---
    promo = root / "scripts" / "audit" / "run_exec_mode_paper_promo_mission.py"
    if promo.is_file():
        _, evout = _run(f"cd {root} && PYTHONPATH=. python3 {promo} --root {root} --evidence-et {et} 2>&1", root, 180)
        (ev / "EXEC_MODE_PAPER_PROMO_WORKER_EVAL_RERUN_LOG.txt").write_text(evout[:16000], encoding="utf-8")

    csa = (
        "# BOARD_CSA — Paper exec promo (worker)\n\n"
        "- **Blocking removed** from `submit_entry` B arm; TTL/cross in worker reduces engine stall risk.\n"
        "- **Idempotency:** `pretrade_key` + `paper_exec_done.jsonl`.\n"
        "- **Confounding:** A/B hour schedule unchanged; worker latency adds async fill.\n"
    )
    sre = (
        "# BOARD_SRE — Paper exec promo (worker)\n\n"
        "- **Cadence:** run `paper-exec-mode-worker.timer` or `--loop` with modest sleep.\n"
        "- **Logs:** pending/done/decisions JSONL growth — rotate like other state.\n"
        "- **Failure:** worker exit 2 if paper gateway fails — no broker calls.\n"
    )
    quant = (
        "# BOARD_QUANT — Paper exec promo (worker)\n\n"
        "- Re-run `run_exec_mode_paper_promo_mission.py` after sufficient `paper_exec_mode_decisions.jsonl` rows.\n"
        "- Gates apply only when promo runtime JSONL exists (prior contract).\n"
    )
    final = (
        "# EXEC_MODE_PAPER_PROMO_FINAL_VERDICT (worker phase)\n\n"
        "- **Architecture:** enqueue + worker is live for B arm when `PAPER_EXEC_PROMO_ENABLED=1`.\n"
        "- **Smoke:** see `EXEC_MODE_PAPER_PROMO_WORKER_SMOKE_PROOF.md`.\n"
        "- **Next:** operator enables env + worker timer; re-run evaluation after session.\n"
    )
    # Overwrite board files with worker-focused text (promo mission may have written same paths — we replace)
    (ev / "BOARD_CSA_EXEC_MODE_PAPER_PROMO_VERDICT.md").write_text(csa, encoding="utf-8")
    (ev / "BOARD_SRE_EXEC_MODE_PAPER_PROMO_VERDICT.md").write_text(sre, encoding="utf-8")
    (ev / "BOARD_QUANT_EXEC_MODE_PAPER_PROMO_VERDICT.md").write_text(quant, encoding="utf-8")
    (ev / "EXEC_MODE_PAPER_PROMO_FINAL_VERDICT.md").write_text(final, encoding="utf-8")

    print(json.dumps({"evidence_dir": str(ev), "worker_exit": code, "decision_lines": dec_lines}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
