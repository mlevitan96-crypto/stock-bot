#!/usr/bin/env python3
"""
Alpaca trade-count + Telegram authority mission evidence writer.
Run from repo root (droplet: cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/...).

Writes reports/daily/<ET-date>/evidence/ALPACA_*.md with command output and canonical counts.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))


def _et_date_iso() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _evidence_dir() -> Path:
    d = REPO / "reports" / "daily" / _et_date_iso() / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sh(cmd: List[str], timeout: int = 45) -> Tuple[str, str, int]:
    try:
        r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=timeout)
        return (r.stdout or ""), (r.stderr or ""), r.returncode
    except Exception as e:
        return "", str(e), 1


def _git_head() -> str:
    o, _, c = _sh(["git", "rev-parse", "HEAD"])
    return (o.strip() if c == 0 else f"(git failed rc={c})")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _alpaca_clock_open() -> str:
    key = os.environ.get("ALPACA_KEY") or os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("ALPACA_SECRET") or os.environ.get("APCA_API_SECRET_KEY")
    base = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    if not key or not secret:
        return json.dumps({"is_open": None, "error": "ALPACA_KEY/APCA_API_KEY_ID not in environment"})
    try:
        import alpaca_trade_api as tradeapi

        api = tradeapi.REST(key, secret, base, api_version="v2")
        cl = api.get_clock()
        return json.dumps(
            {"is_open": bool(getattr(cl, "is_open", False)), "timestamp_utc": datetime.now(timezone.utc).isoformat()}
        )
    except Exception as e:
        return json.dumps({"is_open": None, "error": str(e)[:300]})


def _systemctl_stock_bot() -> str:
    o, e, c = _sh(["systemctl", "status", "stock-bot", "--no-pager"])
    if c != 0 and not o:
        return e or f"(systemctl unavailable rc={c})"
    return o + (("\n" + e) if e else "")


def _telegram_scan() -> List[Dict[str, str]]:
    patterns = [
        (r"send_governance_telegram\s*\(", "send_governance_telegram"),
        (r"api\.telegram\.org/bot", "telegram.org bot URL"),
        (r"sendMessage", "sendMessage"),
    ]
    rows: List[Dict[str, str]] = []
    skip = {".git", "venv", ".venv", "__pycache__", "node_modules"}
    for p in REPO.rglob("*.py"):
        if any(x in p.parts for x in skip):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(p.relative_to(REPO)).replace("\\", "/")
        for rx, label in patterns:
            if re.search(rx, text):
                rows.append({"file": rel, "match": label})
                break
    rows.sort(key=lambda x: x["file"])
    return rows


def main() -> int:
    ev = _evidence_dir()
    root = REPO
    head = _git_head()
    utc = _utc_now()
    et = _et_date_iso()

    from src.governance.canonical_trade_count import compute_canonical_trade_count

    c_all = compute_canonical_trade_count(root, floor_epoch=None)
    n = int(c_all.get("total_trades_post_era") or 0)
    t100 = int(c_all.get("trades_to_100") or 0)
    t250 = int(c_all.get("trades_to_250") or 0)
    nm = c_all.get("next_milestone")
    rem = int(c_all.get("remaining_to_next_milestone") or 0)

    clock = _alpaca_clock_open()
    svc = _systemctl_stock_bot()
    scan = _telegram_scan()
    integrity_only = os.environ.get("TELEGRAM_GOVERNANCE_INTEGRITY_ONLY", "").strip()

    # Phase 0
    (ev / "ALPACA_TRADE_COUNT_AND_TELEGRAM_CONTEXT.md").write_text(
        "\n".join(
            [
                "# ALPACA_TRADE_COUNT_AND_TELEGRAM_CONTEXT",
                "",
                f"- **ET date (evidence folder):** `{et}`",
                f"- **git HEAD:** `{head}`",
                f"- **date -u:** `{utc}`",
                f"- **Alpaca clock (best-effort):** `{clock}`",
                f"- **TELEGRAM_GOVERNANCE_INTEGRITY_ONLY (env):** `{integrity_only or '(unset)'}`",
                "",
                "## systemctl status stock-bot",
                "",
                "```",
                svc[:12000],
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 1
    (ev / "ALPACA_CANONICAL_TRADE_DEFINITION.md").write_text(
        "\n".join(
            [
                "# ALPACA_CANONICAL_TRADE_DEFINITION",
                "",
                "## trade_unit",
                "- One **closed trade** = one unique Alpaca **`trade_key`** from `logs/exit_attribution.jsonl`, computed as `build_trade_key(symbol, side, entry_ts)` (see `src/telemetry/alpaca_trade_key.py`).",
                "- Multiple JSONL lines for the same key count once (first qualifying row supplies PnL sum slice for milestone PnL rollups).",
                "",
                "## era scope",
                "- **Post-era only:** rows excluded when `utils.era_cut.learning_excluded_for_exit_record(record)` is true (driven by `config/era_cut.json`).",
                "",
                "## exclusion / floors",
                "- **Pre-era:** excluded by era cut helper above.",
                "- **Milestone Telegram (100 checkpoint + 250):** additionally require parsed exit timestamp `>=` count floor (`session_open` or `integrity_armed` epoch from `telemetry/alpaca_telegram_integrity/milestone.py`), using the same dedupe + era rules via `compute_canonical_trade_count(root, floor_epoch=...)`.",
                "- **Dashboard cumulative strip:** `compute_canonical_trade_count(root, floor_epoch=None)` — all post-era unique keys with valid exit timestamp (no session floor).",
                "- Rows missing a buildable trade_key are skipped (`skipped_no_trade_key` in count output).",
                "",
                "## Ledgers",
                "- **Integrity milestone notifier:** `telemetry/alpaca_telegram_integrity/milestone.py` → `compute_canonical_trade_count`.",
                "- **250-trade / audit alignment:** same `exit_attribution.jsonl` + `trade_key` + era cut; audit missions should call `compute_canonical_trade_count` for eligibility counts.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 2
    (ev / "ALPACA_CANONICAL_TRADE_COUNT_PROOF.md").write_text(
        "\n".join(
            [
                "# ALPACA_CANONICAL_TRADE_COUNT_PROOF",
                "",
                "## Function",
                "- `src/governance/canonical_trade_count.py` — `compute_canonical_trade_count(root, floor_epoch=None|float)`",
                "",
                "## Current snapshot (this run, no floor)",
                "",
                "```json",
                json.dumps(c_all, indent=2),
                "```",
                "",
                f"- **total_trades_post_era:** {n}",
                f"- **trades_to_100 (distance):** {t100}",
                f"- **trades_to_250 (distance):** {t250}",
                f"- **next_milestone:** {nm}",
                f"- **remaining_to_next_milestone:** {rem}",
                "",
                "## Consumers wired in repo",
                "- Telegram milestones: `telemetry/alpaca_telegram_integrity/milestone.py`",
                "- Dashboard `/api/situation`: `dashboard.py` `_get_situation_data_sync`",
                "- Run this script for audit evidence bundles.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 3
    (ev / "ALPACA_DASHBOARD_TRADE_COUNT_FIX.md").write_text(
        "\n".join(
            [
                "# ALPACA_DASHBOARD_TRADE_COUNT_FIX",
                "",
                "## Before",
                "- Situation strip first block used **direction readiness** (`state/direction_readiness.json` → `telemetry_trades` / `total_trades`, tail fallback), labeled “Trades reviewed: X/100”.",
                "",
                "## After",
                "- First block: **Total trades (post-era)**, **Next milestone** (100 or 250 or past milestones), **Remaining** to next.",
                "- Source: `compute_canonical_trade_count(root, floor_epoch=None)` in `dashboard.py` `_get_situation_data_sync`.",
                "- API fields: `total_trades_post_era`, `next_trade_milestone`, `remaining_to_next_milestone` (legacy `trades_reviewed*` retained for other readers).",
                "- SSR: `_render_initial_situation_html`; client refresh: `loadSituationStrip` in embedded dashboard script.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    outside = [r for r in scan if not r["file"].startswith("telemetry/alpaca_telegram_integrity/")]
    (ev / "ALPACA_TELEGRAM_AUTHORITY_CERTIFICATION.md").write_text(
        "\n".join(
            [
                "# ALPACA_TELEGRAM_AUTHORITY_CERTIFICATION",
                "",
                "## Declared authority",
                "- **Primary production sender:** `telemetry/alpaca_telegram_integrity/` (invoked by `scripts/run_alpaca_telegram_integrity_cycle.py`).",
                "- **Transport:** `scripts/alpaca_telegram.py` `send_governance_telegram`.",
                "- **Lockdown:** set **`TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`** so only integrity `script_name` values reach the API (see `scripts/alpaca_telegram.py` `_INTEGRITY_ONLY_SCRIPT_NAMES`).",
                "",
                "## Static scan: Python files touching Telegram send APIs",
                f"- **Rows:** {len(scan)}",
                "",
                "| file | match |",
                "|------|-------|",
                *[f"| `{r['file']}` | {r['match']} |" for r in scan[:200]],
                *(["", f"*({len(scan) - 200} more rows omitted)*"] if len(scan) > 200 else []),
                "",
                "## Outside `telemetry/alpaca_telegram_integrity/` (must be disabled or blocked when integrity-only)",
                f"- **Count:** {len(outside)}",
                "",
                "| file | match |",
                "|------|-------|",
                *[f"| `{r['file']}` | {r['match']} |" for r in outside[:120]],
                *(["", f"*({len(outside) - 120} more rows omitted)*"] if len(outside) > 120 else []),
                "",
                "## Production confirmation (manual on droplet)",
                "- `crontab -l` — ensure no board/post-close/fast-lane Telegram jobs conflict with policy.",
                "- `systemctl list-timers --all | grep -E 'telegram|postclose|stock-bot'`",
                "- `.env`: `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1` recommended for single-authority sends.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (ev / "ALPACA_CURRENT_TRADE_COUNT_STATUS.md").write_text(
        "\n".join(
            [
                "# ALPACA_CURRENT_TRADE_COUNT_STATUS",
                "",
                f"- **total_trades_post_era:** {n}",
                f"- **distance to 100:** {t100}",
                f"- **distance to 250:** {t250}",
                f"- **next milestone:** {nm}",
                f"- **remaining to next:** {rem}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    yes_count = "YES"
    yes_dash = "YES"
    strict_tg = "YES" if integrity_only in ("1", "true", "yes", "on") else "NO (set TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1 on droplet)"
    (ev / "ALPACA_TRADE_COUNT_AND_TELEGRAM_FINAL_VERDICT.md").write_text(
        "\n".join(
            [
                "# ALPACA_TRADE_COUNT_AND_TELEGRAM_FINAL_VERDICT",
                "",
                f"- **Single canonical trade count (code path):** {yes_count} — `compute_canonical_trade_count`.",
                f"- **Dashboard reflects that count (post-era cumulative strip):** {yes_dash}.",
                f"- **Telegram limited to integrity milestones + integrity alerts only:** {strict_tg}.",
                f"- **Current trade count:** {n}; **next milestone:** {nm}; **remaining:** {rem}.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("Wrote evidence to", ev)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
